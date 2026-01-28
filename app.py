import streamlit as st
import google.generativeai as genai
import re
import json

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Guru Saku AI Pro", page_icon="🎓", layout="wide")

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
    st.text_input("Masukkan Password:", type="password", key="input_password", on_change=check_password)
    st.stop()

# ==========================================
# ⚙️ SETUP UTAMA
# ==========================================
if 'kurikulum' not in st.session_state:
    st.session_state.kurikulum = []
if 'materi_sekarang' not in st.session_state:
    st.session_state.materi_sekarang = ""
if 'quiz_data' not in st.session_state:
    st.session_state.quiz_data = None
if 'diagram_code' not in st.session_state:
    st.session_state.diagram_code = ""

if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Masukkan API Key:", type="password")

if not api_key:
    st.warning("⚠️ Masukkan API Key di sidebar kiri dulu ya.")
    st.stop()

genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-2.0-flash')

# ==========================================
# 🖥️ TAMPILAN APLIKASI
# ==========================================

# --- SIDEBAR ---
with st.sidebar:
    st.title("🎛️ Panel Kontrol")
    topik_belajar = st.text_input("Mau belajar apa?", placeholder="Misal: Sistem Tata Surya")
    
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
                    st.session_state.materi_sekarang = ""
                    st.session_state.quiz_data = None
                    st.session_state.diagram_code = ""
                    st.success("Kurikulum siap!")
                except Exception as e:
                    st.error(f"Gagal: {e}")

    st.markdown("---")
    pilihan_bab = None
    if st.session_state.kurikulum:
        st.header("📚 Daftar Isi")
        pilihan_bab = st.radio("Pilih Bab:", st.session_state.kurikulum)

# --- AREA UTAMA ---
st.title("🎓 Guru Saku AI: Edisi Interaktif")

if not st.session_state.kurikulum:
    st.info("👈 Mulai dengan memasukkan topik di sebelah kiri.")
else:
    if pilihan_bab:
        st.subheader(f"Bab: {pilihan_bab}")
        
        # TAB MENU
        tab_materi, tab_kuis = st.tabs(["📖 Materi & Visual", "📝 Kuis Interaktif (10 Soal)"])

        # === TAB 1: MATERI ===
        with tab_materi:
            if st.button("Buka Materi Bab Ini"):
                with st.spinner(f"Guru sedang menyiapkan materi..."):
                    try:
                        prompt_materi = f"""
                        Saya belajar: '{topik_belajar}', Bab: '{pilihan_bab}'.
                        Gaya: '{gaya_belajar}'.
                        Jelaskan materi lengkap (Markdown).
                        Jika materi ini cocok dibuatkan diagram alur/konsep, sertakan kode diagram Graphviz DOT di dalam ```dot ... ```.
                        """
                        response = model.generate_content(prompt_materi)
                        full_text = response.text
                        
                        # Ekstrak Diagram
                        diagram_match = re.search(r'```dot(.*?)```', full_text, re.DOTALL)
                        if diagram_match:
                            st.session_state.diagram_code = diagram_match.group(1).strip()
                            st.session_state.materi_sekarang = full_text.replace(diagram_match.group(0), "")
                        else:
                            st.session_state.diagram_code = ""
                            st.session_state.materi_sekarang = full_text
                            
                        st.session_state.quiz_data = None
                    except Exception as e:
                        st.error(f"Error: {e}")

            if st.session_state.materi_sekarang:
                # --- BAGIAN DIAGRAM YANG BISA DI-ZOOM (EXPANDER) ---
                if st.session_state.diagram_code:
                    # Kita bungkus dalam expander agar bisa melebar
                    with st.expander("🧩 Peta Konsep Visual (Klik untuk Memperbesar/Mengecilkan)", expanded=True):
                        try:
                            # use_container_width=True membuatnya selebar mungkin
                            st.graphviz_chart(st.session_state.diagram_code, use_container_width=True)
                            st.caption("Tip: Jika di HP, diagram akan terlihat lebih besar dalam mode layar landscape.")
                        except Exception as e:
                            st.warning(f"Diagram tidak dapat ditampilkan: {e}")
                    st.markdown("---")
                
                st.markdown(st.session_state.materi_sekarang)

        # === TAB 2: KUIS INTERAKTIF ===
        with tab_kuis:
            st.write("Uji pemahamanmu dengan 10 soal pilihan ganda.")
            
            if st.button("Buat Soal Kuis Baru 🎲"):
                with st.spinner("Sedang membuat 10 soal..."):
                    try:
                        prompt_quiz = f"""
                        Buatkan 10 Soal Pilihan Ganda tentang '{pilihan_bab}' ({topik_belajar}).
                        PENTING: Output HANYA JSON Murni list of objects:
                        [
                            {{
                                "question": "Pertanyaan?",
                                "options": ["A", "B", "C", "D"],
                                "answer": "A",
                                "explanation": "Kenapa benar."
                            }}, ...
                        ]
                        Pastikan string 'answer' sama persis dengan salah satu 'options'.
                        """
                        response = model.generate_content(prompt_quiz)
                        text_json = response.text.replace("```json", "").replace("```", "").strip()
                        st.session_state.quiz_data = json.loads(text_json)
                    except Exception as e:
                        st.error(f"Gagal memuat soal. Coba klik lagi. Error: {e}")

            if st.session_state.quiz_data:
                with st.form("form_kuis"):
                    user_answers = {}
                    for i, q in enumerate(st.session_state.quiz_data):
                        st.markdown(f"**{i+1}. {q['question']}**")
                        user_answers[i] = st.radio(f"Pilih jawaban no {i+1}:", q['options'], key=f"soal_{i}", index=None, label_visibility="collapsed")
                        st.write("") # Spasi
                    
                    submitted = st.form_submit_button("Periksa Nilai 📝")
                    
                    if submitted:
                        st.write("---")
                        st.subheader("📊 Hasil Kuis")
                        benar = 0
                        for i, q in enumerate(st.session_state.quiz_data):
                            if user_answers[i] == q['answer']:
                                benar += 1
                                st.success(f"No. {i+1}: Benar! ✅")
                            else:
                                st.error(f"No. {i+1}: Salah. Jawaban kamu: {user_answers[i]}")
                                st.markdown(f"**Kunci Jawaban:** {q['answer']}")
                            st.info(f"💡 {q['explanation']}")
                        
                        nilai = (benar / len(st.session_state.quiz_data)) * 100
                        st.metric("Skor Akhir", f"{nilai:.0f}")
                        if nilai == 100: st.balloons()
