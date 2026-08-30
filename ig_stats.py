#!/usr/bin/env python3
"""
Instagram Insights -> CSV
Hesap özeti + tüm Reel'lerin metriklerini çeker.

Çıktılar (data/):
    ig_media_YYYY-MM-DD.csv   — Reel başına metrikler
    ig_account_history.csv    — günlük takipçi/medya sayısı (append)

Kullanım:
    python3 ig_stats.py
"""
import csv
import json
import sys
from datetime import date
from pathlib import Path

import requests

BASE = Path(__file__).resolve().parent
CONFIG = json.loads((BASE / "config.json").read_text())
IG = CONFIG["instagram"]
ACCOUNTS = IG.get("accounts") or [{"name": "MD", "ig_user_id": IG["ig_user_id"]}]
OUT = BASE / CONFIG.get("output_dir", "data")
OUT.mkdir(exist_ok=True)

GRAPH = "https://graph.facebook.com/v21.0"
MEDIA_INSIGHT_METRICS = "views,reach,saved,shares,comments,likes,total_interactions"


class IGApiError(Exception):
    def __init__(self, err: dict):
        self.err = err
        super().__init__(str(err))


def api_get(path: str, **params) -> dict:
    params.setdefault("access_token", IG["access_token"])
    r = requests.get(f"{GRAPH}/{path}", params=params, timeout=30)
    data = r.json()
    if "error" in data:
        msg = data["error"].get("message", "")
        if "expired" in msg.lower() or data["error"].get("code") == 190:
            sys.exit(
                "HATA: IG access token geçersiz/süresi dolmuş.\n"
                "renew_ig_token.py çalıştır (token hâlâ geçerliyken) ya da "
                "Graph Explorer'dan yeni token al."
            )
        raise IGApiError(data["error"])
    return data


def account_snapshot(acc: dict) -> None:
    d = api_get(acc["ig_user_id"], fields="followers_count,media_count,username")
    path = OUT / "ig_account_history.csv"
    new = not path.exists()
    with path.open("a", newline="") as f:
        w = csv.writer(f)
        if new:
            w.writerow(["date", "account", "username", "followers", "media_count"])
        w.writerow([date.today().isoformat(), acc["name"], d.get("username"),
                    d.get("followers_count"), d.get("media_count")])
    print(f"[{acc['name']}] {d.get('followers_count')} takipçi, "
          f"{d.get('media_count')} medya")


def media_list(ig_user_id: str) -> list[dict]:
    items, url_params = [], {
        "fields": "id,caption,timestamp,media_type,media_product_type,permalink",
        "limit": 50,
    }
    data = api_get(f"{ig_user_id}/media", **url_params)
    items.extend(data.get("data", []))
    while data.get("paging", {}).get("next"):
        r = requests.get(data["paging"]["next"], timeout=30)
        data = r.json()
        items.extend(data.get("data", []))
    return items


def media_insights(media_id: str) -> dict:
    try:
        data = api_get(f"{media_id}/insights", metric=MEDIA_INSIGHT_METRICS)
    except IGApiError as e:
        sub = e.err.get("error_subcode")
        if sub == 2108006:  # hesap dönüşümünden önce atılmış medya
            print(f"  (atlandı — dönüşüm öncesi medya: {media_id})")
        else:
            print(f"  (uyarı — {media_id}: {e.err.get('message')})")
        return {}
    out = {}
    for m in data.get("data", []):
        vals = m.get("values", [{}])
        out[m["name"]] = vals[0].get("value") if vals else None
    return out


def fetch_account(acc: dict) -> None:
    account_snapshot(acc)
    rows = []
    for m in media_list(acc["ig_user_id"]):
        if m.get("media_product_type") not in (None, "REELS", "FEED"):
            continue
        ins = media_insights(m["id"]) if m.get("media_type") == "VIDEO" or \
            m.get("media_product_type") == "REELS" else {}
        caption = (m.get("caption") or "").split("\n")[0][:80]
        rows.append({
            "published": m.get("timestamp"),
            "caption": caption,
            "views": ins.get("views"),
            "reach": ins.get("reach"),
            "saved": ins.get("saved"),
            "shares": ins.get("shares"),
            "comments": ins.get("comments"),
            "likes": ins.get("likes"),
            "total_interactions": ins.get("total_interactions"),
            "permalink": m.get("permalink"),
            "media_id": m["id"],
        })
    if not rows:
        print(f"[{acc['name']}] medya bulunamadı")
        return
    path = OUT / f"ig_media_{acc['name']}_{date.today().isoformat()}.csv"
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"OK — [{acc['name']}] {len(rows)} medya yazıldı: {path}")


def main() -> None:
    for acc in ACCOUNTS:
        fetch_account(acc)


if __name__ == "__main__":
    main()
