---
tags: [perkakas, "TL12"]
---

# TL12 - m3_setup

**Bagian dari:** [[04-Tools/00 - Hub Tools]]
**Sumber:** `tools/m3_setup.py`

**Ringkas:** setup M3 yang dijalankan builder: deploy LockRegistry + SignalAnchor dengan kunci deployer dari berkas env yang ia tunjuk, baca ulang, kunci committer baru di `.committer.env` (gitignored), isi saldo, kunci spesifikasi B1/B3 oleh committer, opsional variabel Railway lewat stdin.

**Poin kunci:**
- Bawaan rencana; `--go` menjalankan; idempoten (langkah yang sudah terjadi di chain dilewati).
- Gladi: salinan repo + anvil `--chain-id 97` dengan `RPC_PIN=1` (tidak pernah jatuh ke chain 97 sungguhan).

**Yang ia TOLAK lakukan:** mencetak kunci; membuat kunci bila `.committer.env` tidak di-gitignore; mengirim tanpa `--go`; mendeploy ulang kontrak yang kodenya sudah ada.

**Detail:** dijalankan 2 Okt 13:04Z (deploy) dan 15:49Z (rotasi committer). Kunci deployer = tower Lencana atas kata builder; membaca berkas itu butuh izin `/permissions`.

**Terkait:** [[TL11 - komit sinyal M3]] · [[02-Contracts/02 - Deployed on 97]] · [[00-Overview/03 - Decisions]] F-D80/F-D82
