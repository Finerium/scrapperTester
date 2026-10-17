import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

plt.rcParams["font.family"] = "DejaVu Sans"
KON, RES, ENV, TRN = "#cfe3f5", "#f7d4d0", "#e6e6e6", "#e9dcf3"
EDGE = {KON: "#3b6e9c", RES: "#b5483c", ENV: "#777777", TRN: "#7c5ba0"}

# nama, warna, struktur, fungsi, perubahan udara, zona
N = [
 ("Lingkungan", ENV, "Udara atmosfer (±21% O₂)", "Sumber O₂, tempat buang CO₂", "Mengikuti kondisi sekitar", "—"),
 ("Hidung", KON, "Rongga hidung, konka, rambut, mukosa bersilia", "Jalur masuk, saring, hangatkan, lembapkan", "Hangat, lembap, partikel besar tersaring", "Konduksi"),
 ("Faring", KON, "Nasofaring, orofaring, laringofaring", "Saluran bersama udara dan makanan", "Tetap dihangatkan dan dilembapkan", "Konduksi"),
 ("Laring", KON, "Epiglotis, pita suara, tulang rawan", "Cegah makanan masuk; produksi suara", "Aliran diatur celah pita suara", "Konduksi"),
 ("Trakea", KON, "Cincin tulang rawan C, epitel bersilia, sel goblet", "Menyalurkan udara; mukus jebak partikel", "Partikel kecil dan kuman tersaring", "Konduksi"),
 ("Bronkus", KON, "Bronkus utama, lobar, segmental", "Membagi udara ke tiap paru dan lobus", "Dibersihkan lagi oleh mukosiliar", "Konduksi"),
 ("Bronkiolus", TRN, "Otot polos, tanpa tulang rawan", "Atur diameter dan resistensi aliran", "Hampir jenuh uap air, suhu ≈ tubuh", "Konduksi → transisi"),
 ("Alveolus", RES, "Pneumosit I dan II, surfaktan, kapiler paru", "Pertukaran O₂ dan CO₂", "O₂ turun; CO₂ dan uap air naik", "Respirasi"),
]

W, H = 12, 16.3
fig = plt.figure(figsize=(W, H), dpi=150)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, W); ax.set_ylim(0, H); ax.axis("off")
ax.text(W/2, H-0.6, "Jalur Udara dan Mekanisme Respirasi", ha="center", fontsize=22, fontweight="bold")

def box(x, y, w, h, fc, ec, lw=1.6):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.15", fc=fc, ec=ec, lw=lw))

# header kolom
top = H - 1.3
for x, t in [(3.7, "Struktur penting"), (6.3, "Fungsi"), (8.75, "Perubahan pada udara"), (11.0, "Zona")]:
    ax.text(x, top, t, ha="center", va="center", fontsize=11, fontweight="bold", color="#333")

rh, gap = 1.05, 0.38
y = top - 0.45 - rh
ys = []
for name, col, st, fu, ch, zn in N:
    ec = EDGE[col]
    box(0.4, y, 1.9, rh, col, ec, 2.2)
    ax.text(1.35, y+rh/2, name, ha="center", va="center", fontsize=14, fontweight="bold")
    for cx, txt, wd in [(3.7, st, 2.4), (6.3, fu, 2.5), (8.75, ch, 2.3), (11.0, zn, 1.7)]:
        box(cx-wd/2, y+0.08, wd, rh-0.16, "white", ec, 1.0)
        import textwrap
        ax.text(cx, y+rh/2, textwrap.fill(txt, 24 if wd > 2 else 16), ha="center", va="center", fontsize=9.3, linespacing=1.25)
    ys.append(y); y -= rh + gap

for a, b in zip(ys[:-1], ys[1:]):
    ax.add_patch(FancyArrowPatch((1.35, a-0.03), (1.35, b+rh+0.03), arrowstyle="-|>", mutation_scale=22, lw=2.4, color="#444"))

# legenda
ly = ys[-1] - 0.55
for x, col, t in [(0.4, KON, "Zona konduksi (tanpa pertukaran gas)"), (4.9, TRN, "Transisi (bronkiolus respiratorius)"), (9.0, RES, "Zona respirasi (pertukaran gas)")]:
    box(x, ly, 0.3, 0.3, col, EDGE[col], 1.4)
    ax.text(x+0.42, ly+0.15, t, va="center", fontsize=9.5)

# alur 4 proses
py = ly - 1.7
ax.text(W/2, py+1.25, "Perbedaan istilah dalam proses respirasi", ha="center", fontsize=14, fontweight="bold")
steps = [("Ventilasi", "Gerak udara masuk dan keluar paru"),
         ("Respirasi eksternal", "Pertukaran gas alveolus ↔ darah"),
         ("Transport gas", "Angkut O₂ dan CO₂ lewat sirkulasi"),
         ("Respirasi internal", "Pertukaran gas darah ↔ jaringan")]
bw, bg = 2.5, 0.5
x0 = (W - (4*bw + 3*bg)) / 2
import textwrap
for i, (t, d) in enumerate(steps):
    x = x0 + i*(bw+bg)
    box(x, py, bw, 1.15, "#fff4d6", "#b08a1e", 1.8)
    ax.text(x+bw/2, py+0.82, t, ha="center", va="center", fontsize=11, fontweight="bold")
    ax.text(x+bw/2, py+0.36, textwrap.fill(d, 24), ha="center", va="center", fontsize=8.6, linespacing=1.2)
    if i < 3:
        ax.add_patch(FancyArrowPatch((x+bw+0.04, py+0.57), (x+bw+bg-0.04, py+0.57), arrowstyle="-|>", mutation_scale=18, lw=2.2, color="#444"))
ax.text(W/2, py-0.45, "Ventilasi tidak sama dengan respirasi seluler (pemakaian O₂ di sel untuk menghasilkan ATP).", ha="center", fontsize=10, style="italic")
fig.savefig("output/Diagram_Sistem_Respirasi.png")
