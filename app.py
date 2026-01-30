import streamlit as st
import google.generativeai as genai
import re
import json
import base64

# --- 1. KONFIGURASI HALAMAN & CUSTOM CSS ---
st.set_page_config(
    page_title="Guru Saku AI Pro",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS untuk UI Cantik
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .stTextInput>div>div>input, .stSelectbox>div>div>div { border-radius: 10px; }
    .stButton>button {
        border-radius: 20px; font-weight: bold; border: none;
        background-color: #4B4BFF; color: white; transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #3333CC; transform: scale(1.02); }
    h1, h2, h3 { color: #1E1E2E; font-weight: 800; }
    .infographic-box {
        border: 2px solid #e0e0e0; border-radius: 15px; padding: 10px;
        background-color: #ffffff; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 PASSWORD PROTECTION
# ==========================================
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False

def check_password():
    input_pw = st.session_state.input_password
    if "RAHASIA_SAYA" in st.secrets:
        kunci_asli = st.secrets["RAHASIA_SAYA"]
    else:
        kunci_asli = "admin123" 
    if input_pw == kunci_asli:
        st.session_state.is_logged_in = True
        st.session_state.input_password = ""
    else:
        st.error("Password Salah! 😤")

if not st.session_state.is_logged_in:
    st.title("🔒 Aplikasi Terkunci")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.text_input("Masukkan Password:", type="password", key="input_password", on_change=check_password)
    st.stop()

# ==========================================
# ⚙️ SETUP UTAMA
# ==========================================
# Inisialisasi State
for key, default_val in {
    'kurikulum': [],
    'materi_sekarang': "",
    'quiz_data': None,
    'svg_code': "", # Ganti diagram_code jadi svg_code
    'topik_saat_ini': ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = default_val

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    with st.sidebar.expander("🔑 Pengaturan API Key"):
        api_key = st.text_input("Masukkan Gemini API Key:", type="password")

if not api_key:
    st.sidebar.warning("⚠️ API Key belum dimasukkan.")
    st.stop()

genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-2.0-flash')

# Fungsi render SVG agar bisa ditampilkan sebagai gambar
def render_svg(svg_string):
    """Menerjemahkan kode SVG menjadi gambar yang bisa ditampilkan Streamlit"""
    b64 = base64.b64encode(svg_string.encode('utf-8')).decode("utf-8")
    html = r'<img src="data:image/svg+xml;base64,%s" width="100%%"/>' % b64
    st.markdown(html, unsafe_allow_html=True)

# ==========================================
# 🖥️ TAMPILAN APLIKASI
# ==========================================

with st.sidebar:
    st.title("🎨 Guru Saku Control")
    with st.container(border=True):
        topik_input = st.text_input("Belajar apa hari ini?", placeholder="Misal: Metamorfosis")
        gaya_belajar = st.selectbox("Gaya Belajar:", ["👶 ELI5 (Simpel)", "💡 Visual & Analogi", "🏫 Akademis", "🧠 Socratic"])

        if st.button("🚀 Buat Kurikulum"):
            if topik_input:
                st.session_state.topik_saat_ini = topik_input
                with st.spinner("Merancang peta belajar..."):
                    try:
                        prompt_silabus = f"Buatkan silabus 5 BAB untuk topik '{topik_input}'. Hanya list judul bab."
                        response = model.generate_content(prompt_silabus)
                        raw_text = response.text.strip().split('\n')
                        cleaned_list = [re.sub(r'^[\d\.\-\*\s]+', '', line).strip() for line in raw_text if line.strip()]
                        st.session_state.kurikulum = cleaned_list
                        # Reset State
                        st.session_state.materi_sekarang = ""
                        st.session_state.quiz_data = None
                        st.session_state.svg_code = ""
                        st.toast("Siap belajar!", icon="✅")
                    except Exception as e:
                        st.error(f"Gagal: {e}")
            else:
                st.toast("Isi topik dulu!", icon="⚠️")

    st.markdown("---")
    pilihan_bab = None
    if st.session_state.kurikulum:
        st.header("📚 Daftar Materi")
        pilihan_bab = st.radio("Pilih Bab:", st.session_state.kurikulum, label_visibility="collapsed")

# --- MAIN CONTENT ---
if not st.session_state.kurikulum:
    st.title("👋 Guru Saku: Edisi Infografis")
    st.write("Belajar jadi lebih seru dengan rangkuman visual otomatis.")
    col1, col2 = st.columns(2)
    with col1: st.info("🖼️ **Infografis Otomatis**\n\nAI akan menggambar poster visual untuk setiap bab.")
    with col2: st.success("📝 **Kuis & Nilai**\n\nCek pemahamanmu langsung dengan skor real-time.")

else:
    if pilihan_bab:
        st.title(f"🎓 {st.session_state.topik_saat_ini}")
        st.caption(f"Bab: {pilihan_bab}")
        
        tab_materi, tab_kuis = st.tabs(["🖼️ Materi & Infografis", "📝 Kuis Interaktif"])

        # === TAB 1: MATERI & INFOGRAFIS ===
        with tab_materi:
            if st.button("✨ Buka Materi & Infografis", use_container_width=True):
                with st.spinner(f"Sedang mendesain infografis & menulis materi..."):
                    try:
                        # PROMPT SVG INFOGRAFIS
                        prompt_materi = f"""
                        Saya belajar: '{st.session_state.topik_saat_ini}', Bab: '{pilihan_bab}'.
                        Gaya: '{gaya_belajar}'.
                        
                        Tugas 1: Jelaskan materi bab ini secara lengkap (Markdown).
                        
                        Tugas 2: Buatkan INFOGRAFIS visual dalam format kode **SVG (Scalable Vector Graphics)**.
                        - Gunakan warna-warna cerah dan kontras (flat design).
                        - Gunakan bentuk (rect, circle) dan teks untuk menjelaskan poin utama.
                        - WAJIB sertakan EMOJI sebagai ikon di dalam SVG (karena SVG support emoji).
                        - Layout harus rapi, ukuran viewBox="0 0 800 400".
                        - Jangan terlalu banyak teks di dalam SVG, cukup poin kunci.
                        
                        Letakkan kode SVG di DALAM blok code:
                        ```svg
                        <svg ...> ... </svg>
                        ```
                        """
                        response = model.generate_content(prompt_materi)
                        full_text = response.text
                        
                        # Ekstrak SVG
                        svg_match = re.search(r'```svg(.*?)```', full_text, re.DOTALL)
                        if svg_match:
                            st.session_state.svg_code = svg_match.group(1).strip()
                            st.session_state.materi_sekarang = full_text.replace(svg_match.group(0), "").strip()
                        else:
                            st.session_state.svg_code = ""
                            st.session_state.materi_sekarang = full_text
                            
                        st.session_state.quiz_data = None
                    except Exception as e:
                        st.error(f"Error: {e}")

            if st.session_state.materi_sekarang:
                # TAMPILKAN INFOGRAFIS SVG
                if st.session_state.svg_code:
                    st.write("### 🎨 Infografis Ringkasan")
                    with st.expander("Perbesar Infografis (Zoom)", expanded=True):
                        # Render SVG sebagai gambar
                        render_svg(st.session_state.svg_code)
                        st.caption("Gambar ini dibuat otomatis oleh kode AI.")
                    st.markdown("---")

                # TAMPILKAN TEKS MATERI
                st.markdown(st.session_state.materi_sekarang)

        # === TAB 2: KUIS ===
        with tab_kuis:
            st.write("Uji pemahamanmu sekarang!")
            if st.button("🎲 Buat Soal Kuis", use_container_width=True):
                with st.spinner("Membuat soal..."):
                    try:
                        prompt_quiz = f"""
                        Buat 10 Soal Pilgan tentang '{pilihan_bab}'.
                        Output JSON Murni list of objects:
                        [
                            {{ "question": "...", "options": ["A", "B", "C", "D"], "answer": "A", "explanation": "..." }}, ...
                        ]
                        Pastikan 'answer' sama persis dengan salah satu 'options'.
                        """
                        response = model.generate_content(prompt_quiz)
                        text_json = response.text.replace("```json", "").replace("```", "").strip()
                        st.session_state.quiz_data = json.loads(text_json)
                    except:
                        st.error("Gagal buat soal, coba lagi.")

            if st.session_state.quiz_data:
                with st.form("kuis_form"):
                    user_answers = {}
                    for i, q in enumerate(st.session_state.quiz_data):
                        st.markdown(f"**{i+1}. {q['question']}**")
                        user_answers[i] = st.radio(f"Jawab {i+1}", q['options'], key=f"s{i}", label_visibility="collapsed")
                        st.write("")
                    
                    if st.form_submit_button("✅ Cek Nilai"):
                        benar = 0
                        for i, q in enumerate(st.session_state.quiz_data):
                            with st.expander(f"Soal {i+1}: {'✅ Benar' if user_answers[i]==q['answer'] else '❌ Salah'}"):
                                if user_answers[i] == q['answer']:
                                    benar += 1
                                    st.success(f"Jawabanmu Benar: {q['answer']}")
                                else:
                                    st.error(f"Jawabanmu: {user_answers[i]}")
                                    st.success(f"Kunci: {q['answer']}")
                                st.info(f"Pembahasan: {q['explanation']}")
                        
                        nilai = (benar/len(st.session_state.quiz_data))*100
                        st.metric("Nilai Kamu", f"{nilai:.0f}")
                        if nilai == 100: st.balloons()
