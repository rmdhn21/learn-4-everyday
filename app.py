import streamlit as st
import google.generativeai as genai
import re # Library untuk mencari kode diagram dalam teks

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Guru Saku AI Pro", page_icon="🎓", layout="wide")
import streamlit as st
import google.generativeai as genai
import re

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Guru Saku AI", page_icon="🎓", layout="wide")

# ==========================================
# 🔒 FITUR KEAMANAN (PASSWORD PROTECTION)
# ==========================================
# Cek apakah password sudah benar di sesi ini
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False

def check_password():
    # Ambil password dari Input User
    input_pw = st.session_state.input_password
    # Ambil password asli dari Secrets
    if "RAHASIA_SAYA" in st.secrets:
        kunci_asli = st.secrets["RAHASIA_SAYA"]
    else:
        kunci_asli = "admin123" # Password cadangan kalau lupa set secrets

    if input_pw == kunci_asli:
        st.session_state.is_logged_in = True
        # Bersihkan input box supaya password gak kelihatan
        st.session_state.input_password = ""
    else:
        st.error("Password Salah! Minggir lu! 😤")

# JIKA BELUM LOGIN, TAMPILKAN LAYAR LOGIN SAJA
if not st.session_state.is_logged_in:
    st.title("🔒 Aplikasi Terkunci")
    st.text_input("Masukkan Password:", type="password", key="input_password", on_change=check_password)
    st.stop()  # <--- INI PENTING: Menghentikan program di sini. Orang gak bisa lanjut ke bawah.

# ==========================================
# JIKA SUDAH LOGIN, BARU JALANKAN KODE DI BAWAH INI
# ==========================================

# ... (LANJUTKAN DENGAN KODE LAMA KAMU DARI SINI KE BAWAH) ...
# Mulai dari: if 'kurikulum' not in st.session_state: ...
# Inisialisasi Session State
if 'kurikulum' not in st.session_state:
    st.session_state.kurikulum = []
if 'materi_sekarang' not in st.session_state:
    st.session_state.materi_sekarang = ""
if 'kuis_sekarang' not in st.session_state:
    st.session_state.kuis_sekarang = ""
if 'diagram_code' not in st.session_state:
    st.session_state.diagram_code = ""

# --- 2. SETUP API KEY ---
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Masukkan API Key:", type="password")

if not api_key:
    st.warning("⚠️ Masukkan API Key di sidebar kiri dulu ya.")
    st.stop()

genai.configure(api_key=api_key)
# Menggunakan Gemini 2.5 Flash (Cepat & Pintar)
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-2.0-flash')

# --- 3. SIDEBAR ---
with st.sidebar:
    st.title("🎛️ Panel Kontrol")
    topik_belajar = st.text_input("Mau belajar apa?", placeholder="Misal: Metamorfosis Kupu-kupu")
    
    gaya_belajar = st.selectbox(
        "Gaya Belajar:",
        ["👶 ELI5 (Mudah & Simpel)", "💡 Visual & Analogi", "🏫 Akademis (Kuliah)", "🧠 Socratic (Tanya Jawab)"]
    )

    if st.button("Buat Rencana Belajar 📝"):
        if topik_belajar:
            with st.spinner("Menyusun kurikulum..."):
                try:
                    prompt_silabus = f"Buatkan silabus 5 BAB untuk topik '{topik_belajar}'. Hanya list judul bab saja."
                    response = model.generate_content(prompt_silabus)
                    raw_text = response.text.strip().split('\n')
                    st.session_state.kurikulum = [line for line in raw_text if line.strip()]
                    # Reset state lama
                    st.session_state.materi_sekarang = ""
                    st.session_state.kuis_sekarang = ""
                    st.session_state.diagram_code = ""
                    st.success("Kurikulum siap!")
                except Exception as e:
                    st.error(f"Gagal: {e}")

    st.markdown("---")
    pilihan_bab = None
    if st.session_state.kurikulum:
        st.header("📚 Daftar Isi")
        pilihan_bab = st.radio("Pilih Bab:", st.session_state.kurikulum)

# --- 4. AREA UTAMA ---
st.title("🎓 Guru Saku AI: Edisi Visual")

if not st.session_state.kurikulum:
    st.info("👈 Mulai dengan memasukkan topik di sebelah kiri.")
else:
    if pilihan_bab:
        st.subheader(f"Bab: {pilihan_bab}")
        
        # Tombol Buka Materi
        if st.button("📖 Buka Materi & Diagram"):
            with st.spinner(f"Guru sedang menggambar diagram & menulis materi..."):
                try:
                    # PROMPT CANGGIH: Minta Materi + Kode Diagram Graphviz
                    prompt_materi = f"""
                    Saya belajar: '{topik_belajar}', Bab: '{pilihan_bab}'.
                    Gaya: '{gaya_belajar}'.
                    
                    Tugas 1: Jelaskan materi secara lengkap dan rapi (Markdown).
                    
                    Tugas 2: Buatkan diagram visual (Mind Map atau Alur Proses) yang menjelaskan poin utama bab ini.
                    Gunakan format kode **Graphviz DOT**.
                    Letakkan kode diagram di DALAM blok code seperti ini:
                    ```dot
                    digraph G {{
                      rankdir=LR;
                      node [style=filled, fillcolor=lightblue];
                      "Konsep A" -> "Konsep B";
                    }}
                    ```
                    Pastikan syntax DOT valid dan sederhana.
                    """
                    
                    response = model.generate_content(prompt_materi)
                    full_text = response.text
                    
                    # Logika Pemisahan Teks dan Diagram
                    # Kita cari teks yang diapit ```dot ... ```
                    diagram_match = re.search(r'```dot(.*?)```', full_text, re.DOTALL)
                    
                    if diagram_match:
                        st.session_state.diagram_code = diagram_match.group(1).strip()
                        # Hapus kode diagram dari teks materi agar tidak dobel
                        st.session_state.materi_sekarang = full_text.replace(diagram_match.group(0), "")
                    else:
                        st.session_state.diagram_code = ""
                        st.session_state.materi_sekarang = full_text
                        
                    st.session_state.kuis_sekarang = "" 

                except Exception as e:
                    st.error(f"Error: {e}")

        # TAMPILKAN HASIL
        if st.session_state.materi_sekarang:
            # 1. Tampilkan Diagram (Jika ada)
            if st.session_state.diagram_code:
                st.write("### 🧩 Peta Konsep Visual")
                try:
                    st.graphviz_chart(st.session_state.diagram_code)
                except:
                    st.warning("Gagal merender diagram, tapi materi tetap aman.")
            
            # 2. Tombol Cari Gambar Asli (Google Image)
            url_gambar = f"https://www.google.com/search?tbm=isch&q={topik_belajar}+{pilihan_bab}"
            st.link_button(f"🔍 Cari Foto Asli '{pilihan_bab}' di Google", url_gambar)

            # 3. Tampilkan Materi Teks
            st.markdown("---")
            st.markdown(st.session_state.materi_sekarang)
            
            # 4. Bagian Kuis
            st.markdown("---")
            if st.button("Uji Pemahaman (Kuis) 📝"):
                with st.spinner("Membuat soal..."):
                    prompt_kuis = f"Buatkan 3 soal pilgan pendek tentang {pilihan_bab}. Kunci jawaban di akhir (spoiler)."
                    res = model.generate_content(prompt_kuis)
                    st.session_state.kuis_sekarang = res.text

            if st.session_state.kuis_sekarang:
                st.info("Kuis Kilat:")
                st.markdown(st.session_state.kuis_sekarang)
