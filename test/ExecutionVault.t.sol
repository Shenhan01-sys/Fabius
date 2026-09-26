// Uji jalur EKSEKUSI: apakah harga masuk benar-benar datang dari pool, dan apakah pagar plafon
// itu nyata atau cuma komentar.
//
// Kenapa token di sini ERC20 lokal, bukan `X402DemoToken`: token itu ber-ERC20Permit, dan di
// OpenZeppelin 5 jalur itu menyeret `utils/Bytes.sol` yang memakai opcode `mcopy` (Cancun).
// Mengimpornya ke test akan memaksa SEMUA build proyek ikut Cancun - padahal DecisionAnchor sengaja
// ditarget shanghai. Jadi uji eksekusi memakai ERC20 polos; yang kami uji di sini adalah vault dan
// pool-nya, bukan kemampuan permit.
//
// Empat hal yang diuji lebih dulu, karena itu yang membedakan "terdagangkan" dari "tercatat":
//   1. harga masuk TIDAK SAMA dengan harga yang kami klaim - selisihnya fee + dampak harga, dan
//      kami melaporkannya apa adanya;
//   2. menutup posisi untung memang menambah quote vault, menutup posisi rugi memang menguranginya;
//   3. plafon menolak meskipun pemilik menaikkan cap (HARD_CEILING memotong di kontrak);
//   4. posisi tidak bisa lahir tanpa hash keputusan yang di-anchor.
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {DemoPair} from "../contracts/DemoPair.sol";
import {ExecutionVault} from "../contracts/ExecutionVault.sol";

contract PlainToken is ERC20 {
    constructor(string memory n, string memory s) ERC20(n, s) {}

    function decimals() public pure override returns (uint8) {
        return 6;
    }

    function give(address to, uint256 v) external {
        _mint(to, v);
    }
}

contract ExecutionVaultTest is Test {
    PlainToken internal base;
    PlainToken internal usd;
    DemoPair internal pair;
    ExecutionVault internal vault;

    address internal agent = address(0xA0);
    address internal owner = address(0x01);
    bytes32 internal DH = bytes32(uint256(0x11));
    bytes32 internal SH = bytes32(uint256(0x22));

    uint256 internal constant Q = 1e6;       // 1 unit quote (6 desimal)
    uint256 internal constant E = 1e6;       // 1 unit base (desimal token = 6)

    function setUp() public {
        base = new PlainToken("Fabius Demo Asset", "FBAS");
        usd = new PlainToken("Fabius Demo Quote", "FUSD");
        pair = new DemoPair(address(base), address(usd), owner);

        // likuiditas awal: 100.000 base vs 200.000 quote -> spot 2 quote per token
        base.give(address(pair), 100_000 * E);
        usd.give(address(pair), 200_000 * Q);
        pair.bootstrap();

        vault = new ExecutionVault(address(usd), agent, owner);
        // `setVenue` hanya milik owner, jadi setUp harus menyamar. Pagar yang diuji ikut
        // menyingkap setUp yang salah - kegagalan ini lebih murah daripada lolos diam-diam.
        vm.prank(owner);
        vault.setVenue(address(base), address(pair));
        vm.prank(owner);
        vault.setCaps(5 * Q, 1 * Q);                       // $5/hari, $1/posisi

        base.give(address(vault), 100 * E);                // inventaris short
        usd.give(address(vault), 500 * Q);                 // amunisi long
    }

    function quoteOfVault() internal view returns (uint256) {
        return usd.balanceOf(address(vault));
    }

    function entryOf() internal view returns (bool shortSide, uint256 assetQty, uint256 qIn,
                                               uint256 px18, bytes32 d, bytes32 s) {
        return vault.openPositionOf(address(base));
    }

    // ---------------------------------------------------------------- harga dari pool
    function test_harga_masuk_lebih_buruk_dari_spot() public {
        uint256 spot = pair.spotPrice();
        vm.prank(agent);
        vault.openLong(address(base), 1 * Q, DH, SH);
        (, , , uint256 px, , ) = entryOf();
        assertGt(px, spot, "entry harus di atas spot - ini bukti fee + dampak nyata, bukan angka kami");
    }

    function test_dampak_membesar_dengan_ukuran() public {
        vm.startPrank(agent);
        vault.openLong(address(base), 100_000, DH, SH);    // $0,10
        (, , , uint256 pxSmall, , ) = entryOf();
        vault.close(address(base));
        vm.stopPrank();

        // hari baru: plafon harian sengaja MEMBAWA jejak pemakaian, jadi tanpa `warp` uji ini akan
        // gagal karena budget $0,1 yang tadi - bukan karena dampaknya. Itu perilaku yang benar,
        // dan tes yang tidak menyadari hal itu adalah tes yang akan lolos di keadaan salah.
        vm.warp(block.timestamp + 1 days);
        vm.prank(owner);
        vault.setCaps(10 * Q, 10 * Q);
        vm.startPrank(agent);
        vault.openLong(address(base), 9 * Q, DH, SH);       // $9 = 90x ukuran pertama
        (, , , uint256 pxBig, , ) = entryOf();
        vm.stopPrank();
        assertGt(pxBig, pxSmall, "posisi lebih besar harus membayar harga lebih buruk");
    }

    /// @dev Ini jawaban jujur untuk pertanyaan "$5 layak tidak?". Kami TIDAK menggerakkan pasar
    /// sama sekali di sini: hanya masuk lalu keluar. Kalau hasilnya negatif seukuran ~2x fee,
    /// berarti biaya tetap itu yang harus dikalahkan sinyal lebih dulu - bukan angka yang bisa
    /// dikecilkan di laporan.
    function test_round_trip_biaya_tetap_terasa_sekitar_dua_kali_fee() public {
        vm.prank(agent);
        vault.openLong(address(base), 1 * Q, DH, SH);
        (, , uint256 qIn, , , ) = entryOf();
        vm.prank(agent);
        vault.close(address(base));
        int256 realized = vault.realizedQuote();
        // 1 - (1-f)^2 dengan f=0,003 -> ~0,599% dari notional
        int256 mag = realized >= 0 ? realized : -realized;
        uint256 bps = uint256(mag) * 10_000 / qIn;
        assertLt(realized, 0, "masuk-keluar tanpa gerak pasar harus rugi: itu ongkos, bukan nasib");
        // 0,6% = 60 bps. Assertion pertamaku tertulis ">400 bps" dan TERBUKTI salah: alatnya
        // mengukur 59 bps, sesuai kurva. Yang perlu dikoreksi di sini adalah tesnya, bukan
        // angkanya - dan urutan itu penting untuk ditulis, karena godaannya selalu sama.
        assertGt(bps, 40, "biaya round-trip harus terlihat (>=40 bps)");
        assertLt(bps, 90, "dan tidak boleh meleset jauh dari ~60 bps yang dijanjikan kurva");
        emit log_named_uint("BIAYA ROUND-TRIP TERUKUR (bps) untuk posisi 1 unit quote", bps);
    }

    /// @dev Bug yang ditemukan tes, dipaku supaya tidak kembali: reset plafon harian harus terjadi
    /// SEBELUM pemeriksaan budget. Versi pertama menolak posisi pertama di hari baru karena
    /// `spentToday` masih membawa jejak kemarin.
    function test_hari_baru_mereset_plafon_sebelum_memeriksanya() public {
        vm.startPrank(agent);
        vault.openLong(address(base), 1 * Q, DH, SH);
        vault.close(address(base));
        vm.stopPrank();
        assertGt(vault.spentToday(), 0, "budget hari ini harus terpakai");

        vm.warp(block.timestamp + 1 days);
        vm.prank(agent);
        vault.openLong(address(base), 1 * Q, DH, SH);        // harus BOLEH: hari baru
        assertLt(vault.spentToday(), 2 * Q, "spentToday harus mulai dari nol lagi, bukan menumpuk");
    }

    // ---------------------------------------------------------------- ekonomi dua arah
    function test_long_untung_saat_harga_naik() public {
        vm.prank(agent);
        vault.openLong(address(base), 1 * Q, DH, SH);
        uint256 q0 = quoteOfVault();

        // Pasar digerakkan DARI LUAR vault. Besarnya bukan kosmetik: fee round-trip kami ~60 bps,
        // jadi menggerakkan harga 10 bps lalu menutup posisi memang harus rugi - dan rugi itulah
        // yang membuat `test_round_trip_...` di atas layak ada. Kami gerakkan cukup besar (2%)
        // supaya yang diuji di sini adalah ARAH yang benar, bukan ongkos.
        usd.give(address(this), 2_000 * Q);
        usd.approve(address(pair), 2_000 * Q);
        pair.swapBuy(2_000 * Q);

        vm.prank(agent);
        vault.close(address(base));
        assertGt(quoteOfVault(), q0, "long harus meregistrasi untung saat harga naik");
        assertGt(vault.realizedQuote(), 0);
    }

    function test_short_untung_saat_harga_turun() public {
        vm.prank(agent);
        // 0,4 token: `costOfBuy` memaket fee + dampak, jadi notional-nya sedikit DI ATAS
        // harga wajar - 0,5 token sudah ~1,01 unit quote dan menembus cap $1. Bukan kontraknya
        // yang keras kepala; ukuran itulah yang harus disesuaikan dengan notional, bukan sebaliknya.
        vault.openShort(address(base), 400_000, DH, SH);

        base.give(address(this), 5_000 * E);
        base.approve(address(pair), 5_000 * E);
        pair.swapSell(5_000 * E);                            // harga jatuh > biaya

        vm.prank(agent);
        vault.close(address(base));

        // Saldo quote BUKAN ukuran untung untuk short. Membuka short MENERIMA quote (saldo
        // menggelembung), menutup MEMBAYAR quote untuk membeli kembali - jadi saldo turun walau
        // posisinya untung. Assertion lama saya (`quoteOfVault() > q0`) salah konsep, bukan salah
        // angka: yang membukukan PnL adalah kontraknya, dan itu yang harus ditagihkan.
        assertGt(vault.realizedQuote(), 0, "short harus membukukan untung saat harga turun");
        assertEq(vault.closedCount(), 1);
        assertGe(base.balanceOf(address(vault)), 100 * E, "inventaris pulih setelah ditutup");
    }

    function test_rugi_boleh_negatif_dan_tidak_dibersihkan() public {
        vm.prank(agent);
        vault.openLong(address(base), 1 * Q, DH, SH);
        base.give(address(this), 5_000 * E);
        base.approve(address(pair), 5_000 * E);
        pair.swapSell(5_000 * E);                       // harga jatuh
        vm.prank(agent);
        vault.close(address(base));

        assertLt(vault.realizedQuote(), 0, "realized kumulatif harus boleh negatif");
        assertEq(vault.closedCount(), 1);
    }

    // ---------------------------------------------------------------- pagar yang nyata
    function test_bukan_agent_ditolak() public {
        vm.expectRevert(ExecutionVault.NotAgent.selector);
        vault.openLong(address(base), 1 * Q, DH, SH);
    }

    function test_tanpa_hash_keputusan_ditolak() public {
        vm.startPrank(agent);
        vm.expectRevert(ExecutionVault.NoAnchorHash.selector);
        vault.openLong(address(base), 1 * Q, bytes32(0), SH);
        vm.expectRevert(ExecutionVault.NoAnchorHash.selector);
        vault.openLong(address(base), 1 * Q, DH, bytes32(0));
        vm.stopPrank();
    }

    function test_hard_ceiling_memotong_cap_bukan_menolak_diam_diam() public {
        vm.prank(owner);
        vault.setCaps(1_000 * Q, 1_000 * Q);
        assertEq(vault.dailyCap(), 10 * Q, "HARD_CEILING harus memotong cap di kontrak");
        vm.startPrank(agent);
        vault.openLong(address(base), 9 * Q, DH, SH);
        vm.expectRevert(ExecutionVault.OverDailyCap.selector);
        vault.openLong(address(base), 9 * Q, DH, SH);
        vm.stopPrank();
    }

    function test_over_position_cap_ditolak() public {
        vm.prank(agent);
        vm.expectRevert(ExecutionVault.OverPositionCap.selector);
        vault.openLong(address(base), 2 * Q, DH, SH);          // maxPos = 1 * Q
    }

    function test_satu_posisi_per_aset() public {
        vm.startPrank(agent);
        vault.openLong(address(base), 1 * Q, DH, SH);
        vm.expectRevert(ExecutionVault.AlreadyOpen.selector);
        vault.openLong(address(base), 1 * Q, DH, SH);
        vm.stopPrank();
    }

    function test_short_tanpa_inventaris_ditolak() public {
        ExecutionVault fresh = new ExecutionVault(address(usd), agent, owner);
        vm.startPrank(owner);
        fresh.setVenue(address(base), address(pair));
        fresh.setCaps(5 * Q, 5 * Q);
        vm.stopPrank();
        vm.prank(agent);
        vm.expectRevert(ExecutionVault.NeedInventory.selector);
        fresh.openShort(address(base), 1 * E, DH, SH);
    }

    function test_kill_switch_menutup_pintu_masuk() public {
        vm.prank(owner);
        vault.setKillSwitch(true);
        vm.prank(agent);
        vm.expectRevert(ExecutionVault.KillSwitchOn.selector);
        vault.openLong(address(base), 1 * Q, DH, SH);
        vm.prank(owner);
        vault.setKillSwitch(false);
        vm.prank(agent);
        vault.openLong(address(base), 1 * Q, DH, SH);
    }

    function test_close_tanpa_posisi_ditolak() public {
        vm.prank(agent);
        vm.expectRevert(ExecutionVault.NotOpen.selector);
        vault.close(address(base));
    }

    function test_owner_tidak_punya_jalan_pintas_membuka_posisi() public {
        vm.prank(owner);
        vm.expectRevert(ExecutionVault.NotAgent.selector);
        vault.openLong(address(base), 1 * Q, DH, SH);
    }

    function test_aset_tanpa_venue_ditolak() public {
        PlainToken alien = new PlainToken("No Venue", "NOPE");
        vm.prank(agent);
        vm.expectRevert(ExecutionVault.NoVenue.selector);
        vault.openLong(address(alien), 1 * Q, DH, SH);
    }

    function test_event_mencatat_hash_keputusan() public {
        bytes32 d = bytes32(uint256(0xD0D0));
        bytes32 s = bytes32(uint256(0x5EED));
        vm.expectEmit(true, false, false, false, address(vault));
        emit ExecutionVault.Opened(address(base), false, 0, 0, 0, d, s);
        vm.prank(agent);
        vault.openLong(address(base), 1 * Q, d, s);
    }
}
