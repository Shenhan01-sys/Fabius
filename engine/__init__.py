"""Mesin enam bot Fabius + sinyal komit-ungkap + peninjau-bot penerbit (stdlib saja; satu-satunya opsional: `eth-account`).

STATUS: usulan 2 Okt 2026 - vault/08-Backlog/05 - Epik Enam Bot.md, 06 - Epik Gerbang Sinyal.md, 07 - Epik Kolaborasi Bot Terbuka.md;
keputusan F-D70, F-D71, F-D72, F-D73. Belum ada bot yang terkunci, belum ada yang diuji maju, belum ada penerbit luar. Ambang v1 TERKUNCI sementara
(engine/locks/review.lock.json; ter-anchor di chain 97 lewat tools/anchor_lock.py, F-D74) dan BELUM teroptimasi: vault/08-Backlog/08 - Riset Optimasi Ambang.md.
Tidak ada modul di sini yang menyentuh jaringan, kunci, atau chain.

    spec, series, data, target, freshness, quality, bots/   bot murni `targets(spec, data)`; spesifikasi ber-sha + fingerprint efektif; guard bar basi
    replay, report                                          PnL harian dengan penggaris biaya + funding nyata
    chain, sinyal                                           keccak256 / abi.encode / Merkle OZ; Signal -> batch komit-ungkap -> verifikasi pembeli
    submission                                              formulir penerbit (skema tertutup, daftar-izin Unicode, EIP-712; hanya `template` dibuka)
    gates, kpi, review                                      peninjau-bot TANPA agen: gerbang G1-G11 + KPI K1-K5 -> laporan ber-sha
    slots, economics                                        buku sepuluh slot + rolling berpasangan; bagi hasil 60/40 bilangan bulat
    book                                                    buku genesis: bot identitas Fabius = B1-TREND (instrumen kripto saja; penunjukan, bukan kelulusan)
    ledger                                                  ledger paper maju (M2): tick ex-ante <= 12 jam, settle ex-post via replay yang sama, rantai hash, verifikasi dari bar
    funding_est                                             rekonstruksi funding dari indeks premium 1m (P92): ESTIMASI untuk laporan PROVISIONAL dan target B3; settle final tetap dari aktual
    locks                                                   kunci ambang (sha atas semua angka lolos/gagal); v1 ditulis 2 Okt 2026, mengubah angka = kunci baru

Perintah (dari akar repo; `<dir>` = folder CSV keluaran vault/09-Inbox/Session-2026-10-02-skrip/fetch.py):

    python -X utf8 -m engine.cli specs
    python -X utf8 -m engine.cli replay --data <dir> --bot B1-TREND
    python -X utf8 -m engine.cli emit   --data <dir> --bot ALL --asof 2026-08-31 > batch.jsonl
    python -X utf8 -m engine.cli verify --file batch.jsonl
    python -X utf8 -m engine.cli gate   --data <dir> --bot ALL
    python -X utf8 -m engine.cli intake --file engine/examples/submission.example.json [--data <dir>]
    python -X utf8 -m engine.cli review --file engine/examples/submission.example.json --data <dir>
    python -X utf8 -m engine.cli lock                      # keadaan kunci + angka; `--write [--supersede] --note "..."` hanya atas kata builder
    python -X utf8 -m engine.cli book                      # buku genesis (bot identitas) + book_sha
    python -X utf8 -m engine.cli ledger verify|report      # ledger paper maju (ledger/paper + ledger/bars); jaringan HANYA di tools/feed_bars.py
    python -X utf8 -m engine.cli schema
    python -X utf8 -m engine.golden --data <dir>
    python -X utf8 -m unittest discover -s engine/tests -t .
"""
__all__ = ["spec", "series", "data", "target", "sinyal", "freshness", "quality", "replay", "report", "bots", "chain",
           "submission", "gates", "kpi", "review", "slots", "economics", "book", "ledger", "funding_est", "locks"]
