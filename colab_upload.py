import json
import os

try:
    from google.colab import files
    COLAB_AVAILABLE = True
except ImportError:
    COLAB_AVAILABLE = False

def upload_and_set_video():
    print("\n" + "="*60)
    print(" SKRIP UPLOAD VIDEO TEST KE GOOGLE COLAB")
    print("="*60)
    
    if not COLAB_AVAILABLE:
        print("[ERROR] Skrip ini dirancang untuk dijalankan di Google Colab.")
        return

    print("[INFO] Silakan pilih file video (mp4/avi/mov) dari komputer kamu...")
    uploaded = files.upload()

    if not uploaded:
        print("[WARNING] Tidak ada file yang diunggah.")
        return

    # Ambil nama file video yang diunggah pertama
    filename = list(uploaded.keys())[0]
    print(f"[SUCCESS] File video '{filename}' berhasil di-upload ke Colab!")

    # Update config.json
    config_path = "config.json"
    config = {}
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            config = json.load(f)

    config["source"] = filename

    with open(config_path, "w") as f:
        json.dump(config, f, indent=4)

    print(f"[SUCCESS] config.json berhasil diperbarui! Sumber video sekarang: '{filename}'")
    print("="*60 + "\n")
    print("Sekarang kamu tinggal jalankan '!python main.py' untuk memulai stream AI!")

if __name__ == "__main__":
    upload_and_set_video()
