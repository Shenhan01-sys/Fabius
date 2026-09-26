// Venue perdagangan untuk jalur eksekusi Fabius di chain 97.
//
// Kenapa kami bikin sendiri (bukan memakai pool PancakeSwap testnet): supaya angka yang keluar
// dari "eksekusi nyata" itu nyata TAPI tidak bergantung pada likuiditas asing yang bisa habis,
// kosong, atau digerakkan orang lain di testnet. Kalau kami swap ke pool siapa pun lalu menulis
// "ini slippage kami", slippage itu bukan milik kami.
//
// Yang TIDAK diklaim: bahwa kurva x*y=k ini mewakili pasar meme sungguhan. Yang dibuktikan di sini
// adalah PROSESnya - harga masuk datang dari kontrak, bukan dari angka yang kami tulis sendiri -
// plus satu angka yang jujur: berapa besar ongkos (fee + dampak harga) memakan posisi kecil.
//
// Portabilitas: sengaja tanpa opcode pasca-Shanghai (tidak ada `mcopy`, tidak ada transient
// storage), supaya ikut profil default `shanghai` seperti DecisionAnchor dan tidak memaksa kami
// menaikkan target kontrak yang sudah terverifikasi di chain.
pragma solidity ^0.8.24;

import {IERC20} from "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import {SafeERC20} from "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

contract DemoPair {
    using SafeERC20 for IERC20;

    /// @dev biaya swap dalam basis points (30 = 0,30%) - angka tipikal AMM, bukan karangan.
    uint256 public constant FEE_BPS = 30;
    uint256 public constant BPS = 10_000;

    IERC20 public immutable asset;   // token yang diperdagangkan (koin demo)
    IERC20 public immutable quote;   // unit hitungan (USDT demo)

    address public owner;
    bool public paused;

    uint256 public reserveAsset;
    uint256 public reserveQuote;

    event Swapped(address indexed by, bool assetIn, uint256 amountIn, uint256 amountOut,
                  uint256 reserveAssetAfter, uint256 reserveQuoteAfter);
    event Synced(uint256 reserveAsset, uint256 reserveQuote);
    event PausedSet(bool paused);

    error ZeroToken();
    error SameToken();
    error AlreadySeeded();
    error NotOwner();
    error Paused();
    error Empty();
    error BadSize();

    constructor(address asset_, address quote_, address owner_) {
        if (asset_ == address(0) || quote_ == address(0)) revert ZeroToken();
        if (asset_ == quote_) revert SameToken();
        asset = IERC20(asset_);
        quote = IERC20(quote_);
        owner = owner_;
    }

    /// @notice Isi cadangan satu kali. Setelah terisi, tidak bisa disentuh lagi dari luar -
    /// supaya "likuiditas" tidak bisa digesak-geser agar hasil eksekusi terlihat bagus.
    function bootstrap() external {
        if (reserveAsset != 0 || reserveQuote != 0) revert AlreadySeeded();
        reserveAsset = asset.balanceOf(address(this));
        reserveQuote = quote.balanceOf(address(this));
        emit Synced(reserveAsset, reserveQuote);
    }

    function setPaused(bool p) external {
        if (msg.sender != owner) revert NotOwner();
        paused = p;
        emit PausedSet(p);
    }

    /// @notice quote -> asset. Mengembalikan jumlah asset yang AKTUAL diterima, supaya pemanggil
    /// bisa membandingkan harga yang diklaim vs harga yang dieksekusi (itu inti audit ini).
    function swapBuy(uint256 quoteIn) external returns (uint256 assetOut) {
        if (paused) revert Paused();
        if (quoteIn == 0) revert BadSize();
        quote.safeTransferFrom(msg.sender, address(this), quoteIn);
        assetOut = _getOut(quoteIn, reserveQuote, reserveAsset);
        if (assetOut == 0 || assetOut >= reserveAsset) revert BadSize();
        reserveQuote += quoteIn;
        reserveAsset -= assetOut;
        asset.safeTransfer(msg.sender, assetOut);
        emit Swapped(msg.sender, false, quoteIn, assetOut, reserveAsset, reserveQuote);
    }

    /// @notice asset -> quote.
    function swapSell(uint256 assetIn) external returns (uint256 quoteOut) {
        if (paused) revert Paused();
        if (assetIn == 0) revert BadSize();
        asset.safeTransferFrom(msg.sender, address(this), assetIn);
        quoteOut = _getOut(assetIn, reserveAsset, reserveQuote);
        if (quoteOut == 0 || quoteOut >= reserveQuote) revert BadSize();
        reserveAsset += assetIn;
        reserveQuote -= quoteOut;
        quote.safeTransfer(msg.sender, quoteOut);
        emit Swapped(msg.sender, true, assetIn, quoteOut, reserveAsset, reserveQuote);
    }

    function _getOut(uint256 amtIn, uint256 rIn, uint256 rOut) internal view returns (uint256) {
        if (rIn == 0 || rOut == 0) revert Empty();
        uint256 ip = amtIn * (BPS - FEE_BPS);
        return ip * rOut / (rIn * BPS + ip);
    }

    /// @notice Berapa quote yang HARUS dibayar untuk membeli `wantAsset`, termasuk fee dan dampak
    /// harga - dihitung tanpa mengirim transaksi. Ini jawaban jujur untuk "apakah $5 layak?".
    function costOfBuy(uint256 wantAsset) external view returns (uint256 quoteOut) {
        // inapkan dari rumus out: quote = rIn*want / ((BPS-FEE)*(rOut-want)) * BPS
        if (wantAsset == 0 || wantAsset >= reserveAsset) revert BadSize();
        quoteOut = (reserveQuote * BPS * wantAsset) / ((BPS - FEE_BPS) * (reserveAsset - wantAsset));
    }

    /// @dev harga spot quote-per-asset dengan 18 desimal (untuk pelaporan, bukan eksekusi).
    function spotPrice() external view returns (uint256 quotePerAsset) {
        quotePerAsset = (reserveQuote * 1e18) / reserveAsset;
    }
}
