@echo off
rem Snapshot SATU jendela universe BSC, lalu keluar.
rem
rem Kenapa bentuknya "sekali jalan" dan bukan loop panjang: dua percobaan sebelumnya memakai
rem `record_bsc_universe.py --loop` sebagai proses latar, dan keduanya mati saat sesi terminal
rem ditutup - yang kedua menelan 16,2 jam data (perkiraan 15 jendela jam yang tidak bisa dibeli
rem kembali). Loop panjang menaruh nasib koleksi data pada umur proses. Satu panggilan per jam
rem tidak.
rem
rem dijadwalkan oleh: schtasks /create /tn FabiusUniverse /sc hourly ...
rem log: universe\runner.log (di-`gitignore`, lihat _research/universe/README.md)
cd /d "C:\Users\hansg\HansProject\Bnb-Indonesia-Hackathon\Fabius\universe"
python -u record_bsc_universe.py >> runner.log 2>&1
