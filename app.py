import streamlit as st
import google.generativeai as genai
import re
import json

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
        background-color: #0068C9; color: white; transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #004B91; transform: scale(1.02); }
    /* Styling container diagram agar tidak menempel ke tepi */
    .graphviz-box {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ FUNGSI PEMBERSIH KODE (THE SURGEON)
# ==========================================
def bersihkan_kode_dot(text):
    """
    Fungsi Bedah: Mencari 'digraph' dan mengambil isinya sampai kurung kurawal penutup yang pas.
    Mengabaikan teks sampah di awal dan akhir.
    """
    # 1. Cari posisi awal kata 'digraph'
    start_index = text.find("digraph")
    if start_index == -1:
        return None # Gak ketemu diagram

    # 2. Mulai hitung kurung kurawal dari posisi digraph
    balance = 0 # Penghitung keseimbangan kurung
    found_first_brace = False
    end_index = -1

    for i in range(start_index, len(text)):
        char = text[i]
        
        if char == '{':
            balance += 1
            found_first_brace = True
        elif char == '}':
            balance -= 1
        
        # Jika sudah pernah nemu '{' dan balance kembali ke 0, berarti itu ujung kode
        if found_first_brace and balance == 0:
            end_index = i + 1
            break
    
    if end_index != -1:
        return text[start_index:end_index]
    else:
        return None

# ==========================================
# 🔒 PASSWORD PROTECTION & SETUP
# ==========================================
if 'is_logged_in' not in st.session_state:
    st.session_state.is_logged_in = False

def check_password():
    input_pw = st.session_state.input_password
    kunci_asli = st.secrets.get("RAHASIA_SAYA", "admin123")
    if input_pw == kunci_asli:
        st.session_state.is_logged_in = True
        st.session_state.input_password = ""
    else:
        st.error("Password Salah!")

if not st.session_state.is_logged_in:
    st.title("🔒 Login Guru Saku")
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        st.text_input("Masukkan Password:", type="password", key="input_password", on_change=check_password)
    st.stop()

# Inisialisasi State
for key, default_val in {'kurikulum': [], 'materi_sekarang': "", 'quiz_data': None, 'diagram_code': "", 'topik_saat_ini': ""}.items():
    if key not in st.session_state: st.session_state[key] = default_val

# API Key
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Masukkan Gemini API Key:", type="password")

if not api_key:
    st.sidebar.warning("⚠️ Masukkan API Key dulu.")
    st.stop()

genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-2.0-flash')

# ==========================================
# 🖥️ TAMPILAN APLIKASI
# ==========================================

with st.sidebar:
    st.title("🎛️ Kontrol Belajar")
    with st.container(border=True):
        topik_input = st.text_input("Topik:", placeholder="Cth: Fotosintesis")
        gaya_belajar = st.selectbox("Gaya:", ["👶 Pemula", "💡 Visual", "🏫 Akademis", "🚀 Praktis"])

        if st.button("Buat Kurikulum"):
            if topik_input:
                st.session_state.topik_saat_ini = topik_input
                with st.spinner("Menyusun..."):
                    try:
                        prompt = f"Buat 5 Judul Bab belajar '{topik_input}'. Hanya list bab."
                        res = model.generate_content(prompt)
                        clean = [line.strip().lstrip('1234567890.- ') for line in res.text.split('\n') if line.strip()]
                        st.session_state.kurikulum = clean[:5]
                        st.session_state.materi_sekarang = ""
                        st.session_state.diagram_code = ""
                        st.session_state.quiz_data = None
                        st.toast("Siap!")
                    except Exception as e: st.error(f"Error: {e}")
            else: st.warning("Isi topik dulu.")

    if st.session_state.kurikulum:
        st.markdown("---")
        st.subheader("📚 Daftar Isi")
        pilihan_bab = st.radio("Pilih Bab:", st.session_state.kurikulum, label_visibility="collapsed")
    else:
        pilihan_bab = None

# --- AREA UTAMA ---
if not st.session_state.kurikulum:
    st.title("👋 Guru Saku AI")
    st.info("Mulai dengan mengisi topik di menu kiri.")

else:
    if pilihan_bab:
        st.header(f"🎓 {st.session_state.topik_saat_ini}")
        st.caption(f"Bab: {pilihan_bab}")
        
        tab_materi, tab_kuis = st.tabs(["📖 Materi & Diagram", "📝 Kuis"])

        # === TAB MATERI ===
        with tab_materi:
            if st.button("✨ Buka Materi Bab Ini", use_container_width=True):
                with st.spinner("Menyiapkan materi dan menggambar diagram..."):
                    try:
                        # PROMPT DIAGRAM YANG LEBIH SPESIFIK
                        prompt_materi = f"""
                        Saya belajar '{st.session_state.topik_saat_ini}', Bab '{pilihan_bab}'.
                        Gaya: {gaya_belajar}.
                        
                        Tugas 1: Jelaskan materi lengkap (Markdown).
                        
                        Tugas 2: Buat DIAGRAM Peta Konsep (Graphviz DOT).
                        - Gunakan `digraph G {{ ... }}`.
                        - Node style: `node [style="filled", fillcolor="lightblue", shape="box", fontname="Arial"]`.
                        - Rankdir: LR (Kiri ke Kanan).
                        - Sertakan diagram di akhir respons.
                        """
                        response = model.generate_content(prompt_materi)
                        text_full = response.text
                        
                        # --- EKSEKUSI FUNGSI BEDAH KODE ---
                        # Kita ambil kode bersihnya saja
                        kode_bersih = bersihkan_kode_dot(text_full)
                        
                        if kode_bersih:
                            st.session_state.diagram_code = kode_bersih
                            # Hapus kode mentah dari teks materi agar rapi
                            # Kita hapus mulai dari kata 'digraph' sampai akhir teks materi (kasarnya)
                            idx = text_full.find("digraph")
                            st.session_state.materi_sekarang = text_full[:idx].strip()
                        else:
                            st.session_state.diagram_code = ""
                            st.session_state.materi_sekarang = text_full
                        
                        st.session_state.quiz_data = None 
                        
                    except Exception as e:
                        st.error(f"Error: {e}")

            # RENDER HASIL
            if st.session_state.materi_sekarang:
                # 1. BAGIAN DIAGRAM (Ditaruh di atas agar terlihat duluan)
                if st.session_state.diagram_code:
                    st.markdown("### 🧩 Peta Konsep")
                    with st.expander("Klik untuk Memperbesar Diagram", expanded=True):
                        try:
                            # Render diagram graphviz
                            st.graphviz_chart(st.session_state.diagram_code, use_container_width=True)
                        except Exception as e:
                            st.error("Diagram error syntax.")
                            st.code(st.session_state.diagram_code) # Tampilkan kode jika error buat debug
                    st.markdown("---")
                
                # 2. BAGIAN TEKS
                st.markdown(st.session_state.materi_sekarang)

        # === TAB KUIS (Logic tetap sama) ===
        with tab_kuis:
            st.write("### 📝 Kuis")
            if st.button("🎲 Buat Kuis"):
                with st.spinner("Bikin soal..."):
                    try:
                        res = model.generate_content(f"Buat 5 Soal Pilgan tentang {pilihan_bab}. Output JSON murni: [{{'question':'..','options':['A','B'],'answer':'A','explanation':'..'}}]")
                        clean_json = res.text.replace("```json","").replace("```","").strip()
                        st.session_state.quiz_data = json.loads(clean_json)
                    except: st.error("Gagal buat soal.")
            
            if st.session_state.quiz_data:
                with st.form("q"):
                    ans = {}
                    for i, q in enumerate(st.session_state.quiz_data):
                        st.markdown(f"**{i+1}. {q['question']}**")
                        ans[i] = st.radio("Jawab:", q['options'], key=f"q{i}", label_visibility="collapsed")
                        st.write("")
                    if st.form_submit_button("Cek"):
                        sc = 0
                        for i, q in enumerate(st.session_state.quiz_data):
                            if ans[i]==q['answer']: sc+=1; st.success(f"No {i+1}: Benar!")
                            else: st.error(f"No {i+1}: Salah. Jawabannya {q['answer']}")
                            st.caption(q['explanation'])
                        st.metric("Nilai", f"{(sc/len(st.session_state.quiz_data))*100:.0f}")
                        
