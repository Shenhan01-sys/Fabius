// Catatan posisi yang DIEKSEKUSI — bukan jurnal opini.
//
// Kenapa kontrak ini ada. Selama ini "hasil analisis" kami berhenti sebagai angka yang kami tulis
// sendiri: entry_ref diambil dari harga bar, lalu ledger membandingkannya dengan bar lain. Itu
// jejak yang jujur, tapi masih satu langkah dari tanah: tidak ada yang benar-benar berpindah.
// Kontrak ini memotong langkah itu. Harga masuk dibaca dari hasil swap di pool, bukan dari
// klaim kami; harga keluar pun sama; dan keduanya mendarat di event yang bisa dibaca siapa pun.
//
// Konsekuensi yang kami terima dan justru kami cari: ongkos jadi nyata. Fee pool dan dampak
// harga (orang yang masuk $5 ke kurva yang sama) tidak bisa dikecil-kecilkan di laporan, karena
// angkanya keluar dari transaksi — bukan dari spreadsheet kami.
//
// Short dilakukan dengan inventaris kami sendiri: kami JUAL token yang kami pegang, lalu BELI
// kembali untuk menutup. Ekonominya short (jual mahal, beli murah), tanpa perlu orang yang
// mau meminjamkan kami token di testnet. Karena itu `asset` harus benar-benar ada di vault
// sebelum posisi short bisa dibuka — dan kalau tidak ada, kontraknya menolak, bukan
// pura-pura punya.
//
// Empat pagar yang dipasang di kontrak, bukan di niat:
//   1. hanya `agent` yang boleh membuka/menutup (owner tidak punya jalan pintas),
//   2. `decisionHash` dan `snapshotHash` WAJIB ada — sebuah posisi tidak bisa lahir dari
//      keputusan yang tidak di-anchor,
//   3. plafon harian `dailyCap` + plafon per posisi `maxPositionQuote`, dengan `HARD_CEILING`
//      yang bahkan tidak bisa dilewati pemilik (kalau konfigurasi salah, yang terjadi adalah
//      reject, bukan blow-up),
//   4. satu posisi per aset; dan `killSwitch` menutup pintu masuk tanpa bisa membuka kembali
//      posisi yang sudah ada secara diam-diam.
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";
import {DemoPair} from "./DemoPair.sol";

contract ExecutionVault {
    using SafeERC20 for IERC20;

    struct Position {
        bool open;
        bool shortSide;
        uint256 assetQty;       // jumlah token yang dipegang (long) atau dijual (short)
        uint256 quoteAtEntry;   // quote yang benar-benar dibayar/diterima di kaki pertama
        uint256 entryPx18;      // harga EKSEKUSI (1e18), bukan harga yang kami klaim
        uint64 openedAt;
        bytes32 decisionHash;
        bytes32 snapshotHash;
    }

    /// @dev plafon yang tidak bisa dinaikkan pemilik: 10 unit quote per hari. Kalau suatu hari
    /// kami ingin lebih, itu perubahan kontrak (terlihat), bukan perubahan konfigurasi (tidak).
    uint256 public constant HARD_CEILING = 10_000_000;

    IERC20 public immutable quote;
    address public agent;
    address public owner;
    bool public killSwitch;

    /// @dev pasangan aset -> venue. Satu vault, banyak aset, tiap aset punya pool sendiri.
    mapping(address => address) public venueOf;
    mapping(address => Position) public positionOf;
    address[] public trackedAssets;

    uint256 public dailyCap = 5_000_000;      // $5/hari - plafon builder
    uint256 public maxPositionQuote = 1_000_000;
    uint256 public spentToday;
    uint64 public dayStamp;
    int256 public realizedQuote;               // kumulatif, boleh negatif: tidak kami bersihkan
    uint256 public closedCount;

    event Opened(address indexed asset, bool shortSide, uint256 assetQty, uint256 quoteAmount,
                 uint256 entryPx18, bytes32 decisionHash, bytes32 snapshotHash);
    event Closed(address indexed asset, bool shortSide, uint256 quoteAmount, uint256 exitPx18,
                 int256 realizedQuote, int256 realizedBps, uint256 gasUnitsPaid);
    event CapsSet(uint256 dailyCap, uint256 maxPositionQuote);
    event VenueSet(address indexed asset, address indexed pair);

    error NotAgent();
    error NotOwner();
    error NoVenue();
    error AlreadyOpen();
    error NotOpen();
    error NoAnchorHash();
    error OverDailyCap();
    error OverPositionCap();
    error KillSwitchOn();
    error ZeroAddr();
    error NeedInventory();
    error ShortCloseShort();

    modifier onlyAgent() {
        if (msg.sender != agent) revert NotAgent();
        _;
    }

    modifier onlyOwner() {
        if (msg.sender != owner) revert NotOwner();
        _;
    }

    constructor(address quote_, address agent_, address owner_) {
        if (quote_ == address(0) || agent_ == address(0) || owner_ == address(0)) revert ZeroAddr();
        quote = IERC20(quote_);
        agent = agent_;
        owner = owner_;
    }

    // ------------------------------------------------------------------ konfigurasi (owner)
    function setVenue(address asset, address pair) external onlyOwner {
        if (asset == address(0) || pair == address(0)) revert ZeroAddr();
        venueOf[asset] = pair;
        if (positionOf[asset].openedAt == 0) trackedAssets.push(asset);
        emit VenueSet(asset, pair);
    }

    /// @notice Pemilik boleh MENURUNKAN plafon kapan saja. Menaikkannya dibatasi HARD_CEILING.
    function setCaps(uint256 dailyCap_, uint256 maxPos_) external onlyOwner {
        if (dailyCap_ > HARD_CEILING) dailyCap_ = HARD_CEILING;
        dailyCap = dailyCap_;
        maxPositionQuote = maxPos_;
        emit CapsSet(dailyCap, maxPositionQuote);
    }

    function setKillSwitch(bool on) external onlyOwner {
        killSwitch = on;
    }

    // ------------------------------------------------------------------ eksekusi (agent)
    function openLong(address asset, uint256 quoteIn, bytes32 decisionHash, bytes32 snapshotHash)
        external onlyAgent
    {
        _guards(quoteIn, decisionHash, snapshotHash);
        if (positionOf[asset].open) revert AlreadyOpen();
        DemoPair pair = DemoPair(venueOf[asset]);
        if (address(pair) == address(0)) revert NoVenue();

        quote.safeIncreaseAllowance(address(pair), quoteIn);
        uint256 got = pair.swapBuy(quoteIn);          // harga dari pool, bukan dari kami
        Position storage p = positionOf[asset];
        p.open = true;
        p.shortSide = false;
        p.assetQty = got;
        p.quoteAtEntry = quoteIn;
        p.entryPx18 = (quoteIn * 1e18) / got;
        p.openedAt = uint64(block.timestamp);
        p.decisionHash = decisionHash;
        p.snapshotHash = snapshotHash;
        _bumpDay(quoteIn);
        emit Opened(asset, false, got, quoteIn, p.entryPx18, decisionHash, snapshotHash);
    }

    /// @notice Short = jual sebagian inventaris kami, beli kembali nanti untuk menutup.
    function openShort(address asset, uint256 assetQty, bytes32 decisionHash, bytes32 snapshotHash)
        external onlyAgent
    {
        if (positionOf[asset].open) revert AlreadyOpen();
        DemoPair pair = DemoPair(venueOf[asset]);
        if (address(pair) == address(0)) revert NoVenue();
        if (IERC20(asset).balanceOf(address(this)) < assetQty) revert NeedInventory();

        // Notional untuk plafon dihitung dalam QUOTE, bukan dalam jumlah token. Versi pertama
        // meneruskan assetQty ke `_guards` yang satuannya quote - dua satuan berbeda disamakan,
        // jadi plafon harian bisa dilewati dengan token murah yang jumlahnya besar.
        uint256 notional = pair.costOfBuy(assetQty);
        _guards(notional, decisionHash, snapshotHash);

        IERC20(asset).safeIncreaseAllowance(address(pair), assetQty);
        uint256 recv = pair.swapSell(assetQty);
        Position storage p = positionOf[asset];
        p.open = true;
        p.shortSide = true;
        p.assetQty = assetQty;
        p.quoteAtEntry = recv;
        p.entryPx18 = (recv * 1e18) / assetQty;
        p.openedAt = uint64(block.timestamp);
        p.decisionHash = decisionHash;
        p.snapshotHash = snapshotHash;
        _bumpDay(notional);
        emit Opened(asset, true, assetQty, recv, p.entryPx18, decisionHash, snapshotHash);
    }

    function close(address asset) external onlyAgent {
        uint256 startGas = gasleft();
        Position storage p = positionOf[asset];
        if (!p.open) revert NotOpen();
        DemoPair pair = DemoPair(venueOf[asset]);
        uint256 legQuote;
        uint256 exitPx18;

        if (p.shortSide) {
            // +1: `costOfBuy` bulat ke bawah, jadi permintaan persis akan menerima token 1 wei
            // KURANG dari yang harusnya kami kembalikan. Kami beli 1 wei lebih dan sisanya jadi
            // dust yang tercatat, bukan kami samarkan dengan require yang longgar.
            legQuote = pair.costOfBuy(p.assetQty) + 1;
            quote.safeIncreaseAllowance(address(pair), legQuote);
            uint256 gotBack = pair.swapBuy(legQuote);
            if (gotBack < p.assetQty) revert ShortCloseShort();
            exitPx18 = (legQuote * 1e18) / gotBack;
        } else {
            IERC20(asset).safeIncreaseAllowance(address(pair), p.assetQty);
            legQuote = pair.swapSell(p.assetQty);
            exitPx18 = (legQuote * 1e18) / p.assetQty;
        }

        int256 realized = p.shortSide
            ? int256(uint256(p.quoteAtEntry)) - int256(legQuote)
            : int256(uint256(legQuote)) - int256(p.quoteAtEntry);
        int256 mag = int256((uint256(realized >= 0 ? realized : -realized) * 10_000) / p.quoteAtEntry);
        int256 bps = realized >= 0 ? mag : -mag;

        realizedQuote += realized;
        closedCount += 1;
        delete positionOf[asset];
        // gasUnitsPaid = yang benar-benar dipakai panggilan ini. `gasleft()` saja bukan biaya;
        // mengempit angka itu membuat laporan ongkos terlihat nyata padahal tidak diukur.
        emit Closed(asset, p.shortSide, legQuote, exitPx18, realized, bps, startGas - gasleft());
    }

    /// @dev Rollover hari dilakukan SEBELUM budget diperiksa.
    /// Ini bug yang ditemukan test, bukan yang dipilih: versi pertama memeriksa plafon dulu baru
    /// mereset di `_bumpDay`, jadi pada jam pertama hari baru `spentToday` masih membawa pemakain
    /// kemarin dan posisi pertama ditolak dengan OverDailyCap. Plafon harian yang menolak sebelum
    /// ia habis itu bukan pagar - itu kunci yang nyangkut.
    function _rollDay() internal {
        uint64 today = uint64(block.timestamp / 1 days);
        if (today != dayStamp) {
            dayStamp = today;
            spentToday = 0;
        }
    }

    function _guards(uint256 size, bytes32 decisionHash, bytes32 snapshotHash) internal {
        if (killSwitch) revert KillSwitchOn();
        if (size == 0) revert OverPositionCap();
        if (decisionHash == bytes32(0) || snapshotHash == bytes32(0)) revert NoAnchorHash();
        _rollDay();
        if (size > maxPositionQuote) revert OverPositionCap();
        if (spentToday + size > dailyCap) revert OverDailyCap();
    }

    function _bumpDay(uint256 size) internal {
        _rollDay();
        spentToday += size;
    }

    // ------------------------------------------------------------------ bacaan untuk auditor
    function positionCount() external view returns (uint256) {
        return trackedAssets.length;
    }

    /// @dev Pembacaan bersih satu posisi. Getter struct otomatis mengembalikan DELAPAN nilai,
    /// termasuk `open` dan field internal lain - tidak praktis untuk penguji dan untuk alat
    /// eksternal yang cuma butuh kaki ekonominya.
    function openPositionOf(address asset)
        external
        view
        returns (bool isShort, uint256 assetQty, uint256 quoteAtEntry, uint256 entryPx18,
                 bytes32 decisionHash, bytes32 snapshotHash)
    {
        Position storage p = positionOf[asset];
        return (p.shortSide, p.assetQty, p.quoteAtEntry, p.entryPx18, p.decisionHash,
                p.snapshotHash);
    }

    function openPositions() external view returns (uint256 n) {
        for (uint256 i = 0; i < trackedAssets.length; i++) {
            if (positionOf[trackedAssets[i]].open) n++;
        }
    }
}
