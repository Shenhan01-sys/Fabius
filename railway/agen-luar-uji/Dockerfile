# Layanan agent luar UJI 2573 milik builder (P151 + P166): meja PULL 24/7 + pilihan analis harian ke SelectionAnchor + alasan publik di
# /reasons/<bar_close>.json. Service Railway SENDIRI; satu-satunya rahasia = AGEN_LUAR_UJI_KEY (layanan MENOLAK MULAI bila ada variabel lain
# bernamakan rahasia). Image minimal: stdlib Python + eth-account / eth-abi (tanda tangan + ABI) + empat berkas tools.
# Penyiapan (langkah builder): RAILWAY_DOCKERFILE_PATH=railway/agen-luar-uji/Dockerfile, volume di /data, domain publik, deploy
# `python -X utf8 tools/railway_up.py --service agen-luar-uji`.
FROM python:3.12-slim

RUN pip install --no-cache-dir eth-account==0.13.7 eth-abi==5.2.0 \
 && useradd --create-home --uid 10001 agen \
 && mkdir -p /data/alasan && chown -R agen /data
WORKDIR /app
COPY tools/agen_luar_layanan.py tools/desk_agent_client.py tools/agen_luar_uji_jawab.py tools/evm.py tools/

ENV PYTHONUTF8=1 PYTHONUNBUFFERED=1 ALASAN_DIR=/data/alasan
USER agen
CMD ["python", "-X", "utf8", "tools/agen_luar_layanan.py"]
