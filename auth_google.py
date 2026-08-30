#!/usr/bin/env python3
"""
Tek seferlik Google yetkilendirmesi — Mac Studio'da çalıştırılır.
infomoviedecoded@gmail.com hesabıyla (kanal seçiciden TheMovieDecoded'ı seç!)
giriş yapılır; token.json üretilir. Bu dosya sunucuya kopyalanır,
sonrası tamamen otomatik yenilenir.

Kullanım:
    python3 auth_google.py
"""
import json
from pathlib import Path

from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]

BASE = Path(__file__).resolve().parent
CONFIG = json.loads((BASE / "config.json").read_text())
CLIENT_SECRET = BASE / CONFIG["youtube"]["client_secret_file"]
TOKEN_FILE = BASE / CONFIG["youtube"]["token_file"]


def main() -> None:
    if not CLIENT_SECRET.exists():
        raise SystemExit(
            f"client_secret.json bulunamadı: {CLIENT_SECRET}\n"
            "Google Cloud Console > APIs & Services > Credentials'tan indirip "
            "bu klasöre koy."
        )
    flow = InstalledAppFlow.from_client_secrets_file(str(CLIENT_SECRET), SCOPES)
    creds = flow.run_local_server(port=0, prompt="consent")
    TOKEN_FILE.write_text(creds.to_json())
    print(f"OK — token kaydedildi: {TOKEN_FILE}")
    print("Bu dosyayı (token.json) sunucudaki md_stats klasörüne kopyala.")


if __name__ == "__main__":
    main()
