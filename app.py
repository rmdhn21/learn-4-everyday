import streamlit as st
import google.generativeai as genai
import re
import json

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Guru Saku AI Pro",
    page_icon="🎨",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS & UI
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .stButton>button {
        border-radius: 20px; font-weight: bold; border: none;
        background-color: #4B4BFF; color: white; transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #3333CC; transform: scale(1.02); }
    /* Styling khusus untuk kontainer SVG agar punya background putih (biar terlihat di Dark Mode) */
    .svg-container {
        background-color: #ffffff;
        border-radius: 15px;
        padding: 20px;
        text-align: center;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
for key, default_val in {
    'kurikulum': [],
    'materi_sekarang': "",
    'quiz_data': None,
    'svg_code': "", 
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

# --- FUNGSI BARU: RENDER SVG LANGSUNG ---
def render_svg_safe(svg_code):
    """Membersihkan dan menampilkan SVG secara langsung (Inline HTML)"""
    try:
        # 1. Bersihkan kode dari markdown tick (```xml atau ```svg)
        clean_code = re.sub(r'```(xml|svg)?', '', svg_code).replace('```', '').strip()
        
        # 2. Pastikan tag <svg> ada xmlns agar valid
        if "<svg" in clean_code and "xmlns" not in clean_code:
            clean_code = clean_code.replace('<svg', '<svg xmlns="http://www.w3.org/2000/svg"')
            
        # 3. Tampilkan dalam Div HTML dengan background putih
        html_code = f'<div class="svg-container">{clean_code}</div>'
        st.markdown(html_code, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Gagal menampilkan gambar: {e}")
        st.code(svg_code) # Tampilkan kodenya buat debug kalau error

# ==========================================
# 🖥️ TAMPILAN APLIKASI
# ==========================================

with st.sidebar:
    st.title("🎨 Guru Saku Control")
    with st.container(border=True):
        topik_input = st.text_input("Belajar apa hari ini?", placeholder="Misal: Bisnis Kopi")
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
                        
                        # Reset
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
                        prompt_materi = f"""
                        Saya belajar: '{st.session_state.topik_saat_ini}', Bab: '{pilihan_bab}'.
                        Gaya: '{gaya_belajar}'.
                        
                        Tugas 1: Jelaskan materi bab ini secara lengkap (Markdown).
                        
                        Tugas 2: Buatkan INFOGRAFIS visual dalam format kode **SVG**.
                        - Gunakan elemen <svg>, <rect>, <circle>, <text>, <path>.
                        - Warna-warna: flat design (biru muda, oranye, putih).
                        - Sertakan EMOJI di dalam tag <text> sebagai ikon.
                        - Ukuran: viewBox="0 0 800 400".
                        - Pastikan kode SVG VALID dan LENGKAP (ditutup </svg>).
                        
                        PENTING: Bungkus kode SVG dengan format:
                        ```xml
                        <svg ...> ... </svg>
                        ```
                        """
                        response = model.generate_content(prompt_materi)
                        full_text = response.text
                        
                        # Regex lebih longgar agar menangkap variasi output AI
                        svg_match = re.search(r'```(xml|svg)?(.*?)```', full_text, re.DOTALL)
                        
                        if svg_match:
                            # Ambil grup ke-2 (isinya saja)
                            potential_svg = svg_match.group(2).strip()
                            # Pastikan itu benar-benar SVG
                            if "<svg" in potential_svg:
                                st.session_state.svg_code = potential_svg
                                # Hapus kode dari teks materi
                                st.session_state.materi_sekarang = full_text.replace(svg_match.group(0), "").strip()
                            else:
                                st.session_state.svg_code = ""
                                st.session_state.materi_sekarang = full_text
                        else:
                            # Coba cari manual kalau regex gagal (fallback)
                            if "<svg" in full_text and "</svg>" in full_text:
                                start = full_text.find("<svg")
                                end = full_text.find("</svg>") + 6
                                st.session_state.svg_code = full_text[start:end]
                                st.session_state.materi_sekarang = full_text.replace(st.session_state.svg_code, "")
                            else:
                                st.session_state.svg_code = ""
                                st.session_state.materi_sekarang = full_text
                            
                        st.session_state.quiz_data = None
                    except Exception as e:
                        st.error(f"Error: {e}")

            if st.session_state.materi_sekarang:
                # TAMPILKAN INFOGRAFIS (Langsung Render HTML)
                if st.session_state.svg_code:
                    st.write("### 🎨 Infografis Ringkasan")
                    render_svg_safe(st.session_state.svg_code)
                    st.caption("Gambar di-generate otomatis via Kode SVG")
                    st.markdown("---")

                # TAMPILKAN TEKS
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
                        st.error("Gagal buat soal, coba klik lagi.")

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
