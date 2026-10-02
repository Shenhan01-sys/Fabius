"""Spesifikasi bot: satu metode + satu parameter, ber-sha (pola kunci pra-registrasi F-D29/F-D68).

Hash = sha256 atas JSON kanonik (`sort_keys=True`, separators `(",", ":")`, ensure_ascii bawaan) - SAMA dengan
konvensi `tools/direction.py`. Mengubah parameter, konstanta, universe atau penggaris menghasilkan sha lain =
bot baru dengan n maju mulai dari nol (aturan "pivot = kunci baru").

STATUS: usulan 2 Okt 2026 (vault/08-Backlog/05 - Epik Enam Bot.md). Nilai di bawah BELUM dikunci; sha di sini
bukan kunci, hanya sidik jari spesifikasi hari ini.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from typing import Any

PERP_UNIVERSE = ("BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT", "XRPUSDT", "DOGEUSDT", "ADAUSDT", "LINKUSDT",
                 "LTCUSDT", "AVAXUSDT", "TRXUSDT", "DOTUSDT", "BCHUSDT", "ETCUSDT", "ATOMUSDT", "NEARUSDT")


def canon(obj: Any) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def sha0x(obj: Any) -> str:
    return "0x" + hashlib.sha256(canon(obj).encode()).hexdigest()


@dataclass(frozen=True)
class BotSpec:
    bot_id: str                      # "B1-TREND"
    metode: str                      # satu kalimat: apa yang dilakukan bot
    param_nama: str                  # SATU-satunya parameter
    param: Any                       # nilai awal (plateau diuji di vault)
    konstanta: dict = field(default_factory=dict)   # terkunci; BUKAN parameter yang boleh digeser agen
    universe: tuple = ()
    penggaris: dict = field(default_factory=dict)   # biaya per sisi dst. (P69: ukur per venue)
    tier: str = "?"
    pembunuh: str = ""               # kondisi maju yang mematikan bot (usulan, menunggu kunci)
    versi: int = 1
    template: str = ""               # id metode di REGISTRY bila bot ini varian dari metode yang ada (bot penerbit); kosong = bot_id itu sendiri

    @property
    def method(self) -> str:
        """Kunci ke REGISTRY / aturan replay: template bila ada, selain itu bot_id."""
        return self.template or self.bot_id

    def as_dict(self) -> dict:
        d = {k: getattr(self, k) for k in ("bot_id", "metode", "param_nama", "param", "konstanta", "universe",
                                            "penggaris", "tier", "pembunuh", "versi")}
        d["universe"] = list(self.universe)
        if self.template:                # hanya bila ada: sha keenam bot awal tidak berubah
            d["template"] = self.template
        return d

    def sha(self) -> str:
        return sha0x(self.as_dict())

    def fingerprint(self) -> str:
        """Sidik jari EFEKTIF untuk dedupe: metode + parameter (angka kanonik, 60 == 60.0) + universe terurut + konstanta.
        Nama bot, kalimat metode, tier, dan pembunuh TIDAK ikut: ganti nama, ubah kalimat, atau urutan universe tidak membuat bot baru."""
        p = float(self.param) if isinstance(self.param, (int, float)) and not isinstance(self.param, bool) else self.param
        return sha0x({"method": self.method, "param": p, "universe": sorted(self.universe), "konstanta": self.konstanta})


SPECS = {
    "B1-TREND": BotSpec(
        bot_id="B1-TREND",
        metode="long bila penutupan > penutupan N hari lalu, selain itu flat (momentum deret waktu, long/flat)",
        param_nama="N", param=60,
        konstanta={"long_only": True, "bobot": "sama rata atas aset yang punya data"},
        universe=PERP_UNIVERSE,
        penggaris={"fee_bps_sisi": 7, "funding": "nyata dibayar sisi long"},
        tier="A-",
        pembunuh="12 bulan maju tanpa mengalahkan buy&hold pada MDD dan Sharpe; atau kalah dari placebo masuk-acak "
                 "dengan distribusi lama tahan sama",
    ),
    "B2-RS": BotSpec(
        bot_id="B2-RS",
        metode="long k teratas, short k terbawah menurut return L hari (rotasi kekuatan relatif, dollar-neutral); "
               "7 sub-buku, masing-masing dirotasi mingguan pada hari-UTC berbeda (tanpa pilihan hari)",
        param_nama="L", param=28,
        konstanta={"k": 3, "tranche": 7, "min_aset": 8, "gross": 2.0},
        universe=PERP_UNIVERSE,
        penggaris={"fee_bps_sisi": 7, "funding": "nyata dua sisi"},
        tier="B",
        pembunuh="net Sharpe < 0 dua kuartal beruntun, atau tidak mengalahkan placebo peringkat-acak",
    ),
    "B3-CARRY": BotSpec(
        bot_id="B3-CARRY",
        metode="long spot + short perp saat funding rata-rata 7 hari (disetahunkan) > theta, selain itu flat",
        param_nama="theta", param=0.10,
        konstanta={"jendela_funding_hari": 7, "hari_setahun": 365, "kaki": 2},
        universe=PERP_UNIVERSE,
        penggaris={"fee_bps_sisi_per_kaki": 7},
        tier="A (dorman)",
        pembunuh="hasil hedged negatif tiga bulan berjalan saat aktif, atau satu kejadian ADL pada kaki perp",
    ),
    "B4-LISTING-FADE": BotSpec(
        bot_id="B4-LISTING-FADE",
        metode="short perp yang baru onboard pada penutupan hari-1; tutup setelah H hari; ukuran kecil, margin isolated",
        param_nama="H", param=14,
        konstanta={"ukuran_per_trade": 0.02, "min_volume_kuotasi_hari1_usd": 1_000_000, "stop": None,
                   "leverage_maks": 1, "margin": "isolated", "masuk": "penutupan bar hari-1 perp"},
        universe=("event: perp baru di venue",),
        penggaris={"fee_bps_sisi": 7, "biaya_putaran_tipis_pct": 1.0, "catatan": "asumsi; ukur (P69)"},
        tier="B-",
        pembunuh="20 listing maju dengan rata-rata PnL short <= 0, atau satu trade lebih buruk dari -100% notional",
    ),
    "B5-CORE-RWA": BotSpec(
        bot_id="B5-CORE-RWA",
        metode="bobot BTC dan emas proporsional 1/sigma (sigma = simpangan baku return harian L hari); bobot diperbarui bulanan",
        param_nama="L", param=90,
        konstanta={"aset": ["BTCUSDT", "emas"], "emas_kandidat": ["XAUUSDT", "PAXGUSDT"], "rebalance": "bulanan",
                   "hari_pembaruan": 1},
        universe=("BTCUSDT", "XAUUSDT"),
        penggaris={"fee_bps_sisi": 10},
        tier="B",
        pembunuh="Sharpe < BTC buy&hold DAN MDD tidak lebih baik dari -50% dalam 12 bulan maju",
    ),
    "B6-BOUNCE": BotSpec(
        bot_id="B6-BOUNCE",
        metode="beli bila z-score harga (rerata dan simpangan baku N hari) < -z_masuk; keluar saat z >= 0 (long/flat)",
        param_nama="N", param=10,
        konstanta={"z_masuk": 2.0, "z_keluar": 0.0, "long_only": True},
        universe=PERP_UNIVERSE,
        penggaris={"fee_bps_sisi": 7, "funding": "nyata dibayar sisi long"},
        tier="C",
        pembunuh="sinyal maju tidak menaikkan Sharpe EW, atau n >= 20 sinyal dengan rata-rata net <= 0",
    ),
}
