#!/usr/bin/env python3
"""
IG long-lived token'ı (60 gün) süresi dolmadan yeniler ve config.json'a yazar.
Cron ile ayda bir çalıştırılır — token hâlâ geçerliyken yenilenmelidir.

Kullanım:
    python3 renew_ig_token.py
"""
import json
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
CONFIG_PATH = BASE / "config.json"
CONFIG = json.loads(CONFIG_PATH.read_text())
IG = CONFIG["instagram"]

r = requests.get(
    "https://graph.facebook.com/v21.0/oauth/access_token",
    params={
        "grant_type": "fb_exchange_token",
        "client_id": IG["app_id"],
        "client_secret": IG["app_secret"],
        "fb_exchange_token": IG["access_token"],
    },
    timeout=30,
)
data = r.json()
if "access_token" not in data:
    raise SystemExit(f"Yenileme başarısız: {data}")

CONFIG["instagram"]["access_token"] = data["access_token"]
CONFIG_PATH.write_text(json.dumps(CONFIG, indent=2))
print(f"OK — token yenilendi (geçerlilik ~{data.get('expires_in', '?')} sn).")
