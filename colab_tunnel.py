import subprocess
import time
import re
import sys

def start_cloudflare_tunnel(port=5000):
    print(f"[INFO] Mengunduh dan menginisialisasi Cloudflare Tunnel (Port {port})...")
    # Install cloudflared jika belum terinstall
    try:
        subprocess.run(["cloudflared", "--version"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("[INFO] Menginstal cloudflared...")
        subprocess.run("wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && dpkg -i cloudflared-linux-amd64.deb", shell=True, check=True)

    print("[INFO] Membuka Public Tunnel...")
    proc = subprocess.Popen(
        ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    public_url = None
    # Baca log stderr untuk menemukan URL .trycloudflare.com
    for _ in range(30):
        line = proc.stderr.readline()
        if "trycloudflare.com" in line:
            match = re.search(r'https://[a-zA-Z0-9-]+\.trycloudflare\.com', line)
            if match:
                public_url = match.group(0)
                break
        time.sleep(0.3)

    if public_url:
        print("\n" + "="*70)
        print(" CLOUDFLARE PUBLIC LIVE STREAM URL (100% GRATIS & TANPA LOGIN):")
        print(f"    STREAM URL : {public_url}/video_feed")
        print(f"    STATUS URL : {public_url}/status")
        print("="*70 + "\n")
        print(" Copy STREAM URL di atas dan tempel di Web Dashboard Laravel lokal kamu!")
        return public_url
    else:
        print("[ERROR] Gagal mendapatkan URL Cloudflare Tunnel.")
        return None

if __name__ == "__main__":
    start_cloudflare_tunnel(5000)
