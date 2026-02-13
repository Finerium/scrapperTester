# Kesimpulan: Web Scraper drugs.com

## 1. Metode dan Approach yang Digunakan

### Library Utama

| Library | Versi | Fungsi |
|---|---|---|
| **Patchright** | >= 0.5.0 | Browser automation + bypass Cloudflare |
| **BeautifulSoup4** | >= 4.12.0 | Parsing HTML dan ekstraksi data |
| **lxml** | >= 5.0.0 | HTML parser backend (lebih cepat dari html.parser bawaan) |

### Teknik Bypass Cloudflare

Scraper ini menggunakan **Patchright**, yaitu fork dari Playwright yang sudah di-patch di level source code. Teknik bypass-nya bekerja sebagai berikut:

1. **Patch CDP `Runtime.enable`** — Cloudflare mendeteksi browser automation dengan memeriksa apakah browser mengirim perintah `Runtime.enable` melalui Chrome DevTools Protocol (CDP). Semua automation tool standar (Selenium, Playwright, Puppeteer) mengirim perintah ini secara otomatis. Patchright menghilangkan perintah tersebut dan sebagai gantinya mengeksekusi JavaScript di **isolated ExecutionContexts**, sehingga tidak ada jejak automation yang bisa dideteksi.

2. **Persistent Browser Context** — Menggunakan `launch_persistent_context()` yang menyimpan cookies dan session di disk (`/tmp/drugs_scraper_profile`). Begitu Cloudflare challenge berhasil dilewati sekali, session berikutnya dalam sesi yang sama tidak perlu melewati challenge lagi.

3. **Real Chrome, Bukan Chromium** — Browser diluncurkan dengan parameter `channel="chrome"` yang memaksa penggunaan Google Chrome asli yang terinstall di sistem, bukan Chromium bawaan Playwright. Anti-bot system bisa mendeteksi perbedaan fingerprint antara Chrome dan Chromium.

4. **Disable Automation Flag** — Argument `--disable-blink-features=AutomationControlled` menghilangkan flag `navigator.webdriver=true` yang biasanya di-set oleh browser yang dikontrol automation tool.

5. **Tidak Ada Custom User-Agent** — Sengaja tidak men-set custom user-agent karena Patchright secara eksplisit memperingatkan bahwa mengubah user-agent menciptakan inkonsistensi fingerprint yang justru bisa terdeteksi.

6. **Cloudflare Challenge Detection** — Setelah navigasi ke sebuah halaman, scraper memeriksa apakah halaman menampilkan Cloudflare challenge ("Just a moment...", "Checking your browser..."). Jika terdeteksi, scraper menunggu hingga 8 detik sampai challenge selesai sebelum mengambil konten halaman.

### Teknik Anti-Detection Tambahan

- **Random delay 3–7 detik** antar setiap request untuk meniru perilaku browsing manusia
- **Delay tambahan 1–3 detik** antara halaman detail dan halaman side effects obat yang sama
- **Exponential backoff** pada retry: jika request gagal, tunggu 5 detik, lalu 10 detik, lalu 20 detik sebelum mencoba lagi (maksimal 3 retry)

---

## 2. Kenapa Metode Ini Dipilih

### Kenapa `requests` + BeautifulSoup Biasa Tidak Bisa

Library `requests` mengirim HTTP request polos tanpa menjalankan JavaScript. Cloudflare protection bekerja dengan cara:

1. **JavaScript Challenge** — Saat pertama kali mengakses situs, Cloudflare menyajikan halaman HTML yang berisi JavaScript kompleks. JavaScript ini harus dieksekusi oleh browser untuk menghasilkan token (cookie `cf_clearance`). Library `requests` tidak bisa menjalankan JavaScript sama sekali, sehingga tidak pernah melewati challenge ini.

2. **Browser Fingerprinting** — Bahkan jika JavaScript bisa dijalankan, Cloudflare memeriksa ratusan sinyal browser: WebGL rendering, canvas fingerprint, font enumeration, screen resolution, plugin list, dan lainnya. `requests` tidak memiliki semua sinyal ini karena bukan browser sungguhan.

3. **TLS Fingerprinting** — Cloudflare juga memeriksa TLS handshake. Library Python menghasilkan TLS fingerprint yang berbeda dari browser asli, dan ini langsung terdeteksi sebagai bot.

Hasilnya: `requests` selalu mendapat response kosong, halaman challenge HTML, atau HTTP 403 Forbidden.

### Kenapa CloudScraper Tidak Lagi Efektif

CloudScraper dulunya bisa menyelesaikan Cloudflare JavaScript challenge versi lama (challenge v1). Namun Cloudflare terus memperbarui sistemnya — versi terbaru (Turnstile dan managed challenge) melibatkan evaluasi JavaScript yang jauh lebih kompleks, termasuk proof-of-work computation dan browser environment checks yang tidak bisa disimulasikan oleh CloudScraper.

### Kenapa Selenium WebDriver Biasa Terdeteksi

Selenium menggunakan ChromeDriver yang secara default men-set property `navigator.webdriver = true` di browser. Selain itu, Selenium mengirim CDP command `Runtime.enable` yang menjadi sinyal utama deteksi. Meskipun `navigator.webdriver` bisa di-override dengan JavaScript injection, CDP leak tetap terdeteksi. Cloudflare secara spesifik memeriksa sinyal ini.

### Kenapa Patchright Dipilih (Bukan undetected-chromedriver)

| Aspek | undetected-chromedriver | Patchright |
|---|---|---|
| **Mekanisme** | Memodifikasi binary ChromeDriver | Mem-patch source code Playwright |
| **CDP Leak** | Masih mengirim `Runtime.enable` (hanya menutupi sebagian) | Menghilangkan `Runtime.enable` sepenuhnya |
| **Reliabilitas 2025–2026** | Semakin sering terdeteksi karena signature binarynya sudah dikenal | Masih efektif karena bekerja di level yang lebih fundamental |
| **Headless Mode** | Mudah terdeteksi | Lebih sulit terdeteksi dengan `channel="chrome"` |
| **API** | Berbasis Selenium (API lama) | Berbasis Playwright (API modern, async/sync) |
| **Maintenance** | Sporadis | Aktif di-maintain |

Intinya: Patchright mengatasi masalah di **akar penyebabnya** (CDP `Runtime.enable` leak), sementara undetected-chromedriver hanya memodifikasi **gejala di permukaan** (binary ChromeDriver). Pendekatan Patchright lebih tahan lama terhadap update deteksi Cloudflare.

---

## 3. Struktur Data yang Di-scrape

Setiap obat disimpan sebagai `DrugInfo` dataclass dengan 7 field:

| Field | Tipe | Sumber | Contoh |
|---|---|---|---|
| `name` | `str` | Tag `<h1>` di halaman detail | `"Acetaminophen"` |
| `generic_name` | `str` atau `null` | Elemen `<p class="drug-subtitle">` atau pola teks "Generic name: ..." | `"acetaminophen"` |
| `url` | `str` | URL halaman detail obat | `"https://www.drugs.com/acetaminophen.html"` |
| `description` | `str` atau `null` | Paragraf setelah heading "What is [drug]?" | `"Acetaminophen is a pain reliever..."` |
| `drug_class` | `str` atau `null` | Link ke `/drug-class/` atau baris tabel "Drug class" | `"Miscellaneous analgesics"` |
| `rating` | `float` atau `null` | Elemen rating (pola `X.X/10`) | `7.3` |
| `side_effects` | `list[str]` | List item dari halaman `/sfx/[drug]-side-effects.html` | `["nausea", "rash", "headache"]` |

### Alur Pengambilan Data

```
/alpha/a.html ──→ Daftar link obat (nama + URL)
       │
       ▼
/[drug].html ───→ name, generic_name, description, drug_class, rating
       │
       ▼
/sfx/[drug]-side-effects.html ──→ side_effects (list)
       │
       ▼
   DrugInfo ──→ CSV (append per obat) + JSON (ditulis di akhir)
```

### Format Output

**CSV** (`output/drugs_data.csv`):
```
name,generic_name,url,description,drug_class,rating,side_effects
Acetaminophen,acetaminophen,https://www.drugs.com/acetaminophen.html,"Acetaminophen is a pain reliever...",Miscellaneous analgesics,7.3,"nausea; rash; headache"
```
Side effects di CSV dipisahkan dengan titik koma (`;`) untuk menghindari konflik dengan delimiter koma CSV.

**JSON** (`output/drugs_data.json`):
```json
[
  {
    "name": "Acetaminophen",
    "generic_name": "acetaminophen",
    "url": "https://www.drugs.com/acetaminophen.html",
    "description": "Acetaminophen is a pain reliever...",
    "drug_class": "Miscellaneous analgesics",
    "rating": 7.3,
    "side_effects": ["nausea", "rash", "headache"]
  }
]
```

---

## 4. Cara Menjalankan Script

### Prasyarat

- **Python 3.9** atau lebih baru
- **Google Chrome** terinstall di sistem (bukan Chromium)

### Instalasi

```bash
# 1. Install dependencies Python
pip install -r requirements.txt

# 2. Install browser binary untuk Patchright
patchright install chromium
```

### Menjalankan Scraper

**Langkah 1 — Test dulu dengan browser visible (recommended):**
```bash
python main.py --no-headless --letters x
```
Ini akan membuka browser yang terlihat dan hanya scrape huruf X (jumlah obat sedikit). Perhatikan apakah Cloudflare challenge berhasil dilewati. Jika halaman drugs.com ter-load dengan benar (bukan halaman "Checking your browser..."), berarti bypass berhasil.

**Langkah 2 — Jalankan secara headless:**
```bash
python main.py --letters x
```

**Langkah 3 — Full scrape (semua huruf a–z):**
```bash
python main.py
```

**Resume setelah terhenti:**
```bash
python main.py --resume
```

**Debug dengan logging verbose:**
```bash
python main.py --no-headless --log-level DEBUG --letters a
```

### Opsi CLI Lengkap

| Flag | Default | Keterangan |
|---|---|---|
| `--no-headless` | `False` | Tampilkan jendela browser (untuk debugging) |
| `--letters a,b,c` | semua a–z | Hanya scrape huruf tertentu |
| `--resume` | `False` | Lanjutkan dari checkpoint terakhir |
| `--log-level` | `INFO` | Level logging: `DEBUG`, `INFO`, `WARNING`, `ERROR` |

### Hasil Output

Setelah scraping selesai, file output ada di:
- `output/drugs_data.csv` — Data dalam format CSV
- `output/drugs_data.json` — Data dalam format JSON
- `output/progress.json` — Checkpoint progress (untuk resume)
- `logs/scraper.log` — Log lengkap proses scraping

---

## 5. Limitasi dan Catatan Penting

### Limitasi Teknis

1. **Durasi scraping sangat lama** — drugs.com memiliki 24.000+ obat. Setiap obat membutuhkan minimal 2 page load (halaman detail + halaman side effects), dan setiap request diberi delay 3–7 detik untuk menghindari blocking. Estimasi full scrape: **40–93 jam** untuk semua huruf a–z. Fitur `--resume` sangat penting untuk mengatasi ini.

2. **CSS selectors bisa berubah** — Selectors di `parser.py` didasarkan pada pola konvensi drugs.com yang diketahui (prefix `ddc-`). Jika drugs.com mengubah struktur HTML-nya, selectors perlu di-update secara manual. Setiap field sudah memiliki multiple fallback selectors untuk mengurangi risiko ini.

3. **Tidak semua obat punya data lengkap** — Beberapa obat mungkin tidak punya rating, generic name, drug class, atau halaman side effects. Field yang tidak ditemukan akan bernilai `null` (JSON) atau kosong (CSV). Scraper tidak akan error karenanya.

4. **Halaman side effects mungkin tidak ada** — URL `/sfx/[drug]-side-effects.html` tidak selalu tersedia untuk semua obat. Jika halaman ini tidak ditemukan, field `side_effects` akan berupa list kosong, dan scraper melanjutkan ke obat berikutnya tanpa error.

5. **Headless mode mungkin terdeteksi** — Meskipun Patchright dirancang untuk bekerja di headless mode, beberapa konfigurasi Cloudflare yang ketat mungkin masih bisa mendeteksinya. Jika ini terjadi, gunakan `--no-headless` untuk menjalankan dengan browser visible. Di server Linux tanpa GUI, gunakan virtual display (`xvfb`).

### Catatan Penting

1. **Google Chrome harus terinstall** — Patchright membutuhkan Google Chrome asli (bukan Chromium) karena menggunakan parameter `channel="chrome"`. Jika Chrome tidak terinstall, browser tidak bisa diluncurkan.

2. **Jangan ubah user-agent** — Dokumentasi Patchright secara eksplisit memperingatkan agar tidak men-set custom user-agent. Mengubahnya menciptakan inkonsistensi fingerprint yang justru memudahkan deteksi.

3. **Rate limiting dan etika** — Delay 3–7 detik sudah cukup sopan untuk sebagian besar kasus, tetapi jika drugs.com mulai mengembalikan HTTP 429 (Too Many Requests) atau memblokir IP, naikkan nilai `MIN_DELAY` dan `MAX_DELAY` di `config.py`.

4. **Checkpoint untuk crash recovery** — CSV di-append per obat sehingga data yang sudah berhasil di-scrape tidak hilang jika proses crash. Progress disimpan di `output/progress.json` setelah setiap obat. Gunakan `--resume` untuk melanjutkan dari titik terakhir.

5. **Cloudflare bisa berevolusi** — Teknik bypass yang bekerja hari ini mungkin tidak bekerja besok. Cloudflare terus memperbarui metode deteksinya. Arsitektur scraper ini memisahkan layer browser (`browser.py`) dari layer parsing (`parser.py`), sehingga jika Patchright suatu hari tidak lagi efektif, library browser bisa diganti tanpa mengubah logika parsing dan penyimpanan data.

6. **Pertimbangan legal** — robots.txt drugs.com secara eksplisit memblokir banyak bot crawler. Penggunaan scraper ini sepenuhnya menjadi tanggung jawab pengguna. Pastikan penggunaan data hasil scraping sesuai dengan ketentuan layanan drugs.com dan regulasi yang berlaku.
