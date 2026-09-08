# 🎓 Campus Assistant Bot

Bot Telegram untuk membantu mahasiswa mengelola aktivitas akademik dan produktivitas
harian: **Tugas**, **Jadwal Kuliah**, **Catatan**, dan **Tanya AI**.

## ✨ Fitur

- 📚 **Tugas** — catat tugas kuliah dengan deadline, tandai selesai, dan dapatkan
  pengingat otomatis (background scheduler) sebelum deadline.
- 🗓️ **Jadwal Kuliah** — simpan jadwal kuliah mingguan (hari, jam, ruangan).
- 📝 **Catatan** — simpan catatan pribadi.
- 📂 **Dokumen** — upload dan kelola PDF, DOCX, PPT/PPTX, ZIP, serta gambar
  berdasarkan semester, mata kuliah, dan kategori; tersedia pencarian, rename,
  download, dan hapus.
- 🤖 **Tanya AI** — tanya apa saja seputar akademik, dijawab melalui OpenRouter
  atau provider yang kompatibel dengan OpenAI API.
- 🔒 **Multi-user & isolasi data** — setiap pengguna hanya bisa mengakses datanya sendiri
  (difilter berdasarkan `user_id` internal, bukan `telegram_id` langsung).
- ⌨️ Navigasi via **Reply Keyboard** (menu utama) & **Inline Keyboard** (aksi per item).

## 🏗️ Arsitektur

Proyek mengikuti prinsip **clean architecture**: setiap fitur dipisah menjadi
`handler` (presentasi/Telegram) → `service` (business logic & validasi) →
`repository` (akses data) → `model` (entitas database).

```
app/
├── handlers/       # Presentasi: menerima update Telegram, memanggil service
├── services/       # Business logic & validasi input
├── repositories/    # Akses data (query SQLAlchemy), terisolasi per user
├── models/          # Entitas SQLAlchemy (User, Task, Schedule, Note)
├── keyboards/       # Reply & Inline keyboard
├── middlewares/     # DB session, resolve user, logging
├── scheduler/        # APScheduler job pengingat tugas
├── database/         # Base declarative & session factory (async)
├── config/            # Settings (.env) via pydantic-settings
└── utils/              # Logger, validator, custom exceptions
alembic/                # Migrasi database
main.py                 # Entry point (polling + scheduler)
```

## 🚀 Menjalankan

### 1. Prasyarat
- Python 3.12+
- PostgreSQL sudah berjalan
- Bot token dari [@BotFather](https://t.me/BotFather)

### 2. Instalasi

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 3. Konfigurasi environment

```bash
cp .env.example .env
# lalu isi BOT_TOKEN, DATABASE_URL, dan OPENROUTER_API_KEY di file .env
```

### 4. Migrasi database

```bash
# Buat migrasi awal (generate otomatis dari model)
alembic revision --autogenerate -m "initial tables"

# Terapkan migrasi ke database
alembic upgrade head
```

### 5. Jalankan bot

```bash
python main.py
```

## 🗄️ Skema Database

| Tabel      | Deskripsi                                     |
|------------|------------------------------------------------|
| `users`    | Data pengguna Telegram (telegram_id unik)       |
| `tasks`    | Tugas kuliah: judul, deskripsi, deadline, status|
| `schedules`| Jadwal kuliah: mata kuliah, hari, jam, ruangan  |
| `notes`    | Catatan pribadi: judul & isi                    |

Semua tabel turunan (`tasks`, `schedules`, `notes`) memiliki `user_id` (FK ke `users.id`)
dan setiap repository **selalu memfilter query berdasarkan `user_id`** — inilah mekanisme
isolasi data multi-user.

## ⏰ Pengingat Otomatis

`app/scheduler/reminder_scheduler.py` menjalankan job APScheduler setiap
`REMINDER_CHECK_INTERVAL_MINUTES` menit, mencari tugas dengan deadline dalam
`REMINDER_BEFORE_MINUTES` menit ke depan, lalu mengirim notifikasi ke pengguna terkait.

Pengiriman reminder akan mencoba ulang gangguan jaringan sementara sesuai
`REMINDER_SEND_RETRIES` dan `REMINDER_RETRY_DELAY_SECONDS`. Status reminder jadwal
kuliah juga disimpan di database agar tidak terkirim ulang setelah bot restart;
jalankan `alembic upgrade head` setelah memperbarui kode.

Dokumen disimpan pada folder `DOCUMENT_STORAGE_PATH` (default:
`storage/documents`) dan metadata-nya disimpan di database. Ukuran maksimal
default adalah 20 MB per file.

Fitur **Ringkas PDF** mengunduh PDF ke penyimpanan sementara, mengekstrak teks
dengan `pypdf`, melakukan chunking setiap 50 halaman untuk PDF di atas 100
halaman, lalu mengirim hasil terstruktur ke provider AI. File PDF sementara
dihapus oleh job cleanup setelah masa retensi (default satu jam); jika proses
gagal, file langsung dihapus. Histori lima bagian ringkasan tetap tersimpan di
database `pdf_summaries`.

## 🧩 Menambah Fitur Baru

1. Tambahkan model di `app/models/`
2. Tambahkan repository di `app/repositories/` (mewarisi `BaseRepository`)
3. Tambahkan service di `app/services/` (validasi + business logic)
4. Tambahkan keyboard di `app/keyboards/` (jika perlu)
5. Tambahkan handler di `app/handlers/` dan daftarkan router-nya di `app/bot.py`
6. Buat migrasi: `alembic revision --autogenerate -m "nama_fitur"`

## 📌 Catatan Teknis

- Semua I/O (DB, Telegram API, OpenAI API) bersifat **asynchronous**.
- AI dikonfigurasi melalui `AI_PROVIDER`. Nilai default `openrouter` menggunakan
  `OPENROUTER_API_KEY`, `OPENROUTER_MODEL`, dan endpoint OpenRouter.
- Error input pengguna ditangani via `AppError`/`ValidationError`/`NotFoundError`
  (`app/utils/exceptions.py`) dan ditangkap di layer handler untuk ditampilkan
  sebagai pesan ramah pengguna.
- Logging terpusat di `app/utils/logger.py`, mencatat setiap update masuk & error.
