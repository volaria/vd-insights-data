#!/usr/bin/env python3
"""
Token'ın görebildiği tüm Facebook sayfalarını ve bağlı IG hesaplarını listeler.
Çıktıdaki ig_user_id'leri config.json'daki "accounts" listesine kopyala.

Kullanım:
    python3 discover_accounts.py
"""
import json
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
CONFIG = json.loads((BASE / "config.json").read_text())
TOKEN = CONFIG["instagram"]["access_token"]
GRAPH = "https://graph.facebook.com/v21.0"

r = requests.get(f"{GRAPH}/me/accounts", params={
    "fields": "name,instagram_business_account{id,username,followers_count}",
    "access_token": TOKEN, "limit": 50,
}, timeout=30).json()

if "error" in r:
    raise SystemExit(f"API hatası: {r['error']}")

print(f"{'Facebook Sayfası':<25} {'IG hesabı':<22} {'ig_user_id':<20} Takipçi")
print("-" * 80)
for page in r.get("data", []):
    ig = page.get("instagram_business_account")
    if ig:
        print(f"{page['name']:<25} @{ig.get('username',''):<21} "
              f"{ig['id']:<20} {ig.get('followers_count','?')}")
    else:
        print(f"{page['name']:<25} — IG BAĞLI DEĞİL (IG uygulamasından sayfaya bağla)")
