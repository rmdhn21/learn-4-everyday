import streamlit as st
import google.generativeai as genai
import re
import json

# --- 1. KONFIGURASI HALAMAN & CUSTOM CSS ---
st.set_page_config(
    page_title="Guru Saku AI",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS untuk tampilan UI yang bersih
st.markdown("""
<style>
    /* Font modern */
    html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    
    /* Tombol yang lebih menarik */
    .stButton>button {
        border-radius: 12px; font-weight: bold; border: none;
        background-color: #2E86C1; color: white; transition: all 0.3s ease;
        padding: 0.5rem 1rem;
    }
    .stButton>button:hover { background-color: #1B4F72; transform: scale(1.02); }
    
    /* Styling Container Materi */
    div[data-testid="stExpander"] {
        border: 1px solid #ddd;
        border-radius: 10px;
        background-color: #f9f9f9;
    }
    
    /* Header styling */
    h1, h2, h3 { color: #2C3E50; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🔒 PASSWORD PROTECTION
# ==========================================
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False

def check_password():
    input_pw = st.session_state.input_password
    # Ganti "admin123" dengan password yang kamu mau
    kunci_asli = st.secrets.get("RAHASIA_SAYA", "admin123")
    
    if input_pw == kunci_asli:
        st.session_state.is_logged_in = True
        st.session_state.input_password = ""
    else:
        st.error("Password Salah! Coba lagi.")

if not st.session_state.is_logged_in:
    st.title("🔒 Login Guru Saku")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.text_input("Masukkan Password:", type="password", key="input_password", on_change=check_password)
    st.stop()

# ==========================================
# ⚙️ SETUP UTAMA
# ==========================================
# Inisialisasi State (Memory)
for key, default_val in {
    'kurikulum': [],
    'materi_sekarang': "",
    'quiz_data': None,
    'diagram_code': "", 
    'topik_saat_ini': ""
}.items():
    if key not in st.session_state:
        st.session_state[key] = default_val

# Ambil API Key
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Masukkan Gemini API Key:", type="password")

if not api_key:
    st.sidebar.warning("⚠️ API Key diperlukan.")
    st.stop()

genai.configure(api_key=api_key)
# Prioritaskan model Flash yang cepat
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-2.0-flash')

# ==========================================
# 🖥️ TAMPILAN APLIKASI
# ==========================================

with st.sidebar:
    st.title("🎛️ Panel Kontrol")
    with st.container(border=True):
        topik_input = st.text_input("Topik Belajar:", placeholder="Contoh: Digital Marketing")
        gaya_belajar = st.selectbox("Gaya Penjelasan:", ["👶 Pemula (Mudah)", "💡 Visual & Analogi", "🏫 Kuliah (Teoritis)", "🚀 Praktis (To-the-point)"])

        if st.button("Buat Kurikulum 📋"):
            if topik_input:
                st.session_state.topik_saat_ini = topik_input
                with st.spinner("Sedang menyusun silabus..."):
                    try:
                        # Prompt Kurikulum
                        prompt = f"Buatkan daftar 5 Judul Bab untuk belajar '{topik_input}'. Hanya list bab saja tanpa angka/bullet."
                        res = model.generate_content(prompt)
                        # Bersihkan output jadi list
                        clean_list = [line.strip().lstrip('1234567890.- ') for line in res.text.split('\n') if line.strip()]
                        st.session_state.kurikulum = clean_list[:5] # Ambil 5 teratas
                        
                        # Reset layar kanan
                        st.session_state.materi_sekarang = ""
                        st.session_state.quiz_data = None
                        st.session_state.diagram_code = ""
                        st.toast("Kurikulum Siap!", icon="✅")
                    except Exception as e:
                        st.error(f"Gagal: {e}")
            else:
                st.warning("Isi topiknya dulu.")

    st.markdown("---")
    pilihan_bab = None
    if st.session_state.kurikulum:
        st.subheader("📚 Daftar Isi")
        pilihan_bab = st.radio("Pilih Bab:", st.session_state.kurikulum, label_visibility="collapsed")

# --- AREA UTAMA ---
if not st.session_state.kurikulum:
    st.title("👋 Selamat Datang!")
    st.markdown("""
    Aplikasi ini akan membantumu belajar apa saja dengan struktur yang rapi.
    
    1. **Masukkan Topik** di menu kiri.
    2. **Pilih Bab** yang ingin dipelajari.
    3. **Dapatkan Materi** teks + visual diagram otomatis.
    4. **Kerjakan Kuis** untuk tes pemahaman.
    """)
    st.info("👈 Mulai dengan mengisi topik di Sidebar kiri.")

else:
    if pilihan_bab:
        st.header(f"🎓 {st.session_state.topik_saat_ini}")
        st.caption(f"Sedang mempelajari: {pilihan_bab}")
        
        tab_materi, tab_kuis = st.tabs(["📖 Materi & Visual", "📝 Uji Kompetensi"])

        # === TAB MATERI ===
        with tab_materi:
            if st.button("✨ Buka Materi Bab Ini", use_container_width=True):
                with st.spinner("Guru sedang menulis materi & menggambar diagram..."):
                    try:
                        # PROMPT RAHASIA: Meminta Graphviz dengan Style Infografis
                        prompt_materi = f"""
                        Saya belajar '{st.session_state.topik_saat_ini}', Bab '{pilihan_bab}'.
                        Gaya: {gaya_belajar}.
                        
                        Tugas 1: Jelaskan materi secara lengkap dan rapi (Markdown).
                        
                        Tugas 2: Buatkan DIAGRAM VISUAL (Peta Konsep) menggunakan kode **Graphviz DOT**.
                        Syarat Diagram:
                        - Gunakan `node [style="filled", shape="note", fillcolor="#E8DAEF", fontname="Helvetica"]`.
                        - Gunakan warna-warna cerah (pastel) untuk node yang berbeda.
                        - Sertakan EMOJI di dalam label node agar menarik.
                        - Layout dari kiri ke kanan (`rankdir=LR`).
                        
                        Outputkan kode Graphviz di dalam blok:
                        ```dot
                        digraph G {{ ... }}
                        ```
                        """
                        response = model.generate_content(prompt_materi)
                        text_full = response.text
                        
                        # Ekstrak Kode DOT Graphviz
                        match = re.search(r'```dot(.*?)```', text_full, re.DOTALL)
                        if match:
                            st.session_state.diagram_code = match.group(1).strip()
                            # Hapus kode diagram dari teks bacaan
                            st.session_state.materi_sekarang = text_full.replace(match.group(0), "").strip()
                        else:
                            st.session_state.diagram_code = ""
                            st.session_state.materi_sekarang = text_full
                        
                        st.session_state.quiz_data = None # Reset kuis
                        
                    except Exception as e:
                        st.error(f"Error: {e}")

            # TAMPILKAN HASIL
            if st.session_state.materi_sekarang:
                # 1. Tampilkan Diagram (Pasti Muncul)
                if st.session_state.diagram_code:
                    st.markdown("### 🧩 Peta Konsep Visual")
                    with st.expander("Klik untuk Memperbesar Diagram", expanded=True):
                        try:
                            st.graphviz_chart(st.session_state.diagram_code, use_container_width=True)
                            st.caption("Diagram dihasilkan otomatis oleh AI.")
                        except:
                            st.error("Gagal merender diagram.")
                    st.markdown("---")
                
                # 2. Tampilkan Teks
                st.markdown(st.session_state.materi_sekarang)

        # === TAB KUIS ===
        with tab_kuis:
            st.write("### 📝 Kuis Pemahaman")
            if st.button("🎲 Generate 5 Soal", key="btn_soal"):
                with st.spinner("Membuat soal..."):
                    try:
                        p_kuis = f"""
                        Buat 5 Soal Pilihan Ganda tentang '{pilihan_bab}'.
                        Format JSON murni:
                        [
                          {{"question":"...", "options":["A","B","C","D"], "answer":"A", "explanation":"..."}},
                          ...
                        ]
                        """
                        res = model.generate_content(p_kuis)
                        json_text = res.text.replace("```json","").replace("```","").strip()
                        st.session_state.quiz_data = json.loads(json_text)
                    except:
                        st.error("Gagal membuat soal. Coba lagi.")

            if st.session_state.quiz_data:
                with st.form("quiz_form"):
                    user_ans = {}
                    for i, q in enumerate(st.session_state.quiz_data):
                        st.markdown(f"**{i+1}. {q['question']}**")
                        user_ans[i] = st.radio(f"Jawaban {i+1}", q['options'], key=f"q{i}", label_visibility="collapsed")
                        st.write("")
                    
                    if st.form_submit_button("Cek Nilai"):
                        score = 0
                        for i, q in enumerate(st.session_state.quiz_data):
                            if user_ans[i] == q['answer']:
                                score += 1
                                st.success(f"No {i+1}: Benar! ({q['explanation']})")
                            else:
                                st.error(f"No {i+1}: Salah. Jawaban: {q['answer']}")
                                st.caption(f"Penjelasan: {q['explanation']}")
                        
                        final = (score / len(st.session_state.quiz_data)) * 100
                        st.metric("Skor Kamu", f"{final:.0f}")
                        if final == 100: st.balloons()
