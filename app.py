import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re
import os
import json
import bcrypt
from pathlib import Path
from datetime import datetime
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors

# ───────────────────────────────────────────────
#           COOKIE MANAGER – FITUR "INGAT SAYA"
# ───────────────────────────────────────────────

from streamlit_cookies_manager import EncryptedCookieManager

# GANTI PASSWORD INI DENGAN STRING RAHASIA YANG KAMU BUAT SENDIRI (minimal 20-30 karakter, unik)
cookies = EncryptedCookieManager(
    prefix="belanja_jatim_",
    password="rahasia_jatim_2026_rakha_safa_pratama_strong_key_987654321xyzabc"
)

if not cookies.ready():
    st.stop()

# ───────────────────────────────────────────────
#           SISTEM LOGIN + REGISTRASI + LUPA PASSWORD
# ───────────────────────────────────────────────

USERS_FILE = "users.json"

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                pass
    
    default_users = {
        "admin": {
            "password": bcrypt.hashpw("jatim2026".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "nama_lengkap": "Administrator Sistem",
            "email": "admin@jatimprov.go.id",
            "tgl_lahir": "1990-01-01",
            "no_hp": "08123456789"
        },
        "rakha": {
            "password": bcrypt.hashpw("safa123".encode('utf-8'), bcrypt.gensalt()).decode('utf-8'),
            "nama_lengkap": "Rakha Safa Pratama",
            "email": "rakha@example.com",
            "tgl_lahir": "2000-05-15",
            "no_hp": "081234567890"
        }
    }
    save_users(default_users)
    return default_users

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

def show_auth_page():
    st.set_page_config(page_title="Login / Daftar - Realisasi Belanja Jatim", layout="centered")

    # ── LOGO PROVINSI JAWA TIMUR ──
    try:
        logo = Image.open("Logo Provinsi Jawa Timur.png")
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.image(logo, use_container_width=True)
    except FileNotFoundError:
        st.warning("⚠️ File 'Logo Provinsi Jawa Timur.png' tidak ditemukan!")

    # Cek query param untuk menentukan tab awal (default: login)
    query_params = st.query_params
    active_tab = query_params.get("tab", ["login"])[0].lower()

    st.title("Login / Daftar Sistem Realisasi Belanja Jatim")

    tab_login, tab_register, tab_reset = st.tabs(["Login", "Daftar Akun Baru", "Lupa Password"])

    with tab_login:
        # Pesan setelah logout
        if "logout_message" in st.session_state:
            st.success(st.session_state.pop("logout_message"))

        # Pesan setelah registrasi berhasil
        if "just_registered" in st.session_state:
            username = st.session_state.pop("just_registered_username", "")
            nama = st.session_state.pop("just_registered_nama", "")
            msg = st.session_state.pop("just_registered_message", "")
            
            st.success(msg)
            st.info(f"**Username Anda:** `{username}`\nGunakan password yang baru saja Anda buat untuk masuk sekarang.")
            st.markdown("Masukkan username dan password di bawah ini ↓")
            st.balloons()

        st.markdown("**Masuk ke aplikasi**")

        remembered_username = cookies.get("remember_username", "")

        username = st.text_input(
            "Username",
            value=remembered_username,
            key="login_username_unique"
        )
        password = st.text_input("Password", type="password", key="login_password_unique")
        
        remember_me = st.checkbox("Ingat saya di perangkat ini", value=bool(remembered_username))

        if st.button("Masuk", type="primary", use_container_width=True):
            users = load_users()
            if username in users:
                stored_hash = users[username]["password"]
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = username

                    if remember_me:
                        cookies["remember_username"] = username
                    else:
                        cookies.pop("remember_username", None)
                    
                    cookies.save()

                    nama = users[username].get("nama_lengkap", username)
                    st.success(f"**Login berhasil!** Selamat datang kembali, **{nama}** ({username}) 🎉")
                    st.balloons()
                    st.rerun()
                else:
                    st.error("**Password salah.** Coba lagi ya.")
            else:
                st.error("**Username tidak ditemukan.** Pastikan sudah daftar.")

    with tab_register:
        st.markdown("**Buat akun baru (data lengkap)**")
        
        if st.session_state.get("register_error"):
            st.error(st.session_state.pop("register_error"))

        with st.form(key="register_form"):
            new_username     = st.text_input("Username (unik)", key="reg_username_unique")
            
            new_password     = st.text_input(
                "Password",
                type="password",
                key="reg_password_unique"
            )
            
            confirm_password = st.text_input(
                "Konfirmasi Password",
                type="password",
                key="reg_confirm_unique"
            )
            
            nama_lengkap     = st.text_input("Nama Lengkap", key="reg_nama_unique")
            email            = st.text_input("Email", key="reg_email_unique")
            tgl_lahir        = st.date_input("Tanggal Lahir", min_value=datetime(1900, 1, 1), max_value=datetime.now(), key="reg_tgl_lahir_unique")
            no_hp            = st.text_input("Nomor HP / WA", key="reg_hp_unique")

            submit_button = st.form_submit_button("Daftar Akun", type="primary", use_container_width=True)

            if submit_button:
                error_msg = ""
                if not new_username.strip():
                    error_msg = "Username harus diisi."
                elif not new_password.strip() or len(new_password) < 6:
                    error_msg = "Password minimal 6 karakter."
                elif new_password != confirm_password:
                    error_msg = "Konfirmasi password tidak cocok."
                elif not nama_lengkap.strip():
                    error_msg = "Nama lengkap harus diisi."
                elif not re.match(r"[^@]+@[^@]+\.[^@]+", email):
                    error_msg = "Email tidak valid."
                elif not no_hp.strip():
                    error_msg = "Nomor HP harus diisi."

                if error_msg:
                    st.session_state["register_error"] = f"**Registrasi gagal:** {error_msg}"
                    st.rerun()
                else:
                    users = load_users()
                    if new_username in users:
                        st.session_state["register_error"] = f"**Registrasi gagal:** Username '{new_username}' sudah digunakan."
                        st.rerun()
                    else:
                        hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        users[new_username] = {
                            "password": hashed,
                            "nama_lengkap": nama_lengkap.strip(),
                            "email": email.strip(),
                            "tgl_lahir": str(tgl_lahir),
                            "no_hp": no_hp.strip()
                        }
                        save_users(users)

                        st.session_state["just_registered"] = True
                        st.session_state["just_registered_username"] = new_username
                        st.session_state["just_registered_nama"] = nama_lengkap
                        st.session_state["just_registered_message"] = (
                            f"**Registrasi berhasil!**\n"
                            f"Akun **{new_username}** ({nama_lengkap}) telah dibuat.\n\n"
                            "Silakan login menggunakan username dan password di tab Login."
                        )

                        st.query_params["tab"] = "login"
                        st.rerun()

    with tab_reset:
        st.markdown("**Lupa Password? Reset di sini** (verifikasi nomor HP diperlukan)")
        
        if st.session_state.get("reset_success"):
            msg = st.session_state.pop("reset_success")
            st.success(msg)
            st.balloons()
        if st.session_state.get("reset_error"):
            msg = st.session_state.pop("reset_error")
            st.error(msg)

        with st.form(key="reset_form"):
            reset_username         = st.text_input("Username yang ingin direset", key="reset_username_unique")
            reset_no_hp            = st.text_input("Nomor HP terdaftar (untuk verifikasi)", key="reset_hp_unique")
            new_password_reset     = st.text_input("Password Baru", type="password", key="reset_password_unique")
            confirm_password_reset = st.text_input("Konfirmasi Password Baru", type="password", key="reset_confirm_unique")

            reset_button = st.form_submit_button("Reset Password", type="primary", use_container_width=True)

            if reset_button:
                error_msg = ""
                if not reset_username.strip():
                    error_msg = "Username harus diisi."
                elif not reset_no_hp.strip():
                    error_msg = "Nomor HP harus diisi untuk verifikasi."
                elif not new_password_reset.strip() or len(new_password_reset) < 6:
                    error_msg = "Password baru minimal 6 karakter."
                elif new_password_reset != confirm_password_reset:
                    error_msg = "Konfirmasi password baru tidak cocok."

                if error_msg:
                    st.session_state["reset_error"] = f"**Reset gagal:** {error_msg}"
                    st.rerun()
                else:
                    users = load_users()
                    if reset_username not in users:
                        st.session_state["reset_error"] = f"**Username '{reset_username}' tidak ditemukan.**"
                        st.rerun()
                    elif users[reset_username].get("no_hp", "").strip() != reset_no_hp.strip():
                        st.session_state["reset_error"] = "**Nomor HP tidak sesuai dengan akun ini.**"
                        st.rerun()
                    else:
                        hashed = bcrypt.hashpw(new_password_reset.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                        users[reset_username]["password"] = hashed
                        save_users(users)
                        st.session_state["reset_success"] = f"**Password berhasil direset!** Untuk akun '{reset_username}'. Silakan login 🎉"
                        st.rerun()

    st.markdown("---")

# ───────────────────────────────────────────────
#           INISIALISASI SESSION STATE
# ───────────────────────────────────────────────

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    show_auth_page()
    st.stop()

# ───────────────────────────────────────────────
#           APLIKASI UTAMA
# ───────────────────────────────────────────────

st.set_page_config(page_title="Realisasi Belanja Jatim", layout="wide")

st.sidebar.markdown(f"**Pengguna aktif:** {st.session_state.get('current_user', 'User')} 👤")

if st.sidebar.button("Logout", type="secondary"):
    st.session_state["logout_message"] = "Anda telah berhasil logout. Silakan login kembali."
    st.session_state["logged_in"] = False
    for key in list(st.session_state.keys()):
        if key not in ["logged_in", "logout_message"]:
            del st.session_state[key]
    st.query_params.clear()
    st.rerun()

st.sidebar.markdown("---")

# Inisialisasi tahun anggaran terpisah
if "tahun_non_blud" not in st.session_state:
    st.session_state["tahun_non_blud"] = 2026

if "tahun_blud" not in st.session_state:
    st.session_state["tahun_blud"] = 2026

if "tahun_anggaran" not in st.session_state:
    st.session_state["tahun_anggaran"] = 2026

if "tanggal_impor" not in st.session_state:
    st.session_state["tanggal_impor"] = datetime.now().strftime("%d/%m/%Y")

# Direktori history
HISTORY_DIR_NON_BLUD = "history_non_blud"
HISTORY_DIR_BLUD     = "history_blud"
Path(HISTORY_DIR_NON_BLUD).mkdir(exist_ok=True)
Path(HISTORY_DIR_BLUD).mkdir(exist_ok=True)

# ───────────────────────────────────────────────
#           UTILITAS
# ───────────────────────────────────────────────

def rupiah(x):
    try:
        return f"Rp {float(x):,.0f}".replace(",", ".")
    except:
        return ""

def pct_fmt(x):
    try:
        return f"{float(x):.2f}%"
    except:
        return ""

def ensure_cols(df: pd.DataFrame, cols: list):
    for c in cols:
        if c not in df.columns:
            df[c] = 0
    return df

def normalize_headers(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = (
        df.columns.astype(str)
        .str.upper().str.strip()
        .str.replace(r"\s+", " ", regex=True)
        .str.replace(r"\(|\)", "", regex=True)
    )
    return df

def normalize_numeric(df: pd.DataFrame, cols: list) -> pd.DataFrame:
    for col in cols:
        if col in df.columns:
            s = df[col].astype(str).str.replace(",", ".", regex=False)
            s = s.str.replace(r"[^0-9\.\-]", "", regex=True)
            df[col] = pd.to_numeric(s, errors="coerce").fillna(0)
    return df

def coalesce_name(df: pd.DataFrame) -> pd.Series:
    if "NAMA SKPD" in df.columns and "SKPD" in df.columns:
        a = df["NAMA SKPD"].astype(str)
        b = df["SKPD"].astype(str)
        return a.where(a.str.strip() != "", b)
    if "NAMA SKPD" in df.columns:
        return df["NAMA SKPD"].astype(str)
    if "SKPD" in df.columns:
        return df["SKPD"].astype(str)
    return df.iloc[:, 0].astype(str)

def compute_pct(df: pd.DataFrame) -> pd.DataFrame:
    df = ensure_cols(df, ["ANGGARAN", "REALISASI"])
    df = normalize_numeric(df, ["ANGGARAN", "REALISASI"])
    ang  = df["ANGGARAN"].astype(float)
    real = df["REALISASI"].astype(float)
    df["PROSENTASE"] = (real / ang.where(ang > 0, pd.NA) * 100).fillna(0).round(2)
    return df

# ───────────────────────────────────────────────
#           HISTORY
# ───────────────────────────────────────────────

def save_to_history(df: pd.DataFrame, tipe: str, tanggal_impor: str, tahun: int):
    dir_path      = HISTORY_DIR_BLUD if tipe == "BLUD" else HISTORY_DIR_NON_BLUD
    tanggal_clean = tanggal_impor.replace("/", "-")
    timestamp     = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename      = f"{tipe.lower()}_{tanggal_clean}_TA{tahun}_{timestamp}.csv"
    filepath      = os.path.join(dir_path, filename)
    df.to_csv(filepath, index=False, encoding="utf-8-sig")
    return filepath

def load_history_list(tipe: str):
    dir_path = HISTORY_DIR_BLUD if tipe == "BLUD" else HISTORY_DIR_NON_BLUD
    return sorted(Path(dir_path).glob("*.csv"), reverse=True)

def load_history_file(filepath) -> pd.DataFrame:
    return pd.read_csv(filepath, encoding="utf-8-sig")

def get_file_info(filepath) -> dict:
    p    = Path(filepath)
    stat = p.stat()
    modified_dt   = datetime.fromtimestamp(stat.st_mtime)
    modified_time = modified_dt.strftime("%d/%m/%Y %H:%M:%S")
    size_kb = round(stat.st_size / 1024, 1)

    name  = p.stem
    lower = name.lower()

    def ymd_to_dmy(ymd: str) -> str:
        try:
            return datetime.strptime(ymd, "%Y%m%d").strftime("%d/%m/%Y")
        except:
            return "–"

    m = re.match(r"^(blud|nonblud|non-blud)_(\d{2}-\d{2}-\d{4})_ta(\d{4})_(\d{8})_(\d{6})$", lower)
    if m:
        tanggal_data   = m.group(2).replace("-", "/")
        tahun_anggaran = m.group(3)
        try:
            upload_time = datetime.strptime(m.group(4) + m.group(5), "%Y%m%d%H%M%S").strftime("%d/%m/%Y %H:%M:%S")
        except:
            upload_time = modified_time
        return {
            "tanggal_data":   tanggal_data,
            "tahun_anggaran": tahun_anggaran,
            "upload_time":    upload_time,
            "modified_time":  modified_time,
            "size_kb":        size_kb,
        }

    return {
        "tanggal_data":   "–",
        "tahun_anggaran": "–",
        "upload_time":    modified_time,
        "modified_time":  modified_time,
        "size_kb":        size_kb,
    }

# ───────────────────────────────────────────────
#           PDF REPORT
# ───────────────────────────────────────────────

def generate_pdf_report(df, tanggal_impor, total_ang, total_real, total_persen, tahun_anggaran=2026, tipe="blud"):
    buffer  = io.BytesIO()
    is_blud = (str(tipe).lower() == "blud")
    is_gabungan = (str(tipe).lower() == "gabungan")
    page_size = landscape(A4) if is_blud or is_gabungan else A4

    doc = SimpleDocTemplate(
        buffer,
        pagesize=page_size,
        rightMargin=20, leftMargin=20,
        topMargin=30, bottomMargin=30
    )

    elements = []
    styles   = getSampleStyleSheet()

    tipe_label = "GABUNGAN (NON-BLUD + BLUD)" if is_gabungan else ("BLUD" if is_blud else "NON-BLUD")
    title = Paragraph(f"LAPORAN REALISASI BELANJA JAWA TIMUR TA {tahun_anggaran} ({tipe_label})", styles["Heading1"])
    elements.append(title)
    elements.append(Paragraph(f"Data per tanggal: {tanggal_impor}", styles["Normal"]))
    elements.append(Paragraph(f"Dicetak pada: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    summary_data = [
        ["Keterangan", "Nilai"],
        ["Total Anggaran",  f"Rp {total_ang:,.0f}".replace(",", ".")],
        ["Total Realisasi", f"Rp {total_real:,.0f}".replace(",", ".")],
        ["% Realisasi",     f"{total_persen:.2f}%"],
    ]
    summary_table = Table(summary_data, colWidths=[2.5 * inch, 3 * inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
    ]))
    elements.append(summary_table)
    elements.append(Spacer(1, 16))

    if is_gabungan or is_blud:
        headers    = ["No", "Tipe", "Kode SKPD", "Nama SKPD", "Anggaran", "Realisasi", "%"]
        col_widths = [0.4*inch, 0.8*inch, 1.0*inch, 2.6*inch, 1.4*inch, 1.4*inch, 0.7*inch]
    else:
        headers    = ["No", "Kode SKPD", "Nama SKPD", "Anggaran", "Realisasi", "%"]
        col_widths = [0.4*inch, 1.0*inch, 2.6*inch, 1.4*inch, 1.4*inch, 0.7*inch]

    table_data = [headers]
    for idx, row in df.iterrows():
        skpd_name = str(row.get("SKPD", "") or row.get("NAMA SKPD", "") or "")[:40]
        if is_gabungan or is_blud:
            row_list = [
                str(idx + 1),
                str(row.get("TIPE", "")),
                str(row.get("KODE SKPD", "")),
                skpd_name,
                f"Rp {float(row.get('ANGGARAN', 0) or 0):,.0f}".replace(",", "."),
                f"Rp {float(row.get('REALISASI', 0) or 0):,.0f}".replace(",", "."),
                f"{float(row.get('PROSENTASE', 0) or 0):.2f}%"
            ]
        else:
            row_list = [
                str(idx + 1),
                str(row.get("KODE SKPD", "")),
                skpd_name,
                f"Rp {float(row.get('ANGGARAN', 0) or 0):,.0f}".replace(",", "."),
                f"Rp {float(row.get('REALISASI', 0) or 0):,.0f}".replace(",", "."),
                f"{float(row.get('PROSENTASE', 0) or 0):.2f}%"
            ]
        table_data.append(row_list)

    detail_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    detail_table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 7),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("ALIGN",         (3, 1), (3, -1),  "LEFT"),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
        ("GRID",          (0, 0), (-1, -1), 0.4, colors.grey),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [colors.white, colors.HexColor("#f0f4ff")]),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    elements.append(detail_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()

# ───────────────────────────────────────────────
#           SIDEBAR
# ───────────────────────────────────────────────

st.sidebar.title("📊 Realisasi Belanja Jatim")
tipe_data = st.sidebar.radio("Tipe Data", ["Non-BLUD", "BLUD", "Gabungan"])

if tipe_data == "Non-BLUD":
    menu_options = ["Upload Data (Non-BLUD)", "Dashboard (Non-BLUD)", "History (Non-BLUD)"]
elif tipe_data == "BLUD":
    menu_options = ["Upload Data (BLUD)", "Dashboard (BLUD)", "History (BLUD)"]
else:
    menu_options = ["Upload Data (Non-BLUD)", "Upload Data (BLUD)", "Dashboard Gabungan"]

menu = st.sidebar.radio("Menu", menu_options)

st.sidebar.markdown("---")
if st.sidebar.button("Clear Cache & Rerun (Debug)"):
    st.cache_data.clear()
    st.rerun()

# ───────────────────────────────────────────────
#           UPLOAD DATA
# ───────────────────────────────────────────────

if "Upload Data" in menu:
    tipe_upload = "Non-BLUD" if "Non-BLUD" in menu else "BLUD"

    st.title(f"Upload Data Realisasi Belanja ({tipe_upload})")
    uploaded = st.file_uploader("Pilih file .xlsx", type="xlsx")

    st.session_state["tahun_anggaran"] = int(
        st.number_input(
            "Tahun Anggaran (untuk penamaan history & PDF)",
            min_value=2000, max_value=2100,
            value=int(st.session_state["tahun_anggaran"])
        )
    )

    if uploaded:
        try:
            filename   = uploaded.name
            date_match = re.search(r"(\d{2})[/-](\d{2})[/-](\d{4})", filename)
            if date_match:
                day, month, year = date_match.groups()
                tanggal_impor = f"{day}/{month}/{year}"
                st.success(f"✅ Tanggal terdeteksi dari nama file: **{tanggal_impor}**")
            else:
                tanggal_impor = datetime.now().strftime("%d/%m/%Y")
                st.info(f"ℹ️ Tanggal tidak terdeteksi. Menggunakan hari ini: **{tanggal_impor}**")

            st.session_state["tanggal_impor"] = tanggal_impor

            excel = pd.ExcelFile(uploaded)
            default_sheet    = "SD REAL_BLUD" if tipe_upload == "BLUD" else "LAP REALBELANJA"
            sheet_names_norm = [str(s).upper().strip() for s in excel.sheet_names]
            idx   = sheet_names_norm.index(default_sheet) if default_sheet in sheet_names_norm else 0
            sheet = st.selectbox("Pilih Sheet", excel.sheet_names, index=idx)

            skip = 1 if tipe_upload == "BLUD" else 3
            if tipe_upload == "BLUD":
                df = pd.read_excel(excel, sheet_name=sheet, skiprows=skip, header=None)
                df = df.drop(index=[0, 1, 2], errors="ignore").reset_index(drop=True)
                if df.shape[1] >= 13:
                    df.columns = [
                        "NO", "KODE SKPD", "EMPTY", "SKPD", "ANGGARAN",
                        "SP2D GAJI", "SP2D LS", "RINCIAN GU/TU", "KOREKSI",
                        "REALISASI", "PROSENTASE", "SISA KREDIT", "PERSEN SISA"
                    ]
                    df = df.drop(columns=["NO", "EMPTY"], errors="ignore")
            else:
                df = pd.read_excel(excel, sheet_name=sheet, skiprows=skip, header=0)

            df = normalize_headers(df)

            rename_dict = {
                "KREDIT MURNI":        "ANGGARAN",
                "KREDIT MURNI TA":     "ANGGARAN",
                "KREDIT MURNI TA 2026":"ANGGARAN",
                "KREDIT MURNI TA2026": "ANGGARAN",
                "KREDIT MURNI":        "ANGGARAN",

                "JUMLAH":              "REALISASI",
                "REALISASI RILL":      "REALISASI",
                "REALISASI":           "REALISASI",

                "%":                   "PROSENTASE",
                "% BELANJA":           "PROSENTASE",
                "PROSENTASE":          "PROSENTASE",

                "NAMA SKPD":           "NAMA SKPD",
                "SKPD":                "SKPD",
                "KODE SKPD":           "KODE SKPD",

                "SP2D GAJI":           "SP2D GAJI",
                "SP2D LS":             "SP2D LS",
                "RINCIAN GU/TU":       "RINCIAN GU/TU",
                "KOREKSI":             "KOREKSI",
                "SISA KREDIT":         "SISA KREDIT",
                "PERSEN SISA":         "PERSEN SISA",
            }
            df = df.rename(columns=rename_dict)

            df = normalize_numeric(df, [
                "ANGGARAN", "REALISASI", "SP2D GAJI", "SP2D LS",
                "RINCIAN GU/TU", "KOREKSI", "SISA KREDIT", "PROSENTASE", "PERSEN SISA"
            ])

            df = compute_pct(df)

            nm = "NAMA SKPD" if "NAMA SKPD" in df.columns else ("SKPD" if "SKPD" in df.columns else None)
            if nm and "ANGGARAN" in df.columns:
                df = df[df[nm].notna() & (df[nm].astype(str).str.strip() != "") & (df["ANGGARAN"] > 0)]

            if "No" in df.columns:
                df = df.drop(columns=["No"])
            df.insert(0, "No", range(1, len(df) + 1))
            df["Tanggal Impor Data"] = tanggal_impor
            df = df.fillna("")

            if tipe_upload == "Non-BLUD":
                st.session_state["df_non_blud"] = df.copy()
            else:
                st.session_state["df_blud"] = df.copy()

            saved_path = save_to_history(df, tipe_upload, tanggal_impor, int(st.session_state["tahun_anggaran"]))
            st.success(f"✅ Data disimpan ke history: `{saved_path}`")

            st.subheader("Preview Data (Upload)")
            fmt_map = {}
            for col in ["ANGGARAN", "REALISASI", "SP2D GAJI", "SP2D LS", "RINCIAN GU/TU", "KOREKSI", "SISA KREDIT"]:
                if col in df.columns:
                    fmt_map[col] = rupiah
            for col in ["PROSENTASE", "PERSEN SISA"]:
                if col in df.columns:
                    fmt_map[col] = pct_fmt
            st.dataframe(df.style.format(fmt_map), use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Upload gagal: {str(e)}")

# ───────────────────────────────────────────────
#           DASHBOARD NON-BLUD
# ───────────────────────────────────────────────

elif "Dashboard (Non-BLUD)" in menu:
    if st.session_state.get("df_non_blud") is None:
        st.warning("Data Non-BLUD belum di-upload.")
        st.stop()

    df = st.session_state["df_non_blud"].copy()
    st.title("Dashboard Realisasi Belanja Non-BLUD")

    df = ensure_cols(df, ["ANGGARAN", "REALISASI", "PROSENTASE"])
    df = normalize_numeric(df, ["ANGGARAN", "REALISASI", "PROSENTASE"])
    df = compute_pct(df)

    df_display = df.copy()
    pos = df_display.columns.get_loc("REALISASI") + 1 if "REALISASI" in df_display.columns else len(df_display.columns)
    df_display.insert(pos, "TAHUN ANGGARAN", st.session_state["tahun_non_blud"])

    total_ang    = float(df["ANGGARAN"].sum())
    total_real   = float(df["REALISASI"].sum())
    total_persen = (total_real / total_ang * 100) if total_ang > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Anggaran",  rupiah(total_ang))
    col2.metric("Total Realisasi", rupiah(total_real))
    col3.metric("% Realisasi",     f"{total_persen:.2f}%")

    tanggal_non = st.session_state.get("tanggal_impor", datetime.now().strftime("%d/%m/%Y"))
    st.caption(f"**Data Non-BLUD per tanggal: {tanggal_non}** | Tahun Anggaran: **{st.session_state['tahun_non_blud']}**")

    with st.expander("**Urutkan & Filter Tabel**", expanded=True):
        col_sort1, col_sort2 = st.columns([3, 2])
        with col_sort1:
            sort_col = st.selectbox(
                "Urutkan berdasarkan kolom",
                options=[c for c in df_display.columns if c not in ["Tanggal Impor Data", "No"]],
                index=0,
                key="sort_non_unique"
            )
        with col_sort2:
            sort_order = st.radio(
                "Urutan",
                ["Ascending", "Descending"],
                horizontal=True,
                key="order_non_unique"
            )

        q = st.text_input("Cari (Nama/Kode SKPD)", "", key="search_non_unique")

    df_sorted = df_display.sort_values(by=sort_col, ascending=(sort_order == "Ascending"))

    df_view = df_sorted.copy()
    if q.strip():
        cols_search = [c for c in ["KODE SKPD", "NAMA SKPD", "SKPD"] if c in df_view.columns]
        if cols_search:
            mask = pd.Series(False, index=df_view.index)
            for c in cols_search:
                mask |= df_view[c].astype(str).str.contains(q, case=False, na=False)
            df_view = df_view[mask]

    if "No" in df_view.columns:
        df_view = df_view.drop(columns=["No"])
    df_view = df_view.reset_index(drop=True)
    df_view.insert(0, "No", range(1, len(df_view) + 1))

    fmt_map = {}
    for col in ["ANGGARAN", "REALISASI"]:
        if col in df_view.columns:
            fmt_map[col] = rupiah
    if "PROSENTASE" in df_view.columns:
        fmt_map["PROSENTASE"] = pct_fmt

    def highlight_tahun(val):
        if val == "TAHUN ANGGARAN":
            return 'background-color: #1e3a5f; color: white; font-weight: bold;'
        return ''

    st.subheader("Tabel Data Non-BLUD")
    st.dataframe(
        df_view.style.format(fmt_map).map(highlight_tahun, subset=["TAHUN ANGGARAN"]),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Top 10 Persentase Realisasi Tertinggi Non-BLUD")
    df_pct = df.copy()
    df_pct["NAMA_SKPD"] = coalesce_name(df_pct).fillna("Tidak Ada Nama").astype(str).str.strip()
    df_pct["PCT"] = (df_pct["REALISASI"] / df_pct["ANGGARAN"].replace(0, pd.NA) * 100).round(1)
    df_top = df_pct.sort_values("PCT", ascending=False).head(10)

    if not df_top.empty:
        fig = px.bar(
            df_top, x="PCT", y="NAMA_SKPD", orientation="h",
            title="Top 10 Non-BLUD", height=500, text="PCT",
            color_discrete_sequence=["#EF553B"]
        )
        fig.update_traces(
            texttemplate='%{text:.1f}%', textposition='outside',
            textfont_size=12, cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Anggaran: Rp %{customdata[0]:,.0f}<br>Realisasi: Rp %{customdata[1]:,.0f}<br><b>PCT: %{x:.1f}%</b>",
            customdata=df_top[["ANGGARAN", "REALISASI"]].values
        )
        fig.update_layout(
            xaxis_title="Persentase Realisasi (%)", yaxis_title="Nama SKPD / Unit",
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
            xaxis=dict(range=[0, max(120, df_top["PCT"].max() + 10)], dtick=10),
            bargap=0.2, margin=dict(l=20, r=120, t=60, b=60),
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font=dict(color="#e0e0e0"),
        )
        fig.add_vline(x=100, line_dash="dash", line_color="#ff4b4b",
                      annotation_text="Target 100%", annotation_position="top right")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tidak ada data Non-BLUD valid untuk top 10.")

    st.subheader("Export Data")
    csv_data = df_sorted.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Download CSV", csv_data, "realisasi_non_blud.csv", "text/csv")

    pdf_bytes = generate_pdf_report(
        df_sorted, tanggal_non, total_ang, total_real, total_persen,
        st.session_state["tahun_non_blud"], "non_blud"
    )
    st.download_button("📄 Download PDF", pdf_bytes, "realisasi_non_blud.pdf", "application/pdf")

# ───────────────────────────────────────────────
#           DASHBOARD BLUD
# ───────────────────────────────────────────────

elif "Dashboard (BLUD)" in menu:
    if st.session_state.get("df_blud") is None:
        st.warning("Data BLUD belum di-upload.")
        st.stop()

    df = st.session_state["df_blud"].copy()
    st.title("Dashboard Realisasi Belanja BLUD")

    df = ensure_cols(df, ["ANGGARAN", "REALISASI", "SISA KREDIT", "PROSENTASE"])
    df = normalize_numeric(df, ["ANGGARAN", "REALISASI", "SISA KREDIT", "PROSENTASE"])
    df = compute_pct(df)

    df_display = df.copy()
    pos = df_display.columns.get_loc("SISA KREDIT") + 1 if "SISA KREDIT" in df_display.columns else len(df_display.columns)
    df_display.insert(pos, "TAHUN ANGGARAN", st.session_state["tahun_blud"])

    total_ang   = float(df["ANGGARAN"].sum())
    total_real  = float(df["REALISASI"].sum())
    total_sisa  = float(df["SISA KREDIT"].sum()) if "SISA KREDIT" in df.columns else 0
    total_persen = (total_real / total_ang * 100) if total_ang > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Anggaran",    rupiah(total_ang))
    col2.metric("Total Realisasi",   rupiah(total_real))
    col3.metric("% Realisasi",       f"{total_persen:.2f}%")
    col4.metric("Total Sisa Kredit", rupiah(total_sisa))

    tanggal_blud = st.session_state.get("tanggal_impor", datetime.now().strftime("%d/%m/%Y"))
    st.caption(f"**Data BLUD per tanggal: {tanggal_blud}** | Tahun Anggaran: **{st.session_state['tahun_blud']}**")

    with st.expander("**Urutkan & Filter Tabel**", expanded=True):
        col_sort1, col_sort2 = st.columns([3, 2])
        with col_sort1:
            sort_col = st.selectbox(
                "Urutkan berdasarkan kolom",
                options=[c for c in df_display.columns if c not in ["Tanggal Impor Data", "No"]],
                index=0,
                key="sort_blud_unique"
            )
        with col_sort2:
            sort_order = st.radio(
                "Urutan",
                ["Ascending", "Descending"],
                horizontal=True,
                key="order_blud_unique"
            )

        q = st.text_input("Cari (Nama/Kode SKPD)", "", key="search_blud_unique")

    df_sorted = df_display.sort_values(by=sort_col, ascending=(sort_order == "Ascending"))

    df_view = df_sorted.copy()
    if q.strip():
        cols_search = [c for c in ["KODE SKPD", "SKPD", "NAMA SKPD"] if c in df_view.columns]
        if cols_search:
            mask = pd.Series(False, index=df_view.index)
            for c in cols_search:
                mask |= df_view[c].astype(str).str.contains(q, case=False, na=False)
            df_view = df_view[mask]

    if "No" in df_view.columns:
        df_view = df_view.drop(columns=["No"])
    df_view = df_view.reset_index(drop=True)
    df_view.insert(0, "No", range(1, len(df_view) + 1))

    fmt_map = {}
    for col in ["ANGGARAN","REALISASI","SISA KREDIT","SP2D GAJI","SP2D LS","RINCIAN GU/TU","KOREKSI"]:
        if col in df_view.columns:
            fmt_map[col] = rupiah
    for col in ["PROSENTASE","PERSEN SISA"]:
        if col in df_view.columns:
            fmt_map[col] = pct_fmt

    def highlight_tahun(val):
        if val == "TAHUN ANGGARAN":
            return 'background-color: #1e3a5f; color: white; font-weight: bold;'
        return ''

    st.subheader("Tabel Data BLUD")
    st.dataframe(
        df_view.style.format(fmt_map).map(highlight_tahun, subset=["TAHUN ANGGARAN"]),
        use_container_width=True,
        hide_index=True
    )

    st.subheader("Top 10 Persentase Realisasi Tertinggi BLUD")
    df_pct = df.copy()
    df_pct["NAMA_SKPD"] = coalesce_name(df_pct).fillna("Tidak Ada Nama").astype(str).str.strip()
    df_pct["PCT"] = (df_pct["REALISASI"] / df_pct["ANGGARAN"].replace(0, pd.NA) * 100).round(1)
    df_top = df_pct.sort_values("PCT", ascending=False).head(10)

    if not df_top.empty:
        fig = px.bar(
            df_top, x="PCT", y="NAMA_SKPD", orientation="h",
            title="Top 10 BLUD", height=500, text="PCT",
            color_discrete_sequence=["#636EFA"]
        )
        fig.update_traces(
            texttemplate='%{text:.1f}%', textposition='outside',
            textfont_size=12, cliponaxis=False,
            hovertemplate="<b>%{y}</b><br>Anggaran: Rp %{customdata[0]:,.0f}<br>Realisasi: Rp %{customdata[1]:,.0f}<br><b>PCT: %{x:.1f}%</b>",
            customdata=df_top[["ANGGARAN", "REALISASI"]].values
        )
        fig.update_layout(
            xaxis_title="Persentase Realisasi (%)", yaxis_title="Nama SKPD / Unit",
            yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
            xaxis=dict(range=[0, max(120, df_top["PCT"].max() + 10)], dtick=10),
            bargap=0.2, margin=dict(l=20, r=120, t=60, b=60),
            plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font=dict(color="#e0e0e0"),
        )
        fig.add_vline(x=100, line_dash="dash", line_color="#ff4b4b",
                      annotation_text="Target 100%", annotation_position="top right")
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Tidak ada data BLUD valid untuk top 10.")

    st.subheader("Export Data")
    csv_data = df_sorted.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Download CSV", csv_data, "realisasi_blud.csv", "text/csv")

    pdf_bytes = generate_pdf_report(
        df_sorted, tanggal_blud, total_ang, total_real, total_persen,
        st.session_state["tahun_blud"], "blud"
    )
    st.download_button("📄 Download PDF", pdf_bytes, "realisasi_blud.pdf", "application/pdf")

# ───────────────────────────────────────────────
#           DASHBOARD GABUNGAN
# ───────────────────────────────────────────────

elif "Dashboard Gabungan" in menu:
    df_non  = st.session_state.get("df_non_blud")
    df_blud = st.session_state.get("df_blud")

    if df_non is None or df_blud is None:
        st.warning("Upload kedua data (Non-BLUD & BLUD) terlebih dahulu.")
        st.stop()

    df_non  = df_non.copy()
    df_blud = df_blud.copy()

    df_non  = ensure_cols(df_non,  ["ANGGARAN", "REALISASI", "PROSENTASE"])
    df_blud = ensure_cols(df_blud, ["ANGGARAN", "REALISASI", "SISA KREDIT", "PROSENTASE"])

    df_non  = normalize_numeric(df_non,  ["ANGGARAN", "REALISASI", "PROSENTASE"])
    df_blud = normalize_numeric(df_blud, ["ANGGARAN", "REALISASI", "SISA KREDIT", "PROSENTASE"])

    df_non  = compute_pct(df_non)
    df_blud = compute_pct(df_blud)

    st.title("Dashboard Gabungan (Non-BLUD + BLUD)")
    tgl = st.session_state.get("tanggal_impor", datetime.now().strftime("%d/%m/%Y"))
    st.caption(f"Data per tanggal: **{tgl}** | Tahun Anggaran: **{st.session_state.get('tahun_anggaran', '–')}**")

    ang_all  = float(df_non["ANGGARAN"].sum())
    real_non = float(df_non["REALISASI"].sum())
    real_blud = float(df_blud["REALISASI"].sum())
    real_all = real_non + real_blud
    pct_all  = (real_all / ang_all * 100) if ang_all > 0 else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total Anggaran (Non-BLUD)", rupiah(ang_all))
    k2.metric("Total Realisasi (Gabungan)", rupiah(real_all))
    k3.metric("% Realisasi Gabungan", f"{pct_all:.2f}%")

    st.markdown("---")

    tab_all, tab_non, tab_blud = st.tabs(["Gabungan", "Non-BLUD", "BLUD"])

    df_non_g  = df_non.copy();  df_non_g["TIPE"]  = "Non-BLUD"
    df_blud_g = df_blud.copy(); df_blud_g["TIPE"] = "BLUD"

    keep_cols = []
    for c in ["TIPE", "KODE SKPD", "NAMA SKPD", "SKPD", "ANGGARAN", "REALISASI", "PROSENTASE", "SISA KREDIT"]:
        if c in df_non_g.columns or c in df_blud_g.columns:
            keep_cols.append(c)

    df_all = pd.concat(
        [df_non_g.reindex(columns=keep_cols), df_blud_g.reindex(columns=keep_cols)],
        ignore_index=True
    )
    df_all = normalize_numeric(df_all, ["ANGGARAN", "REALISASI", "PROSENTASE", "SISA KREDIT"])

    with tab_all:
        st.subheader("Tabel Gabungan")

        with st.expander("**Urutkan & Filter Tabel**", expanded=True):
            col_sort1, col_sort2 = st.columns([3, 2])
            with col_sort1:
                sort_col = st.selectbox(
                    "Urutkan berdasarkan kolom",
                    options=[c for c in df_all.columns if c not in ["Tanggal Impor Data", "No"]],
                    index=0,
                    key="sort_gab_unique"
                )
            with col_sort2:
                sort_order = st.radio(
                    "Urutan",
                    ["Ascending", "Descending"],
                    horizontal=True,
                    key="order_gab_unique"
                )

            q = st.text_input("Cari (Nama/Kode SKPD)", "", key="q_gab_unique")

        df_view = df_all.copy()
        if q.strip():
            cols_search = [c for c in ["KODE SKPD", "NAMA SKPD", "SKPD"] if c in df_view.columns]
            if cols_search:
                mask = pd.Series(False, index=df_view.index)
                for c in cols_search:
                    mask |= df_view[c].astype(str).str.contains(q, case=False, na=False)
                df_view = df_view[mask]

        df_view = df_view.sort_values(by=sort_col, ascending=(sort_order == "Ascending"))

        if "No" in df_view.columns:
            df_view = df_view.drop(columns=["No"])
        df_view = df_view.reset_index(drop=True)
        df_view.insert(0, "No", range(1, len(df_view) + 1))

        fmt_map = {}
        for col in ["ANGGARAN", "REALISASI", "SISA KREDIT"]:
            if col in df_view.columns:
                fmt_map[col] = rupiah
        if "PROSENTASE" in df_view.columns:
            fmt_map["PROSENTASE"] = pct_fmt
        st.dataframe(df_view.style.format(fmt_map), use_container_width=True, hide_index=True)

        st.subheader("Top 10 Persentase Realisasi Tertinggi (Gabungan)")
        df_pct = df_all.copy()
        df_pct = normalize_numeric(df_pct, ["ANGGARAN", "REALISASI"])
        df_pct = df_pct[df_pct["ANGGARAN"] > 0].copy()
        df_pct["NAMA_SKPD"] = coalesce_name(df_pct).fillna("Tidak Ada Nama").astype(str).str.strip()
        df_pct["PCT"] = (df_pct["REALISASI"] / df_pct["ANGGARAN"].replace(0, pd.NA) * 100).round(1)
        df_top = df_pct.sort_values("PCT", ascending=False).head(10).copy()

        if not df_top.empty:
            color_map = {"BLUD": "#636EFA", "Non-BLUD": "#EF553B"}
            fig = px.bar(
                df_top, x="PCT", y="NAMA_SKPD", color="TIPE", orientation="h",
                title="Top 10 Tertinggi (Gabungan Non-BLUD + BLUD)",
                height=500, color_discrete_map=color_map, text="PCT",
            )
            fig.update_traces(
                texttemplate='%{text:.1f}%', textposition='outside',
                textfont_size=12, cliponaxis=False,
                hovertemplate=(
                    "<b>%{y}</b><br>Tipe: %{customdata[0]}<br>"
                    "Anggaran: Rp %{customdata[1]:,.0f}<br>"
                    "Realisasi: Rp %{customdata[2]:,.0f}<br>"
                    "<b>PCT: %{x:.1f}%</b>"
                ),
                customdata=df_top[["TIPE", "ANGGARAN", "REALISASI"]].values
            )
            fig.update_layout(
                xaxis_title="Persentase Realisasi (%)", yaxis_title="Nama SKPD / Unit",
                yaxis=dict(autorange="reversed", tickfont=dict(size=11)),
                xaxis=dict(range=[0, max(120, df_top["PCT"].max() + 10)], dtick=10),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                bargap=0.2, margin=dict(l=20, r=120, t=60, b=60),
                plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font=dict(color="#e0e0e0"),
            )
            fig.add_vline(x=100, line_dash="dash", line_color="#ff4b4b",
                          annotation_text="Target 100%", annotation_position="top right",
                          annotation_font_size=12, annotation_font_color="#ff4b4b")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.warning("Tidak ada data valid untuk top 10 gabungan.")

    st.subheader("Export Gabungan")
    csv_all = df_all.to_csv(index=False).encode("utf-8-sig")
    st.download_button("⬇️ Download CSV Gabungan", csv_all, "realisasi_gabungan.csv", "text/csv")

    pdf_bytes_gab = generate_pdf_report(
        df_all.sort_values(by="REALISASI", ascending=False),
        tgl,
        ang_all,
        real_all,
        pct_all,
        int(st.session_state.get("tahun_anggaran", 2026)),
        "gabungan"
    )
    st.download_button("📄 Download PDF Gabungan", pdf_bytes_gab, "realisasi_gabungan.pdf", "application/pdf")

    with tab_non:
        st.subheader("Tabel Non-BLUD")
        q = st.text_input("Cari (Non-BLUD)", value="", key="q_tab_non_vfinal")
        df_view = df_non.copy()
        if q.strip():
            cols_search = [c for c in ["KODE SKPD", "NAMA SKPD", "SKPD"] if c in df_view.columns]
            if cols_search:
                mask = pd.Series(False, index=df_view.index)
                for c in cols_search:
                    mask |= df_view[c].astype(str).str.contains(q, case=False, na=False)
                df_view = df_view[mask]
        df_view = df_view.sort_values(by="REALISASI", ascending=False)

        if "No" in df_view.columns:
            df_view = df_view.drop(columns=["No"])
        df_view = df_view.reset_index(drop=True)
        df_view.insert(0, "No", range(1, len(df_view) + 1))

        fmt_map = {"ANGGARAN": rupiah, "REALISASI": rupiah}
        if "PROSENTASE" in df_view.columns:
            fmt_map["PROSENTASE"] = pct_fmt
        st.dataframe(df_view.style.format(fmt_map), use_container_width=True, hide_index=True)

    with tab_blud:
        st.subheader("Tabel BLUD")
        q = st.text_input("Cari (BLUD)", value="", key="q_tab_blud_vfinal")
        df_view = df_blud.copy()
        if q.strip():
            cols_search = [c for c in ["KODE SKPD", "SKPD", "NAMA SKPD"] if c in df_view.columns]
            if cols_search:
                mask = pd.Series(False, index=df_view.index)
                for c in cols_search:
                    mask |= df_view[c].astype(str).str.contains(q, case=False, na=False)
                df_view = df_view[mask]
        df_view = df_view.sort_values(by="REALISASI", ascending=False)

        if "No" in df_view.columns:
            df_view = df_view.drop(columns=["No"])
        df_view = df_view.reset_index(drop=True)
        df_view.insert(0, "No", range(1, len(df_view) + 1))

        fmt_map = {}
        for col in ["ANGGARAN","REALISASI","SISA KREDIT","SP2D GAJI","SP2D LS","RINCIAN GU/TU","KOREKSI"]:
            if col in df_view.columns:
                fmt_map[col] = rupiah
        for col in ["PROSENTASE","PERSEN SISA"]:
            if col in df_view.columns:
                fmt_map[col] = pct_fmt
        st.dataframe(df_view.style.format(fmt_map), use_container_width=True, hide_index=True)

# ───────────────────────────────────────────────
#           HISTORY NON-BLUD
# ───────────────────────────────────────────────

elif "History (Non-BLUD)" in menu:
    st.title("📁 History Upload — Non-BLUD")
    files = load_history_list("Non-BLUD")
    if not files:
        st.info("Belum ada history upload Non-BLUD.")
        st.stop()

    st.subheader("📋 Daftar File History")
    summary_rows = []
    for f in files:
        info = get_file_info(f)
        summary_rows.append({
            "Nama File":      f.name,
            "Tanggal Data":   info["tanggal_data"],
            "Tahun Anggaran": info["tahun_anggaran"],
            "Waktu Upload":   info["upload_time"],
            "Ukuran (KB)":    info["size_kb"],
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔍 Detail & Export File History")
    selected      = st.selectbox("Pilih file history:", [f.name for f in files], key="hist_non_select_final")
    selected_path = next(f for f in files if f.name == selected)

    info    = get_file_info(selected_path)
    df_hist = load_history_file(selected_path)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tanggal Data",    info["tanggal_data"])
    c2.metric("Tahun Anggaran",  info["tahun_anggaran"])
    c3.metric("Waktu Upload",    info["upload_time"])
    c4.metric("Ukuran File",     f"{info['size_kb']} KB")

    st.subheader("Preview Data History")
    st.dataframe(df_hist, use_container_width=True, hide_index=True)

    st.subheader("📤 Export")
    col_csv, col_pdf, col_del = st.columns(3)

    with col_csv:
        csv_hist = df_hist.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Download CSV", csv_hist, f"history_{selected}", "text/csv", use_container_width=True)

    with col_pdf:
        dfh = normalize_headers(df_hist.copy())
        dfh = normalize_numeric(dfh, ["ANGGARAN", "REALISASI", "PROSENTASE"])
        dfh = compute_pct(dfh)
        total_ang_h  = float(dfh["ANGGARAN"].sum())  if "ANGGARAN"  in dfh.columns else 0
        total_real_h = float(dfh["REALISASI"].sum()) if "REALISASI" in dfh.columns else 0
        total_pct_h  = (total_real_h / total_ang_h * 100) if total_ang_h > 0 else 0
        ta_pdf = info["tahun_anggaran"]
        if not str(ta_pdf).isdigit():
            ta_pdf = int(st.session_state.get("tahun_anggaran", 2026))
        pdf_hist = generate_pdf_report(dfh, info["tanggal_data"], total_ang_h, total_real_h, total_pct_h, int(ta_pdf), "non_blud")
        st.download_button("📄 Download PDF", pdf_hist, f"history_{selected.replace('.csv', '.pdf')}", "application/pdf", use_container_width=True)

    with col_del:
        if st.button("🗑️ Hapus File Ini", type="primary", use_container_width=True, key="del_non_final"):
            os.remove(selected_path)
            st.success(f"File `{selected}` berhasil dihapus.")
            st.rerun()

# ───────────────────────────────────────────────
#           HISTORY BLUD
# ───────────────────────────────────────────────

elif "History (BLUD)" in menu:
    st.title("📁 History Upload — BLUD")
    files = load_history_list("BLUD")
    if not files:
        st.info("Belum ada history upload BLUD.")
        st.stop()

    st.subheader("📋 Daftar File History")
    summary_rows = []
    for f in files:
        info = get_file_info(f)
        summary_rows.append({
            "Nama File":      f.name,
            "Tanggal Data":   info["tanggal_data"],
            "Tahun Anggaran": info["tahun_anggaran"],
            "Waktu Upload":   info["upload_time"],
            "Ukuran (KB)":    info["size_kb"],
        })
    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔍 Detail & Export File History")
    selected      = st.selectbox("Pilih file history:", [f.name for f in files], key="hist_blud_select_final")
    selected_path = next(f for f in files if f.name == selected)

    info    = get_file_info(selected_path)
    df_hist = load_history_file(selected_path)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Tanggal Data",   info["tanggal_data"])
    c2.metric("Tahun Anggaran", info["tahun_anggaran"])
    c3.metric("Waktu Upload",   info["upload_time"])
    c4.metric("Ukuran File",    f"{info['size_kb']} KB")

    st.subheader("Preview Data History")
    st.dataframe(df_hist, use_container_width=True, hide_index=True)

    st.subheader("📤 Export")
    col_csv, col_pdf, col_del = st.columns(3)

    with col_csv:
        csv_hist = df_hist.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇️ Download CSV", csv_hist, f"history_{selected}", "text/csv", use_container_width=True)

    with col_pdf:
        dfh = normalize_headers(df_hist.copy())
        dfh = normalize_numeric(dfh, ["ANGGARAN", "REALISASI", "SISA KREDIT", "PROSENTASE"])
        dfh = compute_pct(dfh)
        total_ang_h  = float(dfh["ANGGARAN"].sum())  if "ANGGARAN"  in dfh.columns else 0
        total_real_h = float(dfh["REALISASI"].sum()) if "REALISASI" in dfh.columns else 0
        total_pct_h  = (total_real_h / total_ang_h * 100) if total_ang_h > 0 else 0
        ta_pdf = info["tahun_anggaran"]
        if not str(ta_pdf).isdigit():
            ta_pdf = int(st.session_state.get("tahun_anggaran", 2026))
        pdf_hist = generate_pdf_report(dfh, info["tanggal_data"], total_ang_h, total_real_h, total_pct_h, int(ta_pdf), "blud")
        st.download_button("📄 Download PDF", pdf_hist, f"history_{selected.replace('.csv', '.pdf')}", "application/pdf", use_container_width=True)

    with col_del:
        if st.button("🗑️ Hapus File Ini", type="primary", use_container_width=True, key="del_blud_final"):
            os.remove(selected_path)
            st.success(f"File `{selected}` berhasil dihapus.")
            st.rerun()

# ───────────────────────────────────────────────
#           DEBUG
# ───────────────────────────────────────────────
if st.sidebar.button("Clear Cache & Rerun"):
    st.cache_data.clear()
    st.rerun()
