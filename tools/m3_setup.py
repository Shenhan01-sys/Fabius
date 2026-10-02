"""Setup M3 di chain 97 (F-D80) - DIJALANKAN BUILDER, bukan worker:
  1. deploy `LockRegistry` + `SignalAnchor` (maxLag 12 jam, jendela ungkap 7 hari) dengan kunci deployer dari berkas env yang builder tunjuk
     (mis. deployer Lencana yang punya tBNB) - lalu dibaca ulang dan dicatat di `deployments/97.json` (ter-track, alamat publik);
  2. kunci committer BARU di `.committer.env` (gitignored; tidak pernah dicetak; hanya alamatnya);
  3. saldo committer diisi dari deployer;
  4. spesifikasi B1-TREND dan B3-CARRY dikunci OLEH committer di LockRegistry (SignalAnchor hanya menerima komit dari pengunci spesifikasi);
  5. opsional `--railway-service`: kunci committer + dua alamat dipasang sebagai variabel Railway (nilai lewat stdin, tidak pernah dicetak).

Default = RENCANA (tidak mengirim apa pun). `--go` menjalankan. Idempoten: langkah yang sudah terjadi di chain dilewati, jadi aman diulang.

Kenapa builder yang menjalankan, bukan sesi asisten: kunci deployer ada di proyek lain (Lencana) dan pemeriksa otomatis sesi menolak asisten membaca
berkas kredensial proyek lain (2 Okt). Alat ini membaca SATU variabel dari berkas yang builder tunjuk sendiri, di mesin builder, dan tidak mencetaknya.

Pakai (dari akar repo Fabius):
  python -X utf8 tools/m3_setup.py --deployer-env ../app/.env                     # rencana: alamat, saldo, langkah
  python -X utf8 tools/m3_setup.py --deployer-env ../app/.env --go                # deploy + committer + saldo + kunci spesifikasi
  python -X utf8 tools/m3_setup.py --railway-service fabius-engine --go           # variabel Railway (worker redeploy otomatis)
  (nama variabel kunci di berkas env bukan DEPLOYER_PRIVATE_KEY? tambah --deployer-var NAMA)
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import secrets
import shutil
import subprocess
import sys
import time

for _s in (sys.stdout, sys.stderr):
    try:
        _s.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

from engine import chain, ledger                       # noqa: E402
from engine.spec import SPECS                          # noqa: E402
import signal_commit as sc                             # noqa: E402

MAX_LAG_S = 12 * 3600
REVEAL_WINDOW_S = 7 * 86400
ARTIFACTS = {"LockRegistry": os.path.join(ROOT, "out", "LockRegistry.sol", "LockRegistry.json"),
             "SignalAnchor": os.path.join(ROOT, "out", "SignalAnchor.sol", "SignalAnchor.json")}
SECP256K1_N = 0xFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFFEBAAEDCE6AF48A03BBFD25E8CD0364141
REPO_URL = "https://github.com/Shenhan01-sys/Fabius"
WEI = 10**18


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def tbnb(wei: int) -> str:
    return f"{wei / WEI:.6f} tBNB"


def artifact(name: str) -> dict:
    p = ARTIFACTS[name]
    if not os.path.isfile(p):
        print(f"artefak {os.path.relpath(p, ROOT)} belum ada -> forge build")
        subprocess.run(["forge", "build"], cwd=ROOT, check=True)
    with open(p, encoding="utf-8") as f:
        a = json.load(f)
    return {"bytecode": bytes.fromhex(a["bytecode"]["object"][2:]), "deployed": bytes.fromhex(a["deployedBytecode"]["object"][2:])}


def read_deployments() -> tuple:
    with open(sc.DEPLOYMENTS, "rb") as f:
        raw = f.read()
    return json.loads(raw.decode("utf-8")), raw.endswith(b"\n")


def write_deployments(d: dict, trailing_nl: bool) -> None:
    text = json.dumps(d, indent=1, sort_keys=True, ensure_ascii=False) + ("\n" if trailing_nl else "")
    with open(sc.DEPLOYMENTS, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def new_private_key() -> str:
    while True:
        k = int.from_bytes(secrets.token_bytes(32), "big")
        if 0 < k < SECP256K1_N:
            return "0x" + k.to_bytes(32, "big").hex()


def git_ignored(path: str) -> bool:
    r = subprocess.run(["git", "check-ignore", "-q", os.path.relpath(path, ROOT)], cwd=ROOT)
    return r.returncode == 0


def head_commit() -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, check=True, capture_output=True, text=True).stdout.strip()


def ok_or_die(r: dict, what: str) -> dict:
    from evm import receipt_ok
    if not receipt_ok(r):
        raise SystemExit(f"BERHENTI: {what} status 0 (tx {r.get('transactionHash')})")
    return r


# ---------------------------------------------------------------- langkah

def step_deploy(ev, dep_pk: str, go: bool, d: dict) -> dict:
    """-> {'LockRegistry': addr, 'SignalAnchor': addr} (yang sudah ada dipakai ulang bila kodenya ada di chain)."""
    from eth_abi import encode
    from eth_utils import to_checksum_address
    cs = d.setdefault("contracts", {})
    have = {k: cs.get(k) for k in ("LockRegistry", "SignalAnchor")}
    if all(have.values()) and all(ev.code_size(a) > 0 for a in have.values()):
        print(f"deploy : sudah ada - LockRegistry {have['LockRegistry']}, SignalAnchor {have['SignalAnchor']}")
        return have
    lr, sa = artifact("LockRegistry"), artifact("SignalAnchor")
    print(f"deploy : LockRegistry ({len(lr['deployed'])} B) lalu SignalAnchor ({len(sa['deployed'])} B, maxLag {MAX_LAG_S} s, jendela {REVEAL_WINDOW_S} s)")
    if not go:
        return have
    r1 = ok_or_die(ev.send(dep_pk, None, lr["bytecode"]), "deploy LockRegistry")
    reg = to_checksum_address(r1["contractAddress"])
    print(f"  LockRegistry {reg}  tx {r1['transactionHash']}  blok {ev.num(r1['blockNumber'])}")
    r2 = ok_or_die(ev.send(dep_pk, None, sa["bytecode"] + encode(["address", "uint64", "uint64"], [reg, MAX_LAG_S, REVEAL_WINDOW_S])),
                   "deploy SignalAnchor")
    anc = to_checksum_address(r2["contractAddress"])
    print(f"  SignalAnchor {anc}  tx {r2['transactionHash']}  blok {ev.num(r2['blockNumber'])}")
    # baca ulang: kode LockRegistry harus byte-sama dengan artefak (tanpa immutable); SignalAnchor: panjang sama + tiga immutable benar
    if ev.code(reg) != lr["deployed"]:
        raise SystemExit("BERHENTI: kode LockRegistry di chain beda dari artefak build lokal")
    if ev.code_size(anc) != len(sa["deployed"]):
        raise SystemExit("BERHENTI: panjang kode SignalAnchor di chain beda dari artefak")
    got = (ev.call_decode(anc, "registry()", (), (), ("address",))[0], ev.call_decode(anc, "maxLag()", (), (), ("uint64",))[0],
           ev.call_decode(anc, "revealWindow()", (), (), ("uint64",))[0])
    if (got[0].lower(), got[1], got[2]) != (reg.lower(), MAX_LAG_S, REVEAL_WINDOW_S):
        raise SystemExit(f"BERHENTI: immutable SignalAnchor tidak sesuai: {got}")
    print("  baca ulang cocok: kode LockRegistry = artefak; SignalAnchor.registry/maxLag/revealWindow benar")
    cs["LockRegistry"], cs["SignalAnchor"] = reg, anc
    v = d.setdefault("verification", {})
    v["LockRegistry"], v["SignalAnchor"] = f"bytecode {len(lr['deployed'])} B", f"bytecode {len(sa['deployed'])} B"
    m3 = d.setdefault("m3", {})
    m3.update({"deployer": to_checksum_address(r1["from"]), "deploy_tx": {"LockRegistry": r1["transactionHash"], "SignalAnchor": r2["transactionHash"]},
               "deploy_block": {"LockRegistry": ev.num(r1["blockNumber"]), "SignalAnchor": ev.num(r2["blockNumber"])},
               "maxLag_s": MAX_LAG_S, "revealWindow_s": REVEAL_WINDOW_S, "written_utc": utc_now(),
               "why": "M3 (F-D79/F-D80): pra-registrasi spesifikasi (LockRegistry) + komit-ungkap sinyal per bot per bar (SignalAnchor)"})
    return {"LockRegistry": reg, "SignalAnchor": anc}


def step_committer(go: bool) -> str:
    """-> kunci committer (dibuat bila belum ada). Tidak pernah dicetak."""
    pk = sc.read_env_file(sc.COMMITTER_ENV, sc.KEY_VAR)
    if pk:
        return pk
    if not git_ignored(sc.COMMITTER_ENV):
        raise SystemExit("BERHENTI: .committer.env TIDAK di-gitignore - kunci tidak dibuat (satu `git add -A` = kunci publik)")
    if not go:
        print("committer: belum ada -> akan dibuat di .committer.env (gitignored)")
        return ""
    pk = new_private_key()
    from evm import address_of
    addr = address_of(pk)
    with open(sc.COMMITTER_ENV, "w", encoding="utf-8", newline="\n") as f:
        f.write("# Kunci committer SignalAnchor Fabius (M3, F-D80). JANGAN di-commit, JANGAN dicetak, JANGAN ditempel ke chat.\n"
                f"# Alamat: {addr}. Salinan lain hanya variabel Railway {sc.KEY_VAR}. Mengganti kunci = ungkap dulu semua komit yang masih terbuka.\n"
                f"{sc.KEY_VAR}={pk}\n")
    print(f"committer: kunci BARU ditulis ke .committer.env (gitignored) - alamat {addr}")
    return pk


def step_fund(ev, dep_pk: str, committer: str, go: bool, fund_wei: int, min_wei: int) -> None:
    bal = ev.balance(committer)
    if bal >= min_wei:
        print(f"saldo  : committer {tbnb(bal)} (>= {tbnb(min_wei)}) - tidak diisi")
        return
    amt = fund_wei - bal
    print(f"saldo  : committer {tbnb(bal)} -> isi {tbnb(amt)} dari deployer")
    if go:
        r = ok_or_die(ev.send(dep_pk, committer, b"", value=amt, gas=21_000), "isi saldo committer")
        time.sleep(4)          # RPC publik ber-load-balancer: beri waktu node lain melihat saldo baru sebelum estimasi gas lock()
        print(f"  tx {r['transactionHash']}  saldo sekarang {tbnb(ev.balance(committer))}")


def step_locks(ev, pk: str, committer: str, registry: str, go: bool, d: dict) -> None:
    from evm import calldata
    m3 = d.setdefault("m3", {})
    locks = m3.setdefault("locks", {})
    commit = head_commit()
    for bot in sc.BOTS_DEFAULT:
        recs = ledger.load(os.path.join(ROOT, "ledger", "paper", f"{bot}.jsonl"))
        spec_sha = SPECS[bot].sha()
        if recs and recs[0].get("spec_sha") != spec_sha:
            raise SystemExit(f"BERHENTI: spec_sha ledger {bot} != kode (pivot?) - tidak dikunci")
        at = ev.call_decode(registry, sc.SIG_LOCKED_AT, ("address", "bytes32", "bytes32"), (committer, chain.ascii32(bot), chain.from_hex(spec_sha)), ("uint64",))[0]
        if at:
            print(f"kunci  : {bot} sudah dikunci committer pada {ledger.utc_iso(at * 1000)}")
            locks.setdefault(bot, {"specSha": spec_sha, "lockedAt": at, "lockedAt_utc": ledger.utc_iso(at * 1000)})
            continue
        uri = f"{REPO_URL}/blob/{commit}/engine/spec.py#{bot}"
        print(f"kunci  : {bot} spec {spec_sha[:18]}… -> lock() oleh committer (uri {uri[:70]}…)")
        if not go:
            continue
        r = ok_or_die(ev.send(pk, registry, calldata(sc.SIG_LOCK, ("bytes32", "bytes32", "string"), (chain.ascii32(bot), chain.from_hex(spec_sha), uri))),
                      f"lock {bot}")
        at = ev.call_decode(registry, sc.SIG_LOCKED_AT, ("address", "bytes32", "bytes32"), (committer, chain.ascii32(bot), chain.from_hex(spec_sha)), ("uint64",))[0]
        print(f"  tx {r['transactionHash']}  lockedAt {at} = {ledger.utc_iso(at * 1000)}")
        locks[bot] = {"specSha": spec_sha, "lockedAt": at, "lockedAt_utc": ledger.utc_iso(at * 1000), "tx": r["transactionHash"], "uri": uri}


def step_railway(service: str, pk: str, addrs: dict, go: bool) -> int:
    """Kunci + alamat -> variabel Railway. Nilai lewat stdin; keluaran CLI tidak dicetak mentah (nilai rahasia disensor bila muncul)."""
    kv = [("SIGNAL_ANCHOR_ADDRESS", addrs["SignalAnchor"]), ("LOCK_REGISTRY_ADDRESS", addrs["LockRegistry"]), (sc.KEY_VAR, pk)]
    exe = shutil.which("railway")              # di Windows CLI npm = railway.cmd; CreateProcess tidak menemukan "railway" polos
    if go and not exe:
        print("BERHENTI: CLI railway tidak ditemukan di PATH")
        return 2
    for i, (k, v) in enumerate(kv):
        last = i == len(kv) - 1
        print(f"railway: {k} -> service {service}" + ("" if k != sc.KEY_VAR else " (nilai rahasia, lewat stdin)") + ("" if go else "  [rencana]"))
        if not go:
            continue
        cmd = [exe, "variable", "set", k, "--stdin", "--service", service] + ([] if last else ["--skip-deploys"])
        r = subprocess.run(cmd, cwd=ROOT, input=v, text=True, capture_output=True)
        if r.returncode != 0:
            msg = (r.stderr or r.stdout or "").replace(pk, "***")[:300]
            print(f"  GAGAL ({r.returncode}): {msg}")
            return 1
        print("  ok" + (" - redeploy dipicu (worker mulai dengan kunci)" if last else ""))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Setup M3 chain 97 (default = rencana; --go menjalankan).")
    ap.add_argument("--deployer-env", help="berkas env berisi kunci deployer (mis. ../app/.env)")
    ap.add_argument("--deployer-var", default="DEPLOYER_PRIVATE_KEY")
    ap.add_argument("--fund", type=float, default=0.05, help="isi saldo committer sampai sekian tBNB")
    ap.add_argument("--min", type=float, default=0.02, help="isi hanya bila saldo committer di bawah ini")
    ap.add_argument("--railway-service", help="pasang kunci committer + alamat ke variabel service Railway ini")
    ap.add_argument("--go", action="store_true", help="jalankan (tanpa ini: rencana, tidak mengirim apa pun)")
    a = ap.parse_args()
    import evm as evmmod

    d, nl = read_deployments()
    if a.railway_service:
        pk = sc.read_env_file(sc.COMMITTER_ENV, sc.KEY_VAR)
        cs = d.get("contracts", {})
        if not pk or not cs.get("SignalAnchor") or not cs.get("LockRegistry"):
            print("BERHENTI: jalankan dulu langkah deploy/committer (--deployer-env ... --go)")
            return 2
        return step_railway(a.railway_service, pk, cs, a.go)

    if not a.deployer_env:
        ap.error("--deployer-env wajib untuk deploy/committer/saldo/kunci")
    dep_pk = sc.read_env_file(a.deployer_env, a.deployer_var)
    if not dep_pk:
        print(f"BERHENTI: variabel {a.deployer_var} tidak ada di {a.deployer_env} (beri --deployer-var NAMA)")
        return 2
    ev = evmmod.Evm(sc.rpc_urls(), sc.CHAIN_ID)
    ev.chain_check()
    dep = evmmod.address_of(dep_pk)
    dep_bal, gp = ev.balance(dep), ev.gas_price()
    print(f"chain  : {sc.CHAIN_ID} | deployer {dep} saldo {tbnb(dep_bal)} | gas {gp / 1e9:.2f} gwei")
    need = int(a.fund * WEI) + 3_000_000 * gp            # dua deploy (~1,6 juta gas terukur lokal) + isi committer, dengan cadangan
    if dep_bal < need:
        print(f"{'BERHENTI' if a.go else 'PERINGATAN'}: saldo deployer < {tbnb(need)} (deploy + isi committer)." + (" Tidak ada yang dikirim." if a.go else ""))
        if a.go:
            return 2

    def save() -> None:                                   # tulis segera sesudah tiap langkah yang mengubah chain: proses mati di tengah tidak menghilangkan alamat
        if a.go:
            write_deployments(d, nl)

    addrs = step_deploy(ev, dep_pk, a.go, d)
    save()
    pk = step_committer(a.go)
    committer = evmmod.address_of(pk) if pk else None
    if committer:
        d.setdefault("m3", {})["committer"] = committer
        save()
        step_fund(ev, dep_pk, committer, a.go, int(a.fund * WEI), int(a.min * WEI))
        if addrs.get("LockRegistry"):
            step_locks(ev, pk, committer, addrs["LockRegistry"], a.go, d)
            save()
        else:
            print(f"kunci  : {', '.join(sc.BOTS_DEFAULT)} akan dikunci committer sesudah deploy")
    else:
        print(f"saldo  : committer baru akan diisi {a.fund} tBNB dari deployer\nkunci  : {', '.join(sc.BOTS_DEFAULT)} akan dikunci committer")
    if a.go:
        print(f"\nditulis: deployments/97.json (alamat + committer + kunci; publik). Berikutnya: commit + push berkas itu, lalu\n"
              f"  python -X utf8 tools/m3_setup.py --railway-service fabius-engine --go")
    else:
        print("\nRENCANA: tidak ada yang dikirim atau ditulis. Ulangi dengan --go.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
