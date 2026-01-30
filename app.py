import streamlit as st
import google.generativeai as genai
import re
import json
from gtts import gTTS
import tempfile
import os

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Guru Saku AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .stButton>button {
        border-radius: 12px; font-weight: bold; border: none;
        background-color: #E74C3C; color: white; transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #C0392B; transform: scale(1.02); }
    /* Box Presentasi */
    .presentation-box {
        border: 2px solid #3498DB;
        border-radius: 15px;
        padding: 20px;
        background-color: #f0f8ff;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ FUNGSI BEDAH KODE (Penyelamat Diagram)
# ==========================================
def bersihkan_kode_dot(text):
    start_index = text.find("digraph")
    if start_index == -1: return None
    balance = 0
    found_first_brace = False
    for i in range(start_index, len(text)):
        if text[i] == '{': balance += 1; found_first_brace = True
        elif text[i] == '}': balance -= 1
        if found_first_brace and balance == 0: return text[start_index:i+1]
    return None

# ==========================================
# 🔒 LOGIN & SETUP
# ==========================================
if 'is_logged_in' not in st.session_state: st.session_state.is_logged_in = False

def check_password():
    input_pw = st.session_state.input_password
    kunci_asli = st.secrets.get("RAHASIA_SAYA", "admin123")
    if input_pw == kunci_asli: st.session_state.is_logged_in = True; st.session_state.input_password = ""
    else: st.error("Password Salah!")

if not st.session_state.is_logged_in:
    st.title("🔒 Login Guru Saku")
    col1, col2 = st.columns([1,2])
    with col2: st.text_input("Password:", type="password", key="input_password", on_change=check_password)
    st.stop()

# State Init
for key, val in {'kurikulum':[], 'materi_sekarang':"", 'quiz_data':None, 'diagram_code':"", 'topik_saat_ini':"", 'audio_path':None}.items():
    if key not in st.session_state: st.session_state[key] = val

# API Key
if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]
else: api_key = st.sidebar.text_input("API Key:", type="password")

if not api_key: st.sidebar.warning("Masukkan API Key."); st.stop()

genai.configure(api_key=api_key)
try: model = genai.GenerativeModel('gemini-2.5-flash')
except: model = genai.GenerativeModel('gemini-2.0-flash')

# ==========================================
# 🖥️ TAMPILAN APLIKASI
# ==========================================
with st.sidebar:
    st.title("🎛️ Kontrol Belajar")
    with st.container(border=True):
        topik_input = st.text_input("Topik:", placeholder="Cth: Revolusi Industri")
        gaya_belajar = st.selectbox("Gaya:", ["👶 Pemula", "💡 Visual", "🏫 Akademis", "🚀 Praktis"])
        if st.button("Buat Kurikulum"):
            if topik_input:
                st.session_state.topik_saat_ini = topik_input
                with st.spinner("Menyusun..."):
                    try:
                        res = model.generate_content(f"Buat 5 Judul Bab belajar '{topik_input}'. List saja.")
                        st.session_state.kurikulum = [l.strip().lstrip('1234567890.- ') for l in res.text.split('\n') if l.strip()][:5]
                        # Reset
                        st.session_state.materi_sekarang = ""
                        st.session_state.diagram_code = ""
                        st.session_state.quiz_data = None
                        st.session_state.audio_path = None
                        st.toast("Siap!")
                    except Exception as e: st.error(f"Error: {e}")

    if st.session_state.kurikulum:
        st.markdown("---"); st.subheader("📚 Daftar Isi")
        pilihan_bab = st.radio("Bab:", st.session_state.kurikulum, label_visibility="collapsed")
    else: pilihan_bab = None

# --- AREA UTAMA ---
if not st.session_state.kurikulum:
    st.title("👋 Guru Saku AI")
    st.info("Masukkan topik di kiri untuk mulai.")

# TABS
tab_teks, tab_video = st.tabs(["📚 Modul Belajar", "🎬 Buat Video Presentasi (Baru!)"])

# === TAB 1: MODUL BELAJAR (Fitur Standar) ===
with tab_teks:
    if st.session_state.kurikulum and pilihan_bab:
        st.header(f"🎓 {st.session_state.topik_saat_ini}")
        st.caption(f"Bab: {pilihan_bab}")
        
        if st.button("✨ Buka Materi"):
            with st.spinner("Menulis..."):
                try:
                    p = f"Jelaskan '{pilihan_bab}' ({gaya_belajar}). Buat Diagram Graphviz DOT: `digraph G {{...}}` node style filled box lightblue."
                    res = model.generate_content(p)
                    full = res.text
                    dot = bersihkan_kode_dot(full)
                    if dot:
                        st.session_state.diagram_code = dot
                        st.session_state.materi_sekarang = full.replace(dot, "").replace("digraph", "").strip()
                    else: st.session_state.diagram_code = ""; st.session_state.materi_sekarang = full
                except Exception as e: st.error(str(e))
        
        if st.session_state.materi_sekarang:
            if st.session_state.diagram_code:
                st.graphviz_chart(st.session_state.diagram_code)
            st.markdown(st.session_state.materi_sekarang)

# === TAB 2: AI VIDEO MAKER (FITUR YANG KAMU MINTA) ===
with tab_video:
    st.header("🎬 Studio Presentasi AI")
    st.write("Fitur ini akan mengubah teks menjadi Video Slide (Suara + Visual) secara otomatis.")
    
    if st.session_state.kurikulum and pilihan_bab:
        if st.button("🎥 GENERATE VIDEO PRESENTASI", use_container_width=True):
            with st.spinner("Langkah 1: Membuat Naskah & Diagram..."):
                try:
                    # 1. Minta Naskah Pendek & Diagram Visual
                    prompt_video = f"""
                    Saya ingin membuat video presentasi pendek tentang: '{pilihan_bab}'.
                    Gaya Bahasa: {gaya_belajar}.
                    
                    Tugas 1: Buatkan Naskah Narasi Pendek (maksimal 3 paragraf) yang enak didengar jika dibacakan.
                    Tugas 2: Buatkan Diagram Visual (Graphviz DOT) yang menggambarkan inti naskah tersebut.
                    
                    Format Output:
                    [NASKAH]
                    ...teks naskah di sini...
                    [/NASKAH]
                    
                    [DIAGRAM]
                    digraph G {{ ... }}
                    [/DIAGRAM]
                    """
                    response = model.generate_content(prompt_video)
                    raw_text = response.text
                    
                    # Parsing Hasil
                    naskah = ""
                    diagram = ""
                    
                    if "[NASKAH]" in raw_text:
                        naskah = raw_text.split("[NASKAH]")[1].split("[/NASKAH]")[0].strip()
                    if "[DIAGRAM]" in raw_text:
                        diagram_raw = raw_text.split("[DIAGRAM]")[1].split("[/DIAGRAM]")[0].strip()
                        diagram = bersihkan_kode_dot(diagram_raw)
                    
                    # Simpan ke state sementara
                    st.session_state.materi_sekarang = naskah # Pakai slot materi utk naskah
                    st.session_state.diagram_code = diagram
                    
                    # 2. Generate Audio (TTS)
                    if naskah:
                        with st.spinner("Langkah 2: Mengisi Suara (Dubbing)..."):
                            tts = gTTS(text=naskah, lang='id', slow=False)
                            # Simpan ke file temp
                            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
                                tts.save(fp.name)
                                st.session_state.audio_path = fp.name
                            st.success("Video Presentasi Siap! 🎥")
                    
                except Exception as e:
                    st.error(f"Gagal membuat video: {e}")
        
        # TAMPILAN PEMUTAR VIDEO (Slide + Audio)
        if st.session_state.audio_path and st.session_state.diagram_code:
            st.markdown("---")
            col_kiri, col_kanan = st.columns([1, 1])
            
            with col_kiri:
                st.info("🔊 **Dengarkan Penjelasan Guru:**")
                st.audio(st.session_state.audio_path, format="audio/mp3")
                
                with st.expander("Lihat Teks Naskah"):
                    st.write(st.session_state.materi_sekarang)

            with col_kanan:
                st.info("🖼️ **Visualisasi Materi:**")
                st.graphviz_chart(st.session_state.diagram_code, use_container_width=True)
            
            st.markdown("---")
            st.caption("💡 Tips: Klik tombol 'Play' pada audio sambil memperhatikan gambar di sebelah kanan.")

    else:
        st.warning("Pilih Topik dan Bab di menu sebelah kiri dulu ya!")
