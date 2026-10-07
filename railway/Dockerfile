# Worker Railway Fabius (F-D80, tahap 1): komit sinyal ledger paper ke SignalAnchor (chain 97). Lihat tools/operator_loop.py.
# Image hanya berisi kode (engine/ + tiga alat); ledger dan bar diambil segar dari GitHub tiap putaran (clone sparse), kunci hanya dari variabel Railway.
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY railway/requirements.txt railway/requirements.txt
RUN pip install --no-cache-dir -r railway/requirements.txt

COPY engine engine
COPY tools/evm.py tools/signal_commit.py tools/operator_loop.py tools/paper_tick.py tools/rest_vs_vision.py tools/rest_latency.py tools/shadow_tick.py tools/feed_bars.py tools/pin_book.py tools/alert.py tools/eksekutor.py tools/venue_binance.py tools/exec_feed.py tools/canary.py tools/erc8004_validasi.py tools/x402_sinyal.py tools/sinyal_gambar.py tools/analis.py tools/privy_server.py tools/kabar.py tools/meja.py tools/meja_data.py tools/meja2.py tools/meja_slot.py tools/meja_eval.py tools/pengajuan.py tools/feed_gerbang.py tools/pin_spec.py tools/agen_luar.py tools/peninjau_llm.py tools/
COPY config/agents.json config/agents.json

ENV PYTHONUTF8=1 PYTHONUNBUFFERED=1 WORKDIR=/tmp/fabius-ledger
# FABIUS_JOB memilih skrip di tools/ (bawaan: worker `operator_loop`). Service lain di proyek yang sama memakai image ini dengan variabelnya sendiri,
# mis. `fabius-probe`: FABIUS_JOB=rest_vs_vision FABIUS_ARGS="--from-github --exit-zero" (jalan sekali, tanpa variabel rahasia), atau
# FABIUS_JOB=shadow_tick (mode bayangan tahap 2+3, jalan terus, tanpa variabel rahasia).
CMD ["sh", "-c", "exec python -X utf8 tools/${FABIUS_JOB:-operator_loop}.py ${FABIUS_ARGS:-}"]
