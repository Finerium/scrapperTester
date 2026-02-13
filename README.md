# drugs.com Web Scraper

Web scraper Python untuk mengambil data obat-obatan dari drugs.com. Menggunakan **Patchright** (fork Playwright yang sudah di-patch) untuk bypass Cloudflare protection.

## Data yang Di-scrape

| Field | Deskripsi |
|---|---|
| `name` | Nama obat (brand name) |
| `generic_name` | Nama generik |
| `url` | URL halaman obat |
| `description` | Deskripsi / "What is [drug]?" |
| `drug_class` | Kelas obat |
| `rating` | Rating pengguna (skala 10) |
| `side_effects` | Daftar efek samping umum |

## Prerequisites

- Python 3.9+
- Google Chrome terinstall di sistem

## Instalasi

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Install browser untuk Patchright
patchright install chromium
```

## Cara Pakai

### Test dulu (recommended)

Jalankan dengan browser visible dan satu huruf saja untuk verify Cloudflare bypass berhasil:

```bash
python main.py --no-headless --letters x
```

### Scrape semua (a-z)

```bash
python main.py
```

### Scrape huruf tertentu

```bash
python main.py --letters a,b,c
```

### Resume setelah interrupt

Kalau proses terhenti (Ctrl+C, error, dll), lanjutkan dari checkpoint:

```bash
python main.py --resume
```

### Debug mode

```bash
python main.py --no-headless --log-level DEBUG --letters a
```

## CLI Options

| Option | Default | Deskripsi |
|---|---|---|
| `--no-headless` | `False` | Tampilkan browser (untuk debugging) |
| `--letters` | `a-z` | Huruf yang mau di-scrape (comma-separated) |
| `--resume` | `False` | Lanjutkan dari checkpoint terakhir |
| `--log-level` | `INFO` | Level logging: DEBUG, INFO, WARNING, ERROR |

## Output

Hasil disimpan di folder `output/`:

- `output/drugs_data.csv` - Format CSV (di-append per obat, crash-resilient)
- `output/drugs_data.json` - Format JSON (ditulis di akhir proses)
- `output/progress.json` - Checkpoint untuk resume

### Format CSV

```csv
name,generic_name,url,description,drug_class,rating,side_effects
Acetaminophen,acetaminophen,https://www.drugs.com/acetaminophen.html,"...",Miscellaneous analgesics,7.3,"nausea; rash; headache"
```

### Format JSON

```json
[
  {
    "name": "Acetaminophen",
    "generic_name": "acetaminophen",
    "url": "https://www.drugs.com/acetaminophen.html",
    "description": "...",
    "drug_class": "Miscellaneous analgesics",
    "rating": 7.3,
    "side_effects": ["nausea", "rash", "headache"]
  }
]
```

## Struktur Project

```
scrapperTester/
├── main.py              # Entry point + CLI
├── config.py            # Konfigurasi (URL, delay, paths)
├── browser.py           # Patchright browser + Cloudflare bypass
├── scraper.py           # Orchestrasi scraping
├── parser.py            # BeautifulSoup HTML parsing
├── storage.py           # CSV/JSON writer + progress checkpoint
├── models.py            # DrugInfo dataclass
├── utils.py             # Retry, delay, logging
├── requirements.txt     # Dependencies
└── output/              # Hasil scraping
```

## Kenapa Patchright?

| | requests/BS4 | Selenium | undetected-chromedriver | **Patchright** |
|---|---|---|---|---|
| Cloudflare bypass | Gagal | Gagal | Sering gagal | Berhasil |
| Cara kerja | HTTP biasa | WebDriver protocol | Patch ChromeDriver binary | Patch CDP Runtime.enable leak |
| Deteksi | Instant | `navigator.webdriver=true` | Signature dikenal | Isolated ExecutionContexts |

Patchright mem-patch leak `Runtime.enable` CDP command yang digunakan Cloudflare untuk mendeteksi automation tools.

## Konfigurasi

Edit `config.py` untuk mengubah:

- `MIN_DELAY` / `MAX_DELAY` - Delay antar request (default: 3-7 detik)
- `MAX_RETRIES` - Jumlah retry kalau gagal (default: 3)
- `CLOUDFLARE_WAIT` - Waktu tunggu Cloudflare challenge (default: 8 detik)
- `HEADLESS` - Default headless mode (default: True)

## Troubleshooting

**Browser tidak bisa launch:**
- Pastikan Google Chrome terinstall
- Jalankan `patchright install chromium`

**Cloudflare masih blocking:**
- Coba `--no-headless` dulu untuk lihat apakah ada challenge
- Naikkan `CLOUDFLARE_WAIT` di `config.py`
- Kurangi kecepatan: naikkan `MIN_DELAY` dan `MAX_DELAY`

**Data kosong / selector tidak match:**
- Jalankan dengan `--log-level DEBUG` untuk lihat detail
- Inspect page source manual lewat browser (klik kanan > View Source)
- Update CSS selectors di `parser.py` sesuai struktur HTML terbaru

**Resume tidak jalan:**
- Pastikan pakai flag `--resume`
- Check `output/progress.json` masih ada
