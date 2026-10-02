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
COPY tools/evm.py tools/signal_commit.py tools/operator_loop.py tools/paper_tick.py tools/

ENV PYTHONUTF8=1 PYTHONUNBUFFERED=1 WORKDIR=/tmp/fabius-ledger
CMD ["python", "-X", "utf8", "tools/operator_loop.py"]
