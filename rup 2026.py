"""
═══════════════════════════════════════════════════════════════════════════════
  DASHBOARD RUP 2026 — Jawa Timur, Jawa Barat, Makassar
  Telkomsel Enterprise | Bid Management — Data Science
  Pie Chart ICT vs Non-ICT per Wilayah
═══════════════════════════════════════════════════════════════════════════════
"""

import streamlit as st
import pandas as pd
import sqlite3
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import textwrap
import re
import os
import numpy as np
import gdown
from datetime import datetime

# ═══════════════════════════════════════════════════════════════════════════
# GOOGLE DRIVE — auto download DB saat deploy di Streamlit Cloud
# ═══════════════════════════════════════════════════════════════════════════
GDRIVE_FILE_ID = "1oiXdW38emWi8ReGfhMpxIlEXHlXgV0fz"
DB_FILENAME = "sirup 2026.db"

if not os.path.exists(DB_FILENAME):
    url = f"https://drive.google.com/uc?id={GDRIVE_FILE_ID}"
    gdown.download(url, DB_FILENAME, quiet=False)

st.set_page_config(
    page_title="Dashboard RUP 2026 — Jatim, Jabar, Makassar",
    page_icon="📊", layout="wide", initial_sidebar_state="expanded",
)

# ═══════════════════════════════════════════════════════════════════════════
# CSS
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
    .stApp { background-color: #FFFFFF; }
    .stApp, .stApp p, .stApp span, .stApp div, .stApp label, .stApp li,
    .stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp h5 { color: #111 !important; }
    section[data-testid="stSidebar"] { background:#F5F5F5; border-right:3px solid #DDD; }
    section[data-testid="stSidebar"] * { color:#111!important; }
    .main-header { background:linear-gradient(135deg,#ED1C24,#9B1B1F); padding:28px 36px;
        border-radius:16px;margin-bottom:28px; box-shadow:0 6px 24px rgba(237,28,36,0.2); }
    .main-header h1 { color:#FFF!important;font-size:30px!important;font-weight:800!important;margin:0!important; }
    .main-header p { color:#FFCCCC!important;font-size:14px!important;margin:5px 0 0!important; }
    .mc { background:#FFF;border:2px solid #DDD;border-radius:14px;padding:18px 14px;
        text-align:center;box-shadow:0 3px 12px rgba(0,0,0,0.05); }
    .mc .lb { color:#444!important;font-size:10px;font-weight:700;text-transform:uppercase;
        letter-spacing:1px;margin-bottom:6px; }
    .mc .vl { color:#111!important;font-size:22px;font-weight:800;line-height:1.1; }
    .mc .sb { color:#666!important;font-size:10px;margin-top:5px; }
    .sh { background:#F5F5F5;border-left:6px solid #ED1C24;padding:14px 22px;
        margin:28px 0 16px;border-radius:0 10px 10px 0; }
    .sh h2 { color:#111!important;font-size:21px!important;font-weight:800!important;margin:0!important; }
    .sh p { color:#555!important;font-size:13px!important;margin:5px 0 0!important; }
    .rc { border-radius:14px;padding:20px 24px;margin:10px 0;border:3px solid; }
    .rc h3 { font-size:20px;font-weight:800;margin:0 0 4px; }
    .rc p { font-size:12px;margin:2px 0; }
    .streamlit-expanderHeader { font-size:14px!important;font-weight:700!important;color:#111!important; }
    .stTabs [data-baseweb="tab"] { font-weight:700;font-size:13px;padding:10px 18px;color:#111!important; }
    .stDownloadButton>button { background:#1A1A2E!important;color:#FFF!important;
        font-weight:700!important;border-radius:10px!important;border:none!important; }
    .stDownloadButton>button:hover { background:#ED1C24!important; }
    #MainMenu{visibility:hidden;}footer{visibility:hidden;}header{visibility:hidden;}
</style>
""", unsafe_allow_html=True)

# ═══════════════════════════════════════════════════════════════════════════
# WILAYAH
# ═══════════════════════════════════════════════════════════════════════════
WILAYAH = {
    "Jawa Timur":  {"keyword":"Jawa Timur", "color":"#ED1C24","bg":"#FFF3F3","icon":"🔴"},
    "Jawa Barat":  {"keyword":"Jawa Barat", "color":"#1565C0","bg":"#E8F0FE","icon":"🔵"},
    "Makassar":    {"keyword":"Makassar",    "color":"#2E7D32","bg":"#E8F5E9","icon":"🟢"},
}

# ═══════════════════════════════════════════════════════════════════════════
# ICT WHITELIST + BLACKLIST
# ═══════════════════════════════════════════════════════════════════════════
ICT_WL = {
    'CONNECTIVITY': [r'\bINTERNET\b',r'\bBANDWIDTH\b',r'\bBROADBAND\b',r'\bFIBER\s*OPTI[CK]\b',
        r'\bFIBER\b(?!\s*GLASS)',r'\bMPLS\b',r'\bVPN\b',r'\bVSAT\b',r'\bWI[\s\-]?FI\b',
        r'\bWIFI\b',r'\bWIRELESS\b',r'\bHOTSPOT\b'],
    'CLOUD_DC': [r'\bCLOUD\b(?!\s*NINE)',r'\bDATA\s*CENTER\b',r'\bCOLOCATION\b',
        r'\bHOSTING\b',r'\bVPS\b'],
    'TELECOM': [r'\bPULSA\b',r'\bPAKET\s+DATA\b',r'\bSIM\s*CARD\b',r'\bTELEKOMUNIKASI\b',
        r'\bPABX\b',r'\bVOIP\b',r'\bIP\s+PHONE\b',r'\bCALL\s+CENTER\b'],
    'COLLABORATION': [r'\bVIDEO\s*CONFERENCE\b',r'\bZOOM\b(?!\s*IN|\s*OUT)',
        r'\bWEBINAR\b',r'\bMICROSOFT\s+TEAMS\b'],
    'IOT_SMART': [r'\bIOT\b',r'\bGPS\s+TRACK(ER|ING)\b',r'\bTELEMATIC[S]?\b',r'\bSMART\s+CITY\b'],
    'SURVEILLANCE': [r'\bCCTV\b',r'\bSURVEILLANCE\b',r'\bIP\s+CAMERA\b',r'\bNVR\b',
        r'\bDVR\b(?!\s+PLAYER)',r'\bACCESS\s+CONTROL\b',r'\bBIOMETRIC\b'],
    'HW_COMPUTER': [r'\bKOMPUTER\b',r'\bCOMPUTER\b',r'\bLAPTOP\b',r'\bNOTEBOOK\b',
        r'\bDESKTOP\b',r'\bWORKSTATION\b'],
    'HW_SERVER': [r'\bSERVER\b(?!\s+MAKANAN|\s+MINUMAN)',r'\bSTORAGE\b(?!\s+BOX|\s+RACK\s+BESI)',
        r'\bRACK\s+SERVER\b',r'\bUPS\b(?!\s+DELIVERY)'],
    'HW_NETWORK': [r'\bROUTER\b',r'\bSWITCH\b(?!\s+ON|\s+OFF)',r'\bFIREWALL\b',r'\bMODEM\b'],
    'SOFTWARE': [r'\bSOFTWARE\b',r'\bAPLIKASI\b(?!\s+LAMARAN)',r'\bSISTEM\s+INFORMASI\b',
        r'\bWEBSITE\b',r'\bDATABASE\b',r'\bERP\b',r'\bANTIVIRUS\b',r'\bLISENSI\b',r'\bLICENSE\b'],
    'IT_SERVICES': [r'\bMAINTENANCE\s+(JARINGAN|SERVER|IT|NETWORK)\b',
        r'\bSYSTEM\s+INTEGRAT(OR|ION)\b',r'\bMANAGED\s+SERVICE\b'],
    'SECURITY': [r'\bCYBER\s*SECURITY\b',r'\bNETWORK\s+SECURITY\b'],
}
BL = [r'\bBUKU\b',r'\bPRINTER\b',r'\bTONER\b',r'\bBANGUNAN\b',r'\bKONSTRUKSI\b',r'\bTINTA\b',
    r'\bOBAT\b',r'\bVAKSIN\b',r'\bALAT\s+KESEHATAN\b',r'\bMEDIS\b',r'\bELEKTROMEDI[CKS]?\b',
    r'\bMAKANAN\b',r'\bMINUMAN\b',r'\bKATERING\b',r'\bATK\b',r'\bSERAGAM\b',
    r'\bMOBIL\b(?!\s+APP)',r'\bKENDARAAN\b']

_ax = []
for p in ICT_WL.values(): _ax.extend(p)
_ir = re.compile("|".join(_ax), re.IGNORECASE)
_br = re.compile("|".join(BL), re.IGNORECASE)
_cr = {c: re.compile("|".join(p), re.IGNORECASE) for c, p in ICT_WL.items()}

def is_ict(t):
    if pd.isna(t): return False
    return bool(_ir.search(str(t)) and not _br.search(str(t)))

def ict_cat(t):
    if pd.isna(t): return None
    s = str(t)
    if _br.search(s): return None
    for c, rx in _cr.items():
        if rx.search(s): return c
    return None


# ═══════════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════════
def fmt_rp(v):
    if pd.isna(v) or v == 0: return "Rp 0"
    a = abs(v)
    if a >= 1e12: return f"Rp {v/1e12:,.2f} T"
    if a >= 1e9:  return f"Rp {v/1e9:,.2f} M"
    if a >= 1e6:  return f"Rp {v/1e6:,.1f} Jt"
    return f"Rp {v:,.0f}"

def fmt_s(v):
    if pd.isna(v) or v == 0: return "0"
    a = abs(v)
    if a >= 1e12: return f"{v/1e12:.2f} T"
    if a >= 1e9:  return f"{v/1e9:.1f} M"
    if a >= 1e6:  return f"{v/1e6:.0f} Jt"
    return f"{v:,.0f}"

def fmt_n(v):
    if pd.isna(v): return "0"
    return f"{int(v):,}".replace(",", ".")

def mcard(lb, vl, sb=""):
    s = f'<div class="sb">{sb}</div>' if sb else ""
    return f'<div class="mc"><div class="lb">{lb}</div><div class="vl">{vl}</div>{s}</div>'

def to_csv(df):
    return df.to_csv(index=False).encode("utf-8")


# ═══════════════════════════════════════════════════════════════════════════
# PIE CHART — ICT vs Non-ICT
# Semesta = TOTAL pagu wilayah (dijumlahkan, bukan rata-rata)
# ═══════════════════════════════════════════════════════════════════════════
def pie_chart(df_region, region_name):
    """
    Donut-style Pie Chart:
      - ICT  = biru tua (#1B4F72)
      - Non-ICT = hijau tua (#1E6F3E)
      - Center: TOTAL pagu (sum) + jumlah paket semesta wilayah
      - Legend di bawah chart dengan info lengkap
    """
    pagu_total = df_region["Pagu_Cleaned"].sum()   # TOTAL, bukan rata-rata
    paket_total = len(df_region)
    pagu_ict = df_region[df_region["Is_ICT"]]["Pagu_Cleaned"].sum()
    paket_ict = int(df_region["Is_ICT"].sum())
    pagu_non = pagu_total - pagu_ict
    paket_non = paket_total - paket_ict

    pct_ict = pagu_ict / pagu_total * 100 if pagu_total > 0 else 0
    pct_non = 100 - pct_ict

    C_ICT = "#1B4F72"
    C_NON = "#1E6F3E"

    fig, ax = plt.subplots(figsize=(6, 6))
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    # ── Pie chart (donut style) ──
    sizes = [pagu_ict, pagu_non]
    colors = [C_ICT, C_NON]
    labels_pie = ["ICT", "Non-ICT"]

    wedges, texts, autotexts = ax.pie(
        sizes, colors=colors,
        autopct=lambda pct: f"{pct:.1f}%",
        startangle=90,
        pctdistance=0.78,
        wedgeprops=dict(width=0.38, edgecolor="white", linewidth=3),
        textprops=dict(color="white", fontsize=12, fontweight="bold"),
    )

    # Pastikan autopct text terlihat jelas
    for at in autotexts:
        at.set_fontsize(13)
        at.set_fontweight("bold")
        at.set_color("#FFFFFF")

    # ── Center text: Total Pagu (SUM) ──
    ax.text(0, 0.06, fmt_rp(pagu_total),
            ha="center", va="center", fontsize=16, fontweight="bold", color="#111111")
    ax.text(0, -0.10, f"Total {region_name}",
            ha="center", va="center", fontsize=10, fontweight="bold", color="#444444")
    ax.text(0, -0.22, f"{fmt_n(paket_total)} paket",
            ha="center", va="center", fontsize=9, color="#666666")

    # ── Legend di bawah chart ──
    legend_labels = [
        f"ICT — {fmt_rp(pagu_ict)}  ({pct_ict:.1f}%)  •  {fmt_n(paket_ict)} paket",
        f"Non-ICT — {fmt_rp(pagu_non)}  ({pct_non:.1f}%)  •  {fmt_n(paket_non)} paket",
    ]
    legend = ax.legend(
        wedges, legend_labels,
        loc="lower center",
        bbox_to_anchor=(0.5, -0.12),
        fontsize=9,
        frameon=False,
        ncol=1,
        handlelength=1.2,
        handleheight=1.2,
    )
    for text in legend.get_texts():
        text.set_color("#222222")

    ax.set_aspect("equal")
    ax.axis("off")
    plt.subplots_adjust(bottom=0.15, top=0.95, left=0.05, right=0.95)
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# HBAR — seaborn 0.12.x (no hue, no legend param)
# ═══════════════════════════════════════════════════════════════════════════
def hbar(data, x_col, y_col, title, subtitle, colors, total_u=None, figsize=(14, 7)):
    sns.set_theme(style="white")
    fig, ax = plt.subplots(figsize=figsize)
    fig.patch.set_facecolor("#FFF"); ax.set_facecolor("#FFF")
    d = data.copy(); n = len(d)
    if n == 0:
        ax.text(0.5, 0.5, "Tidak ada data", ha="center", va="center", fontsize=18, color="#999")
        return fig
    d[y_col] = d[y_col].apply(lambda t: "\n".join(textwrap.wrap(str(t), 36)))
    sns.barplot(data=d, x=x_col, y=y_col, palette=colors[:n], ax=ax, edgecolor="none")
    ax.set_title(title, fontsize=19, fontweight="bold", color="#111", loc="left", pad=22)
    if subtitle:
        ax.text(0, 1.03, subtitle, transform=ax.transAxes, fontsize=12, color="#555", ha="left")
    mx = d[x_col].max() if n > 0 else 1
    for i, val in enumerate(d[x_col]):
        lb = fmt_s(val)
        if total_u and total_u > 0:
            lb += f"  ({val / total_u * 100:.1f}%)"
        ax.text(val + mx * 0.012, i, lb, va="center", ha="left",
                fontsize=11, fontweight="bold", color="#111")
    if total_u:
        ax.text(1.0, -0.07, f"SEMESTA WILAYAH: {fmt_rp(total_u)}",
                transform=ax.transAxes, fontsize=12, fontweight="bold",
                color="#ED1C24", ha="right", va="top")
    ax.set_xlabel(""); ax.set_ylabel("")
    ax.tick_params(axis="y", labelsize=11, labelcolor="#111", width=0)
    ax.tick_params(axis="x", labelsize=10, labelcolor="#777")
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: fmt_s(x)))
    for sp in ["top", "right"]: ax.spines[sp].set_visible(False)
    ax.spines["bottom"].set_color("#DDD"); ax.spines["left"].set_color("#DDD")
    if mx > 0: ax.set_xlim(0, mx * 1.45)
    plt.tight_layout()
    return fig


# ═══════════════════════════════════════════════════════════════════════════
# DETAIL RENDER PER WILAYAH
# ═══════════════════════════════════════════════════════════════════════════
def render_detail(df_r, rname, key_pf):
    rp = df_r["Pagu_Cleaned"].sum()

    # ── Top 10 K/L/PD ──
    st.markdown(f'<div class="sh"><h2>🏛️ Top 10 K/L/PD — {rname}</h2>'
                f'<p>Instansi dengan rencana pengadaan terbesar</p></div>', unsafe_allow_html=True)
    if "K_L_PD" in df_r.columns:
        dk = (df_r.groupby("K_L_PD")
              .agg(Total_Pagu=("Pagu_Cleaned", "sum"), Jml=("Pagu_Cleaned", "count"))
              .sort_values("Total_Pagu", ascending=False).head(10).reset_index())
        if len(dk) > 0:
            dk["Label"] = dk["K_L_PD"].apply(lambda x: str(x)[:42])
            fig = hbar(dk, "Total_Pagu", "Label", f"Top 10 K/L/PD — {rname}",
                       f"Dari {fmt_n(df_r['K_L_PD'].nunique())} K/L/PD",
                       sns.color_palette("Blues_r", 10), rp, figsize=(14, 6))
            st.pyplot(fig, use_container_width=True); plt.close(fig)

            st.markdown("#### 📋 Detail Satker per K/L/PD")
            for _, row in dk.iterrows():
                klpd = row["K_L_PD"]
                with st.expander(f"🏛️ **{klpd}** — {fmt_rp(row['Total_Pagu'])} "
                                 f"({fmt_n(row['Jml'])} paket)"):
                    det = (df_r[df_r["K_L_PD"] == klpd]
                           .groupby("Satuan_Kerja")
                           .agg(Pagu=("Pagu_Cleaned", "sum"), Paket=("Pagu_Cleaned", "count"))
                           .sort_values("Pagu", ascending=False).head(5).reset_index())
                    det["Pagu"] = det["Pagu"].apply(fmt_rp)
                    det.columns = ["Satuan Kerja", "Total Pagu", "Jml Paket"]
                    st.dataframe(det, use_container_width=True, hide_index=True)

    # ── Top 10 Satuan Kerja ──
    st.markdown(f'<div class="sh"><h2>🏢 Top 10 Satuan Kerja — {rname}</h2>'
                f'<p>Satker terbesar</p></div>', unsafe_allow_html=True)
    if "Satuan_Kerja" in df_r.columns:
        ds = (df_r.groupby("Satuan_Kerja")
              .agg(Total_Pagu=("Pagu_Cleaned", "sum"), Jml=("Pagu_Cleaned", "count"))
              .sort_values("Total_Pagu", ascending=False).head(10).reset_index())
        if len(ds) > 0:
            ds["Label"] = ds["Satuan_Kerja"].apply(lambda x: str(x)[:42])
            fig = hbar(ds, "Total_Pagu", "Label", f"Top 10 Satuan Kerja — {rname}",
                       f"Dari {fmt_n(df_r['Satuan_Kerja'].nunique())} satker",
                       sns.color_palette("Oranges_r", 10), rp, figsize=(14, 6))
            st.pyplot(fig, use_container_width=True); plt.close(fig)

    # ── Distribusi ──
    st.markdown(f'<div class="sh"><h2>📊 Distribusi — {rname}</h2>'
                f'<p>Per jenis pengadaan dan metode</p></div>', unsafe_allow_html=True)
    ca, cb = st.columns(2)
    with ca:
        if "Jenis_Pengadaan" in df_r.columns:
            dj = (df_r.groupby("Jenis_Pengadaan")
                  .agg(Total_Pagu=("Pagu_Cleaned", "sum"))
                  .sort_values("Total_Pagu", ascending=False).head(6).reset_index())
            if len(dj) > 0:
                fig = hbar(dj, "Total_Pagu", "Jenis_Pengadaan", "Per Jenis Pengadaan", "",
                           sns.color_palette("Greens_r", len(dj)), rp, figsize=(8, 4))
                st.pyplot(fig, use_container_width=True); plt.close(fig)
    with cb:
        if "Metode" in df_r.columns:
            dm = (df_r.groupby("Metode")
                  .agg(Total_Pagu=("Pagu_Cleaned", "sum"))
                  .sort_values("Total_Pagu", ascending=False).head(6).reset_index())
            if len(dm) > 0:
                fig = hbar(dm, "Total_Pagu", "Metode", "Per Metode Pemilihan", "",
                           sns.color_palette("Purples_r", len(dm)), rp, figsize=(8, 4))
                st.pyplot(fig, use_container_width=True); plt.close(fig)

    # ── ICT Breakdown ──
    df_ict = df_r[df_r["Is_ICT"]]
    if len(df_ict) > 0:
        st.markdown(f'<div class="sh"><h2>💻 Breakdown Kategori ICT — {rname}</h2>'
                    f'<p>Pagu per kategori ICT</p></div>', unsafe_allow_html=True)
        dc = (df_ict.groupby("Kategori_ICT")
              .agg(Total_Pagu=("Pagu_Cleaned", "sum"), Jml=("Pagu_Cleaned", "count"))
              .sort_values("Total_Pagu", ascending=False).reset_index())
        dc = dc[dc["Total_Pagu"] > 0]
        if len(dc) > 0:
            fig = hbar(dc, "Total_Pagu", "Kategori_ICT",
                       f"Kategori ICT — {rname}",
                       f"Total ICT: {fmt_rp(df_ict['Pagu_Cleaned'].sum())}",
                       sns.color_palette("coolwarm_r", len(dc)),
                       df_ict["Pagu_Cleaned"].sum(), figsize=(14, 5))
            st.pyplot(fig, use_container_width=True); plt.close(fig)

    # ── Download CSV ──
    st.download_button(f"📥 Download CSV — {rname}", to_csv(df_r),
                       f"RUP2026_{rname.replace(' ','_')}_{datetime.now():%Y%m%d}.csv",
                       "text/csv", key=f"dl_{key_pf}")


# ═══════════════════════════════════════════════════════════════════════════
# LOAD DATA — langsung dari DB (data sudah difilter oleh user)
# ═══════════════════════════════════════════════════════════════════════════
@st.cache_data(ttl=3600)
def load_data(db_path):
    conn = sqlite3.connect(db_path)
    tables = pd.read_sql("SELECT name FROM sqlite_master WHERE type='table'", conn)
    if len(tables) == 0:
        conn.close(); return pd.DataFrame()
    tbl = tables.iloc[0]["name"]
    for t in tables["name"]:
        if "sirup" in t.lower() or "rup" in t.lower():
            tbl = t; break
    df = pd.read_sql(f"SELECT * FROM [{tbl}]", conn)
    conn.close()

    # ── Helper: bersihkan format angka Pagu ──
    # Menangani kedua format: koma ribuan ('120,000,000') DAN titik ribuan ('120.000.000')
    def _clean_pagu_series(s):
        return (
            s.astype(str)
             .str.replace(r'[Rr][Pp]\.?\s*', '', regex=True)   # hapus prefix "Rp"
             .str.replace(r'[,\.](?=\d{3}(\D|$))', '', regex=True)  # hapus koma/titik pemisah ribuan
             .str.replace(r'[^\d.]', '', regex=True)             # hapus karakter non-angka
             .pipe(pd.to_numeric, errors="coerce")
             .fillna(0)
        )

    # Pagu — utamakan Pagu__Rp karena Pagu_Cleaned di DB bisa kosong (None)
    if "Pagu__Rp" in df.columns:
        df["Pagu_Cleaned"] = _clean_pagu_series(df["Pagu__Rp"])
    elif "Pagu_Rp" in df.columns:
        df["Pagu_Cleaned"] = _clean_pagu_series(df["Pagu_Rp"])
    elif "Pagu_Cleaned" in df.columns:
        df["Pagu_Cleaned"] = _clean_pagu_series(df["Pagu_Cleaned"])
    else:
        df["Pagu_Cleaned"] = 0

    # Paket col
    pcol = None
    for c in ["Paket", "Nama_Paket"]:
        if c in df.columns: pcol = c; break
    if pcol:
        df["Is_ICT"] = df[pcol].apply(is_ict)
        df["Kategori_ICT"] = df[pcol].apply(ict_cat)
    else:
        df["Is_ICT"] = False; df["Kategori_ICT"] = None

    df["Sektor"] = df["Is_ICT"].map({True: "ICT", False: "Non-ICT"})

    # Region assign
    def assign_region(lok):
        if pd.isna(lok): return "Lainnya"
        up = str(lok).upper()
        if "JAWA TIMUR" in up: return "Jawa Timur"
        if "JAWA BARAT" in up: return "Jawa Barat"
        if "MAKASSAR" in up: return "Makassar"
        return "Lainnya"

    df["Region"] = df["Lokasi"].apply(assign_region) if "Lokasi" in df.columns else "Lainnya"
    return df


# ═══════════════════════════════════════════════════════════════════════════
# MAIN APP
# ═══════════════════════════════════════════════════════════════════════════

st.markdown("""
<div class="main-header">
    <h1>📊 Dashboard RUP 2026 — Potensi Pengadaan</h1>
    <p>Jawa Timur • Jawa Barat • Makassar | ICT & Non-ICT | Telkomsel Enterprise</p>
</div>
""", unsafe_allow_html=True)

# ── Sidebar ──
with st.sidebar:
    st.markdown("## ⚙️ Konfigurasi")
    st.markdown("---")
    db_path = DB_FILENAME
    if not os.path.exists(db_path):
        st.error(f"⚠️ Database `{db_path}` tidak ditemukan. Gagal download dari Google Drive.")
        st.stop()
    with st.spinner("⏳ Memuat data..."):
        df = load_data(db_path)
    if df.empty:
        st.error("❌ Database kosong.")
        st.stop()
    st.success(f"✅ **{fmt_n(len(df))}** paket dimuat")
    st.markdown("---")

    st.markdown("### 📋 Filter")
    if "Jenis_Pengadaan" in df.columns:
        jp = sorted(df["Jenis_Pengadaan"].dropna().unique().tolist())
        sel_jp = st.multiselect("Jenis Pengadaan", jp, jp, key="f_jp")
    else:
        sel_jp = []
    if "Metode" in df.columns:
        mt = sorted(df["Metode"].dropna().unique().tolist())
        sel_mt = st.multiselect("Metode Pemilihan", mt, mt, key="f_mt")
    else:
        sel_mt = []

    st.markdown("---")
    st.caption(f"Telkomsel Enterprise\n{datetime.now():%d %B %Y}")

# ── Apply filters ──
mask = pd.Series(True, index=df.index)
if sel_jp and "Jenis_Pengadaan" in df.columns:
    mask = mask & df["Jenis_Pengadaan"].isin(sel_jp)
if sel_mt and "Metode" in df.columns:
    mask = mask & df["Metode"].isin(sel_mt)
df_f = df[mask].copy()


# ═══════════════════════════════════════════════════════════════════════════
# HOMEPAGE — 3 PIE CHARTS (1 per wilayah)
# ═══════════════════════════════════════════════════════════════════════════

st.markdown('<div class="sh"><h2>📊 Potensi Pengadaan per Wilayah — ICT vs Non-ICT</h2>'
            '<p>Total Pagu (Rp) dijumlahkan per wilayah</p></div>', unsafe_allow_html=True)

cols = st.columns(3)

for col, (rname, rinfo) in zip(cols, WILAYAH.items()):
    df_reg = df_f[df_f["Region"] == rname]
    with col:
        if len(df_reg) == 0:
            st.warning(f"Tidak ada data {rname}")
            continue

        reg_pagu = df_reg["Pagu_Cleaned"].sum()
        reg_paket = len(df_reg)

        # Region header card
        st.markdown(f"""
        <div class="rc" style="background:{rinfo['bg']};border-color:{rinfo['color']}">
            <h3 style="color:{rinfo['color']}!important">{rinfo['icon']} {rname}</h3>
            <p style="color:#333!important"><strong>{fmt_rp(reg_pagu)}</strong> | {fmt_n(reg_paket)} paket</p>
        </div>""", unsafe_allow_html=True)

        # Pie chart ICT vs Non-ICT
        fig = pie_chart(df_reg, rname)
        st.pyplot(fig, use_container_width=True)
        plt.close(fig)

        # Mini metrics
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(mcard("K/L/PD",
                              fmt_n(df_reg["K_L_PD"].nunique()) if "K_L_PD" in df_reg.columns else "0"),
                        unsafe_allow_html=True)
        with c2:
            st.markdown(mcard("Satuan Kerja",
                              fmt_n(df_reg["Satuan_Kerja"].nunique()) if "Satuan_Kerja" in df_reg.columns else "0"),
                        unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)


# ═══════════════════════════════════════════════════════════════════════════
# TABS DETAIL PER WILAYAH
# ═══════════════════════════════════════════════════════════════════════════

st.markdown('<div class="sh"><h2>🔍 Detail per Wilayah</h2>'
            '<p>Top K/L/PD, Satuan Kerja, Distribusi, ICT Breakdown</p></div>',
            unsafe_allow_html=True)

tabs = st.tabs([f"{info['icon']} {name}" for name, info in WILAYAH.items()])

for tab, (rname, rinfo) in zip(tabs, WILAYAH.items()):
    with tab:
        df_reg = df_f[df_f["Region"] == rname]
        if len(df_reg) == 0:
            st.warning(f"Tidak ada data untuk {rname}.")
            continue

        st1, st2, st3 = st.tabs(["📊 Semua Sektor", "💻 ICT Saja", "📦 Non-ICT Saja"])
        with st1:
            render_detail(df_reg, rname, f"all_{rname}")
        with st2:
            di = df_reg[df_reg["Is_ICT"]]
            if len(di) > 0:
                render_detail(di, f"{rname} — ICT", f"ict_{rname}")
            else:
                st.info("Tidak ada paket ICT.")
        with st3:
            dn = df_reg[~df_reg["Is_ICT"]]
            if len(dn) > 0:
                render_detail(dn, f"{rname} — Non-ICT", f"non_{rname}")
            else:
                st.info("Tidak ada paket Non-ICT.")


# ═══════════════════════════════════════════════════════════════════════════
# FOOTER
# ═══════════════════════════════════════════════════════════════════════════
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;padding:20px 0;color:#999!important;font-size:12px;">
    Dashboard RUP 2026 — Jawa Timur, Jawa Barat, Makassar<br>
    Telkomsel Enterprise | Bid Management — Data Science | {datetime.now():%Y}
</div>
""", unsafe_allow_html=True)