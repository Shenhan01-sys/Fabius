// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;

import {Test} from "forge-std/Test.sol";
import {ERC20} from "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {Clones} from "@openzeppelin/contracts/proxy/Clones.sol";
import {Math} from "@openzeppelin/contracts/utils/math/Math.sol";
import {ReentrancyGuard} from "@openzeppelin/contracts/utils/ReentrancyGuard.sol";
import {RevenueSplitter} from "../contracts/RevenueSplitter.sol";

/// Token uji biasa (seperti FAB: ERC-20 polos tanpa hook).
contract MockToken is ERC20 {
    constructor(string memory n) ERC20(n, n) {}

    function mint(address to, uint256 v) external {
        _mint(to, v);
    }

    /// Meniru rebase negatif / penyitaan oleh admin token: saldo splitter menyusut tanpa `release`.
    function burnFrom(address a, uint256 v) external {
        _burn(a, v);
    }
}

/// Fee-on-transfer: 1 % dari setiap transfer dibakar dan ditanggung PENERIMA (saldo pengirim turun persis `value`).
contract FeeToken is ERC20 {
    constructor() ERC20("FEE", "FEE") {}

    function mint(address to, uint256 v) external {
        _mint(to, v);
    }

    function _update(address from, address to, uint256 value) internal override {
        if (from != address(0) && to != address(0)) {
            uint256 fee = value / 100;
            super._update(from, address(0), fee);
            super._update(from, to, value - fee);
        } else {
            super._update(from, to, value);
        }
    }
}

/// Token jahat: saat splitter mengirim token ini, ia mencoba masuk lagi ke splitter (release / releaseIssuer / releaseFabius).
contract ReentrantToken is ERC20 {
    RevenueSplitter public target;
    uint8 public mode;
    bool public tried;
    bool public succeeded;
    bytes public reason;

    constructor() ERC20("JAHAT", "JAHAT") {}

    function mint(address to, uint256 v) external {
        _mint(to, v);
    }

    function arm(RevenueSplitter t, uint8 m) external {
        target = t;
        mode = m;
    }

    function _update(address from, address to, uint256 value) internal override {
        super._update(from, to, value);
        if (address(target) != address(0) && from == address(target) && !tried) {
            tried = true;
            if (mode == 0) {
                try target.release(IERC20(address(this))) {
                    succeeded = true;
                } catch (bytes memory e) {
                    reason = e;
                }
            } else if (mode == 1) {
                try target.releaseIssuer(IERC20(address(this))) {
                    succeeded = true;
                } catch (bytes memory e) {
                    reason = e;
                }
            } else {
                try target.releaseFabius(IERC20(address(this))) {
                    succeeded = true;
                } catch (bytes memory e) {
                    reason = e;
                }
            }
        }
    }
}

/// Pengganti BotRegistry untuk uji unit: memasang klon dengan bagian Fabius berapa pun dan menjawab `owner()` (= Fabius bagi splitter).
contract FakeRegistry {
    address public owner;
    address public immutable impl;

    constructor(address owner_) {
        owner = owner_;
        impl = address(new RevenueSplitter());
    }

    function setOwner(address o) external {
        owner = o;
    }

    function make(bytes32 botId, address issuer, address issuerPayee, address fabiusPayee, uint16 fabiusBps) external returns (RevenueSplitter s) {
        s = RevenueSplitter(Clones.clone(impl));
        s.initialize(botId, issuer, issuerPayee, fabiusPayee, fabiusBps);
    }
}

/// Yang diuji (P81, C-H): (1) pembagian PERSIS sama dengan `engine/economics.py` (vektor `tools/gen_splitter_vectors.py`, jumlah 0 .. 2^256-1);
/// (2) jumlah selalu sama dengan masukan, debu ke Fabius, release bertahap tidak kehilangan / menggandakan wei (fuzz); (3) bagian Fabius hanya
/// turun, hanya oleh Fabius; payout penerbit hanya oleh penerbit; tidak ada yang bisa menyita saldo; (4) banyak token terpisah; (5) token jahat
/// (re-entrancy), fee-on-transfer, saldo menyusut, BNB. Tidak ada test yang mengklaim sinyal bot itu laku - kontrak ini hanya membagi uang.
contract RevenueSplitterTest is Test {
    uint16 internal constant BPS = 10_000;
    bytes32 internal constant BOT = "X1-PENERBIT";

    address internal fabius = makeAddr("fabius-operator");
    address internal fabiusPayee = makeAddr("fabius-kas");
    address internal issuer = makeAddr("penerbit");
    address internal issuerPayee = makeAddr("penerbit-payout");
    address internal stranger = makeAddr("orang-luar");
    address internal buyer = makeAddr("pembeli");

    FakeRegistry internal reg;
    MockToken internal fab;
    MockToken internal usd;

    function setUp() public {
        reg = new FakeRegistry(fabius);
        fab = new MockToken("FAB");
        usd = new MockToken("USD");
    }

    function _make(uint16 fabiusBps) internal returns (RevenueSplitter) {
        return reg.make(BOT, issuer, issuerPayee, fabiusPayee, fabiusBps);
    }

    function _pay(MockToken t, RevenueSplitter s, uint256 v) internal {
        t.mint(buyer, v);
        vm.prank(buyer);
        t.transfer(address(s), v);
    }

    function _none() internal pure returns (IERC20[] memory) {
        return new IERC20[](0);
    }

    function _one(IERC20 t) internal pure returns (IERC20[] memory a) {
        a = new IERC20[](1);
        a[0] = t;
    }

    function _json() internal view returns (string memory) {
        return vm.readFile(string.concat(vm.projectRoot(), "/test/fixtures/splitter_vectors.json"));
    }

    // -------------------------------------------------- vektor lintas bahasa (engine/economics.py <-> kontrak)

    function test_vektor_split_engine_sama_dengan_kontrak() public {
        string memory j = _json();
        uint256[] memory amount = vm.parseJsonUintArray(j, ".split.amount");
        uint256[] memory ibps = vm.parseJsonUintArray(j, ".split.issuerBps");
        uint256[] memory wantI = vm.parseJsonUintArray(j, ".split.issuer");
        uint256[] memory wantF = vm.parseJsonUintArray(j, ".split.fabius");
        assertEq(amount.length, 98, "jumlah vektor split");
        for (uint256 i = 0; i < amount.length; i++) {
            RevenueSplitter s = _make(uint16(BPS - ibps[i]));
            deal(address(fab), address(s), amount[i]);                 // saldo langsung: jumlah raksasa tidak meluapkan totalSupply
            deal(address(fab), issuerPayee, 0);                         // payee dikosongkan per vektor (saldo 2^256-1 tidak menumpuk)
            deal(address(fab), fabiusPayee, 0);
            (uint256 toI, uint256 toF) = s.release(fab);
            assertEq(toI, wantI[i], "bagian penerbit == economics.split");
            assertEq(toF, wantF[i], "bagian Fabius == economics.split");
            assertEq(fab.balanceOf(issuerPayee), wantI[i]);
            assertEq(fab.balanceOf(fabiusPayee), wantF[i]);
            assertEq(fab.balanceOf(address(s)), 0, "tidak ada sisa");
        }
    }

    function test_vektor_share_change_sama_dengan_engine() public {
        string memory j = _json();
        uint256[] memory olds = vm.parseJsonUintArray(j, ".share.old");
        uint256[] memory news = vm.parseJsonUintArray(j, ".share.new");
        bool[] memory ok = vm.parseJsonBoolArray(j, ".share.allowed");
        assertEq(olds.length, 70, "jumlah vektor share");
        for (uint256 i = 0; i < olds.length; i++) {
            RevenueSplitter s = _make(uint16(olds[i]));
            vm.prank(fabius);
            if (ok[i]) {
                s.lowerFabiusShare(uint16(news[i]), _none());
                assertEq(s.fabiusBps(), news[i], "diterima seperti share_change_allowed");
            } else {
                vm.expectRevert(abi.encodeWithSelector(RevenueSplitter.ShareMayOnlyDecrease.selector, uint16(olds[i]), uint16(news[i])));
                s.lowerFabiusShare(uint16(news[i]), _none());
            }
        }
    }

    function test_vektor_skenario_sama_dengan_model_engine() public {
        string memory j = _json();
        uint256 n;
        while (vm.keyExistsJson(j, string.concat(".skenario[", vm.toString(n), "]"))) {
            _skenario(j, string.concat(".skenario[", vm.toString(n), "]"));
            n++;
        }
        assertEq(n, 8, "jumlah skenario");
    }

    function _skenario(string memory j, string memory p) internal {
        string memory nama = vm.parseJsonString(j, string.concat(p, ".nama"));
        uint256[] memory op = vm.parseJsonUintArray(j, string.concat(p, ".op"));
        uint256[] memory val = vm.parseJsonUintArray(j, string.concat(p, ".nilai"));
        uint256[] memory wantI = vm.parseJsonUintArray(j, string.concat(p, ".issuerTotal"));
        uint256[] memory wantF = vm.parseJsonUintArray(j, string.concat(p, ".fabiusTotal"));
        MockToken t = new MockToken("SKN");
        RevenueSplitter s = _make(uint16(vm.parseJsonUint(j, string.concat(p, ".fabiusBpsAwal"))));
        for (uint256 i = 0; i < op.length; i++) {
            _langkah(s, t, op[i], val[i]);
            assertEq(t.balanceOf(issuerPayee), wantI[i], string.concat(nama, " penerbit"));
            assertEq(t.balanceOf(fabiusPayee), wantF[i], string.concat(nama, " Fabius"));
        }
        s.release(t);
        assertEq(t.balanceOf(issuerPayee) + t.balanceOf(fabiusPayee), t.totalSupply(), "semua yang masuk keluar, tanpa sisa");
    }

    /// Kode operasi = `tools/gen_splitter_vectors.py`: 0 setor, 1 release, 2 releaseIssuer, 3 releaseFabius, 4 turun, 5 turun + checkpoint.
    function _langkah(RevenueSplitter s, MockToken t, uint256 op, uint256 v) internal {
        if (op == 0) {
            _pay(t, s, v);
        } else if (op == 1) {
            s.release(t);
        } else if (op == 2) {
            s.releaseIssuer(t);
        } else if (op == 3) {
            s.releaseFabius(t);
        } else if (op == 4) {
            vm.prank(fabius);
            s.lowerFabiusShare(uint16(v), _none());
        } else {
            vm.prank(fabius);
            s.lowerFabiusShare(uint16(v), _one(t));
        }
    }

    // -------------------------------------------------- invarian (fuzz)

    function testFuzz_jumlah_selalu_sama_dan_debu_ke_fabius(uint256 amount, uint16 issuerBps) public {
        issuerBps = uint16(bound(issuerBps, 0, BPS));
        RevenueSplitter s = _make(BPS - issuerBps);
        deal(address(fab), address(s), amount);
        (uint256 toI, uint256 toF) = s.release(fab);
        assertEq(toI + toF, amount, "jumlah == masukan");
        assertEq(toI, Math.mulDiv(amount, issuerBps, BPS), "penerbit = floor(amount x bps / 10000)");
        // debu ke Fabius: bagian Fabius >= hasil bagi eksaknya (dibulatkan ke bawah)
        assertGe(toF, Math.mulDiv(amount, BPS - issuerBps, BPS));
    }

    function testFuzz_rilis_bertahap_tidak_kehilangan_atau_menggandakan_wei(uint96[6] memory dep, uint8 mask, uint16 issuerBps) public {
        issuerBps = uint16(bound(issuerBps, 0, BPS));
        RevenueSplitter s = _make(BPS - issuerBps);
        uint256 total;
        for (uint256 i = 0; i < dep.length; i++) {
            _pay(fab, s, dep[i]);
            total += dep[i];
            if ((mask >> i) & 1 == 1) {
                if (i % 3 == 0) s.release(fab);
                else if (i % 3 == 1) s.releaseIssuer(fab);
                else s.releaseFabius(fab);
                // pada setiap titik: hak kumulatif penerbit tidak pernah melebihi split total sejauh ini
                assertLe(fab.balanceOf(issuerPayee), Math.mulDiv(total, issuerBps, BPS));
            }
        }
        s.release(fab);
        uint256 wantI = Math.mulDiv(total, issuerBps, BPS);
        assertEq(fab.balanceOf(issuerPayee), wantI, "berapa kali pun release, hasilnya = satu split atas total");
        assertEq(fab.balanceOf(fabiusPayee), total - wantI);
        assertEq(fab.balanceOf(address(s)), 0);
        (uint256 pi, uint256 pf) = s.pending(fab);
        assertEq(pi + pf, 0);
    }

    function testFuzz_tarif_turun_jumlah_tetap_dan_segmen_terpisah(uint96 a, uint96 b, uint96 c, uint16 newFabius, bool cp) public {
        newFabius = uint16(bound(newFabius, 0, 4000));
        RevenueSplitter s = _make(4000);
        _pay(fab, s, a);
        s.release(fab);
        _pay(fab, s, b);                                                // belum di-checkpoint saat tarif turun
        vm.prank(fabius);
        s.lowerFabiusShare(newFabius, cp ? _one(fab) : _none());
        _pay(fab, s, c);
        s.release(fab);
        uint256 nb = BPS - newFabius;
        uint256 wantI = cp ? Math.mulDiv(uint256(a) + b, 6000, BPS) + Math.mulDiv(c, nb, BPS)
                           : Math.mulDiv(a, 6000, BPS) + Math.mulDiv(uint256(b) + c, nb, BPS);
        assertEq(fab.balanceOf(issuerPayee), wantI, "tiap segmen = economics.split atas total segmen");
        assertEq(fab.balanceOf(issuerPayee) + fab.balanceOf(fabiusPayee), uint256(a) + b + c, "tidak ada wei hilang");
        // tanpa checkpoint, saldo yang belum dibukukan ikut tarif baru (lebih tinggi untuk penerbit). Karena dua floor terpisah, penerbit bisa
        // menerima 1 wei LEBIH SEDIKIT daripada dengan checkpoint (contoh fuzz: a=22473 b=4 c=24160 bps Fabius 3091 -> 30177 vs 30178); tidak lebih.
        uint256 noCp = Math.mulDiv(a, 6000, BPS) + Math.mulDiv(uint256(b) + c, nb, BPS);
        uint256 withCp = Math.mulDiv(uint256(a) + b, 6000, BPS) + Math.mulDiv(c, nb, BPS);
        assertGe(noCp + 1, withCp);
    }

    function testFuzz_bagian_fabius_hanya_turun(uint16 oldBps, uint16 newBps) public {
        oldBps = uint16(bound(oldBps, 0, BPS));
        RevenueSplitter s = _make(oldBps);
        vm.prank(issuer);
        vm.expectRevert(RevenueSplitter.NotFabius.selector);
        s.lowerFabiusShare(newBps, _none());
        vm.prank(fabius);
        if (newBps <= oldBps) {
            s.lowerFabiusShare(newBps, _none());
            assertEq(s.fabiusBps(), newBps);
            assertEq(s.issuerBps(), BPS - newBps);
        } else {
            vm.expectRevert(abi.encodeWithSelector(RevenueSplitter.ShareMayOnlyDecrease.selector, oldBps, newBps));
            s.lowerFabiusShare(newBps, _none());
        }
    }

    function testFuzz_pending_sama_dengan_yang_dibayar(uint96 a, uint96 b, uint16 newFabius) public {
        newFabius = uint16(bound(newFabius, 0, 4000));
        RevenueSplitter s = _make(4000);
        _pay(fab, s, a);
        s.releaseFabius(fab);
        vm.prank(fabius);
        s.lowerFabiusShare(newFabius, _none());
        _pay(fab, s, b);
        (uint256 pi, uint256 pf) = s.pending(fab);
        (uint256 toI, uint256 toF) = s.release(fab);
        assertEq(pi, toI);
        assertEq(pf, toF);
    }

    // -------------------------------------------------- banyak token

    function test_banyak_token_pembukuan_terpisah() public {
        RevenueSplitter s = _make(4000);
        _pay(fab, s, 1_001);
        _pay(usd, s, 7);
        s.release(fab);                                                 // usd belum di-checkpoint
        vm.prank(fabius);
        s.lowerFabiusShare(2_000, _none());
        (uint256 toI, uint256 toF) = s.release(usd);
        assertEq(toI, 5, "usd seluruhnya dengan tarif baru: floor(7 x 0,8)");
        assertEq(toF, 2);
        assertEq(fab.balanceOf(issuerPayee), 600, "fab dibukukan dengan tarif lama sebelum turun");
        assertEq(fab.balanceOf(fabiusPayee), 401);
        assertEq(s.bookOf(fab).releasedIssuer, 600);
        assertEq(s.bookOf(usd).releasedIssuer, 5);
    }

    // -------------------------------------------------- hak akses + tidak ada penyitaan

    function test_hanya_penerbit_yang_mengganti_payout_penerbit() public {
        RevenueSplitter s = _make(4000);
        address baru = makeAddr("payout-baru");
        vm.prank(fabius);
        vm.expectRevert(RevenueSplitter.NotIssuer.selector);
        s.setIssuerPayee(fabius);
        vm.prank(issuerPayee);
        vm.expectRevert(RevenueSplitter.NotIssuer.selector);
        s.setIssuerPayee(baru);
        vm.startPrank(issuer);
        vm.expectRevert(abi.encodeWithSelector(RevenueSplitter.BadPayee.selector, address(0)));
        s.setIssuerPayee(address(0));
        vm.expectRevert(abi.encodeWithSelector(RevenueSplitter.BadPayee.selector, address(s)));
        s.setIssuerPayee(address(s));
        vm.expectEmit(true, true, false, false, address(s));
        emit RevenueSplitter.IssuerPayeeChanged(issuerPayee, baru);
        s.setIssuerPayee(baru);
        vm.stopPrank();
        assertEq(s.issuerPayee(), baru);
    }

    function test_hanya_fabius_yang_mengganti_dompet_fabius() public {
        RevenueSplitter s = _make(4000);
        address baru = makeAddr("kas-baru");
        vm.prank(issuer);
        vm.expectRevert(RevenueSplitter.NotFabius.selector);
        s.setFabiusPayee(issuer);
        vm.prank(fabius);
        s.setFabiusPayee(baru);
        assertEq(s.fabiusPayee(), baru);
        reg.setOwner(stranger);                                         // pemilik registry berganti = Fabius berganti
        vm.prank(fabius);
        vm.expectRevert(RevenueSplitter.NotFabius.selector);
        s.setFabiusPayee(fabius);
    }

    function test_payout_baru_menerima_hak_yang_belum_dilepas() public {
        RevenueSplitter s = _make(4000);
        _pay(fab, s, 100);
        s.release(fab);
        _pay(fab, s, 50);
        address baru = makeAddr("payout-baru");
        vm.prank(issuer);
        s.setIssuerPayee(baru);
        s.release(fab);
        assertEq(fab.balanceOf(issuerPayee), 60, "yang sudah dilepas tetap di payout lama");
        assertEq(fab.balanceOf(baru), 30, "hak yang belum dilepas ikut ke payout baru");
    }

    function test_tidak_ada_yang_bisa_menyita_saldo() public {
        RevenueSplitter s = _make(4000);
        _pay(fab, s, 1_000);
        // Fabius mengarahkan dompet Fabius ke dirinya sendiri dan menurunkan bagiannya: bagian penerbit tetap ke payout penerbit
        vm.startPrank(fabius);
        s.setFabiusPayee(fabius);
        vm.expectRevert(RevenueSplitter.NotIssuer.selector);
        s.setIssuerPayee(fabius);
        vm.expectRevert(RevenueSplitter.AlreadyInitialized.selector);
        s.initialize(BOT, fabius, fabius, fabius, BPS);
        vm.stopPrank();
        vm.prank(stranger);                                             // pull: siapa pun memicu, uang tetap ke payee
        (uint256 toI, uint256 toF) = s.release(fab);
        assertEq(toI, 600);
        assertEq(toF, 400);
        assertEq(fab.balanceOf(issuerPayee), 600);
        assertEq(fab.balanceOf(fabius), 400);
        assertEq(fab.balanceOf(stranger), 0);
    }

    function test_implementasi_tidak_bisa_dipasang_atau_dipakai() public {
        RevenueSplitter impl = RevenueSplitter(reg.impl());
        vm.expectRevert(RevenueSplitter.AlreadyInitialized.selector);
        impl.initialize(BOT, issuer, issuerPayee, fabiusPayee, 4000);
        deal(address(fab), address(impl), 10);
        vm.expectRevert(RevenueSplitter.NotInitialized.selector);
        impl.release(fab);
        vm.expectRevert(RevenueSplitter.NotInitialized.selector);
        impl.setIssuerPayee(issuer);
    }

    function test_inisialisasi_menolak_nilai_nol_dan_bps_di_atas_penuh() public {
        RevenueSplitter s = RevenueSplitter(Clones.clone(reg.impl()));
        vm.expectRevert(RevenueSplitter.ZeroValue.selector);
        s.initialize(bytes32(0), issuer, issuerPayee, fabiusPayee, 4000);
        vm.expectRevert(RevenueSplitter.ZeroValue.selector);
        s.initialize(BOT, address(0), issuerPayee, fabiusPayee, 4000);
        vm.expectRevert(abi.encodeWithSelector(RevenueSplitter.BadPayee.selector, address(0)));
        s.initialize(BOT, issuer, address(0), fabiusPayee, 4000);
        vm.expectRevert(abi.encodeWithSelector(RevenueSplitter.BadPayee.selector, address(s)));
        s.initialize(BOT, issuer, issuerPayee, address(s), 4000);
        vm.expectRevert(abi.encodeWithSelector(RevenueSplitter.BadBps.selector, uint16(BPS + 1)));
        s.initialize(BOT, issuer, issuerPayee, fabiusPayee, BPS + 1);
        s.initialize(BOT, issuer, issuerPayee, fabiusPayee, 4000);
        assertEq(s.registry(), address(this));
        vm.expectRevert(RevenueSplitter.AlreadyInitialized.selector);
        s.initialize(BOT, issuer, issuerPayee, fabiusPayee, 4000);
    }

    // -------------------------------------------------- token aneh

    function test_reentrancy_ditolak_tanpa_bayar_ganda() public {
        for (uint8 mode = 0; mode < 3; mode++) {
            ReentrantToken t = new ReentrantToken();
            RevenueSplitter s = _make(4000);
            t.arm(s, mode);
            t.mint(address(s), 1_001);
            s.release(IERC20(address(t)));
            assertTrue(t.tried(), "token jahat memang mencoba masuk lagi");
            assertFalse(t.succeeded(), "masuk lagi ditolak");
            assertEq(bytes4(t.reason()), ReentrancyGuard.ReentrancyGuardReentrantCall.selector);
            assertEq(t.balanceOf(issuerPayee), 600, "penerbit dibayar tepat sekali");
            assertEq(t.balanceOf(fabiusPayee), 401, "Fabius dibayar tepat sekali (debu ke Fabius)");
            assertEq(t.balanceOf(address(s)), 0);
        }
    }

    /// Didokumentasikan, bukan "didukung": yang dibagi adalah yang TIBA (990 dari 1000), fee keluar ditanggung penerima; pembukuan splitter
    /// tetap utuh (dilepas == diterima) karena saldo splitter turun persis sebesar yang dikirim. Gerbang x402 tidak menerima token semacam ini
    /// (SK-X1/SK-X2: Transfer ke payTo harus tepat harga).
    function test_fee_on_transfer_yang_dibagi_adalah_yang_tiba() public {
        FeeToken t = new FeeToken();
        RevenueSplitter s = _make(4000);
        t.mint(buyer, 1_000);
        vm.prank(buyer);
        t.transfer(address(s), 1_000);
        assertEq(t.balanceOf(address(s)), 990);
        (uint256 toI, uint256 toF) = s.release(IERC20(address(t)));
        assertEq(toI, 594, "floor(990 x 0,6)");
        assertEq(toF, 396);
        assertEq(t.balanceOf(issuerPayee), 589, "594 - fee 5");
        assertEq(t.balanceOf(fabiusPayee), 393, "396 - fee 3");
        RevenueSplitter.Book memory b = s.bookOf(IERC20(address(t)));
        assertEq(b.releasedIssuer + b.releasedFabius, 990, "pembukuan: dilepas == diterima");
        assertEq(t.balanceOf(address(s)), 0);
    }

    function test_saldo_menyusut_berhenti_bukan_salah_bagi() public {
        RevenueSplitter s = _make(4000);
        _pay(fab, s, 1_000);
        s.releaseIssuer(fab);                                           // 600 ke penerbit, 400 hak Fabius masih di saldo
        fab.burnFrom(address(s), 100);                                  // admin token menyita 100
        vm.expectRevert(abi.encodeWithSelector(RevenueSplitter.BalanceShrank.selector, address(fab), 1_000, 900));
        s.release(fab);
        vm.expectRevert();
        s.pending(fab);
        fab.mint(address(s), 100);                                      // saldo pulih -> jalan lagi
        (, uint256 toF) = s.release(fab);
        assertEq(toF, 400);
    }

    function test_bnb_ditolak() public {
        RevenueSplitter s = _make(4000);
        vm.deal(buyer, 1 ether);
        vm.prank(buyer);
        (bool ok,) = address(s).call{value: 1}("");
        assertFalse(ok, "koin native ditolak: hanya token ERC-20");
    }

    function test_release_tanpa_saldo_tidak_mengirim_apa_pun() public {
        RevenueSplitter s = _make(4000);
        vm.recordLogs();
        (uint256 toI, uint256 toF) = s.release(fab);
        assertEq(toI + toF, 0);
        assertEq(vm.getRecordedLogs().length, 0, "tanpa event Released / Transfer");
    }

    function test_event_released_dan_turun() public {
        RevenueSplitter s = _make(4000);
        _pay(fab, s, 10);
        vm.expectEmit(true, true, true, true, address(s));
        emit RevenueSplitter.Released(fab, issuerPayee, true, 6);
        vm.expectEmit(true, true, true, true, address(s));
        emit RevenueSplitter.Released(fab, fabiusPayee, false, 4);
        s.release(fab);
        vm.expectEmit(false, false, false, true, address(s));
        emit RevenueSplitter.FabiusShareLowered(4000, 3000);
        vm.prank(fabius);
        s.lowerFabiusShare(3000, _none());
    }
}
