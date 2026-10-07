# Pelari kode `kind=code` (P167b, epik 12 §3.2): layanan Railway SENDIRI, TANPA rahasia, tanpa domain publik (hanya jaringan privat
# `*.railway.internal` dari gerbang fabius-x402). Image MINIMAL: stdlib Python + empat berkas; tidak ada eth-account, tidak ada alat lain, tidak ada
# repo, tidak ada kunci. Kode penerbit dijalankan proses anak berbatas (engine/kode_anak.py) di bawah pengguna non-root (batas sumber daya tidak bisa
# dinaikkan lagi). Variabel lingkungan bernama seperti rahasia = pelari MENOLAK mulai (tools/pelari_kode.py::rahasia_di_env).
# Penyiapan service Railway (Dockerfile path = railway/pelari/Dockerfile, tanpa variabel, tanpa domain publik) = langkah builder; jenis `code`
# tetap TERTUTUP sampai builder menyetujui jalur privat ini.
FROM python:3.12-slim

RUN useradd --create-home --uid 10001 pelari
WORKDIR /app
COPY engine/__init__.py engine/kode.py engine/kode_anak.py engine/
COPY tools/pelari_kode.py tools/

ENV PYTHONUTF8=1 PYTHONUNBUFFERED=1
USER pelari
CMD ["python", "-X", "utf8", "tools/pelari_kode.py"]
