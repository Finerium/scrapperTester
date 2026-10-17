from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

D = "/usr/share/fonts/truetype/dejavu/"
pdfmetrics.registerFont(TTFont("S", D + "DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("SB", D + "DejaVuSerif-Bold.ttf"))
pdfmetrics.registerFont(TTFont("SI", D + "DejaVuSerif.ttf"))
pdfmetrics.registerFontFamily("S", normal="S", bold="SB", italic="SI", boldItalic="SB")

base = ParagraphStyle("b", fontName="S", fontSize=9.5, leading=14)
h1 = ParagraphStyle("h1", parent=base, fontName="SB", fontSize=14, leading=18, spaceAfter=4)
h2 = ParagraphStyle("h2", parent=base, fontName="SB", fontSize=11, leading=15, spaceBefore=10, spaceAfter=4)
cell = ParagraphStyle("c", parent=base, fontSize=8.5, leading=11.5)
cellb = ParagraphStyle("cb", parent=cell, fontName="SB")
ref = ParagraphStyle("r", parent=base, fontSize=9, leading=13, leftIndent=18, firstLineIndent=-18, spaceAfter=3)

P = lambda t, s=cell: Paragraph(t, s)
story = [
    P("Sistem Respirasi — Bagian 2: Jalur Udara dan Mekanisme Respirasi", h1),
    P("Ringkasan materi (siap dijadikan diagram)", ParagraphStyle("sub", parent=base, fontName="SI")),
    P("A. Jalur Udara", h2),
    P("<b>Lingkungan → Hidung → Faring → Laring → Trakea → Bronkus → Bronkiolus → Alveolus</b>", base),
    Spacer(1, 6),
]

rows = [
    ["Bagian", "Struktur penting", "Fungsi", "Perubahan pada udara", "Zona"],
    ["Lingkungan", "Udara atmosfer (±21% O₂)", "Sumber O₂ dan tempat pembuangan CO₂", "Suhu, kelembapan, dan partikel mengikuti kondisi sekitar", "—"],
    ["Hidung", "Rongga hidung, konka, rambut hidung, mukosa bersilia", "Jalur masuk udara, penyaring, penghangat, pelembap", "Dihangatkan, dilembapkan, partikel besar tersaring", "Konduksi"],
    ["Faring", "Nasofaring, orofaring, laringofaring", "Saluran bersama udara dan makanan; tonsil untuk imunitas", "Udara masih dilembapkan dan dihangatkan", "Konduksi"],
    ["Laring", "Epiglotis, pita suara, tulang rawan", "Mencegah makanan masuk saluran napas; produksi suara", "Aliran udara diatur oleh celah pita suara", "Konduksi"],
    ["Trakea", "Cincin tulang rawan C, epitel bersilia, sel goblet", "Menyalurkan udara; mukus menjebak partikel, silia menyapunya ke atas", "Partikel kecil dan kuman tersaring; kelembapan terjaga", "Konduksi"],
    ["Bronkus", "Bronkus utama kanan-kiri, percabangan lobar dan segmental", "Membagi udara ke tiap paru dan lobus", "Disaring dan dibersihkan lebih lanjut oleh mukosiliar", "Konduksi"],
    ["Bronkiolus", "Otot polos, tanpa tulang rawan; bronkiolus terminal → respiratorius", "Mengatur diameter jalan napas dan resistensi aliran", "Udara hampir jenuh uap air, suhu mendekati suhu tubuh", "Konduksi (terminal); transisi (respiratorius)"],
    ["Alveolus", "Pneumosit tipe I dan II, surfaktan, kapiler paru", "Tempat pertukaran O₂ dan CO₂; surfaktan menurunkan tegangan permukaan", "Kaya CO₂ dan uap air, O₂ lebih rendah daripada udara inspirasi", "Respirasi"],
]
data = [[P(c, cellb if (i == 0 or j == 0) else cell) for j, c in enumerate(r)] for i, r in enumerate(rows)]
t = Table(data, colWidths=[2.5*cm, 3.5*cm, 3.7*cm, 3.6*cm, 2.7*cm], repeatRows=1)
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dfe8f1")),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8a8a8a")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f6f6f6")]),
]))
story += [t, Spacer(1, 4),
    P("Catatan: zona konduksi (hidung sampai bronkiolus terminal) hanya menyalurkan, menghangatkan, melembapkan, dan menyaring udara, tanpa pertukaran gas. Zona respirasi (bronkiolus respiratorius, duktus alveolaris, alveolus) adalah tempat pertukaran gas.", base),
    P("B. Perbedaan Istilah", h2)]

rows2 = [
    ["Istilah", "Pengertian", "Lokasi"],
    ["Ventilasi", "Pergerakan udara masuk dan keluar sistem respirasi", "Jalan napas dan paru"],
    ["Respirasi eksternal", "Pertukaran gas antara permukaan respirasi (alveolus) dan darah", "Alveolus ↔ kapiler paru"],
    ["Transport gas", "Pengangkutan O₂ dan CO₂ melalui sistem sirkulasi", "Darah"],
    ["Respirasi internal", "Pertukaran gas antara darah dan jaringan tubuh", "Kapiler sistemik ↔ sel"],
]
data2 = [[P(c, cellb if (i == 0 or j == 0) else cell) for j, c in enumerate(r)] for i, r in enumerate(rows2)]
t2 = Table(data2, colWidths=[3.4*cm, 8.2*cm, 4.4*cm], repeatRows=1)
t2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dfe8f1")),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#8a8a8a")),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
]))
story += [t2, Spacer(1, 4),
    P("<b>Poin kunci:</b> ventilasi tidak sama dengan respirasi seluler. Ventilasi hanya menggerakkan udara, sedangkan respirasi seluler adalah pemanfaatan O₂ di dalam sel untuk menghasilkan energi (ATP).", base),
    P("Alur proses: Ventilasi → Respirasi eksternal → Transport gas → Respirasi internal → Respirasi seluler.", base),
    P("C. Daftar Pustaka", h2)]

refs = [
 "Bustamante-Marin, X. M., &amp; Ostrowski, L. E. (2017). Cilia and mucociliary clearance. <i>Cold Spring Harbor Perspectives in Biology, 9</i>(4), a028241. https://doi.org/10.1101/cshperspect.a028241",
 "Hsia, C. C. W., Hyde, D. M., &amp; Weibel, E. R. (2016). Lung structure and the intrinsic challenges of gas exchange. <i>Comprehensive Physiology, 6</i>(2), 827–895. https://doi.org/10.1002/cphy.c150028",
 "Kuek, L. E., &amp; Lee, R. J. (2020). First contact: The role of respiratory cilia in host-pathogen interactions in the airways. <i>American Journal of Physiology-Lung Cellular and Molecular Physiology, 319</i>(4), L603–L619. https://doi.org/10.1152/ajplung.00283.2020",
 "Schittny, J. C. (2017). Development of the lung. <i>Cell and Tissue Research, 367</i>(3), 427–444. https://doi.org/10.1007/s00441-016-2545-0",
 "Weibel, E. R. (2017). Lung morphometry: The link between structure and function. <i>Cell and Tissue Research, 367</i>(3), 413–426. https://doi.org/10.1007/s00441-016-2541-4",
]
story += [Paragraph(r, ref) for r in refs]

SimpleDocTemplate("output/Materi_Sistem_Respirasi_Bagian2.pdf", pagesize=A4,
    leftMargin=2*cm, rightMargin=2*cm, topMargin=1.8*cm, bottomMargin=1.8*cm,
    title="Sistem Respirasi — Bagian 2").build(story)
