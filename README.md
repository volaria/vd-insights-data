# md_stats — Movie Decoded veri araçları

Supermetrics'in yerini alan, IG + YT verisini resmi (ücretsiz) API'lerden çeken
mini araç seti. Günlük CSV üretir; Hetzner'de cron ile tam otomatik çalışır.

## Mimari
- `ig_stats.py`   → Instagram Graph API: Reel metrikleri + takipçi geçmişi
- `yt_stats.py`   → YouTube Analytics API: video metrikleri, ülke, trafik kaynağı
- `auth_google.py`→ tek seferlik Google yetkilendirmesi (Mac'te çalışır)
- `renew_ig_token.py` → IG token'ını 60 gün dolmadan yeniler (cron)
- Çıktılar `data/` klasörüne tarihli CSV olarak düşer.

---

## ADIM 1 — Meta app (IG tarafı) [Mac'te, ~15 dk]
1. https://developers.facebook.com → My Apps → **Create App** → tip: *Business*.
2. App'e **Instagram Graph API** ürününü ekle.
3. App Settings → Basic'ten **App ID** ve **App Secret**'ı not al.
4. https://developers.facebook.com/tools/explorer → app'ini seç →
   **User Token** al; izinler: `instagram_basic`, `instagram_manage_insights`,
   `pages_show_list`, `pages_read_engagement`, `business_management`.
5. Bu kısa ömürlü token'ı, App ID/Secret ile birlikte `config.json`'a yaz
   (şablon: `config.example.json` → kopyala `config.json` yap).
6. `python3 renew_ig_token.py` çalıştır → token long-lived (60 gün) olur.

## ADIM 2 — Google Cloud (YT tarafı) [Mac'te, ~15 dk]
1. https://console.cloud.google.com → yeni proje: `md-stats`.
2. **YouTube Analytics API** ve **YouTube Data API v3**'ü etkinleştir.
3. OAuth consent screen: External, test user olarak
   `infomoviedecoded@gmail.com` ekle.
4. Credentials → **Create OAuth client ID** → *Desktop app* →
   `client_secret.json` indir, bu klasöre koy.
5. `pip3 install -r requirements.txt`
6. `python3 auth_google.py` → tarayıcı açılır →
   **infomoviedecoded@gmail.com** ile gir, kanal seçiciden **TheMovieDecoded**'ı
   seç → `token.json` üretilir.
7. Test: `python3 yt_stats.py` ve `python3 ig_stats.py` → `data/` içinde
   CSV'ler oluşmalı.

## ADIM 3 — Hetzner kurulumu [~10 dk]
```bash
# sunucuda:
sudo mkdir -p /opt/md_stats && sudo chown $USER /opt/md_stats
# Mac'ten (md_stats klasöründeyken):
scp -r . KULLANICI@SUNUCU:/opt/md_stats/
# sunucuda:
cd /opt/md_stats
python3 -m venv venv && ./venv/bin/pip install -r requirements.txt
./venv/bin/python ig_stats.py && ./venv/bin/python yt_stats.py   # test
crontab -e   # crontab.txt içindeki satırları ekle
```

## Güvenlik notları
- `config.json`, `token.json`, `client_secret.json` **asla** repoya/paylaşıma
  girmez; sunucuda `chmod 600` yap.
- Tüm token'lar yalnızca okuma (insights/readonly) yetkisinde — yayınlama,
  silme, mesaj yetkisi YOK.

## Skip rate notu
IG API "skip rate" vermez (Supermetrics türetiyordu). Yaklaşık eşdeğeri
Insights uygulama içi izlenme eğrisidir; API tarafında `views` ile `reach`
ve `avg watch time` (ileride eklenebilir) üzerinden kendi oranımızı
hesaplayacağız. YT tarafında `avg_view_pct` zaten birebir geliyor.
