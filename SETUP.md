# 🤖 HERMES Voice Interface for Hermes Desktop

Dokumentasi dan panduan setup aplikasi pendamping (Companion App) untuk menghubungkan mikrofon lokal dan UI Kustom HERMES ke **Hermes Desktop** melalui jalur integrasi **Discord API / Webhook**.

---

## 📐 Arsitektur Integrasi

Aplikasi ini bertindak sebagai jembatan (bridge) antara input lokal di PC lo dengan Hermes Desktop yang berjalan di background menggunakan platform Discord sebagai perantara.

[ Suara Lo ] ──> ( Bilang "Hermes" ) ──> [ Python / openWakeWord ]
                                                           │
                                                ( Auto Munculin UI Jarvis )
                                                           │
      [ Perintah Suara ] ──> ( STT Converter ) ────────────┘
                                   │
                                   ▼
                [ Kirim via Discord Webhook HTTP POST ]
                                   │
                                   ▼
                           ( Server Discord )
                                   │
                     [ Dibaca & Dijawab Hermes ]
                                   │
                                   ▼
         ( Python UI Dengerin Channel via Discord Gateway )
                                   │
         ┌─────────────────────────┴─────────────────────────┐
         ▼                                                   ▼
[ Teks Masuk ke UI Log ]                           [ TTS Bunyiin Suara ]

---

## 📂 Struktur Project (`E:\Hermes-Voice\`)

Pastiin struktur file di VS Code lo udah sesuai kayak gini bre:

```text
E:\Hermes-Voice\
│
├── app.py           # Backend utama (FastAPI) untuk handle Mic & Discord Bridge
├── requirements.txt # Daftar library Python yang wajib diinstall
└── static/          # Folder khusus Frontend UI
    ├── index.html   # UI Futuristik HERMES
    ├── style.css    # Styling tema Iron Man / Cyberpunk
    └── app.js       # Logic WebSocket & update UI secara Real-time