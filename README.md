# 🚀 MultipleLite - Auto Login Bot

MultipleLite adalah bot otomatis yang membantu login ke platform multiple.cc dengan cepat dan efisien.  
Menggunakan **multi-threading**, **proxy support**, dan **progress bar** untuk pengalaman yang lebih baik.

---

## 🌟 Fitur Utama
✅ **Login otomatis** ke multiple.cc dengan private key  
✅ **Dukungan Proxy** (Proxy Gratis, Proxy Pribadi, atau Tanpa Proxy)  
✅ **Multi-threading** dengan `ThreadPoolExecutor` untuk kecepatan maksimal  
✅ **Progress bar (`tqdm`)** untuk memantau proses login  
✅ **Looping otomatis** (Script berjalan terus menerus)  
✅ **Log berwarna (`colorama`)** agar lebih jelas  

---

## 📥 Instalasi

### **1️⃣ Clone Repository**
```bash
git clone https://github.com/Yuurichan-N3/Multiple-Bot.git
cd Multiple-Lite
```

2️⃣ Install Dependencies

Pastikan Python 3.8+ sudah terinstal, lalu jalankan:

```bahs
pip install -r requirements.txt
```

3️⃣ Siapkan Private Key

Buka file privateKeys.txt, lalu tambahkan private key setiap akun di sana (1 akun per baris).

Contoh privateKeys.txt:

0x123456789abcdef123456789abcdef123456789abcdef123456789abcdef1234
0xabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcdefabcd

4️⃣ Jalankan Script

python bot.py

Saat pertama kali dijalankan, script akan meminta pilihan proxy:
1️⃣ Proxy Gratis (Diunduh otomatis)
2️⃣ Proxy Pribadi (Menggunakan proxy.txt)
3️⃣ Tanpa Proxy

Setelah memilih, script akan memproses semua akun di privateKeys.txt dan mengulang otomatis setiap 10 menit.


---

## ⚙️ Konfigurasi Tambahan

Gunakan proxy pribadi: Tambahkan daftar proxy ke proxy.txt (1 proxy per baris).

Ganti delay loop: Edit await asyncio.sleep(600) di main.py jika ingin mengganti waktu jeda.



---

## 📜 Lisensi  

Script ini didistribusikan untuk keperluan pembelajaran dan pengujian. Penggunaan di luar tanggung jawab pengembang.  

Untuk update terbaru, bergabunglah di grup **Telegram**: [Klik di sini](https://t.me/sentineldiscus).


---

## 💡 Disclaimer
Penggunaan bot ini sepenuhnya tanggung jawab pengguna. Kami tidak bertanggung jawab atas penyalahgunaan skrip ini.
