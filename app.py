import streamlit as st
import google.generativeai as genai
from groq import Groq
import json
import streamlit.components.v1 as components
import re
from gtts import gTTS
from io import BytesIO
import urllib.parse
import time
import uuid  # ### PERBAIKAN: Import UUID untuk ID unik widget

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Guru Saku AI Ultimate",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS (Tetap sama, bagus)
st.markdown("""
<style>
    html, body, [class*="css"] { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; }
    .stButton>button {
        border-radius: 12px; font-weight: bold; border: none;
        background-color: #0068C9; color: white; transition: all 0.3s ease;
    }
    .stButton>button:hover { background-color: #004B91; transform: scale(1.02); }
    .stSelectbox, .stTextInput { margin-bottom: 15px; }
    .streamlit-expanderHeader {
        background-color: #f0f8ff; color: #0068C9; font-weight: 700;
        border-radius: 8px; border: 1px solid #cce5ff;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ FUNGSI KRUSIAL (DIPERBAIKI)
# ==========================================

# 1. RENDER MATERI INTERAKTIF
def render_interactive_content(text):
    """
    Memecah teks materi berdasarkan tanda '##' menjadi kotak interaktif.
    """
    # Regex untuk memisahkan Judul (##) dan Isi
    sections = re.split(r'(^##\s+.*)', text, flags=re.MULTILINE)
    
    if sections[0].strip():
        st.markdown(sections[0])
    
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            # ### PERBAIKAN: Membersihkan tanda ## agar judul lebih rapi
            title = sections[i].replace("##", "").strip()
            content = sections[i+1].strip()
            with st.expander(f"📘 {title}", expanded=False):
                st.markdown(content)

# 2. PENCARI JSON (LEBIH ROBUST)
def temukan_json_murni(text):
    try:
        # ### PERBAIKAN: Regex lebih spesifik mencari array JSON [...]
        match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        return None
    except Exception as e:
        st.error(f"Gagal parsing JSON: {e}") # Debugging info
        return None

# 3. AUDIO PLAYER (DENGAN CACHE SEDERHANA)
@st.cache_data(show_spinner=False) # ### PERBAIKAN: Gunakan cache agar tidak generate ulang teks yang sama
def generate_audio_memory(text):
    try:
        mp3_fp = BytesIO()
        # Batasi karakter agar tidak timeout
        tts = gTTS(text=text[:3000], lang='id') 
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp
    except Exception as e:
        return None

# 4. DIAGRAM GRAPHVIZ (PARSING LEBIH KUAT)
def bersihkan_kode_dot(text):
    # ### PERBAIKAN: Menggunakan Regex daripada loop manual yang rawan error
    try:
        # Cari pola digraph G { ... } secara greedy tapi hati-hati
        match = re.search(r'(digraph\s+\w+\s*\{.*?\})', text, re.DOTALL)
        if match:
            return match.group(1)
        return None
    except:
        return None

def render_interactive_graphviz(dot_code):
    try:
        safe_code = urllib.parse.quote(dot_code)
        url = f"https://quickchart.io/graphviz?graph={safe_code}&format=svg"
        
        # HTML & JS untuk Zooming (Tetap dipertahankan karena fitur bagus)
        html_code = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <script src="https://bumbu.me/svg-pan-zoom/dist/svg-pan-zoom.min.js"></script>
            <style>
                body, html {{ margin: 0; padding: 0; height: 100%; overflow: hidden; background: white; }}
                #container {{ width: 100%; height: 100%; border: 1px solid #ddd; border-radius: 8px; }}
                #diagram-svg {{ width: 100%; height: 100%; }}
            </style>
        </head>
        <body>
            <div id="container">
                <object id="diagram-svg" type="image/svg+xml" data="{url}"></object>
            </div>
            <script>
                window.onload = function() {{
                    var svgElement = document.getElementById('diagram-svg');
                    svgElement.addEventListener('load', function() {{
                        // Tambahkan timeout untuk memastikan load sempurna di HP
                        setTimeout(function(){{
                            svgPanZoom(svgElement, {{ zoomEnabled: true, controlIconsEnabled: true, fit: true, center: true, minZoom: 0.5, maxZoom: 10 }});
                        }}, 500);
                    }});
                }};
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=500, scrolling=False)
        st.caption("💡 **Zoom:** Klik tombol (+) dan (-) di pojok kiri atas diagram.")
    except:
        st.graphviz_chart(dot_code)

# 5. OTAK AI
def ask_the_brain(provider, model_name, api_key, prompt):
    if not api_key: return "⚠️ API Key Belum Diisi!" # ### PERBAIKAN: Cek awal
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=api_key)
            # Setting safety agar tidak memblokir materi biologi/anatomi
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
            ]
            generation_config = genai.types.GenerationConfig(temperature=0.3) # Sedikit naikkan temp agar kreatif
            model = genai.GenerativeModel(model_name, safety_settings=safety_settings, generation_config=generation_config)
            response = model.generate_content(prompt)
            return response.text
        elif provider == "Groq (Super Cepat)":
            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": "Kamu adalah Dosen Senior. Jawab dengan Bahasa Indonesia yang akademis namun mudah dimengerti."}, {"role": "user", "content": prompt}],
                model=model_name, 
                temperature=0.3
            )
            return chat_completion.choices[0].message.content
    except Exception as e:
        if "429" in str(e): return "⛔ **KUOTA HABIS**\n\nTunggu sebentar atau ganti API Key."
        return f"⚠️ ERROR {provider}: {str(e)}"

# ==========================================
# 🔒 LOGIN & STATE MANAGEMENT (DIPERBAIKI)
# ==========================================
if 'is_logged_in' not in st.session_state: st.session_state.is_logged_in = False

def check_password():
    kunci = st.secrets.get("RAHASIA_SAYA", "admin123")
    if st.session_state.input_pw == kunci:
        st.session_state.is_logged_in = True
        st.session_state.input_pw = ""
    else: st.error("Password Salah!")

if not st.session_state.is_logged_in:
    st.title("🔒 Login Guru Saku")
    col1, col2 = st.columns([1,2])
    with col2: st.text_input("Password:", type="password", key="input_pw", on_change=check_password)
    st.info("Default password: admin123 (Jika belum diset di secrets)")
    st.stop()

# Inisialisasi State Lengkap
state_keys = {
    'kurikulum': [], 
    'materi_sekarang': "", 
    'quiz_data': None, 
    'quiz_id': str(uuid.uuid4()), # ### PERBAIKAN: ID unik untuk kuis
    'diagram_code': "", 
    'topik_saat_ini': "", 
    'audio_data': None, 
    'chat_history': []
}

for k, v in state_keys.items():
    if k not in st.session_state: st.session_state[k] = v

# ==========================================
# 🎛️ SIDEBAR
# ==========================================
with st.sidebar:
    st.title("⚡ Pilih Mesin AI")
    provider = st.radio("Otak:", ["Google Gemini", "Groq (Super Cepat)"])
    api_key = ""; model_name = ""
    
    if provider == "Google Gemini":
        model_name = st.selectbox("Versi:", ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]) # Update model names
        if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]; st.caption("✅ API Key Ready (Secrets)")
        else: api_key = st.text_input("Gemini Key:", type="password")
    elif provider == "Groq (Super Cepat)":
        model_name = st.selectbox("Versi:", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"])
        if "GROQ_API_KEY" in st.secrets: api_key = st.secrets["GROQ_API_KEY"]; st.caption("✅ API Key Ready (Secrets)")
        else: api_key = st.text_input("Groq Key:", type="password")

    st.markdown("---"); st.header("🎛️ Kontrol Belajar")
    with st.container(border=True):
        topik_input = st.text_input("Topik:", placeholder="Cth: Geologi, Sejarah RI")
        gaya_belajar = st.selectbox("Gaya:", ["👶 Pemula", "💡 Visual", "🏫 Akademis (Kuliah)", "🚀 Praktis (Kerja)"])
        
        if st.button("Buat Kurikulum", type="primary"):
            if not api_key: st.error("Isi API Key!")
            elif topik_input:
                st.session_state.topik_saat_ini = topik_input
                with st.spinner(f"Menyusun kurikulum..."):
                    p = f"Buat 5 Judul Bab belajar '{topik_input}' untuk level {gaya_belajar}. Hanya list bab bernomor. Jangan ada bold/markdown aneh."
                    res = ask_the_brain(provider, model_name, api_key, p)
                    if "⛔" in res or "⚠️" in res: st.error(res) 
                    else:
                        # Membersihkan list agar rapi
                        raw_list = res.split('\n')
                        clean_list = [l.strip().lstrip('1234567890.-*# ') for l in raw_list if l.strip()]
                        st.session_state.kurikulum = clean_list[:5]
                        
                        # Reset State saat ganti topik
                        st.session_state.materi_sekarang = ""
                        st.session_state.diagram_code = ""
                        st.session_state.quiz_data = None
                        st.session_state.audio_data = None
                        st.session_state.chat_history = [] 
                        st.rerun() # ### PERBAIKAN: Rerun agar UI refresh otomatis

    if st.session_state.kurikulum:
        st.markdown("---"); st.subheader("📚 Daftar Isi")
        pilihan_bab = st.radio("Bab:", st.session_state.kurikulum, label_visibility="collapsed")
    else: pilihan_bab = None

# ==========================================
# 🖥️ AREA UTAMA
# ==========================================
if not st.session_state.kurikulum:
    st.title("🎓 Guru Saku Ultimate (v47 Stable)")
    st.info("👋 Selamat datang! Masukkan topik di sidebar kiri untuk mulai belajar.")
    st.stop() # Hentikan eksekusi di bawah jika belum ada kurikulum

tab_belajar, tab_video, tab_kuis, tab_chat = st.tabs(["📚 Materi (Deep)", "🎬 Audio Guru", "📝 Kuis (15 Soal)", "💬 Tanya Guru"])

# === TAB 1: MATERI ===
with tab_belajar:
    if st.session_state.kurikulum and pilihan_bab:
        st.header(f"🎓 {st.session_state.topik_saat_ini}")
        st.caption(f"Bab: {pilihan_bab} | Guru: {model_name}")
        
        if st.button("✨ Buka Materi Lengkap", type="primary"):
            if not api_key: st.error("API Key kosong.")
            else:
                with st.spinner("Menulis materi & Menggambar diagram..."):
                    p = f"""
                    Saya belajar '{st.session_state.topik_saat_ini}', Bab '{pilihan_bab}'.
                    Gaya: {gaya_belajar}.
                    
                    INSTRUKSI 1 (MATERI): 
                    - Jelaskan secara MENDALAM (Min 800 kata).
                    - **WAJIB:** Gunakan Heading 2 Markdown (##) untuk setiap Sub-Bab.
                    - Struktur: ## Konsep Dasar -> ## Mekanisme -> ## Contoh Kasus -> ## Kesimpulan.
                    
                    INSTRUKSI 2 (DIAGRAM): 
                    - Buat Graphviz DOT `digraph G {{...}}` di bagian paling bawah. 
                    - Node style fillcolor="lightblue", style="filled", shape="box", fontname="Arial".
                    """
                    full = ask_the_brain(provider, model_name, api_key, p)
                    
                    if "⛔" in full or "⚠️" in full: 
                        st.error(full)
                    else:
                        kode_dot = bersihkan_kode_dot(full)
                        if kode_dot: 
                            st.session_state.diagram_code = kode_dot
                            # Hapus kode DOT dari teks materi agar tidak muncul sebagai teks sampah
                            st.session_state.materi_sekarang = full.replace(kode_dot, "").strip()
                        else: 
                            st.session_state.diagram_code = ""
                            st.session_state.materi_sekarang = full
                            
                        # Reset data terkait materi lama
                        st.session_state.quiz_data = None
                        st.session_state.audio_data = None
                        st.session_state.quiz_id = str(uuid.uuid4()) # Reset ID kuis
        
        # TAMPILKAN DIAGRAM DI ATAS (Agar visual dulu baru teks)
        if st.session_state.diagram_code: 
            st.markdown("### 🧩 Peta Konsep")
            render_interactive_graphviz(st.session_state.diagram_code)
        
        # TAMPILKAN MATERI
        if st.session_state.materi_sekarang: 
            st.markdown("---")
            render_interactive_content(st.session_state.materi_sekarang)

# === TAB 2: AUDIO ===
with tab_video:
    st.header("🎬 Audio Guru")
    if st.session_state.materi_sekarang:
        if st.button("🎙️ Generate Suara"):
            with st.spinner("Mengubah teks ke suara (Mungkin butuh 10-20 detik)..."):
                clean_text = st.session_state.materi_sekarang.replace("#", "").replace("*", "")
                # ### PERBAIKAN: Ambil max 4000 char untuk menghindari error gTTS
                audio_buffer = generate_audio_memory(clean_text[:4000])
                
                if audio_buffer: 
                    st.session_state.audio_data = audio_buffer
                    st.success("Suara berhasil dibuat!")
                else: 
                    st.error("Gagal membuat audio. Coba lagi.")
        
        if st.session_state.audio_data:
            st.audio(st.session_state.audio_data, format="audio/mpeg")
            st.info("Tips: Audio ini dihasilkan dari ringkasan materi.")
    else:
        st.warning("Silakan generate materi di Tab Materi terlebih dahulu.")

# === TAB 3: KUIS ===
with tab_kuis:
    st.header("📝 Kuis Pemahaman")
    
    col_k1, col_k2 = st.columns([1,3])
    with col_k1:
        if st.button("🎲 Buat Kuis Baru"):
            if not api_key: st.error("API Key?")
            elif not st.session_state.materi_sekarang: st.error("Buat materi dulu!")
            else:
                with st.spinner("Menyusun soal..."):
                    p = f"""
                    Dari materi ini: '{st.session_state.materi_sekarang[:2000]}...'
                    Buat 5 Soal Pilihan Ganda.
                    Output WAJIB JSON Array murni: 
                    [
                        {{"question":"Pertanyaan?","options":["A. ..","B. ..", "C. ..", "D. .."],"answer":"A","explanation":"Penjelasan singkat"}}
                    ]
                    Tanpa markdown ```json ```. Hanya raw text.
                    """
                    res = ask_the_brain(provider, model_name, api_key, p)
                    data_kuis = temukan_json_murni(res)
                    
                    if data_kuis: 
                        st.session_state.quiz_data = data_kuis
                        st.session_state.quiz_id = str(uuid.uuid4()) # ### PERBAIKAN: Ganti ID agar widget fresh
                    else: 
                        st.error("Gagal membuat soal. AI memberikan format salah.")

    if st.session_state.quiz_data:
        with st.form(key=f"form_quiz_{st.session_state.quiz_id}"): # ### PERBAIKAN: Key unik form
            ans = {}
            for i, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**{i+1}. {q['question']}**")
                # ### PERBAIKAN: Key widget unik kombinasi ID kuis + nomor soal
                ans[i] = st.radio("Jawaban:", q['options'], key=f"{st.session_state.quiz_id}_q{i}", label_visibility="collapsed")
                st.markdown("---")
            
            submit = st.form_submit_button("Cek Nilai")
            
            if submit:
                sc = 0
                for i, q in enumerate(st.session_state.quiz_data):
                    # Ambil huruf depan jawaban user (A/B/C/D)
                    user_ans_letter = ans[i].split(".")[0].strip() if ans[i] else ""
                    correct_ans = q['answer'].strip()
                    
                    if user_ans_letter == correct_ans: 
                        sc += 1
                        st.success(f"No {i+1}: Benar! ({ans[i]})")
                    else: 
                        st.error(f"No {i+1}: Salah. Jawaban yang benar: {correct_ans}")
                        st.caption(f"💡 Penjelasan: {q['explanation']}")
                
                final_score = (sc/len(st.session_state.quiz_data))*100
                st.metric("SKOR AKHIR", f"{final_score:.0f}")
                if final_score > 80: st.balloons()

# === TAB 4: CHAT ===
with tab_chat:
    st.header("💬 Asisten Dosen")
    
    # Render History Dulu
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["message"])
        
    if q := st.chat_input("Tanya sesuatu tentang materi ini..."):
        # 1. Tampilkan pertanyaan user
        st.session_state.chat_history.append({"role":"user", "message":q})
        with st.chat_message("user"): st.markdown(q)
        
        # 2. Proses Jawaban
        with st.chat_message("assistant"):
            with st.spinner("Berpikir..."):
                context = st.session_state.materi_sekarang[:4000] if st.session_state.materi_sekarang else "Belum ada materi spesifik."
                prompt_chat = f"Konteks Materi: {context}\n\nPertanyaan Siswa: {q}\nJawablah dengan ramah dan membantu."
                
                ans = ask_the_brain(provider, model_name, api_key, prompt_chat)
                st.markdown(ans)
        
        # 3. Simpan ke history
        st.session_state.chat_history.append({"role":"assistant", "message":ans})
