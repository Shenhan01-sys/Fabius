# Vault Fabius — isi dan pagar scope

Vault ini milik **jalur AI Agents / agentic trading saja**. Ia hidup di dalam repo supaya setiap
klaim punya alamat: angka di notes ini harus bisa ditelusuri ke berkas atau artefak di repo yang
sama.

## Yang TIDAK boleh masuk ke sini

Kredensial, Open Badges 3.0, VC/JSON-LD, status-list, soulbound mint, e-course, peserta didik,
penerbit lisensi, atau apa pun dari jalur Consumer Apps / Combined. Termasuk: tidak menyalin
kesimpulan vault induk ke dalam file di sini.

Alasannya bukan kerapian. Repo publik yang isinya tercampur membuat riwayat commit tidak bisa
dibaca sebagai bukti orisinalitas — dan itu satu-satunya bukti jenis itu yang kita punya. Keputusan
yang sama sudah diambil untuk `AgenticTrack/`; ini meneruskannya, bukan menandinginya.

Kalau sebuah fakta jalur lain memaksa keputusan di sini (mis. registry ERC-8004 dipakai bersama),
yang ditulis adalah **fakta yang kita ukur sendiri** + tautan keluar, bukan salinan catatannya.

## Struktur

| Berkas | Isi |
|---|---|
| `01-Klaim-Dan-Batas.md` | apa yang boleh diucapkan, apa yang dilarang, dan kenapa |
| `02-Ambang.md` | tiap angka ambang + `file:line` asal + tanggal diverifikasi |
| `03-Dataset.md` | jendela jam, skema 1/2/3, baris salah-label, aturan dedupe, rantai sha256 |
| `04-Kontrak.md` | apa yang ditegakkan `DecisionAnchor`, apa yang tidak |
| `05-Belum-Terbukti.md` | lubang yang masih menganga + cara menutupnya |
| `06-Keputusan.md` | log keputusan jalur ini, penomoran `F-D##` sendiri |
| `07-Deploy-97.md` | alamat & biaya nyata di chain 97 + koreksi tooling (RPC/User-Agent) + **17 anchor** keputusan (Enter=3 / Abstain=14) + `--verify` tanpa kunci |
| `08-Kelas-Aset-dan-Kursi.md` | 7 bidang data, 8 kelas aset, aturan 5 kursi & ambang rotasinya (asal tiap angka disebut) + cara menilai ⑦ tanpa kontrol |
| `09-Uji-Arah-Tidak-Ada-Edge.md` | **hasil negatif** uji aturan arah di 400 hari × 12 aset (3 varian) + hasil pertama 2 prediksi yang di-anchor + vonis ⑦ smart money vs kerumunan |
| `10-Pra-Registrasi-Uji-Aliran.md` | hipotesis & ambang **dikunci SEBELUM hasil dilihat**, lalu vonisnya: aliran kerumunan gagal 3-3-nya — termasuk daftar penyimpangan kami sendiri saat menjalankan |

## Aturan penulisan

1. **Angka tanpa artefak bukan temuan.** Setiap angka membawa tanggal dan dari mana ia datang:
   `fork test` / `HTTP probe` / `dibaca dari dokumen` / `dihitung dari dataset lokal`. Yang
   terakhir itu level terlemah di sini dan harus ditulis begitu.
2. **"Belum diuji" adalah hasil, bukan aib.** Kolom kosong yang dilabeli lebih berguna daripada
   kolom terisi yang tidak bisa dipertahankan.
3. **Koreksi dicatat, tidak dihapus diam-diam.** Kalau sebuah angka digugurkan pengukuran
   berikutnya, catatan lamanya ditandai salah + apa yang menggantikannya.
4. **Tidak ada angka yang dikutip dari dokumen turunan.** Dokumen membulatkan hasil run jadi
   prosa; konstanta wajib diambil dari kode yang menghitungnya.
