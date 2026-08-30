#!/usr/bin/env python3
"""
YouTube Analytics -> CSV
Video listesi + video başına metrikler, ülke kırılımı, trafik kaynakları.

Çıktılar (data/):
    yt_videos_YYYY-MM-DD.csv
    yt_geo_YYYY-MM-DD.csv
    yt_traffic_YYYY-MM-DD.csv

Kullanım:
    python3 yt_stats.py
"""
import csv
import json
from datetime import date
from pathlib import Path

from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

BASE = Path(__file__).resolve().parent
CONFIG = json.loads((BASE / "config.json").read_text())
YT = CONFIG["youtube"]
OUT = BASE / CONFIG.get("output_dir", "data")
OUT.mkdir(exist_ok=True)

SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly",
    "https://www.googleapis.com/auth/youtube.readonly",
]
START_DATE = "2025-01-01"


def creds() -> Credentials:
    c = Credentials.from_authorized_user_file(str(BASE / YT["token_file"]), SCOPES)
    if c.expired and c.refresh_token:
        c.refresh(Request())
        (BASE / YT["token_file"]).write_text(c.to_json())
    return c


def video_titles(youtube) -> dict[str, dict]:
    """uploads playlist -> {video_id: {title, published}}"""
    ch = youtube.channels().list(part="contentDetails", mine=True).execute()
    uploads = ch["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    out, page = {}, None
    while True:
        res = youtube.playlistItems().list(
            part="snippet", playlistId=uploads, maxResults=50, pageToken=page
        ).execute()
        for it in res.get("items", []):
            sn = it["snippet"]
            out[sn["resourceId"]["videoId"]] = {
                "title": sn["title"],
                "published": sn["publishedAt"],
            }
        page = res.get("nextPageToken")
        if not page:
            return out


def run_report(analytics, **kw) -> list[list]:
    res = analytics.reports().query(
        ids="channel==MINE", startDate=START_DATE,
        endDate=date.today().isoformat(), **kw
    ).execute()
    return res.get("rows", []) or []


def write_csv(name: str, header: list[str], rows: list[list]) -> None:
    path = OUT / f"{name}_{date.today().isoformat()}.csv"
    with path.open("w", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        w.writerows(rows)
    print(f"OK — {len(rows)} satır: {path}")


def main() -> None:
    c = creds()
    youtube = build("youtube", "v3", credentials=c)
    analytics = build("youtubeAnalytics", "v2", credentials=c)

    titles = video_titles(youtube)

    vid_rows = run_report(
        analytics,
        dimensions="video",
        metrics=("views,engagedViews,estimatedMinutesWatched,"
                 "averageViewPercentage,likes,shares,subscribersGained"),
        sort="-views", maxResults=200,
    )
    enriched = []
    for r in vid_rows:
        meta = titles.get(r[0], {})
        enriched.append([meta.get("title", r[0]), meta.get("published", "")] + r[1:])
    write_csv("yt_videos",
              ["title", "published", "views", "engaged_views", "minutes_watched",
               "avg_view_pct", "likes", "shares", "subs_gained"], enriched)

    geo = run_report(analytics, dimensions="country",
                     metrics="views,estimatedMinutesWatched",
                     sort="-views", maxResults=50)
    write_csv("yt_geo", ["country", "views", "minutes_watched"], geo)

    traffic = run_report(analytics, dimensions="insightTrafficSourceType",
                         metrics="views,estimatedMinutesWatched", sort="-views")
    write_csv("yt_traffic", ["source", "views", "minutes_watched"], traffic)


if __name__ == "__main__":
    main()
