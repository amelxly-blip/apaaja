# Lua Source Cleaner

Web app kecil untuk membantu memulihkan source Lua milik sendiri atau yang memang kamu punya izin untuk analisis. Ia menghapus komentar, merapikan token, menyederhanakan angka konstan, mendecode escape desimal, dan menampilkan indikator obfuscation.

## Jalankan lokal

```bash
npm start
```

Buka `http://localhost:3000`.

## Deploy ke Railway

Push folder ini ke GitHub, lalu pilih repository tersebut di Railway. Railway akan mendeteksi `Dockerfile` dan mengisi `PORT` secara otomatis.

Tool ini tidak menjalankan Lua dan tidak menjamin pemulihan source asli 100%; nama variabel, struktur, atau informasi yang hilang karena obfuscation tidak selalu bisa direkonstruksi.
