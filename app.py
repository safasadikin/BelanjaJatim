import streamlit as st
import pandas as pd
import plotly.express as px
import io
import re
import os
import bcrypt
from pathlib import Path
from datetime import datetime, timedelta, timezone

WIB = timezone(timedelta(hours=7))
def now_wib() -> datetime:
    """Waktu sekarang dalam WIB (UTC+7)."""
    return datetime.now(WIB).replace(tzinfo=None)
from PIL import Image
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.lib import colors
from supabase import create_client, Client

# ───────────────────────────────────────────────
#           COOKIE MANAGER – FITUR "INGAT SAYA"
# ───────────────────────────────────────────────

from streamlit_cookies_manager import EncryptedCookieManager

cookies = EncryptedCookieManager(
    prefix="belanja_jatim_",
    password="rahasia_jatim_2026_rakha_safa_pratama_strong_key_987654321xyzabc"
)

if not cookies.ready():
    st.stop()

# ───────────────────────────────────────────────
#           SUPABASE CLIENT
# ───────────────────────────────────────────────

SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ───────────────────────────────────────────────
#           CEK KEKUATAN PASSWORD
# ───────────────────────────────────────────────

def check_password_strength(password: str) -> dict:
    has_upper   = bool(re.search(r"[A-Z]", password))
    has_lower   = bool(re.search(r"[a-z]", password))
    has_digit   = bool(re.search(r"\d", password))
    has_special = bool(re.search(r"[!@#$%^&*()_+\-=\[\]{};':\"\\|,.<>\/?]", password))
    has_min_len = len(password) >= 8

    score = sum([has_upper, has_lower, has_digit, has_special, has_min_len])

    if score <= 2:
        level = "Lemah";      color = "#e74c3c"; emoji = "🔴"
    elif score == 3:
        level = "Sedang";     color = "#f39c12"; emoji = "🟡"
    elif score == 4:
        level = "Kuat";       color = "#27ae60"; emoji = "🟢"
    else:
        level = "Sangat Kuat"; color = "#1abc9c"; emoji = "✅"

    return {
        "level": level, "color": color, "emoji": emoji, "score": score,
        "has_upper": has_upper, "has_lower": has_lower, "has_digit": has_digit,
        "has_special": has_special, "has_min_len": has_min_len, "is_strong": score >= 4,
    }

# ───────────────────────────────────────────────
#           SISTEM LOGIN + REGISTRASI + LUPA PASSWORD
# ───────────────────────────────────────────────

def load_users():
    try:
        res = supabase.table("users").select("*").execute()
        users = {}
        for row in res.data:
            users[row["username"]] = {
                "password":     row["password"],
                "nama_lengkap": row.get("nama_lengkap", ""),
                "email":        row.get("email", ""),
                "tgl_lahir":    row.get("tgl_lahir", ""),
                "no_hp":        row.get("no_hp", ""),
            }
        return users
    except Exception as e:
        st.error(f"Gagal load users: {e}")
        return {}

def save_users(users):
    pass

def save_user(username, data):
    try:
        supabase.table("users").upsert({
            "username":     username,
            "password":     data["password"],
            "nama_lengkap": data.get("nama_lengkap", ""),
            "email":        data.get("email", ""),
            "tgl_lahir":    data.get("tgl_lahir", ""),
            "no_hp":        data.get("no_hp", ""),
        }).execute()
        return True
    except Exception as e:
        st.error(f"Gagal simpan user: {e}")
        return False

def delete_user(username):
    try:
        supabase.table("users").delete().eq("username", username).execute()
        return True
    except:
        return False

def show_auth_page():
    st.set_page_config(page_title="Login - Realisasi Belanja Jatim", layout="centered")

    import base64
    try:
        with open("thumb-1920-719571.jpg", "rb") as f:
            bg_data = base64.b64encode(f.read()).decode()
        st.markdown(f"""
            <style>
            .stApp {{
                background-image: url("data:image/jpg;base64,{bg_data}");
                background-size: cover;
                background-position: center;
                background-repeat: no-repeat;
                background-attachment: fixed;
            }}
            .block-container {{ position: relative; z-index: 1; }}
            @keyframes fadeInDown {{
                0%   {{ opacity: 0; transform: translateY(-30px); }}
                100% {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes fadeInUp {{
                0%   {{ opacity: 0; transform: translateY(30px); }}
                100% {{ opacity: 1; transform: translateY(0); }}
            }}
            @keyframes fadeIn {{ 0% {{ opacity:0; }} 100% {{ opacity:1; }} }}
            [data-testid="stImage"] img {{ animation: fadeInDown 1s ease forwards; margin-bottom: -40px !important; display: block; }}
            .block-container h1 {{ animation: fadeInDown 1.2s ease forwards; font-weight: 900 !important; color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.9) !important; }}
            .stTabs {{ animation: fadeIn 1.5s ease forwards; }}
            .block-container > div > div > div > div {{ animation: fadeInUp 1.4s ease forwards; }}
            .block-container h2, .block-container h3 {{ font-weight: 900 !important; color: white !important; text-shadow: 2px 2px 4px rgba(0,0,0,0.9) !important; }}
            .block-container p, .block-container label, .block-container span {{ font-weight: 700 !important; color: white !important; text-shadow: 1px 1px 3px rgba(0,0,0,0.9) !important; }}
            .block-container {{ background: transparent !important; padding-top: 10rem !important; margin-top: 0 !important; }}
            .stTextInput input {{ background: rgba(255,255,255,0.92) !important; font-weight: 600 !important; color: #111 !important; border: 1.5px solid #ccc !important; }}
            .stTabs [data-baseweb="tab"] {{ font-weight: 700 !important; }}
            [data-testid="stToolbar"] {{ display: none !important; visibility: hidden !important; }}
            [data-testid="stDecoration"] {{ display: none !important; visibility: hidden !important; }}
            #MainMenu {{ display: none !important; visibility: hidden !important; }}
            footer {{ display: none !important; visibility: hidden !important; }}
            [data-testid="stActionButtonIcon"] {{ display: none !important; visibility: hidden !important; }}
            .stActionButton {{ display: none !important; visibility: hidden !important; }}
            [data-testid="baseButton-actionButton"] {{ display: none !important; visibility: hidden !important; }}
            button[kind="actionButton"] {{ display: none !important; visibility: hidden !important; }}
            [class*="ActionButton"] {{ display: none !important; visibility: hidden !important; }}
            [class*="actionButton"] {{ display: none !important; visibility: hidden !important; }}
            header[data-testid="stHeader"] {{ background: transparent !important; border: none !important; box-shadow: none !important; }}
            [data-testid="stHeader"] > * {{ display: none !important; }}
            button[title="View fullscreen"] {{ display: none !important; visibility: hidden !important; }}
            button[data-testid="StyledFullScreenButton"] {{ display: none !important; visibility: hidden !important; }}
            </style>
        """, unsafe_allow_html=True)
    except FileNotFoundError:
        pass

    try:
        import base64 as _b64
        with open("Logo Provinsi Jawa Timur.png", "rb") as _f:
            _logo_b64 = _b64.b64encode(_f.read()).decode()
        st.markdown(f"""
            <div style="display:flex;justify-content:center;margin-bottom:-30px;">
                <img src="data:image/png;base64,{_logo_b64}" style="width:400px;pointer-events:none;" />
            </div>
        """, unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ File 'Logo Provinsi Jawa Timur.png' tidak ditemukan!")

    st.title("Login / Daftar Sistem Realisasi Belanja Jatim")
    tab_login, tab_register, tab_reset = st.tabs(["Login", "Daftar Akun Baru", "Lupa Password"])

    with tab_login:
        if "logout_message" in st.session_state:
            st.success(st.session_state.pop("logout_message"))
        st.markdown("**Masuk ke aplikasi**")
        remembered_username = cookies.get("remember_username", "")
        remembered_password = cookies.get("remember_password", "")
        username = st.text_input("Username", value=remembered_username, key="login_username_unique")
        password = st.text_input("Password", type="password", value=remembered_password, key="login_password_unique")
        remember_me = st.checkbox("Ingat saya", value=bool(remembered_username and remembered_password))

        if st.button("Masuk", type="primary", use_container_width=True):
            users = load_users()
            if username in users:
                stored_hash = users[username]["password"]
                if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                    st.session_state["logged_in"] = True
                    st.session_state["current_user"] = username
                    st.session_state["nama_lengkap"] = users[username].get("nama_lengkap", username)
                    if remember_me:
                        cookies["remember_username"] = username
                        cookies["remember_password"] = password
                    else:
                        cookies.pop("remember_username", None)
                        cookies.pop("remember_password", None)
                    cookies.save()
                    nama = users[username].get("nama_lengkap", username)
                    import time
                    st.markdown(f"""
                        <style>
                        @keyframes fadeInWelcome {{ 0% {{ opacity:0; transform:translateY(-20px); }} 100% {{ opacity:1; transform:translateY(0); }} }}
                        .welcome-box {{ text-align:center; padding:40px; animation:fadeInWelcome 0.8s ease forwards; }}
                        .welcome-box h2 {{ color:white !important; font-size:28px !important; font-weight:900 !important; text-shadow:2px 2px 8px rgba(0,0,0,0.8) !important; }}
                        .welcome-box p {{ color:#f0f0f0 !important; font-size:16px !important; text-shadow:1px 1px 4px rgba(0,0,0,0.8) !important; }}
                        </style>
                        <div class="welcome-box">
                            <h2>✅ Login Berhasil!</h2>
                            <p>Selamat datang, <b>{nama}</b> 👋<br>Sedang memuat dashboard...</p>
                        </div>
                    """, unsafe_allow_html=True)
                    bar = st.progress(0, text="Memuat sistem...")
                    for i in range(1, 101):
                        time.sleep(0.015)
                        bar.progress(i, text=f"Memuat sistem... {i}%")
                    time.sleep(0.3)
                    st.rerun()
                else:
                    st.error("**Password salah.** Coba lagi ya.")
            else:
                st.error("**Username tidak ditemukan.** Pastikan sudah daftar.")

    with tab_register:
        # Counter sebagai suffix key — naik setiap registrasi berhasil → semua widget dapat key baru → kosong otomatis
        if "reg_form_counter" not in st.session_state:
            st.session_state["reg_form_counter"] = 0
        _c = st.session_state["reg_form_counter"]

        st.markdown("**Buat akun baru (data lengkap)**")
        if st.session_state.get("register_success"):
            st.success(st.session_state.pop("register_success"))
        if st.session_state.get("register_error"):
            st.error(st.session_state.pop("register_error"))

        new_username = st.text_input("Username (unik)", key=f"reg_username_{_c}")
        new_password = st.text_input("Password", type="password", key=f"reg_password_{_c}",
                                     help="Min. 8 karakter, huruf kapital, huruf kecil, angka, dan karakter spesial")

        if new_password:
            _strength = check_password_strength(new_password)
            _bar_pct  = int(_strength["score"] / 5 * 100)
            def _mk_badge(ok, label):
                bg = "rgba(39,174,96,0.85)" if ok else "rgba(231,76,60,0.85)"; mark = "✓" if ok else "✗"
                return f'<span style="background:{bg};color:white;padding:2px 8px;border-radius:12px;font-size:11px;font-weight:700;">{mark} {label}</span>'
            _badges = " ".join([_mk_badge(_strength["has_min_len"],"Min. 8 karakter"),_mk_badge(_strength["has_upper"],"Huruf Kapital"),_mk_badge(_strength["has_lower"],"Huruf Kecil"),_mk_badge(_strength["has_digit"],"Angka (0-9)"),_mk_badge(_strength["has_special"],"Karakter Spesial (!@#$...)")])
            st.markdown(f'<div style="margin:-8px 0 10px 0;"><div style="background:rgba(255,255,255,0.2);border-radius:10px;height:6px;width:100%;margin-bottom:5px;"><div style="background:{_strength["color"]};width:{_bar_pct}%;height:6px;border-radius:10px;"></div></div><p style="color:{_strength["color"]}!important;font-weight:800!important;font-size:12px!important;margin:0 0 5px 0;">{_strength["emoji"]} Kekuatan Password: <b>{_strength["level"]}</b></p><div style="display:flex;flex-wrap:wrap;gap:4px;">{_badges}</div></div>', unsafe_allow_html=True)
            if not _strength["is_strong"]:
                st.warning("⚠️ Password belum cukup kuat! Lengkapi kriteria yang masih merah.")

        with st.form(key=f"register_form_{_c}"):
            confirm_password = st.text_input("Konfirmasi Password", type="password", key=f"reg_confirm_{_c}")
            nama_lengkap     = st.text_input("Nama Lengkap", key=f"reg_nama_{_c}")
            email            = st.text_input("Email", key=f"reg_email_{_c}")
            tgl_lahir        = st.date_input("Tanggal Lahir", min_value=datetime(1900,1,1), max_value=datetime.now(), key=f"reg_tgl_{_c}")
            no_hp            = st.text_input("Nomor HP / WA", key=f"reg_hp_{_c}")
            submit_button    = st.form_submit_button("Daftar Akun", type="primary", use_container_width=True)

        if submit_button:
            error_msg = ""
            if not new_username.strip(): error_msg = "Username harus diisi."
            elif not new_password.strip(): error_msg = "Password harus diisi."
            elif not check_password_strength(new_password)["is_strong"]: error_msg = "Password tidak cukup kuat!"
            elif new_password != confirm_password: error_msg = "Konfirmasi password tidak cocok."
            elif not nama_lengkap.strip(): error_msg = "Nama lengkap harus diisi."
            elif not re.match(r"[^@]+@[^@]+\.[^@]+", email): error_msg = "Email tidak valid."
            elif not no_hp.strip(): error_msg = "Nomor HP harus diisi."

            if error_msg:
                st.session_state["register_error"] = f"**Registrasi gagal:** {error_msg}"; st.rerun()
            else:
                users = load_users()
                if new_username in users:
                    st.session_state["register_error"] = f"**Registrasi gagal:** Username '{new_username}' sudah digunakan."; st.rerun()
                else:
                    hashed = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    save_user(new_username, {"password": hashed, "nama_lengkap": nama_lengkap.strip(), "email": email.strip(), "tgl_lahir": str(tgl_lahir), "no_hp": no_hp.strip()})
                    # Naikkan counter → semua widget dapat key baru → form kosong otomatis
                    st.session_state["reg_form_counter"] = _c + 1
                    st.session_state["register_success"] = f"✅ Akun **{new_username}** berhasil dibuat! Silakan login."
                    st.rerun()

    with tab_reset:
        st.markdown("**Lupa Password? Reset di sini**")
        if st.session_state.get("reset_success"): st.success(st.session_state.pop("reset_success"))
        if st.session_state.get("reset_error"):   st.error(st.session_state.pop("reset_error"))
        _reset_form_key = st.session_state.get("reset_form_counter", 0)
        with st.form(key=f"reset_form_{_reset_form_key}"):
            reset_username         = st.text_input("Username yang ingin direset", key=f"reset_username_unique_{_reset_form_key}")
            reset_no_hp            = st.text_input("Nomor HP terdaftar (untuk verifikasi)", key=f"reset_hp_unique_{_reset_form_key}")
            new_password_reset     = st.text_input("Password Baru", type="password", key=f"reset_pw_unique_{_reset_form_key}")
            confirm_password_reset = st.text_input("Konfirmasi Password Baru", type="password", key=f"reset_confirm_unique_{_reset_form_key}")
            reset_button           = st.form_submit_button("Reset Password", type="primary", use_container_width=True)
        if reset_button:
            error_msg = ""
            if not reset_username.strip(): error_msg = "Username harus diisi."
            elif not reset_no_hp.strip(): error_msg = "Nomor HP harus diisi."
            elif not new_password_reset.strip(): error_msg = "Password baru harus diisi."
            elif not check_password_strength(new_password_reset)["is_strong"]: error_msg = "Password baru tidak cukup kuat!"
            elif new_password_reset != confirm_password_reset: error_msg = "Konfirmasi password tidak cocok."
            if error_msg:
                st.session_state["reset_error"] = f"**Reset gagal:** {error_msg}"; st.rerun()
            else:
                users = load_users()
                if reset_username not in users:
                    st.session_state["reset_error"] = f"**Username '{reset_username}' tidak ditemukan.**"; st.rerun()
                elif users[reset_username].get("no_hp","").strip() != reset_no_hp.strip():
                    st.session_state["reset_error"] = "**Nomor HP tidak sesuai.**"; st.rerun()
                else:
                    hashed = bcrypt.hashpw(new_password_reset.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                    users[reset_username]["password"] = hashed
                    save_user(reset_username, users[reset_username])
                    st.session_state["reset_form_counter"] = _reset_form_key + 1
                    st.session_state["reset_success"] = f"**Password berhasil direset!** Silakan login 🎉"; st.rerun()
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

st.markdown("""
<style>
[data-testid="stAppViewContainer"] > .main { background: #f0f4f9; }
[data-testid="stAppViewContainer"] > .main .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
[data-testid="stSidebar"] { background: #0d1b2e !important; border-right: none !important; }
[data-testid="stSidebar"] > div:first-child { padding-top: 0 !important; }
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
[data-testid="stSidebar"] label,
[data-testid="stSidebar"] .stRadio > label { color: rgba(255,255,255,0.55) !important; font-size: 12px !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] > div { gap: 2px !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label { color: rgba(255,255,255,0.55) !important; font-size: 12px !important; padding: 6px 10px !important; border-radius: 8px !important; transition: all 0.15s !important; }
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background: rgba(255,255,255,0.06) !important; color: rgba(255,255,255,0.85) !important; }
[data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.08) !important; }
[data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: rgba(255,255,255,0.85) !important; font-size: 14px !important; }
[data-testid="stSidebar"] .stButton > button { background: transparent !important; border: 0.5px solid rgba(255,255,255,0.15) !important; color: rgba(255,255,255,0.5) !important; font-size: 11px !important; border-radius: 8px !important; width: 100% !important; }
[data-testid="stSidebar"] .stButton > button:hover { border-color: rgba(255,99,99,0.5) !important; color: #f87171 !important; background: rgba(255,99,99,0.08) !important; }
.pro-card { background: white; border: 0.5px solid #e2e8f0; border-radius: 12px; overflow: hidden; margin-bottom: 16px; }
.pro-card-header { padding: 14px 20px; border-bottom: 0.5px solid #f1f5f9; display: flex; align-items: center; justify-content: space-between; }
.pro-card-title { font-size: 14px; font-weight: 600; color: #0d1b2e; }
.pro-card-body { padding: 20px; }
.stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 20px; }
.stat-card { background: white; border: 0.5px solid #e2e8f0; border-radius: 12px; padding: 16px 18px; position: relative; overflow: hidden; }
.stat-card::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; border-radius: 12px 12px 0 0; }
.stat-card.blue::before  { background: #2563eb; }
.stat-card.green::before { background: #16a34a; }
.stat-card.amber::before { background: #d97706; }
.stat-icon   { font-size: 20px; margin-bottom: 10px; display: block; }
.stat-label  { font-size: 10px; color: #94a3b8; margin-bottom: 4px; font-weight: 600; letter-spacing: 0.06em; text-transform: uppercase; }
.stat-val    { font-size: 22px; font-weight: 600; color: #0d1b2e; line-height: 1.2; }
.stat-sub    { font-size: 11px; color: #16a34a; margin-top: 4px; }
.stat-sub.warn { color: #d97706; }
.page-topbar { background: white; border: 0.5px solid #e2e8f0; border-radius: 10px; padding: 12px 20px; display: flex; align-items: center; justify-content: space-between; margin-bottom: 18px; }
.breadcrumb-trail { font-size: 12px; color: #94a3b8; display: flex; align-items: center; gap: 6px; }
.breadcrumb-trail .current { color: #0d1b2e; font-weight: 600; }
.tipe-badge { font-size: 11px; font-weight: 600; padding: 4px 14px; border-radius: 20px; }
.tipe-badge.non-blud { background: #eff6ff; color: #2563eb; border: 0.5px solid #bfdbfe; }
.tipe-badge.blud     { background: #f0fdf4; color: #16a34a; border: 0.5px solid #bbf7d0; }
.tipe-badge.gabungan { background: #fff7ed; color: #d97706; border: 0.5px solid #fed7aa; }
.drop-zone-pro { border: 1.5px dashed #c7d7f0; border-radius: 12px; background: #f8faff; padding: 32px 20px; text-align: center; transition: all 0.2s; cursor: pointer; }
.drop-zone-pro:hover { border-color: #2563eb; background: #eff6ff; }
.page-title-pro { font-size: 22px; font-weight: 700; color: #0d1b2e; margin-bottom: 2px; }
.page-subtitle-pro { font-size: 13px; color: #94a3b8; margin-bottom: 20px; }
.history-row { display: flex; align-items: center; gap: 14px; padding: 12px 20px; border-bottom: 0.5px solid #f1f5f9; font-size: 13px; }
.history-row:last-child { border-bottom: none; }
.history-tag { font-size: 10px; font-weight: 600; padding: 3px 10px; border-radius: 20px; background: #f0fdf4; color: #16a34a; border: 0.5px solid #bbf7d0; margin-left: auto; flex-shrink: 0; }

/* ── INFO BANNER (area atas) ── */
.info-banner {
    background: linear-gradient(135deg, #1e3a5f 0%, #2563eb 100%);
    border-radius: 12px;
    padding: 16px 22px;
    margin-bottom: 18px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    flex-wrap: wrap;
    gap: 10px;
}
.info-banner-left { display: flex; align-items: center; gap: 14px; }
.info-banner-icon { font-size: 28px; }
.info-banner-title { font-size: 14px; font-weight: 700; color: white; margin-bottom: 2px; }
.info-banner-sub   { font-size: 12px; color: rgba(255,255,255,0.7); }
.info-banner-stats { display: flex; gap: 20px; }
.info-banner-stat  { text-align: center; }
.info-banner-stat-val   { font-size: 18px; font-weight: 700; color: white; }
.info-banner-stat-label { font-size: 10px; color: rgba(255,255,255,0.6); text-transform: uppercase; letter-spacing: 0.05em; }
.info-banner-divider    { width: 1px; background: rgba(255,255,255,0.2); height: 36px; align-self: center; }

/* ── tombol "Lihat semua history" ── */
.btn-history-link {
    display: inline-flex;
    align-items: center;
    gap: 5px;
    font-size: 12px;
    font-weight: 600;
    color: #2563eb;
    background: #eff6ff;
    border: 0.5px solid #bfdbfe;
    border-radius: 20px;
    padding: 5px 14px;
    cursor: pointer;
    text-decoration: none;
    transition: all 0.15s;
}
.btn-history-link:hover { background: #dbeafe; }
[data-testid="stToolbar"] { display: none !important; visibility: hidden !important; }
[data-testid="stDecoration"] { display: none !important; visibility: hidden !important; }
#MainMenu { display: none !important; visibility: hidden !important; }
footer { display: none !important; visibility: hidden !important; }
[data-testid="stActionButtonIcon"] { display: none !important; visibility: hidden !important; }
.stActionButton { display: none !important; visibility: hidden !important; }
[data-testid="baseButton-actionButton"] { display: none !important; visibility: hidden !important; }
#stDecoration { display: none !important; visibility: hidden !important; }
.viewerBadge_container__r5tak { display: none !important; visibility: hidden !important; }
.styles_viewerBadge__CvC9N { display: none !important; visibility: hidden !important; }
button[kind="actionButton"] { display: none !important; visibility: hidden !important; }
[class*="ActionButton"] { display: none !important; visibility: hidden !important; }
[class*="actionButton"] { display: none !important; visibility: hidden !important; }
button[title="View fullscreen"] { display: none !important; visibility: hidden !important; }
button[data-testid="StyledFullScreenButton"] { display: none !important; visibility: hidden !important; }
</style>
""", unsafe_allow_html=True)

# ── SIDEBAR ──
import base64

current_user  = st.session_state.get('current_user', 'User')
# Ambil nama_lengkap dari session_state (disimpan saat login berhasil)
display_name  = st.session_state.get('nama_lengkap', current_user) or current_user
user_initial  = display_name[0].upper() if display_name else 'U'

# ── Daftar username yang boleh akses Developer Tools ──
ADMIN_USERS = ["admin"]  # tambahkan username admin lain di sini

logo_html = ""
try:
    with open("Logo Provinsi Jawa Timur.png", "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" width="56" style="flex-shrink:0;object-fit:contain;">'
except FileNotFoundError:
    logo_html = '<div style="width:56px;height:56px;border-radius:10px;background:linear-gradient(135deg,#2563eb,#1e40af);display:flex;align-items:center;justify-content:center;font-size:26px;flex-shrink:0;">📊</div>'

st.sidebar.markdown(f"""
<div style="padding:20px 16px 16px;border-bottom:0.5px solid rgba(255,255,255,0.07);display:flex;align-items:center;gap:12px;margin-bottom:8px;">
    {logo_html}
    <div>
        <div style="font-size:14px;font-weight:700;color:rgba(255,255,255,0.95);line-height:1.3;">BPKAD</div>
        <div style="font-size:12px;font-weight:600;color:rgba(255,255,255,0.80);">Provinsi Jawa Timur</div>
        <div style="font-size:10px;color:rgba(255,255,255,0.38);margin-top:2px;">Realisasi Belanja</div>
    </div>
</div>
<div style="padding:10px 16px 4px;">
    <div style="font-size:9px;font-weight:600;letter-spacing:0.1em;color:rgba(255,255,255,0.28);text-transform:uppercase;margin-bottom:6px;">Tipe Data</div>
</div>
""", unsafe_allow_html=True)

if "tahun_non_blud" not in st.session_state: st.session_state["tahun_non_blud"] = 2026
if "tahun_blud"     not in st.session_state: st.session_state["tahun_blud"]     = 2026
if "tahun_anggaran" not in st.session_state: st.session_state["tahun_anggaran"] = 2026
if "tanggal_impor"  not in st.session_state: st.session_state["tanggal_impor"]  = now_wib().strftime("%d/%m/%Y")

HISTORY_DIR_NON_BLUD = "history_non_blud"
HISTORY_DIR_BLUD     = "history_blud"
Path(HISTORY_DIR_NON_BLUD).mkdir(exist_ok=True)
Path(HISTORY_DIR_BLUD).mkdir(exist_ok=True)

# ───────────────────────────────────────────────
#           UTILITAS
# ───────────────────────────────────────────────

def rupiah(x):
    try:    return f"Rp {float(x):,.0f}".replace(",", ".")
    except: return ""

def pct_fmt(x):
    try:    return f"{float(x):.2f}%"
    except: return ""

def ensure_cols(df, cols):
    for c in cols:
        if c not in df.columns: df[c] = 0
    return df

def normalize_headers(df):
    df.columns = df.columns.astype(str).str.upper().str.strip().str.replace(r"\s+", " ", regex=True).str.replace(r"\(|\)", "", regex=True)
    return df

def normalize_numeric(df, cols):
    for col in cols:
        if col in df.columns:
            s = df[col].astype(str).str.replace(",", ".", regex=False).str.replace(r"[^0-9\.\-]", "", regex=True)
            df[col] = pd.to_numeric(s, errors="coerce").fillna(0)
    return df

def coalesce_name(df):
    if "NAMA SKPD" in df.columns and "SKPD" in df.columns:
        a = df["NAMA SKPD"].astype(str); b = df["SKPD"].astype(str)
        return a.where(a.str.strip() != "", b)
    if "NAMA SKPD" in df.columns: return df["NAMA SKPD"].astype(str)
    if "SKPD"      in df.columns: return df["SKPD"].astype(str)
    return df.iloc[:, 0].astype(str)

def compute_pct(df):
    df = ensure_cols(df, ["ANGGARAN", "REALISASI"])
    df = normalize_numeric(df, ["ANGGARAN", "REALISASI"])
    ang  = df["ANGGARAN"].astype(float)
    real = df["REALISASI"].astype(float)
    df["PROSENTASE"] = (real / ang.where(ang > 0, pd.NA) * 100).fillna(0).round(2)
    return df

# ───────────────────────────────────────────────
#           HISTORY
# ───────────────────────────────────────────────

def save_to_history(df, tipe, tanggal_impor, tahun):
    dir_path      = HISTORY_DIR_BLUD if tipe == "BLUD" else HISTORY_DIR_NON_BLUD
    tanggal_clean = tanggal_impor.replace("/", "-")
    # Catat waktu TEPAT saat fungsi ini dipanggil = waktu upload sebenarnya
    waktu_upload_aktual = now_wib()
    timestamp     = waktu_upload_aktual.strftime("%Y%m%d_%H%M%S")
    filename      = f"{tipe.lower()}_{tanggal_clean}_TA{tahun}_{timestamp}.csv"
    filepath      = os.path.join(dir_path, filename)

    # Hapus file lama dengan tanggal + tahun yang sama agar tidak bertambah terus
    tipe_prefix = tipe.lower()
    for old_file in Path(dir_path).glob(f"{tipe_prefix}_{tanggal_clean}_TA{tahun}_*.csv"):
        try:
            old_file.unlink()
        except Exception:
            pass

    # Tulis baris metadata waktu upload di baris ke-1 CSV (sebelum header data)
    # Format: #UPLOAD_TIME=DD/MM/YYYY HH:MM:SS
    waktu_str = waktu_upload_aktual.strftime("%d/%m/%Y %H:%M:%S")
    with open(filepath, "w", encoding="utf-8-sig") as f:
        f.write(f"#UPLOAD_TIME={waktu_str}\n")
        df.to_csv(f, index=False)

def load_history_list(tipe):
    dir_path = HISTORY_DIR_BLUD if tipe == "BLUD" else HISTORY_DIR_NON_BLUD
    return sorted(Path(dir_path).glob("*.csv"), key=lambda x: x.stat().st_mtime, reverse=True)

def load_history_file(filepath):
    # Baca CSV, skip baris metadata #UPLOAD_TIME jika ada
    with open(filepath, encoding="utf-8-sig") as f:
        first = f.readline()
    skip = 1 if first.startswith("#UPLOAD_TIME=") else 0
    return pd.read_csv(filepath, encoding="utf-8-sig", skiprows=skip)

def get_file_info(filepath):
    p       = Path(filepath)
    size_kb = round(p.stat().st_size / 1024, 1)
    name    = p.stem

    # ── 1. Baca #UPLOAD_TIME dari baris pertama CSV (paling akurat) ──
    upload_time = None
    try:
        with open(filepath, encoding="utf-8-sig") as fh:
            first_line = fh.readline().strip()
        if first_line.startswith("#UPLOAD_TIME="):
            val = first_line.split("=", 1)[1].strip()
            # Validasi format DD/MM/YYYY HH:MM:SS
            datetime.strptime(val, "%d/%m/%Y %H:%M:%S")
            upload_time = val
    except Exception:
        upload_time = None

    # ── 2. Fallback: parse timestamp dari nama file ──
    m = re.match(
        r"^(blud|non-blud|non_blud|nonblud)_"
        r"(\d{2}-\d{2}-\d{4})_"
        r"ta(\d{4})_"
        r"(\d{8})_(\d{6})$",
        name.lower()
    )
    tanggal_data   = m.group(2).replace("-", "/") if m else "–"
    tahun_anggaran = m.group(3)                   if m else "–"

    if not upload_time and m:
        ts_raw = m.group(4) + m.group(5)
        try:
            upload_dt   = datetime.strptime(ts_raw, "%Y%m%d%H%M%S") + timedelta(hours=7)
            upload_time = upload_dt.strftime("%d/%m/%Y %H:%M:%S")
        except ValueError:
            pass

    # ── 3. Last resort: waktu modifikasi file ──
    if not upload_time:
        upload_time = (datetime.fromtimestamp(p.stat().st_mtime) + timedelta(hours=7)).strftime("%d/%m/%Y %H:%M:%S")

    return {
        "tanggal_data":   tanggal_data,
        "tahun_anggaran": tahun_anggaran,
        "upload_time":    upload_time,
        "size_kb":        size_kb,
    }

# ───────────────────────────────────────────────
#           PDF REPORT
# ───────────────────────────────────────────────

def generate_pdf_report(df, tanggal_impor, total_ang, total_real, total_persen, tahun_anggaran=2026, tipe="blud"):
    buffer      = io.BytesIO()
    is_blud     = (str(tipe).lower() == "blud")
    is_gabungan = (str(tipe).lower() == "gabungan")
    # Semua tipe pakai landscape agar lebih lega
    page_size   = landscape(A4)
    doc = SimpleDocTemplate(buffer, pagesize=page_size, rightMargin=25, leftMargin=25, topMargin=30, bottomMargin=30)
    elements = []; styles = getSampleStyleSheet()

    # Style untuk wrap text
    wrap_style = styles["Normal"].clone("wrap_style")
    wrap_style.fontSize = 7
    wrap_style.leading  = 9

    header_style = styles["Normal"].clone("header_style")
    header_style.fontSize   = 7
    header_style.leading    = 9
    header_style.textColor  = colors.white
    header_style.fontName   = "Helvetica-Bold"
    header_style.alignment  = 1  # center

    tipe_label = "GABUNGAN (NON-BLUD + BLUD)" if is_gabungan else ("BLUD" if is_blud else "NON-BLUD")
    elements.append(Paragraph(f"LAPORAN REALISASI BELANJA JAWA TIMUR TA {tahun_anggaran} ({tipe_label})", styles["Heading1"]))
    elements.append(Paragraph(f"Data per tanggal: {tanggal_impor}", styles["Normal"]))
    elements.append(Paragraph(f"Dicetak pada: {now_wib().strftime('%d/%m/%Y %H:%M:%S')}", styles["Normal"]))
    elements.append(Spacer(1, 12))

    summary_data  = [["Keterangan","Nilai"],["Total Anggaran",f"Rp {total_ang:,.0f}".replace(",",".")],["Total Realisasi",f"Rp {total_real:,.0f}".replace(",",".")],["% Realisasi",f"{total_persen:.2f}%"]]
    summary_table = Table(summary_data, colWidths=[2.5*inch, 3*inch])
    summary_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("GRID",(0,0),(-1,-1),0.5,colors.grey),
        ("FONTSIZE",(0,0),(-1,-1),9),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f0f4ff")])
    ]))
    elements.append(summary_table); elements.append(Spacer(1,16))

    # Lebar halaman landscape A4 = 841.89pt - margin kiri kanan 50pt = ~791pt
    if is_gabungan or is_blud:
        headers    = ["No","Tipe","Kode SKPD","Nama SKPD","Anggaran","Realisasi","%"]
        col_widths = [0.35*inch, 0.7*inch, 1.2*inch, 3.2*inch, 1.6*inch, 1.6*inch, 0.7*inch]
    else:
        headers    = ["No","No\nAsal","Kode SKPD","Nama SKPD","Anggaran","Realisasi","%"]
        col_widths = [0.3*inch, 0.4*inch, 1.3*inch, 3.0*inch, 1.65*inch, 1.65*inch, 0.65*inch]

    # Buat header row dengan Paragraph agar bisa wrap
    header_row = [Paragraph(h, header_style) for h in headers]
    table_data = [header_row]

    df_reset = df.reset_index(drop=True)
    for urut, (_, row) in enumerate(df_reset.iterrows(), start=1):
        skpd_name = str(row.get("SKPD","") or row.get("NAMA SKPD","") or "")
        no_asal   = str(int(row["No"])) if "No" in row and str(row["No"]).replace(".0","").isdigit() else str(urut)
        anggaran  = f"Rp {float(row.get('ANGGARAN',0) or 0):,.0f}".replace(",",".")
        realisasi = f"Rp {float(row.get('REALISASI',0) or 0):,.0f}".replace(",",".")
        persen    = f"{float(row.get('PROSENTASE',0) or 0):.2f}%"

        # Nama SKPD pakai Paragraph agar bisa word wrap
        nama_para = Paragraph(skpd_name, wrap_style)

        if is_gabungan or is_blud:
            row_list = [str(urut), str(row.get("TIPE","")), str(row.get("KODE SKPD","")), nama_para, anggaran, realisasi, persen]
        else:
            row_list = [str(urut), no_asal, str(row.get("KODE SKPD","")), nama_para, anggaran, realisasi, persen]
        table_data.append(row_list)

    detail_table = Table(table_data, colWidths=col_widths, repeatRows=1)
    detail_table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#1e3a5f")),
        ("TEXTCOLOR",(0,0),(-1,0),colors.white),
        ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),
        ("FONTSIZE",(0,0),(-1,-1),7),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("ALIGN",(3,1),(3,-1),"LEFT"),
        ("ALIGN",(4,1),(5,-1),"RIGHT"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("GRID",(0,0),(-1,-1),0.4,colors.grey),
        ("ROWBACKGROUNDS",(0,1),(-1,-1),[colors.white,colors.HexColor("#f0f4ff")]),
        ("TOPPADDING",(0,0),(-1,-1),4),
        ("BOTTOMPADDING",(0,0),(-1,-1),4),
        ("LEFTPADDING",(0,0),(-1,-1),4),
        ("RIGHTPADDING",(0,0),(-1,-1),4),
    ]))
    elements.append(detail_table)
    doc.build(elements); buffer.seek(0)
    return buffer.getvalue()

# ───────────────────────────────────────────────
#           SIDEBAR – NAVIGASI
# ───────────────────────────────────────────────

tipe_data = st.sidebar.radio(
    "Tipe Data",
    ["Non-BLUD", "BLUD", "Gabungan"],
    format_func=lambda x: {"Non-BLUD":"🔴  Non-BLUD","BLUD":"🔵  BLUD","Gabungan":"🟢  Gabungan"}[x]
)

if tipe_data == "Non-BLUD":
    menu_options = ["Upload Data (Non-BLUD)", "Dashboard (Non-BLUD)", "History (Non-BLUD)"]
elif tipe_data == "BLUD":
    menu_options = ["Upload Data (BLUD)", "Dashboard (BLUD)", "History (BLUD)"]
else:
    menu_options = ["Upload Data (Non-BLUD)", "Upload Data (BLUD)", "Dashboard Gabungan"]

st.sidebar.markdown("""
<div style="padding:14px 16px 4px;">
    <div style="font-size:9px;font-weight:600;letter-spacing:0.1em;color:rgba(255,255,255,0.28);text-transform:uppercase;margin-bottom:6px;">Menu</div>
</div>
""", unsafe_allow_html=True)

# ── Navigasi programatik ke History via session_state ──
_nav = st.session_state.pop("navigate_to", None)
if _nav and _nav in menu_options:
    default_idx = menu_options.index(_nav)
else:
    default_idx = st.session_state.get("_menu_idx", 0)
    # Jaga agar default_idx valid
    if default_idx >= len(menu_options):
        default_idx = 0

menu = st.sidebar.radio(
    "Menu",
    menu_options,
    index=default_idx,
    format_func=lambda x: {
        "Upload Data (Non-BLUD)": "  Upload Data Non-BLUD",
        "Upload Data (BLUD)":     "  Upload Data BLUD",
        "Dashboard (Non-BLUD)":   "  Dashboard",
        "Dashboard (BLUD)":       "  Dashboard",
        "History (Non-BLUD)":     "  History",
        "History (BLUD)":         "  History",
        "Dashboard Gabungan":     "  Dashboard Gabungan",
    }.get(x, x),
    label_visibility="collapsed"
)
# Simpan index pilihan saat ini
st.session_state["_menu_idx"] = menu_options.index(menu)

# ── USER & LOGOUT ──
st.sidebar.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
_admin_badge = '<div style="font-size:10px;color:rgba(255,255,255,0.35);">Administrator</div>' if current_user in ADMIN_USERS else ""
_profile_html = (
    '<div style="padding:10px 16px 8px;border-top:0.5px solid rgba(255,255,255,0.07);margin-top:12px;">'
    '<div style="display:flex;align-items:center;gap:9px;padding:8px 8px;border-radius:8px;">'
    '<div style="width:30px;height:30px;border-radius:50%;background:linear-gradient(135deg,#1d4ed8,#7c3aed);display:flex;align-items:center;justify-content:center;font-size:12px;font-weight:600;color:white;flex-shrink:0;">' + user_initial + '</div>'
    '<div style="flex:1;min-width:0;">'
    '<div style="font-size:12px;font-weight:600;color:rgba(255,255,255,0.88);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">' + display_name + '</div>'
    + _admin_badge +
    '</div>'
    '</div>'
    '</div>'
)
st.sidebar.markdown(_profile_html, unsafe_allow_html=True)

if st.sidebar.button("🚪  Keluar", type="secondary", use_container_width=True):
    st.session_state["logout_message"] = "Anda telah berhasil logout. Silakan login kembali."
    st.session_state["logged_in"] = False
    for key in list(st.session_state.keys()):
        if key not in ["logged_in", "logout_message"]:
            del st.session_state[key]
    st.query_params.clear()
    st.rerun()

if current_user in ADMIN_USERS:
    with st.sidebar.expander("⚙ Developer Tools", expanded=False):
        st.caption("Hanya tersedia untuk akun admin.")
        if st.button("🔄 Clear Cache & Rerun", use_container_width=True, key="dev_clear_cache"):
            st.cache_data.clear()
            st.rerun()

# ───────────────────────────────────────────────
#           UPLOAD DATA
# ───────────────────────────────────────────────

if "Upload Data" in menu:
    tipe_upload = "Non-BLUD" if "Non-BLUD" in menu else "BLUD"
    tipe_class  = "non-blud" if tipe_upload == "Non-BLUD" else "blud"
    tipe_icon   = "🔴" if tipe_upload == "Non-BLUD" else "🔵"
    menu_history = f"History ({tipe_upload})"

    tanggal_now = now_wib().strftime("%d %b %Y")

    # ── TOPBAR BREADCRUMB ──
    st.markdown(f"""
    <div class="page-topbar">
        <div class="breadcrumb-trail">
            <span>{tipe_upload}</span>
            <span style="opacity:0.4">›</span>
            <span class="current">Upload Data</span>
        </div>
        <div style="display:flex;align-items:center;gap:8px;">
            <span style="font-size:11px;color:#94a3b8;background:#f8fafc;border:0.5px solid #e2e8f0;padding:4px 12px;border-radius:20px;">📅 {tanggal_now}</span>
            <span class="tipe-badge {tipe_class}">{tipe_icon} {tipe_upload}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── PAGE TITLE ──
    st.markdown(f"""
    <div class="page-title-pro">Upload Data Realisasi Belanja</div>
    <div class="page-subtitle-pro">Import file Excel untuk memperbarui data realisasi {tipe_upload} Jawa Timur</div>
    """, unsafe_allow_html=True)

    # ── Tampilkan notifikasi sukses setelah rerun ──
    if st.session_state.pop("upload_just_done", False):
        waktu_sukses = st.session_state.get(f"last_upload_time_{tipe_upload}", "")
        HARI_ID_NOTIF = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
        try:
            _dt = datetime.strptime(waktu_sukses, "%d/%m/%Y %H:%M:%S")
            _hari = HARI_ID_NOTIF[_dt.weekday()]
            waktu_sukses = f"{_hari}, {waktu_sukses}"
        except Exception:
            pass
        st.success(f"✅ Upload berhasil disimpan! Diupload pada: **{waktu_sukses}**")

    # ── INFO BANNER ──
    history_dir   = HISTORY_DIR_BLUD if tipe_upload == "BLUD" else HISTORY_DIR_NON_BLUD
    # Selalu baca ulang dari filesystem agar real-time setelah upload
    history_files = sorted(Path(history_dir).glob("*.csv"), key=lambda x: x.stat().st_mtime, reverse=True)
    jumlah_file   = len(history_files)

    _HARI_ID = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]
    from datetime import date as _date
    if history_files:
        # Ambil info file terbaru (sudah sort by mtime, index 0 = paling baru)
        newest_info   = get_file_info(history_files[0])
        last_upload   = newest_info.get("upload_time", "–")   # DD/MM/YYYY HH:MM:SS
        last_modified_date = datetime.fromtimestamp(history_files[0].stat().st_mtime).date()
        selisih    = (_date.today() - last_modified_date).days
        last_label = "Hari ini" if selisih == 0 else (f"{selisih} hari lalu" if selisih > 0 else "Baru saja")
        last_class = "warn" if selisih > 7 else ""
        # Tambahkan nama hari ke stat card
        try:
            _dt_last  = datetime.strptime(last_upload, "%d/%m/%Y %H:%M:%S")
            _hari_last = _HARI_ID[_dt_last.weekday()]
            last_short = f"{_hari_last}, {last_upload}"
        except Exception:
            last_short = last_upload
    else:
        last_upload = "Belum ada"; last_label = "–"; last_class = "warn"; last_short = "Belum ada"

    tahun_aktif = int(st.session_state.get("tahun_anggaran", 2026))

    tip_msg = f"Tahun Anggaran aktif: <b>{tahun_aktif}</b> &nbsp;·&nbsp; Total file tersimpan: <b>{jumlah_file} file</b> &nbsp;·&nbsp; Upload terakhir: <b>{last_short}</b>"
    st.markdown(f"""
    <div class="info-banner">
        <div class="info-banner-left">
            <div class="info-banner-icon">{'' if tipe_upload == 'Non-BLUD' else '🏥'}</div>
            <div>
                <div class="info-banner-title">Sistem Upload Realisasi Belanja — {tipe_upload}</div>
                <div class="info-banner-sub">{tip_msg}</div>
            </div>
        </div>
        <div class="info-banner-stats">
            <div class="info-banner-stat">
                <div class="info-banner-stat-val">{tahun_aktif}</div>
                <div class="info-banner-stat-label">Tahun</div>
            </div>
            <div class="info-banner-divider"></div>
            <div class="info-banner-stat">
                <div class="info-banner-stat-val">{jumlah_file}</div>
                <div class="info-banner-stat-label">File</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── STAT CARDS (selalu baca jumlah_file dari filesystem, bukan cache) ──
    st.markdown(f"""
    <div class="stat-grid">
        <div class="stat-card blue">
            <span class="stat-icon"></span>
            <div class="stat-label">Tahun Anggaran</div>
            <div class="stat-val">{tahun_aktif}</div>
            <div class="stat-sub">Aktif saat ini</div>
        </div>
        <div class="stat-card green">
            <span class="stat-icon"></span>
            <div class="stat-label">File Tersimpan</div>
            <div class="stat-val">{jumlah_file}</div>
            <div class="stat-sub">Total di history</div>
        </div>
        <div class="stat-card amber">
            <span class="stat-icon">⏱</span>
            <div class="stat-label">Upload Terakhir</div>
            <div class="stat-val" style="font-size:13px;margin-top:4px;line-height:1.4;">{last_short}</div>
            <div class="stat-sub {last_class}">{last_label}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── UPLOAD CARD ──
    st.markdown("""
    <div class="pro-card">
        <div class="pro-card-header">
            <span class="pro-card-title"> Import File Excel</span>
            <span style="font-size:10px;font-weight:600;padding:3px 10px;border-radius:20px;background:#eff6ff;color:#2563eb;border:0.5px solid #bfdbfe;">Langkah 1 dari 2</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    uploaded = st.file_uploader("Pilih file .xlsx", type="xlsx", label_visibility="collapsed")

    if uploaded:
        try:
            filename   = uploaded.name
            date_match = re.search(r"(\d{2})[/-](\d{2})[/-](\d{4})", filename)
            if date_match:
                day, month, year = date_match.groups()
                tanggal_impor = f"{day}/{month}/{year}"
                st.success(f"✅ Tanggal terdeteksi dari nama file: **{tanggal_impor}**")
            else:
                tanggal_impor = now_wib().strftime("%d/%m/%Y")
                st.info(f" Tanggal tidak terdeteksi. Menggunakan hari ini: **{tanggal_impor}**")

            st.session_state["tanggal_impor"] = tanggal_impor

            excel = pd.ExcelFile(uploaded)
            sheet_names_upper = [str(s).upper().strip() for s in excel.sheet_names]

            # ── Pilih sheet default sesuai tipe ──
            if tipe_upload == "BLUD":
                preferred = ["SD REAL_BLUD", "SD_REAL_BLUD", "SDREAL_BLUD", "REAL BLUD", "BLUD"]
            else:
                preferred = ["TABLE REAL_BELANJA", "TABLE REAL BELANJA", "SD_REAL", "SD REAL", "REAL_BELANJA"]

            idx = 0
            for p_name in preferred:
                if p_name in sheet_names_upper:
                    idx = sheet_names_upper.index(p_name); break

            sheet = st.selectbox("Pilih Sheet", excel.sheet_names, index=idx)

            # ── Baca sheet: deteksi header otomatis ──
            raw = pd.read_excel(excel, sheet_name=sheet, header=None)

            if tipe_upload == "BLUD":
                # ── Parse sheet BLUD / SD Real_BLUD ──
                # Struktur: baris 0-1 = kosong/judul, baris 2 = header, baris 3 = nomor urut → skip
                # Deteksi header row secara fleksibel
                header_row_blud = 2
                for _hi in range(min(6, len(raw))):
                    _row_vals = [str(v).strip().upper() for v in raw.iloc[_hi] if str(v).strip() not in ("NAN","")]
                    if any(k in _row_vals for k in ["NO","KODE SKPD","SKPD","KREDIT"]):
                        header_row_blud = _hi; break
                skip_rows_blud = [header_row_blud + 1]

                df = pd.read_excel(excel, sheet_name=sheet, header=header_row_blud, skiprows=skip_rows_blud)
                # Bersihkan nama kolom
                cols_clean = []
                seen = {}
                for c in df.columns:
                    c2 = str(c).strip().upper().replace("\n", " ")
                    if c2 in seen:
                        seen[c2] += 1; c2 = f"{c2}_{seen[c2]}"
                    else:
                        seen[c2] = 0
                    cols_clean.append(c2)
                df.columns = cols_clean

                # Map ke nama standar
                col_map_blud = {
                    "NO": "NO", "KODE SKPD": "KODE SKPD", "UNNAMED: 2": "EMPTY",
                    "SKPD": "NAMA SKPD",
                    "KREDIT  ( MURNI)": "ANGGARAN", "KREDIT ( MURNI)": "ANGGARAN",
                    "KREDIT\n( MURNI)": "ANGGARAN", "KREDIT  ( MURNI) ": "ANGGARAN",
                    "KREDIT MURNI": "ANGGARAN", "KREDIT (MURNI)": "ANGGARAN",
                    "SP2D GAJI": "SP2D GAJI", "SP2D LS": "SP2D LS",
                    "RINCIAN PENGGUNAAN SP2D GU/TU": "RINCIAN GU/TU",
                    "RINCIAN GU/TU": "RINCIAN GU/TU", "KOREKSI": "KOREKSI",
                    "JUMLAH": "REALISASI",
                    "%": "PROSENTASE", "%_1": "PERSEN SISA", "%.1": "PERSEN SISA",
                    "SISA KREDIT": "SISA KREDIT",
                }
                df = df.rename(columns=col_map_blud)
                df = df.drop(columns=[c for c in ["NO","EMPTY"] if c in df.columns], errors="ignore")

                # ── Normalisasi sebelum generate tabel turunan ──
                df = normalize_headers(df)
                df = normalize_numeric(df, ["ANGGARAN","REALISASI","SP2D GAJI","SP2D LS","RINCIAN GU/TU","KOREKSI","SISA KREDIT","PROSENTASE","PERSEN SISA"])
                df = compute_pct(df)

                # Filter hanya baris valid (ada nama SKPD & anggaran > 0)
                nm_col = "NAMA SKPD" if "NAMA SKPD" in df.columns else ("SKPD" if "SKPD" in df.columns else None)
                if nm_col and "ANGGARAN" in df.columns:
                    df = df[df[nm_col].notna() & (df[nm_col].astype(str).str.strip() != "") & (df["ANGGARAN"] > 0)]

                # ── Generate Table Master_Unit dari SD Real_BLUD ──
                df_master_blud = pd.DataFrame()
                if nm_col and "KODE SKPD" in df.columns:
                    df_master_blud = df[["KODE SKPD", nm_col]].drop_duplicates(subset=["KODE SKPD"]).reset_index(drop=True)
                    df_master_blud.insert(0, "ID", range(1, len(df_master_blud)+1))
                    df_master_blud = df_master_blud.rename(columns={nm_col: "NAMA SKPD"})

                # ── Generate Table Real_Belanja_BLUD ──
                rb_cols = ["KODE SKPD", nm_col if nm_col else "NAMA SKPD", "ANGGARAN", "REALISASI", "PROSENTASE"]
                df_real_blud = df[[c for c in rb_cols if c in df.columns]].copy()
                df_real_blud.insert(0, "id", range(1, len(df_real_blud)+1))
                df_real_blud["Tanggal Impor Data"] = tanggal_impor
                if nm_col and nm_col != "NAMA SKPD":
                    df_real_blud = df_real_blud.rename(columns={nm_col: "NAMA SKPD"})

                # Hitung total
                _total_ang_blud  = float(df["ANGGARAN"].sum()) if "ANGGARAN" in df.columns else 0
                _total_real_blud = float(df["REALISASI"].sum()) if "REALISASI" in df.columns else 0
                _total_pct_blud  = round(_total_real_blud / _total_ang_blud * 100, 2) if _total_ang_blud > 0 else 0.0

                # ── Simpan ke session_state ──
                st.session_state["df_master_unit_blud"]      = df_master_blud.copy()
                st.session_state["df_real_belanja_blud"]     = df_real_blud.copy()
                st.session_state["blud_sd_real_parsed"]      = True
                st.session_state["blud_total_anggaran"]      = _total_ang_blud
                st.session_state["blud_total_realisasi"]     = _total_real_blud
                st.session_state["blud_total_persen"]        = _total_pct_blud
                st.session_state["tahun_blud"]               = int(st.session_state.get("tahun_anggaran", 2026))

            else:
                # ── Non-BLUD: deteksi apakah sheet ini SD_Real atau Table Real_Belanja ──
                sheet_upper = str(sheet).upper().strip()
                # Deteksi SD_Real: nama sheet cocok, ATAU kolom tunggal & baris pertama = "Belanja"
                first_cell_val = str(raw.iloc[0, 0]).strip().upper() if len(raw) > 0 else ""
                is_sd_real = sheet_upper in ["SD_REAL", "SD REAL", "SHEET1"] or (
                    len(raw.columns) == 1 and (
                        str(raw.columns[0]).upper().strip() == "BELANJA" or first_cell_val == "BELANJA"
                    )
                )

                if is_sd_real:
                    # ── Parse SD_Real: format kolom tunggal berisi blok per SKPD ──
                    # Pola per blok (9 baris): Nama SKPD, "SKPD", "Kode: X.XX...", NaN, "RpX,00Anggaran", "X.XX%", NaN, "RpX,00Realisasi Rill", NaN
                    def parse_rp(s):
                        s = str(s).replace("Rp","").replace(".","").replace(",",".")
                        s = re.sub(r"[^0-9\.]", "", s.split(".")[0] + ("." + s.split(".")[1] if "." in s else ""))
                        s = re.sub(r"[^0-9]", "", str(s).split(".")[0])
                        return int(s) if s else 0

                    def parse_rp_full(s):
                        # Ambil angka dari format "Rp1.425.508.583.583,00Anggaran"
                        s = str(s)
                        m2 = re.search(r"Rp([\d\.,]+)", s)
                        if not m2: return 0
                        num_str = m2.group(1).replace(".","").replace(",",".")
                        try: return float(num_str.split(".")[0])
                        except: return 0

                    raw_vals = raw.iloc[:, 0].tolist()
                    records = []
                    i = 0
                    while i < len(raw_vals):
                        val = str(raw_vals[i]).strip()
                        # Skip baris kosong, header "Belanja"
                        if not val or val.upper() in ("NAN", "BELANJA"):
                            i += 1; continue
                        # Nama SKPD biasanya baris sebelum "SKPD"
                        if i + 1 < len(raw_vals) and str(raw_vals[i+1]).strip().upper() == "SKPD":
                            nama = val
                            # Baris i+2: "Kode: X.XX...."
                            kode_raw = str(raw_vals[i+2]).strip() if i+2 < len(raw_vals) else ""
                            kode = kode_raw.replace("Kode:", "").strip()
                            # Baris i+4: "RpX,00Anggaran"
                            anggaran_raw = str(raw_vals[i+4]).strip() if i+4 < len(raw_vals) else "0"
                            anggaran = parse_rp_full(anggaran_raw)
                            # Baris i+5: "X.XX%"
                            pct_raw = str(raw_vals[i+5]).strip() if i+5 < len(raw_vals) else "0"
                            pct_val = float(re.sub(r"[^0-9\.]","", pct_raw)) if re.search(r"[\d]", pct_raw) else 0.0
                            # Baris i+7: "RpX,00Realisasi Rill"
                            real_raw = str(raw_vals[i+7]).strip() if i+7 < len(raw_vals) else "0"
                            realisasi = parse_rp_full(real_raw)
                            records.append({
                                "Kode SKPD": kode,
                                "Nama SKPD": nama,
                                "Anggaran": anggaran,
                                "Realisasi": realisasi,
                                "Prosentase": pct_val,
                            })
                            i += 9
                        else:
                            i += 1

                    if not records:
                        raise ValueError("Tidak ada data SKPD yang berhasil dibaca dari sheet SD_Real. Pastikan format file sesuai.")

                    df_parsed = pd.DataFrame(records)

                    # ── Generate Table Master_Unit ──
                    auto_id_map = {
                        r["Kode SKPD"]: re.sub(r"[^0-9]","", r["Kode SKPD"]).ljust(15,"0")[:15]
                        for r in records
                    }
                    df_master = pd.DataFrame([
                        {"ID": auto_id_map[r["Kode SKPD"]], "Kode SKPD": r["Kode SKPD"], "Nama SKPD": r["Nama SKPD"]}
                        for r in records
                    ]).drop_duplicates(subset=["Kode SKPD"]).reset_index(drop=True)

                    # ── Generate Table Real_Belanja ──
                    df_real_belanja = df_parsed.copy()
                    df_real_belanja.insert(0, "No", range(1, len(df_real_belanja)+1))
                    df_real_belanja["Tanggal impor Data"] = tanggal_impor

                    # ── Generate Lap RealBelanja ──
                    df_lap = df_parsed.copy()
                    df_lap.insert(0, "NO", range(1, len(df_lap)+1))
                    df_lap = df_lap.rename(columns={
                        "Kode SKPD": "KODE SKPD",
                        "Nama SKPD": "NAMA SKPD",
                        "Anggaran": "ANGGARAN",
                        "Realisasi": "REALISASI",
                        "Prosentase": "% BELANJA",
                    })

                    # ── Hitung total dari Lap RealBelanja (sumber kebenaran angka) ──
                    _total_ang  = float(df_lap["ANGGARAN"].sum())
                    _total_real = float(df_lap["REALISASI"].sum())
                    _total_pct  = round(_total_real / _total_ang * 100, 2) if _total_ang > 0 else 0.0

                    # ── Simpan ke session state untuk dashboard ──
                    st.session_state["df_master_unit"]      = df_master.copy()
                    st.session_state["df_real_belanja"]     = df_real_belanja.copy()
                    st.session_state["df_lap_real"]         = df_lap.copy()
                    st.session_state["sd_real_parsed"]      = True
                    st.session_state["lap_total_anggaran"]  = _total_ang
                    st.session_state["lap_total_realisasi"] = _total_real
                    st.session_state["lap_total_persen"]    = _total_pct

                    # ── Bentuk df utama untuk dashboard & history (dari Real_Belanja) ──
                    df = df_real_belanja.copy()
                    df = df.rename(columns={
                        "Kode SKPD": "KODE SKPD",
                        "Nama SKPD": "NAMA SKPD",
                        "Anggaran": "ANGGARAN",
                        "Realisasi": "REALISASI",
                        "Prosentase": "PROSENTASE",
                        "Tanggal impor Data": "Tanggal Impor Data",
                    })

                else:
                    # Sheet Table Real_Belanja / format standar
                    header_row = 0
                    for i in range(min(5, len(raw))):
                        row_vals = [str(v).strip().upper() for v in raw.iloc[i] if str(v).strip() not in ("NAN","")]
                        if any(k in row_vals for k in ["NO","KODE SKPD","ANGGARAN","NAMA SKPD"]):
                            header_row = i; break

                    df = pd.read_excel(excel, sheet_name=sheet, header=header_row)
                    cols_clean = []
                    seen = {}
                    for c in df.columns:
                        c2 = str(c).strip().upper().replace("\n"," ")
                        if c2 in seen:
                            seen[c2] += 1; c2 = f"{c2}_{seen[c2]}"
                        else:
                            seen[c2] = 0
                        cols_clean.append(c2)
                    df.columns = cols_clean

                    col_map_non = {
                        "NO": "NO", "KODE SKPD": "KODE SKPD",
                        "NAMA SKPD": "NAMA SKPD",
                        "ANGGARAN": "ANGGARAN", "REALISASI": "REALISASI",
                        "PROSENTASE": "PROSENTASE",
                        "TANGGAL IMPOR DATA": "Tanggal Impor Data",
                    }
                    df = df.rename(columns=col_map_non)
                    st.session_state["sd_real_parsed"] = False

            # Non-BLUD: normalize di sini (BLUD sudah dinormalize di atas)
            if tipe_upload == "Non-BLUD":
                df = normalize_headers(df)
                df = normalize_numeric(df, ["ANGGARAN","REALISASI","SP2D GAJI","SP2D LS","RINCIAN GU/TU","KOREKSI","SISA KREDIT","PROSENTASE","PERSEN SISA"])
                df = compute_pct(df)

                nm = "NAMA SKPD" if "NAMA SKPD" in df.columns else ("SKPD" if "SKPD" in df.columns else None)
                if nm and "ANGGARAN" in df.columns:
                    df = df[df[nm].notna() & (df[nm].astype(str).str.strip() != "") & (df["ANGGARAN"] > 0)]

            if "NO" in df.columns: df = df.drop(columns=["NO"])
            if "No" in df.columns: df = df.drop(columns=["No"])
            df.insert(0, "No", range(1, len(df)+1))
            df["Tanggal Impor Data"] = tanggal_impor
            df = df.fillna("")

            if tipe_upload == "Non-BLUD":
                st.session_state["df_non_blud"] = df.copy()
            else:
                st.session_state["df_blud"] = df.copy()

            # Simpan ke history dengan timestamp SEKARANG (real-time saat upload)
            waktu_upload_sekarang = now_wib()
            save_to_history(df, tipe_upload, tanggal_impor, int(st.session_state["tahun_anggaran"]))
            # Catat waktu upload terakhir ke session_state agar stat cards update
            st.session_state[f"last_upload_time_{tipe_upload}"] = waktu_upload_sekarang.strftime("%d/%m/%Y %H:%M:%S")
            st.session_state[f"last_upload_count_{tipe_upload}"] = len(list(Path(history_dir).glob("*.csv")))
            st.session_state["upload_just_done"] = True

            st.success(f"✅ Data berhasil diimport & disimpan ke history!  {waktu_upload_sekarang.strftime('%d/%m/%Y %H:%M:%S')}")
            st.rerun()

            # ── Preview: jika BLUD → tampilkan semua tabel generate ──
            if tipe_upload == "BLUD" and st.session_state.get("blud_sd_real_parsed"):
                st.markdown("""
                <div class="pro-card" style="margin-top:20px;">
                    <div class="pro-card-header"><span class="pro-card-title">🔍 Preview Data — Hasil Generate dari SD Real_BLUD</span></div>
                </div>
                """, unsafe_allow_html=True)
                tab_mu_b, tab_rb_b, tab_all_b = st.tabs([" Table Master_Unit", " Table Real_Belanja_BLUD", " Data Lengkap BLUD"])
                with tab_mu_b:
                    st.dataframe(st.session_state["df_master_unit_blud"], use_container_width=True, hide_index=True)
                with tab_rb_b:
                    df_rb_b = st.session_state["df_real_belanja_blud"].copy()
                    fmt_rb_b = {c: rupiah for c in ["ANGGARAN","REALISASI"] if c in df_rb_b.columns}
                    fmt_rb_b.update({c: pct_fmt for c in ["PROSENTASE"] if c in df_rb_b.columns})
                    st.dataframe(df_rb_b.style.format(fmt_rb_b), use_container_width=True, hide_index=True)
                with tab_all_b:
                    fmt_all_b = {}
                    for col in ["ANGGARAN","REALISASI","SP2D GAJI","SP2D LS","RINCIAN GU/TU","KOREKSI","SISA KREDIT"]:
                        if col in df.columns: fmt_all_b[col] = rupiah
                    for col in ["PROSENTASE","PERSEN SISA"]:
                        if col in df.columns: fmt_all_b[col] = pct_fmt
                    st.dataframe(df.style.format(fmt_all_b), use_container_width=True, hide_index=True)

            # ── Preview: jika SD_Real → tampilkan semua tabel generate ──
            elif tipe_upload == "Non-BLUD" and st.session_state.get("sd_real_parsed"):
                st.markdown("""
                <div class="pro-card" style="margin-top:20px;">
                    <div class="pro-card-header"><span class="pro-card-title"> Preview Data — Hasil Generate dari SD_Real</span></div>
                </div>
                """, unsafe_allow_html=True)
                tab_mu, tab_rb, tab_lap = st.tabs([" Table Master_Unit", " Table Real_Belanja", " Lap RealBelanja"])
                with tab_mu:
                    st.dataframe(st.session_state["df_master_unit"], use_container_width=True, hide_index=True)
                with tab_rb:
                    df_rb_prev = st.session_state["df_real_belanja"].copy()
                    fmt_rb = {c: rupiah for c in ["Anggaran","Realisasi"] if c in df_rb_prev.columns}
                    fmt_rb.update({c: pct_fmt for c in ["Prosentase"] if c in df_rb_prev.columns})
                    st.dataframe(df_rb_prev.style.format(fmt_rb), use_container_width=True, hide_index=True)
                with tab_lap:
                    df_lap_prev = st.session_state["df_lap_real"].copy()
                    fmt_lap = {c: rupiah for c in ["ANGGARAN","REALISASI"] if c in df_lap_prev.columns}
                    fmt_lap.update({c: pct_fmt for c in ["% BELANJA"] if c in df_lap_prev.columns})
                    st.dataframe(df_lap_prev.style.format(fmt_lap), use_container_width=True, hide_index=True)
            else:
                st.markdown("""
                <div class="pro-card" style="margin-top:20px;">
                    <div class="pro-card-header"><span class="pro-card-title">🔍 Preview Data</span></div>
                </div>
                """, unsafe_allow_html=True)
                fmt_map = {}
                for col in ["ANGGARAN","REALISASI","SP2D GAJI","SP2D LS","RINCIAN GU/TU","KOREKSI","SISA KREDIT"]:
                    if col in df.columns: fmt_map[col] = rupiah
                for col in ["PROSENTASE","PERSEN SISA"]:
                    if col in df.columns: fmt_map[col] = pct_fmt
                st.dataframe(df.style.format(fmt_map), use_container_width=True, hide_index=True)

        except Exception as e:
            st.error(f"Upload gagal: {str(e)}")

    # ── HISTORY TERBARU ──
    # Refresh history_files setelah upload
    history_files = sorted(Path(history_dir).glob("*.csv"), key=lambda x: x.stat().st_mtime, reverse=True)

    if history_files:
        st.markdown("""
        <div style="background:white;border:0.5px solid #e2e8f0;border-radius:12px;overflow:hidden;margin-top:16px;">
            <div style="padding:14px 20px;border-bottom:0.5px solid #f1f5f9;display:flex;align-items:center;justify-content:space-between;">
                <span style="font-size:14px;font-weight:600;color:#0d1b2e;"> Upload Terbaru</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        HARI_ID = ["Senin","Selasa","Rabu","Kamis","Jumat","Sabtu","Minggu"]

        for hf in history_files[:5]:
            info      = get_file_info(hf)
            fname     = hf.name
            size_str  = f"{info['size_kb']} KB"
            tgl_str   = info.get("tanggal_data", "–")
            # Tampilkan waktu upload real-time dari timestamp di nama file
            upload_str = info.get("upload_time", info.get("modified_time", "–"))

            # Tambahkan nama hari dalam Bahasa Indonesia
            try:
                upload_dt   = datetime.strptime(upload_str, "%d/%m/%Y %H:%M:%S")
                nama_hari   = HARI_ID[upload_dt.weekday()]
                upload_full = f"{nama_hari}, {upload_str}"
            except Exception:
                upload_full = upload_str

            is_last   = (hf == history_files[:5][-1])
            border    = "none" if is_last else "0.5px solid #f1f5f9"
            st.markdown(f"""
            <div style="background:white;border-left:0.5px solid #e2e8f0;border-right:0.5px solid #e2e8f0;{'border-bottom:0.5px solid #e2e8f0;border-radius:0 0 12px 12px;' if is_last else ''}padding:12px 20px;display:flex;align-items:center;gap:14px;border-bottom:{border};">
                <div style="width:32px;height:32px;border-radius:8px;background:#eff6ff;display:flex;align-items:center;justify-content:center;font-size:16px;flex-shrink:0;">📗</div>
                <div style="flex:1;min-width:0;">
                    <div style="color:#0d1b2e;font-weight:500;font-size:13px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;">{fname}</div>
                    <div style="font-size:11px;color:#94a3b8;margin-top:2px;">
                        Data: <b>{tgl_str}</b> &nbsp;·&nbsp; Diupload: <b>{upload_full}</b> &nbsp;·&nbsp; {size_str}
                    </div>
                </div>
                <div style="font-size:10px;font-weight:600;padding:3px 10px;border-radius:20px;background:#f0fdf4;color:#16a34a;border:0.5px solid #bbf7d0;flex-shrink:0;">Tersimpan</div>
            </div>
            """, unsafe_allow_html=True)

        # ── TOMBOL "Lihat semua history" yang bisa diklik ──
        st.markdown('<div style="margin-top:10px;"></div>', unsafe_allow_html=True)
        if st.button(f" Lihat semua di menu History {tipe_upload} →", key="btn_goto_history", use_container_width=False):
            st.session_state["navigate_to"] = menu_history
            st.rerun()

# ───────────────────────────────────────────────
#           DASHBOARD NON-BLUD
# ───────────────────────────────────────────────

elif "Dashboard (Non-BLUD)" in menu:
    if st.session_state.get("df_non_blud") is None:
        st.warning("Data Non-BLUD belum di-upload."); st.stop()

    df = st.session_state["df_non_blud"].copy()
    st.title("Dashboard Realisasi Belanja Non-BLUD")
    df = ensure_cols(df, ["ANGGARAN","REALISASI","PROSENTASE"])
    df = normalize_numeric(df, ["ANGGARAN","REALISASI","PROSENTASE"])
    df = compute_pct(df)

    df_display = df.copy()
    pos = df_display.columns.get_loc("REALISASI")+1 if "REALISASI" in df_display.columns else len(df_display.columns)
    df_display.insert(pos, "TAHUN ANGGARAN", st.session_state["tahun_non_blud"])

    # Gunakan total dari Lap RealBelanja jika tersedia (lebih akurat), fallback ke df
    if st.session_state.get("sd_real_parsed") and "lap_total_anggaran" in st.session_state:
        total_ang    = st.session_state["lap_total_anggaran"]
        total_real   = st.session_state["lap_total_realisasi"]
        total_persen = st.session_state["lap_total_persen"]
    else:
        total_ang    = float(df["ANGGARAN"].sum())
        total_real   = float(df["REALISASI"].sum())
        total_persen = (total_real/total_ang*100) if total_ang > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Anggaran",  rupiah(total_ang))
    col2.metric("Total Realisasi", rupiah(total_real))
    col3.metric("% Realisasi",     f"{total_persen:.2f}%")

    tanggal_non = st.session_state.get("tanggal_impor", datetime.now().strftime("%d/%m/%Y"))
    st.caption(f"**Data Non-BLUD per tanggal: {tanggal_non}** | Tahun Anggaran: **{st.session_state['tahun_non_blud']}**")

    with st.expander("**Urutkan & Filter Tabel**", expanded=True):
        col_sort1, col_sort2 = st.columns([3,2])
        with col_sort1:
            sort_col = st.selectbox("Urutkan berdasarkan kolom", options=[c for c in df_display.columns if c not in ["Tanggal Impor Data","No"]], index=0, key="sort_non_unique")
        with col_sort2:
            sort_order = st.radio("Urutan", ["Ascending","Descending"], horizontal=True, key="order_non_unique")
        q = st.text_input("Cari (Nama/Kode SKPD)", "", key="search_non_unique")

    df_sorted = df_display.sort_values(by=sort_col, ascending=(sort_order=="Ascending"))
    df_view = df_sorted.copy()
    if q.strip():
        cols_search = [c for c in ["KODE SKPD","NAMA SKPD","SKPD"] if c in df_view.columns]
        if cols_search:
            mask = pd.Series(False, index=df_view.index)
            for c in cols_search: mask |= df_view[c].astype(str).str.contains(q, case=False, na=False)
            df_view = df_view[mask]
    if "No" in df_view.columns: df_view = df_view.drop(columns=["No"])
    df_view = df_view.reset_index(drop=True); df_view.insert(0, "No", range(1, len(df_view)+1))
    fmt_map = {}
    for col in ["ANGGARAN","REALISASI"]:
        if col in df_view.columns: fmt_map[col] = rupiah
    if "PROSENTASE" in df_view.columns: fmt_map["PROSENTASE"] = pct_fmt
    st.subheader("Tabel Data Non-BLUD")
    st.dataframe(df_view.style.format(fmt_map), use_container_width=True, hide_index=True)

    st.subheader("Top 10 Persentase Realisasi Tertinggi Non-BLUD")
    df_pct = df.copy()
    df_pct["NAMA_SKPD"] = coalesce_name(df_pct).fillna("Tidak Ada Nama").astype(str).str.strip()
    df_pct["PCT"]       = (df_pct["REALISASI"]/df_pct["ANGGARAN"].replace(0,pd.NA)*100).round(1)
    df_top = df_pct.sort_values("PCT", ascending=False).head(10)
    if not df_top.empty:
        # ── Grafik 1: Bar Chart (existing) ──
        fig = px.bar(df_top, x="PCT", y="NAMA_SKPD", orientation="h", title="Top 10 Non-BLUD", height=500, text="PCT", color_discrete_sequence=["#EF553B"])
        fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside', textfont_size=12, cliponaxis=False, hovertemplate="<b>%{y}</b><br>PCT: %{x:.1f}%", customdata=df_top[["ANGGARAN","REALISASI"]].values)
        fig.update_layout(xaxis_title="Persentase Realisasi (%)", yaxis_title="Nama SKPD", yaxis=dict(autorange="reversed"), xaxis=dict(range=[0,max(120,df_top["PCT"].max()+10)],dtick=10), bargap=0.2, margin=dict(l=20,r=120,t=60,b=60), plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font=dict(color="#e0e0e0"))
        fig.add_vline(x=100, line_dash="dash", line_color="#ff4b4b", annotation_text="Target 100%", annotation_position="top right")
        st.plotly_chart(fig, use_container_width=True)

        # ── Grafik 2: Donut Chart + Treemap berdampingan ──
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            fig_donut = px.pie(
                df_top, values="PCT", names="NAMA_SKPD",
                title="Proporsi % Realisasi — Top 10 Non-BLUD",
                hole=0.45, height=480,
                color_discrete_sequence=px.colors.sequential.RdBu
            )
            fig_donut.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="<b>%{label}</b><br>PCT: %{value:.1f}%")
            fig_donut.update_layout(
                showlegend=False,
                plot_bgcolor="#0e1117", paper_bgcolor="#0e1117",
                font=dict(color="#e0e0e0"),
                margin=dict(l=10,r=10,t=60,b=10),
                annotations=[dict(text="Top 10", x=0.5, y=0.5, font_size=16, showarrow=False, font_color="#e0e0e0")]
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with col_g2:
            import plotly.graph_objects as go
            df_ranked = df_top.sort_values("PCT", ascending=False).reset_index(drop=True)

            fig_heat = go.Figure(go.Heatmap(
                z=[df_ranked["PCT"].tolist()],
                x=df_ranked["NAMA_SKPD"].tolist(),
                y=["% Realisasi"],
                colorscale="Turbo",
                zmin=df_ranked["PCT"].min() * 0.85,
                zmax=df_ranked["PCT"].max() * 1.05,
                text=[[f"{v:.1f}%" for v in df_ranked["PCT"].tolist()]],
                texttemplate="%{text}",
                textfont={"size": 12, "color": "white"},
                hovertemplate="<b>%{x}</b><br>Realisasi: <b>%{z:.1f}%</b><extra></extra>",
                showscale=True,
            ))
            fig_heat.update_layout(
                title=dict(text="Heatmap % Realisasi — Top 10 Non-BLUD", font=dict(size=14, color="#e0e0e0")),
                height=480,
                xaxis=dict(
                    tickangle=-35,
                    tickfont=dict(size=9, color="#cccccc"),
                    side="bottom",
                ),
                yaxis=dict(
                    tickfont=dict(size=11, color="#cccccc"),
                ),
                plot_bgcolor="#0e1117",
                paper_bgcolor="#0e1117",
                font=dict(color="#e0e0e0"),
                margin=dict(l=10, r=60, t=60, b=140),
            )
            st.plotly_chart(fig_heat, use_container_width=True)

    # ── Tabel tambahan jika data berasal dari SD_Real ──
    if st.session_state.get("sd_real_parsed"):
        st.markdown("---")
        st.subheader(" Data Hasil Generate dari SD_Real")
        tab_mu, tab_rb, tab_lap = st.tabs([" Table Master_Unit", " Table Real_Belanja", " Lap RealBelanja"])

        with tab_mu:
            st.markdown("**Tabel Master Unit (Data SKPD)**")
            q_mu = st.text_input("Cari (Nama/Kode SKPD)", "", key="q_mu_dash")
            df_mu = st.session_state.get("df_master_unit", pd.DataFrame()).copy()
            if q_mu.strip():
                mask = pd.Series(False, index=df_mu.index)
                for c in ["Kode SKPD","Nama SKPD"]:
                    if c in df_mu.columns: mask |= df_mu[c].astype(str).str.contains(q_mu, case=False, na=False)
                df_mu = df_mu[mask]
            st.dataframe(df_mu.reset_index(drop=True), use_container_width=True, hide_index=True)

        with tab_rb:
            st.markdown("**Table Real_Belanja (Data Impor)**")
            q_rb = st.text_input("Cari (Nama/Kode SKPD)", "", key="q_rb_dash")
            df_rb = st.session_state.get("df_real_belanja", pd.DataFrame()).copy()
            if q_rb.strip():
                mask = pd.Series(False, index=df_rb.index)
                for c in ["Kode SKPD","Nama SKPD"]:
                    if c in df_rb.columns: mask |= df_rb[c].astype(str).str.contains(q_rb, case=False, na=False)
                df_rb = df_rb[mask]
            fmt_rb = {c: rupiah for c in ["Anggaran","Realisasi"] if c in df_rb.columns}
            fmt_rb.update({c: pct_fmt for c in ["Prosentase"] if c in df_rb.columns})
            st.dataframe(df_rb.reset_index(drop=True).style.format(fmt_rb), use_container_width=True, hide_index=True)

        with tab_lap:
            st.markdown(f"**Laporan Realisasi Belanja Provinsi Jawa Timur — {tanggal_non}**")
            q_lap = st.text_input("Cari (Nama/Kode SKPD)", "", key="q_lap_dash")
            df_lap = st.session_state.get("df_lap_real", pd.DataFrame()).copy()
            if q_lap.strip():
                mask = pd.Series(False, index=df_lap.index)
                for c in ["KODE SKPD","NAMA SKPD"]:
                    if c in df_lap.columns: mask |= df_lap[c].astype(str).str.contains(q_lap, case=False, na=False)
                df_lap = df_lap[mask]
            # Tambah baris TOTAL
            if not df_lap.empty and "ANGGARAN" in df_lap.columns:
                total_row = {c: "" for c in df_lap.columns}
                total_row["NAMA SKPD"] = "TOTAL"
                total_row["ANGGARAN"]  = float(df_lap["ANGGARAN"].sum())
                total_row["REALISASI"] = float(df_lap["REALISASI"].sum())
                total_ang_lap = total_row["ANGGARAN"]; total_real_lap = total_row["REALISASI"]
                total_row["% BELANJA"] = round(total_real_lap/total_ang_lap*100, 2) if total_ang_lap > 0 else 0
                df_lap = pd.concat([df_lap, pd.DataFrame([total_row])], ignore_index=True)
            fmt_lap = {c: rupiah for c in ["ANGGARAN","REALISASI"] if c in df_lap.columns}
            fmt_lap.update({c: pct_fmt for c in ["% BELANJA"] if c in df_lap.columns})
            st.dataframe(df_lap.reset_index(drop=True).style.format(fmt_lap), use_container_width=True, hide_index=True)

    st.subheader("Export Data")

    # ── Siapkan DataFrame CSV yang rapi: kolom terpisah, No urut + No Asal, angka penuh ──
    df_csv = df_sorted.reset_index(drop=True).copy()

    # Hapus kolom duplikat Tanggal
    if "TANGGAL IMPOR DATA" in df_csv.columns and "Tanggal Impor Data" in df_csv.columns:
        df_csv = df_csv.drop(columns=["Tanggal Impor Data"])
    df_csv.columns = [c.strip() for c in df_csv.columns]

    # Buat kolom No urut baru & No Asal
    no_asal = df_csv["No"].tolist() if "No" in df_csv.columns else list(range(1, len(df_csv)+1))
    df_csv = df_csv.drop(columns=["No"], errors="ignore")
    df_csv.insert(0, "No Asal", no_asal)
    df_csv.insert(0, "No", range(1, len(df_csv)+1))

    # Format angka penuh (bukan scientific notation)
    for col in ["ANGGARAN","REALISASI","SP2D GAJI","SP2D LS","RINCIAN GU/TU","KOREKSI","SISA KREDIT"]:
        if col in df_csv.columns:
            df_csv[col] = df_csv[col].apply(lambda x: f"{float(x):,.0f}".replace(",",".") if str(x).strip() not in ("","nan") else "")
    for col in ["PROSENTASE","PERSEN SISA"]:
        if col in df_csv.columns:
            df_csv[col] = df_csv[col].apply(lambda x: f"{float(x):.2f}%" if str(x).strip() not in ("","nan") else "")

    csv_data = df_csv.to_csv(index=False, sep=";").encode("utf-8-sig")
    st.download_button("⬇ Download CSV", csv_data, "realisasi_non_blud.csv", "text/csv")
    pdf_bytes = generate_pdf_report(df_sorted, tanggal_non, total_ang, total_real, total_persen, st.session_state["tahun_non_blud"], "non_blud")
    st.download_button(" Download PDF", pdf_bytes, "realisasi_non_blud.pdf", "application/pdf")

# ───────────────────────────────────────────────
#           DASHBOARD BLUD
# ───────────────────────────────────────────────

elif "Dashboard (BLUD)" in menu:
    if st.session_state.get("df_blud") is None:
        st.warning("Data BLUD belum di-upload."); st.stop()

    df = st.session_state["df_blud"].copy()
    st.title("Dashboard Realisasi Belanja BLUD")
    df = ensure_cols(df, ["ANGGARAN","REALISASI","SISA KREDIT","PROSENTASE"])
    df = normalize_numeric(df, ["ANGGARAN","REALISASI","SISA KREDIT","PROSENTASE"])
    df = compute_pct(df)

    df_display = df.copy()
    pos = df_display.columns.get_loc("SISA KREDIT")+1 if "SISA KREDIT" in df_display.columns else len(df_display.columns)
    df_display.insert(pos, "TAHUN ANGGARAN", st.session_state["tahun_blud"])

    total_ang    = float(df["ANGGARAN"].sum())
    total_real   = float(df["REALISASI"].sum())
    total_sisa   = float(df["SISA KREDIT"].sum()) if "SISA KREDIT" in df.columns else 0
    total_persen = (total_real/total_ang*100) if total_ang > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Anggaran",    rupiah(total_ang))
    col2.metric("Total Realisasi",   rupiah(total_real))
    col3.metric("% Realisasi",       f"{total_persen:.2f}%")
    col4.metric("Total Sisa Kredit", rupiah(total_sisa))

    tanggal_blud = st.session_state.get("tanggal_impor", datetime.now().strftime("%d/%m/%Y"))
    st.caption(f"**Data BLUD per tanggal: {tanggal_blud}** | Tahun Anggaran: **{st.session_state['tahun_blud']}**")

    # ── Tab navigasi: Master_Unit | Real_Belanja_BLUD | Dashboard ──
    dash_tab1, dash_tab2, dash_tab3 = st.tabs([" Table Master_Unit", " Table Real_Belanja_BLUD", " Dashboard BLUD"])

    with dash_tab1:
        df_mu = st.session_state.get("df_master_unit_blud")
        if df_mu is not None and not df_mu.empty:
            st.subheader("Table Master_Unit")
            q_mu = st.text_input("Cari (Master Unit)", "", key="q_mu_blud")
            df_mu_view = df_mu.copy()
            if q_mu.strip():
                mask_mu = pd.Series(False, index=df_mu_view.index)
                for c in ["KODE SKPD","NAMA SKPD"]:
                    if c in df_mu_view.columns:
                        mask_mu |= df_mu_view[c].astype(str).str.contains(q_mu, case=False, na=False)
                df_mu_view = df_mu_view[mask_mu]
            st.dataframe(df_mu_view, use_container_width=True, hide_index=True)
        else:
            st.info("Upload data BLUD terlebih dahulu untuk melihat Table Master_Unit.")

    with dash_tab2:
        df_rb = st.session_state.get("df_real_belanja_blud")
        if df_rb is not None and not df_rb.empty:
            st.subheader("Table Real_Belanja_BLUD")
            q_rb = st.text_input("Cari (Real Belanja BLUD)", "", key="q_rb_blud")
            df_rb_view = df_rb.copy()
            if q_rb.strip():
                mask_rb = pd.Series(False, index=df_rb_view.index)
                for c in ["KODE SKPD","NAMA SKPD"]:
                    if c in df_rb_view.columns:
                        mask_rb |= df_rb_view[c].astype(str).str.contains(q_rb, case=False, na=False)
                df_rb_view = df_rb_view[mask_rb]
            fmt_rb = {}
            for col in ["ANGGARAN","REALISASI"]:
                if col in df_rb_view.columns: fmt_rb[col] = rupiah
            if "PROSENTASE" in df_rb_view.columns: fmt_rb["PROSENTASE"] = pct_fmt
            st.dataframe(df_rb_view.style.format(fmt_rb), use_container_width=True, hide_index=True)
            # Download Real_Belanja_BLUD
            csv_rb = df_rb.to_csv(index=False).encode("utf-8-sig")
            st.download_button(" Download CSV Real_Belanja_BLUD", csv_rb, "real_belanja_blud.csv", "text/csv", key="dl_rb_blud")
        else:
            st.info("Upload data BLUD terlebih dahulu untuk melihat Table Real_Belanja_BLUD.")

    with dash_tab3:
        with st.expander("**Urutkan & Filter Tabel**", expanded=True):
            col_sort1, col_sort2 = st.columns([3,2])
            with col_sort1:
                sort_col = st.selectbox("Urutkan berdasarkan kolom", options=[c for c in df_display.columns if c not in ["Tanggal Impor Data","No"]], index=0, key="sort_blud_unique")
            with col_sort2:
                sort_order = st.radio("Urutan", ["Ascending","Descending"], horizontal=True, key="order_blud_unique")
            q = st.text_input("Cari (Nama/Kode SKPD)", "", key="search_blud_unique")

        df_sorted = df_display.sort_values(by=sort_col, ascending=(sort_order=="Ascending"))
        df_view = df_sorted.copy()
        if q.strip():
            cols_search = [c for c in ["KODE SKPD","SKPD","NAMA SKPD"] if c in df_view.columns]
            if cols_search:
                mask = pd.Series(False, index=df_view.index)
                for c in cols_search: mask |= df_view[c].astype(str).str.contains(q, case=False, na=False)
                df_view = df_view[mask]
        if "No" in df_view.columns: df_view = df_view.drop(columns=["No"])
        df_view = df_view.reset_index(drop=True); df_view.insert(0, "No", range(1, len(df_view)+1))
        fmt_map = {}
        for col in ["ANGGARAN","REALISASI","SISA KREDIT","SP2D GAJI","SP2D LS","RINCIAN GU/TU","KOREKSI"]:
            if col in df_view.columns: fmt_map[col] = rupiah
        for col in ["PROSENTASE","PERSEN SISA"]:
            if col in df_view.columns: fmt_map[col] = pct_fmt
        st.subheader("Tabel Data BLUD")
        st.dataframe(df_view.style.format(fmt_map), use_container_width=True, hide_index=True)

        st.subheader("Top 10 Persentase Realisasi Tertinggi BLUD")
        df_pct = df.copy()
        df_pct["NAMA_SKPD"] = coalesce_name(df_pct).fillna("Tidak Ada Nama").astype(str).str.strip()
        df_pct["PCT"]       = (df_pct["REALISASI"]/df_pct["ANGGARAN"].replace(0,pd.NA)*100).round(1)
        df_top = df_pct.sort_values("PCT", ascending=False).head(10)
        if not df_top.empty:
            fig = px.bar(df_top, x="PCT", y="NAMA_SKPD", orientation="h", title="Top 10 BLUD", height=500, text="PCT", color_discrete_sequence=["#636EFA"])
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside', textfont_size=12, cliponaxis=False)
            fig.update_layout(xaxis_title="Persentase Realisasi (%)", yaxis_title="Nama SKPD", yaxis=dict(autorange="reversed"), xaxis=dict(range=[0,max(120,df_top["PCT"].max()+10)],dtick=10), bargap=0.2, margin=dict(l=20,r=120,t=60,b=60), plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font=dict(color="#e0e0e0"))
            fig.add_vline(x=100, line_dash="dash", line_color="#ff4b4b", annotation_text="Target 100%", annotation_position="top right")
            st.plotly_chart(fig, use_container_width=True)

        st.subheader("Export Data")
        csv_data  = df_sorted.to_csv(index=False).encode("utf-8-sig")
        st.download_button(" Download CSV", csv_data, "realisasi_blud.csv", "text/csv")
        pdf_bytes = generate_pdf_report(df_sorted, tanggal_blud, total_ang, total_real, total_persen, st.session_state["tahun_blud"], "blud")
        st.download_button(" Download PDF", pdf_bytes, "realisasi_blud.pdf", "application/pdf")

# ───────────────────────────────────────────────
#           DASHBOARD GABUNGAN
# ───────────────────────────────────────────────

elif "Dashboard Gabungan" in menu:
    df_non  = st.session_state.get("df_non_blud")
    df_blud = st.session_state.get("df_blud")
    if df_non is None or df_blud is None:
        st.warning("Upload kedua data (Non-BLUD & BLUD) terlebih dahulu."); st.stop()

    df_non  = df_non.copy();  df_blud = df_blud.copy()
    df_non  = ensure_cols(df_non,  ["ANGGARAN","REALISASI","PROSENTASE"])
    df_blud = ensure_cols(df_blud, ["ANGGARAN","REALISASI","SISA KREDIT","PROSENTASE"])
    df_non  = normalize_numeric(df_non,  ["ANGGARAN","REALISASI","PROSENTASE"])
    df_blud = normalize_numeric(df_blud, ["ANGGARAN","REALISASI","SISA KREDIT","PROSENTASE"])
    df_non  = compute_pct(df_non);  df_blud = compute_pct(df_blud)

    st.title("Dashboard Gabungan (Non-BLUD + BLUD)")
    tgl = st.session_state.get("tanggal_impor", datetime.now().strftime("%d/%m/%Y"))
    st.caption(f"Data per tanggal: **{tgl}** | Tahun Anggaran: **{st.session_state.get('tahun_anggaran','–')}**")

    ang_all   = float(df_non["ANGGARAN"].sum())
    real_non  = float(df_non["REALISASI"].sum())
    real_blud = float(df_blud["REALISASI"].sum())
    real_all  = real_non + real_blud
    pct_all   = (real_all/ang_all*100) if ang_all > 0 else 0

    k1, k2, k3 = st.columns(3)
    k1.metric("Total Anggaran (Non-BLUD)", rupiah(ang_all))
    k2.metric("Total Realisasi (Gabungan)", rupiah(real_all))
    k3.metric("% Realisasi Gabungan", f"{pct_all:.2f}%")

    st.markdown("---")
    tab_all, tab_non, tab_blud = st.tabs(["Gabungan","Non-BLUD","BLUD"])

    df_non_g  = df_non.copy();  df_non_g["TIPE"]  = "Non-BLUD"
    df_blud_g = df_blud.copy(); df_blud_g["TIPE"] = "BLUD"
    keep_cols = [c for c in ["TIPE","KODE SKPD","NAMA SKPD","SKPD","ANGGARAN","REALISASI","PROSENTASE","SISA KREDIT"] if c in df_non_g.columns or c in df_blud_g.columns]
    df_all = pd.concat([df_non_g.reindex(columns=keep_cols), df_blud_g.reindex(columns=keep_cols)], ignore_index=True)
    df_all = normalize_numeric(df_all, ["ANGGARAN","REALISASI","PROSENTASE","SISA KREDIT"])

    with tab_all:
        st.subheader("Tabel Gabungan")
        with st.expander("**Urutkan & Filter Tabel**", expanded=True):
            col_sort1, col_sort2 = st.columns([3,2])
            with col_sort1:
                sort_col = st.selectbox("Urutkan berdasarkan kolom", options=[c for c in df_all.columns if c not in ["Tanggal Impor Data","No"]], index=0, key="sort_gab_unique")
            with col_sort2:
                sort_order = st.radio("Urutan", ["Ascending","Descending"], horizontal=True, key="order_gab_unique")
            q = st.text_input("Cari (Nama/Kode SKPD)", "", key="q_gab_unique")
        df_view = df_all.copy()
        if q.strip():
            cols_search = [c for c in ["KODE SKPD","NAMA SKPD","SKPD"] if c in df_view.columns]
            if cols_search:
                mask = pd.Series(False, index=df_view.index)
                for c in cols_search: mask |= df_view[c].astype(str).str.contains(q, case=False, na=False)
                df_view = df_view[mask]
        df_view = df_view.sort_values(by=sort_col, ascending=(sort_order=="Ascending"))
        if "No" in df_view.columns: df_view = df_view.drop(columns=["No"])
        df_view = df_view.reset_index(drop=True); df_view.insert(0, "No", range(1, len(df_view)+1))
        fmt_map = {}
        for col in ["ANGGARAN","REALISASI","SISA KREDIT"]:
            if col in df_view.columns: fmt_map[col] = rupiah
        if "PROSENTASE" in df_view.columns: fmt_map["PROSENTASE"] = pct_fmt
        st.dataframe(df_view.style.format(fmt_map), use_container_width=True, hide_index=True)

        st.subheader("Top 10 Persentase Realisasi Tertinggi (Gabungan)")
        df_pct = df_all.copy()
        df_pct = normalize_numeric(df_pct, ["ANGGARAN","REALISASI"])
        df_pct = df_pct[df_pct["ANGGARAN"] > 0].copy()
        df_pct["NAMA_SKPD"] = coalesce_name(df_pct).fillna("Tidak Ada Nama").astype(str).str.strip()
        df_pct["PCT"]       = (df_pct["REALISASI"]/df_pct["ANGGARAN"].replace(0,pd.NA)*100).round(1)
        df_top = df_pct.sort_values("PCT", ascending=False).head(10).copy()
        if not df_top.empty:
            color_map = {"BLUD":"#636EFA","Non-BLUD":"#EF553B"}
            fig = px.bar(df_top, x="PCT", y="NAMA_SKPD", color="TIPE", orientation="h", title="Top 10 Tertinggi (Gabungan)", height=500, color_discrete_map=color_map, text="PCT")
            fig.update_traces(texttemplate='%{text:.1f}%', textposition='outside', textfont_size=12, cliponaxis=False)
            fig.update_layout(xaxis_title="Persentase Realisasi (%)", yaxis_title="Nama SKPD", yaxis=dict(autorange="reversed"), xaxis=dict(range=[0,max(120,df_top["PCT"].max()+10)],dtick=10), legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1), bargap=0.2, margin=dict(l=20,r=120,t=60,b=60), plot_bgcolor="#0e1117", paper_bgcolor="#0e1117", font=dict(color="#e0e0e0"))
            fig.add_vline(x=100, line_dash="dash", line_color="#ff4b4b", annotation_text="Target 100%", annotation_position="top right")
            st.plotly_chart(fig, use_container_width=True)

    st.subheader("Export Gabungan")
    csv_all = df_all.to_csv(index=False).encode("utf-8-sig")
    st.download_button(" Download CSV Gabungan", csv_all, "realisasi_gabungan.csv", "text/csv")
    pdf_bytes_gab = generate_pdf_report(df_all.sort_values(by="REALISASI",ascending=False), tgl, ang_all, real_all, pct_all, int(st.session_state.get("tahun_anggaran",2026)), "gabungan")
    st.download_button(" Download PDF Gabungan", pdf_bytes_gab, "realisasi_gabungan.pdf", "application/pdf")

    with tab_non:
        st.subheader("Tabel Non-BLUD")
        q = st.text_input("Cari (Non-BLUD)", value="", key="q_tab_non_vfinal")
        df_view = df_non.copy()
        if q.strip():
            cols_search = [c for c in ["KODE SKPD","NAMA SKPD","SKPD"] if c in df_view.columns]
            if cols_search:
                mask = pd.Series(False, index=df_view.index)
                for c in cols_search: mask |= df_view[c].astype(str).str.contains(q, case=False, na=False)
                df_view = df_view[mask]
        df_view = df_view.sort_values(by="REALISASI", ascending=False)
        if "No" in df_view.columns: df_view = df_view.drop(columns=["No"])
        df_view = df_view.reset_index(drop=True); df_view.insert(0,"No",range(1,len(df_view)+1))
        fmt_map = {"ANGGARAN":rupiah,"REALISASI":rupiah}
        if "PROSENTASE" in df_view.columns: fmt_map["PROSENTASE"] = pct_fmt
        st.dataframe(df_view.style.format(fmt_map), use_container_width=True, hide_index=True)

    with tab_blud:
        st.subheader("Tabel BLUD")
        q = st.text_input("Cari (BLUD)", value="", key="q_tab_blud_vfinal")
        df_view = df_blud.copy()
        if q.strip():
            cols_search = [c for c in ["KODE SKPD","SKPD","NAMA SKPD"] if c in df_view.columns]
            if cols_search:
                mask = pd.Series(False, index=df_view.index)
                for c in cols_search: mask |= df_view[c].astype(str).str.contains(q, case=False, na=False)
                df_view = df_view[mask]
        df_view = df_view.sort_values(by="REALISASI", ascending=False)
        if "No" in df_view.columns: df_view = df_view.drop(columns=["No"])
        df_view = df_view.reset_index(drop=True); df_view.insert(0,"No",range(1,len(df_view)+1))
        fmt_map = {}
        for col in ["ANGGARAN","REALISASI","SISA KREDIT","SP2D GAJI","SP2D LS","RINCIAN GU/TU","KOREKSI"]:
            if col in df_view.columns: fmt_map[col] = rupiah
        for col in ["PROSENTASE","PERSEN SISA"]:
            if col in df_view.columns: fmt_map[col] = pct_fmt
        st.dataframe(df_view.style.format(fmt_map), use_container_width=True, hide_index=True)

# ───────────────────────────────────────────────
#           HISTORY NON-BLUD
# ───────────────────────────────────────────────

elif "History (Non-BLUD)" in menu:
    st.title("📁 History Upload — Non-BLUD")
    files = load_history_list("Non-BLUD")
    if not files:
        st.info("Belum ada history upload Non-BLUD."); st.stop()

    st.subheader(" Detail & Export File History")
    selected      = st.selectbox("Pilih file history:", [f.name for f in files], key="hist_non_select_final")
    selected_path = next(f for f in files if f.name == selected)
    info          = get_file_info(selected_path)
    df_hist       = load_history_file(selected_path)

    # ── Info card detail ──
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:8px;">
        <div style="background:white;border:0.5px solid #e2e8f0;border-radius:10px;padding:16px 18px;border-top:3px solid #7c3aed;">
            <div style="font-size:10px;color:#94a3b8;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">📦 Ukuran File</div>
            <div style="font-size:22px;font-weight:700;color:#0d1b2e;">{info['size_kb']} KB</div>
        </div>
        <div style="background:white;border:0.5px solid #e2e8f0;border-radius:10px;padding:16px 18px;border-top:3px solid #16a34a;">
            <div style="font-size:10px;color:#94a3b8;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">📅 Tahun Anggaran</div>
            <div style="font-size:22px;font-weight:700;color:#0d1b2e;">{info['tahun_anggaran']}</div>
        </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:16px;">
        <div style="background:white;border:0.5px solid #e2e8f0;border-radius:10px;padding:16px 18px;border-top:3px solid #2563eb;">
            <div style="font-size:10px;color:#94a3b8;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">📋 Tanggal Data</div>
            <div style="font-size:20px;font-weight:700;color:#0d1b2e;">{info['tanggal_data']}</div>
        </div>
        <div style="background:white;border:0.5px solid #e2e8f0;border-radius:10px;padding:16px 18px;border-top:3px solid #d97706;">
            <div style="font-size:10px;color:#94a3b8;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">⏰ Waktu Upload</div>
            <div style="font-size:18px;font-weight:700;color:#1d4ed8;">{info['upload_time']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader("📤 Export & Aksi")
    col_csv, col_pdf = st.columns(2)
    with col_csv:
        csv_hist = df_hist.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇ Download CSV", csv_hist, f"history_{selected}", "text/csv", use_container_width=True)
    with col_pdf:
        dfh = normalize_headers(df_hist.copy())
        dfh = normalize_numeric(dfh, ["ANGGARAN","REALISASI","PROSENTASE"])
        dfh = compute_pct(dfh)
        total_ang_h  = float(dfh["ANGGARAN"].sum())  if "ANGGARAN"  in dfh.columns else 0
        total_real_h = float(dfh["REALISASI"].sum()) if "REALISASI" in dfh.columns else 0
        total_pct_h  = (total_real_h/total_ang_h*100) if total_ang_h > 0 else 0
        ta_pdf = info["tahun_anggaran"]
        if not str(ta_pdf).isdigit(): ta_pdf = int(st.session_state.get("tahun_anggaran",2026))
        pdf_hist = generate_pdf_report(dfh, info["tanggal_data"], total_ang_h, total_real_h, total_pct_h, int(ta_pdf), "non_blud")
        st.download_button("📄 Download PDF", pdf_hist, f"history_{selected.replace('.csv','.pdf')}", "application/pdf", use_container_width=True)

    if st.button("🗑️ Hapus File Ini", type="primary", use_container_width=True, key="del_non_final"):
        os.remove(selected_path)
        st.session_state["hist_non_page"] = 1
        st.success(f"File `{selected}` berhasil dihapus.")
        st.rerun()

# ───────────────────────────────────────────────
#           HISTORY BLUD
# ───────────────────────────────────────────────

elif "History (BLUD)" in menu:
    st.title(" History Upload — BLUD")
    files = load_history_list("BLUD")
    if not files:
        st.info("Belum ada history upload BLUD."); st.stop()

    st.subheader("🔍 Detail & Export File History")
    selected      = st.selectbox("Pilih file history:", [f.name for f in files], key="hist_blud_select_final")
    selected_path = next(f for f in files if f.name == selected)
    info          = get_file_info(selected_path)
    df_hist       = load_history_file(selected_path)

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:8px;">
        <div style="background:white;border:0.5px solid #e2e8f0;border-radius:10px;padding:16px 18px;border-top:3px solid #7c3aed;">
            <div style="font-size:10px;color:#94a3b8;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">📦 Ukuran File</div>
            <div style="font-size:22px;font-weight:700;color:#0d1b2e;">{info['size_kb']} KB</div>
        </div>
        <div style="background:white;border:0.5px solid #e2e8f0;border-radius:10px;padding:16px 18px;border-top:3px solid #16a34a;">
            <div style="font-size:10px;color:#94a3b8;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">📅 Tahun Anggaran</div>
            <div style="font-size:22px;font-weight:700;color:#0d1b2e;">{info['tahun_anggaran']}</div>
        </div>
    </div>
    <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:16px;">
        <div style="background:white;border:0.5px solid #e2e8f0;border-radius:10px;padding:16px 18px;border-top:3px solid #2563eb;">
            <div style="font-size:10px;color:#94a3b8;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">📋 Tanggal Data</div>
            <div style="font-size:20px;font-weight:700;color:#0d1b2e;">{info['tanggal_data']}</div>
        </div>
        <div style="background:white;border:0.5px solid #e2e8f0;border-radius:10px;padding:16px 18px;border-top:3px solid #d97706;">
            <div style="font-size:10px;color:#94a3b8;font-weight:600;letter-spacing:0.06em;text-transform:uppercase;margin-bottom:6px;">⏰ Waktu Upload</div>
            <div style="font-size:18px;font-weight:700;color:#16a34a;">{info['upload_time']}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.subheader(" Export & Aksi")
    col_csv, col_pdf = st.columns(2)
    with col_csv:
        csv_hist = df_hist.to_csv(index=False).encode("utf-8-sig")
        st.download_button("⬇ Download CSV", csv_hist, f"history_{selected}", "text/csv", use_container_width=True)
    with col_pdf:
        dfh = normalize_headers(df_hist.copy())
        dfh = normalize_numeric(dfh, ["ANGGARAN","REALISASI","SISA KREDIT","PROSENTASE"])
        dfh = compute_pct(dfh)
        total_ang_h  = float(dfh["ANGGARAN"].sum())  if "ANGGARAN"  in dfh.columns else 0
        total_real_h = float(dfh["REALISASI"].sum()) if "REALISASI" in dfh.columns else 0
        total_pct_h  = (total_real_h/total_ang_h*100) if total_ang_h > 0 else 0
        ta_pdf = info["tahun_anggaran"]
        if not str(ta_pdf).isdigit(): ta_pdf = int(st.session_state.get("tahun_anggaran",2026))
        pdf_hist = generate_pdf_report(dfh, info["tanggal_data"], total_ang_h, total_real_h, total_pct_h, int(ta_pdf), "blud")
        st.download_button(" Download PDF", pdf_hist, f"history_{selected.replace('.csv','.pdf')}", "application/pdf", use_container_width=True)

    if st.button(" Hapus File Ini", type="primary", use_container_width=True, key="del_blud_final"):
        os.remove(selected_path)
        st.session_state["hist_blud_page"] = 1
        st.success(f"File `{selected}` berhasil dihapus.")
        st.rerun()

# ───────────────────────────────────────────────
#           DEBUG — tombol sudah digabung di atas (sidebar expander)
# ───────────────────────────────────────────────