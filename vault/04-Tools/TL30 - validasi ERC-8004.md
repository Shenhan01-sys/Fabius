---
tags: [perkakas, "TL30", erc-8004, validasi]
---

# TL30 - validasi ERC-8004 per komit sinyal (agen 2494)

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/erc8004_validasi.py` (`request_round`, `answer_round`, `candidates`, `RegistryView`) · `tools/verify_signals.py::run` (pemeriksa P106,
kini bisa dipanggil sebagai fungsi) · `tools/operator_loop.py::Worker.validation_step` · `.github/workflows/validasi.yml` (dipicu `paper-ledger`) ·
kartu `docs/agent-card.json` (`tools/x8004_register.py --card`) · `deployments/97.json` -> `erc8004` · tes `engine/tests/test_erc8004_validasi.py`
(6) · T8 SK-I1..SK-I5 · keputusan [[00-Overview/03 - Decisions]] F-D98 · backlog P136

**Ringkas:** tiap komit sinyal Fabius di SignalAnchor dimintakan validasi di `ValidationRegistry` ERC-8004 resmi chain 97
(`0x8004Cb1B…4272`, v2.0.0) atas nama agen **2494**, dengan `requestHash = commitId`. Validator menjawab dari pemeriksa publik P106: SAH = 100,
ALARM / TIDAK DIUNGKAP = 0, vonis belum final = tunggu. Ringkasan siapa pun: `getSummary(2494, [validator], "fabius-komit-ungkap-v1")`.

**Peran dan kunci:**
- **minta** = committer `0xCA9c…64A4` di worker Railway, tiap putaran, dibungkus sendiri (galat tidak pernah mengganggu komit/ungkap), maks 6 tx per
  putaran. Butuh `approve(committer, 2494)` dari pemilik agen `0x4bb3…c862`: **terkirim 5 Okt** tx `0xe98b5021…` (gas 54.038), baca ulang = boleh.
- **jawab** = validator `0x2d9A2f165D6d5B96717a0d95B5C59D7872d0a423`, kunci baru 5 Okt di `.validator.env` (di-gitignore) + GitHub secret
  `VALIDATOR_PK`, dijalankan workflow `validasi.yml` (GitHub Actions, bukan Railway). Diisi 0,02 tBNB dari committer, tx `0xe2f2afb4…`.
  `responseHash` = sha256 laporan JSON yang dicetak di log run (bisa dihitung ulang); `responseURI` = URL run.
- Pemicu jawab: rantai `paper-ledger` mengirim `workflow_dispatch` ke `validasi.yml` bersamaan dengan `web-snapshot.yml` (tanpa cron, F-D78).

**Klaim yang boleh:** "tiap komit Fabius dimintakan validasi di ValidationRegistry ERC-8004 resmi, dan dijawab oleh pemeriksa publik yang dijalankan
di CI publik; siapa pun bisa menjalankan pemeriksa yang sama". **Yang tidak boleh:** "trustless validation" / "divalidasi pihak ketiga" -
validatornya kunci kami sendiri di infrastruktur lain.

**Bukti 5 Okt (lokal):** 6 tes lulus; mode rencana dengan data asli = 4 komit Fabius siap diminta (B1/B3 10-02 dan 10-03), estimasi ±224k gas
per permintaan; sensus 459/0; T8 105 baris, 0 masalah.

**Bukti on-chain 5 Okt (19:39-19:42Z):** worker `2f7d3f43` meminta 4 validasi (B1/B3 bar 10-02, 10-03; tx `0x81aa9cc9…`, `0x7ae3b7a5…`,
`0x21e74f9f…`, `0x1818bf51…`); `validasi.yml` run 37229206657 menjawab keempatnya 100 (SAH; tx `0x283e7b2f…`, `0x8d12d9f3…`, `0x19ca3617…`,
`0x69ae6a87…`), laporan JSON + sha256 tercetak di log run itu; dibaca ulang lokal: `getSummary` = 4 jawaban, rata-rata 100. Deploy pertama
gagal memuat modul (`ModuleNotFoundError`: Dockerfile meng-COPY daftar sendiri) - diperbaiki + `engine/tests/test_deploy_files.py` (SK-I6).

**Terkait:** [[05-Ecosystem/01 - ERC-8004 Identity]] · [[TL29 - canary uang nyata]] · [[08-Backlog/06 - Epik Gerbang Sinyal]]
