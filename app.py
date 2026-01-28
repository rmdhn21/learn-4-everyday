import streamlit as st
import google.generativeai as genai

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(page_title="Guru Saku AI", page_icon="🎓", layout="wide")

# Inisialisasi Session State (Agar data tidak hilang saat klik tombol)
if 'kurikulum' not in st.session_state:
    st.session_state.kurikulum = []
if 'materi_sekarang' not in st.session_state:
    st.session_state.materi_sekarang = ""
if 'kuis_sekarang' not in st.session_state:
    st.session_state.kuis_sekarang = ""

# --- 2. SETUP API KEY ---
# Cek di Secrets atau Sidebar
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Masukkan API Key:", type="password")

if not api_key:
    st.warning("⚠️ Masukkan API Key di sidebar kiri dulu ya.")
    st.stop()

# Setup Model (Pakai Gemini 2.5 Flash yang tersedia di akunmu)
genai.configure(api_key=api_key)
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except:
    model = genai.GenerativeModel('gemini-2.0-flash')

# --- 3. SIDEBAR (KOLOM KIRI: INPUT & DAFTAR ISI) ---
with st.sidebar:
    st.title("🎛️ Panel Kontrol")
    
    # Input Topik
    topik_belajar = st.text_input("Mau belajar apa?", placeholder="Misal: Fisika Kuantum")
    
    # Pilihan Gaya Belajar (Sesuai Konsep Awal)
    gaya_belajar = st.selectbox(
        "Gaya Belajar:",
        [
            "👶 ELI5 (Jelaskan seperti saya umur 5 tahun)",
            "💡 Penuh Analogi (Pakai benda sehari-hari)",
            "🏫 Akademis & Serius (Untuk kuliah)",
            "🧠 Socratic (Pancing saya berpikir, jangan langsung jawab)"
        ]
    )

    # Tombol Buat Kurikulum
    if st.button("Buat Rencana Belajar 📝"):
        if topik_belajar:
            with st.spinner("Menyusun kurikulum..."):
                try:
                    # Prompt khusus untuk membuat Silabus JSON-like sederhana
                    prompt_silabus = f"""
                    Buatkan silabus belajar untuk topik: '{topik_belajar}'.
                    Bagi menjadi 5 BAB UTAMA yang berurutan dari dasar ke mahir.
                    Hanya berikan daftar judul babnya saja. Jangan ada teks lain.
                    Format:
                    1. Judul Bab 1
                    2. Judul Bab 2
                    ...
                    """
                    response = model.generate_content(prompt_silabus)
                    # Membersihkan text agar jadi list rapi
                    raw_text = response.text.strip().split('\n')
                    st.session_state.kurikulum = [line for line in raw_text if line.strip()]
                    st.session_state.materi_sekarang = "" # Reset materi
                    st.session_state.kuis_sekarang = ""   # Reset kuis
                    st.success("Kurikulum siap! Pilih bab di bawah.")
                except Exception as e:
                    st.error(f"Gagal: {e}")

    st.markdown("---")
    
    # --- DAFTAR ISI DINAMIS ---
    # Bagian ini hanya muncul kalau kurikulum sudah dibuat
    pilihan_bab = None
    if st.session_state.kurikulum:
        st.header("📚 Daftar Isi Materi")
        pilihan_bab = st.radio("Pilih Bab untuk Mulai:", st.session_state.kurikulum)

# --- 4. KOLOM TENGAH (MATERI & KUIS) ---
st.title("🎓 Guru Saku AI")

if not st.session_state.kurikulum:
    st.info("👈 Masukkan topik di Sidebar kiri, lalu klik 'Buat Rencana Belajar' untuk memulai.")
    st.markdown("""
    **Fitur Utama:**
    * **Syllabus Generator:** Membuat peta belajar otomatis.
    * **Analogy Master:** Menjelaskan konsep rumit jadi mudah.
    * **Auto-Quiz:** Tes pemahamanmu di setiap bab.
    """)

else:
    # Jika User memilih bab, generate materi
    if pilihan_bab:
        st.subheader(f"Sedang Mempelajari: {pilihan_bab}")
        
        # Tombol untuk memuat materi bab ini
        if st.button("📖 Buka Materi Bab Ini"):
            with st.spinner(f"Guru sedang menjelaskan {pilihan_bab}..."):
                try:
                    prompt_materi = f"""
                    Saya sedang belajar: '{topik_belajar}'.
                    Bab saat ini: '{pilihan_bab}'.
                    Gaya penjelasan: '{gaya_belajar}'.
                    
                    Tugasmu:
                    1. Jelaskan materi bab ini secara mendalam sesuai gaya yang dipilih.
                    2. Jika gaya 'Socratic' dipilih, ajukan pertanyaan retoris.
                    3. Jika gaya 'Analogi' dipilih, wajib pakai perumpamaan benda nyata.
                    4. Gunakan format Markdown rapi (Bold, List, Code block jika perlu).
                    """
                    response = model.generate_content(prompt_materi)
                    st.session_state.materi_sekarang = response.text
                    st.session_state.kuis_sekarang = "" # Reset kuis kalau ganti materi
                except Exception as e:
                    st.error(f"Error: {e}")

        # Menampilkan Materi
        if st.session_state.materi_sekarang:
            st.markdown("---")
            st.markdown(st.session_state.materi_sekarang)
            
            st.markdown("---")
            st.write("### 🧠 Uji Pemahaman")
            
            # Tombol Kuis (Fitur Evaluasi)
            if st.button("Saya sudah paham, beri saya Kuis! 📝"):
                with st.spinner("Membuat soal..."):
                    try:
                        prompt_kuis = f"""
                        Berdasarkan materi '{pilihan_bab}' tentang '{topik_belajar}'.
                        Buatkan 3 Soal Pilihan Ganda sederhana untuk menguji pemahaman user.
                        Di bagian bawah, berikan Kunci Jawaban tersembunyi (di dalam toggle/spoiler jika bisa, atau tulis 'Kunci Jawaban:' di paling bawah).
                        """
                        response = model.generate_content(prompt_kuis)
                        st.session_state.kuis_sekarang = response.text
                    except Exception as e:
                        st.error(f"Gagal buat kuis: {e}")

            # Menampilkan Kuis
            if st.session_state.kuis_sekarang:
                st.info("Jawab pertanyaan ini dalam hati, lalu cek kunci jawaban di bawah.")
                st.markdown(st.session_state.kuis_sekarang)
