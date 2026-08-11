# SKYNET Simple Presence Monitoring

Sistem deteksi status keberadaan karyawan dari video CCTV berbasis Upper-Body detection (YOLOv8) dan zona kursi statis.

## Konsep Utama
- **Status Presence**: **BEKERJA** (Hijau) & **TIDAK DI TEMPAT** (Merah).
- **Upper Body Detection**: Menggunakan YOLOv8 Person (class 0) yang dipotong menjadi upper-body secara otomatis.
- **Zona Kursi Statis**: Zona diset sekali per kamera di `config.json` (atau via `zone_drawer.py`).
- **Logika Robust**: Histeresis counter (toleransi flicker) & 1-to-1 Zone Matching (mencegah klaim ganda).

## Struktur Project
```text
Monitoring/
├── config.json              # Konfigurasi zona kursi & threshold
├── main.py                  # Entrypoint aplikasi utama
├── zone_drawer.py           # GUI gambar zona kursi
├── visualizer.py            # Rendering visualisasi box & top info bar
├── requirements.txt         # Package dependencies
├── detectors/
│   └── person_detector.py   # YOLOv8 Person Detector & Upper Body Crop
└── rules/
    └── rule_zone_presence.py # Engine pencocokan 1-to-1 & histeresis status
```

## Cara Penggunaan

1. **Install Dependensi**:
   ```bash
   pip install -r requirements.txt
   ```

2. **Gambar Zona Kursi (Opsional)**:
   ```bash
   python zone_drawer.py video.mp4
   ```

3. **Jalankan Monitoring**:
   ```bash
   python main.py --source video.mp4
   ```
