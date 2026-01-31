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
import uuid

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Guru Saku AI Ultimate",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS (DESAIN MODERN & CLICKABLE) ---
st.markdown("""
<style>
    /* Font Global */
    html, body, [class*="css"] { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
    
    /* Styling Tombol Utama */
    .stButton>button {
        border-radius: 20px; font-weight: 600; border: none;
        background: linear-gradient(90deg, #0068C9 0%, #0082FA 100%);
        color: white; padding: 0.5rem 2rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        transition: all 0.3s ease;
    }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 6px 8px rgba(0,0,0,0.15); }

    /* STYLING MATERI "CLICKABLE" (EXPANDER) */
    .streamlit-expanderHeader {
        background-color: #FFFFFF;
        border: 1px solid #E0E0E0;
        border-radius: 10px;
        color: #333;
        font-weight: 700;
        font-size: 1.1rem;
        padding: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
    }
    
    /* Efek Hover saat mouse diarahkan ke judul materi */
    .streamlit-expanderHeader:hover {
        background-color: #F0F8FF; /* Warna biru muda lembut */
        border-color: #0068C9;
        color: #0068C9;
        padding-left: 1.5rem; /* Efek geser sedikit */
    }
    
    /* Isi Materi */
    .streamlit-expanderContent {
        background-color: #FAFAFA;
        border-radius: 0 0 10px 10px;
        border: 1px solid #E0E0E0;
        border-top: none;
        padding: 1.5rem;
    }
    
    /* Input Fields */
    .stTextInput>div>div>input { border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ FUNGSI UTILITAS (DIPERBAIKI)
# ==========================================

# 1. RENDER MATERI JADI KARTU (CARD STYLE)
def render_interactive_content(text):
    """
    Memecah teks materi menjadi kartu-kartu yang bisa diklik (Accordion).
    """
    # Regex untuk memisahkan Judul (##) dan Isi
    sections = re.split(r'(^##\s+.*)', text, flags=re.MULTILINE)
    
    # --- BAGIAN 1: PENDAHULUAN (INTRO) ---
    intro = sections[0].strip()
    if intro:
        with st.container():
            st.info(f"💡 **Pengantar:**\n\n{intro}")
            st.caption("👇 *Klik topik di bawah untuk membuka detail materi.*")
    
    # --- BAGIAN 2: ISI MATERI (CLICKABLE) ---
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            # Bersihkan judul
            raw_title = sections[i].replace("##", "").strip()
            content = sections[i+1].strip()
            
            # Auto Emoji jika AI lupa memberi icon
            icons = ["📘", "📙", "📗", "📕", "📓", "🧠", "🎯", "⚡", "🔬"]
            selected_icon = icons[(i // 2) % len(icons)]
            
            # Cek apakah judul sudah ada emoji
            if any(ord(char) > 1000 for char in raw_title[:3]): # Cek simpel karakter unicode di awal
                final_title = raw_title
            else:
                final_title = f"{selected_icon} {raw_title}"
            
            # RENDER EXPANDER (Default tertutup agar rapi)
            with st.expander(final_title, expanded=False):
                st.markdown(content)

# 2. PENCARI JSON (REGEX)
def temukan_json_murni(text):
    try:
        # Cari pola array JSON [...]
        match = re.search(r'\[\s*\{.*\}\s*\]', text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return None
    except:
        return None

# 3. AUDIO PLAYER (CACHE & LIMIT)
@st.cache_data(show_spinner=False) 
def generate_audio_memory(text):
    try:
        mp3_fp = BytesIO()
        # Batasi text agar tidak timeout/error
        tts = gTTS(text=text[:3000], lang='id')
        tts.write_to_fp(mp3_fp)
        mp3_fp.seek(0)
        return mp3_fp
    except:
        return None

# 4. PARSING GRAPHVIZ (REGEX)
def bersihkan_kode_dot(text):
    try:
        # Cari digraph G { ... }
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
                        setTimeout(function(){{
                            svgPanZoom(svgElement, {{ zoomEnabled: true, controlIconsEnabled: true, fit: true, center: true, minZoom: 0.5, maxZoom: 10 }});
                        }}, 500);
                    }});
                }};
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=450, scrolling=False)
        st.caption("💡 **Zoom:** Gunakan tombol (+/-) di kiri atas diagram.")
    except:
        st.graphviz_chart(dot_code)

# 5. INTEGRASI AI
def ask_the_brain(provider, model_name, api_key, prompt):
    if not api_key: return "⚠️ API Key Belum Diisi!"
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=api_key)
            generation_config = genai.types.GenerationConfig(temperature=0.3)
            # Safety settings longgar agar materi edukasi biologi/sejarah tidak terblokir
            safety = [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
            model = genai.GenerativeModel(model_name, safety_settings=safety, generation_config=generation_config)
            response = model.generate_content(prompt)
            return response.text
        elif provider == "Groq (Super Cepat)":
            client = Groq(api_key=api_key)
            chat = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Kamu adalah Dosen Senior yang ahli membuat materi terstruktur dan rapi."},
                    {"role": "user", "content": prompt}
                ],
                model=model_name, 
                temperature=0.3
            )
            return chat.choices[0].message.content
    except Exception as e:
        if "429" in str(e): return "⛔ **KUOTA HABIS**\n\nTunggu sebentar atau ganti API Key."
        return f"⚠️ ERROR: {str(e)}"

# ==========================================
# 🔒 STATE & LOGIN
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
    st.info("Password Default: admin123")
    st.stop()

# Inisialisasi State Awal
keys = {
    'kurikulum': [], 
    'materi_sekarang': "", 
    'quiz_data': None, 
    'quiz_id': str(uuid.uuid4()), # ID unik untuk widget kuis
    'diagram_code': "", 
    'topik_saat_ini': "", 
    'audio_data': None, 
    'chat_history': []
}
for k, v in keys.items():
    if k not in st.session_state: st.session_state[k] = v

# ==========================================
# 🎛️ SIDEBAR NAVIGASI
# ==========================================
with st.sidebar:
    st.title("⚡ Guru Saku Setup")
    
    # 1. Pilih AI
    with st.expander("⚙️ Konfigurasi AI", expanded=True):
        provider = st.radio("Provider:", ["Google Gemini", "Groq (Super Cepat)"])
        api_key = ""; model_name = ""
        
        if provider == "Google Gemini":
            model_name = st.selectbox("Model:", ["gemini-2.0-flash", "gemini-1.5-flash"])
            if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]; st.success("API Key Terdeteksi")
            else: api_key = st.text_input("Gemini API Key:", type="password")
        elif provider == "Groq (Super Cepat)":
            model_name = st.selectbox("Model:", ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"])
            if "GROQ_API_KEY" in st.secrets: api_key = st.secrets["GROQ_API_KEY"]; st.success("API Key Terdeteksi")
            else: api_key = st.text_input("Groq API Key:", type="password")

    # 2. Input Belajar
    st.markdown("---")
    st.header("🎯 Target Belajar")
    with st.container(border=True):
        topik_input = st.text_input("Topik:", placeholder="Cth: Fotosintesis, Sejarah Majapahit")
        gaya_belajar = st.selectbox("Gaya:", ["👶 Pemula (Bahasa Simpel)", "🏫 Akademis (Detail)", "🚀 Praktis (To the point)"])
        
        if st.button("Buat Kurikulum", type="primary", use_container_width=True):
            if not api_key: st.error("API Key Kosong!")
            elif topik_input:
                st.session_state.topik_saat_ini = topik_input
                with st.spinner("Merancang kurikulum..."):
                    p = f"Buat 5 Judul Bab belajar '{topik_input}' gaya {gaya_belajar}. Hanya list nomor. Tanpa intro."
                    res = ask_the_brain(provider, model_name, api_key, p)
                    
                    if "⛔" not in res:
                        # Bersihkan list
                        raw = res.split('\n')
                        clean = [l.strip().lstrip('1234567890.-*# ') for l in raw if l.strip()]
                        st.session_state.kurikulum = clean[:5]
                        
                        # Reset
                        st.session_state.materi_sekarang = ""
                        st.session_state.diagram_code = ""
                        st.session_state.quiz_data = None
                        st.session_state.chat_history = []
                        st.rerun()

    if st.session_state.kurikulum:
        st.markdown("---")
        st.subheader("📖 Daftar Bab")
        pilihan_bab = st.radio("Pilih Bab:", st.session_state.kurikulum, label_visibility="collapsed")
    else: pilihan_bab = None

# ==========================================
# 🖥️ AREA UTAMA
# ==========================================
if not st.session_state.kurikulum:
    st.title("🎓 Guru Saku Ultimate")
    st.info("👈 Mulailah dengan mengisi Topik di Sidebar sebelah kiri.")
    st.markdown("""
    **Fitur Baru v48:**
    - ✨ **Materi Card Style:** Tampilan rapi, tidak bikin pusing.
    - 🧩 **Smart Diagram:** Peta konsep otomatis.
    - 📝 **Kuis Anti-Error:** Widget stabil.
    """)
    st.stop()

# TAB NAVIGASI
tab_belajar, tab_video, tab_kuis, tab_chat = st.tabs(["📚 Materi", "🎧 Audio", "📝 Kuis", "💬 Diskusi"])

# === TAB 1: MATERI (CARD STYLE) ===
with tab_belajar:
    if st.session_state.kurikulum and pilihan_bab:
        st.header(f"{st.session_state.topik_saat_ini}")
        st.caption(f"Bab Aktif: {pilihan_bab}")
        
        if st.button("🚀 Mulai Belajar Bab Ini", type="primary"):
            if not api_key: st.error("API Key belum diisi.")
            else:
                with st.spinner("Guru sedang menulis modul interaktif & menggambar diagram..."):
                    # PROMPT KHUSUS FORMATTING
                    p = f"""
                    Saya belajar '{st.session_state.topik_saat_ini}', Bab '{pilihan_bab}'.
                    Gaya: {gaya_belajar}.
                    
                    Tugasmu: Buat MODUL INTERAKTIF.
                    
                    INSTRUKSI FORMATTING (WAJIB):
                    1. Paragraf pertama adalah Intro Singkat (tanpa heading).
                    2. Gunakan '## Judul' untuk memisahkan sub-topik.
                    3. Isi materi gunakan bullet points agar enak dibaca.
                    4. Berikan emoji pada setiap judul '##'.
                    
                    Struktur:
                    [Intro]
                    ## 🎯 Konsep Utama
                    ...
                    ## ⚙️ Mekanisme / Cara Kerja
                    ...
                    ## 💡 Contoh Kasus
                    ...
                    ## 📝 Kesimpulan
                    ...
                    
                    INSTRUKSI DIAGRAM:
                    Di paling bawah, buat kode Graphviz DOT: `digraph G {{...}}`.
                    Style: node [style=filled, fillcolor=lightblue, shape=box, fontname="Arial"];
                    """
                    
                    full_res = ask_the_brain(provider, model_name, api_key, p)
                    
                    if "⛔" in full_res: st.error(full_res)
                    else:
                        # Pisahkan Kode DOT dan Materi Teks
                        dot = bersihkan_kode_dot(full_res)
                        if dot:
                            st.session_state.diagram_code = dot
                            st.session_state.materi_sekarang = full_res.replace(dot, "").strip()
                        else:
                            st.session_state.diagram_code = ""
                            st.session_state.materi_sekarang = full_res
                        
                        # Reset Tab Lain
                        st.session_state.quiz_data = None
                        st.session_state.audio_data = None
                        st.session_state.quiz_id = str(uuid.uuid4()) # Reset ID Kuis
        
        # 1. TAMPILKAN DIAGRAM (Visual First)
        if st.session_state.diagram_code:
            st.markdown("### 🧩 Peta Konsep")
            render_interactive_graphviz(st.session_state.diagram_code)
            st.markdown("---")
        
        # 2. TAMPILKAN MATERI (Accordion Style)
        if st.session_state.materi_sekarang:
            render_interactive_content(st.session_state.materi_sekarang)
        else:
            st.info("Klik tombol 'Mulai Belajar' di atas.")

# === TAB 2: AUDIO ===
with tab_video:
    st.header("🎧 Dengar Penjelasan")
    if st.session_state.materi_sekarang:
        if st.button("🎙️ Generate Suara"):
            with st.spinner("Memproses audio (10-20 detik)..."):
                # Bersihkan markdown agar suara bersih
                clean = st.session_state.materi_sekarang.replace("#", "").replace("*", "")
                st.session_state.audio_data = generate_audio_memory(clean)
        
        if st.session_state.audio_data:
            st.audio(st.session_state.audio_data, format="audio/mpeg")
            st.success("Audio siap diputar!")
    else:
        st.warning("Silakan buka materi di Tab Materi dulu.")

# === TAB 3: KUIS (ANTI ERROR) ===
with tab_kuis:
    st.header("📝 Tes Pemahaman")
    col_q1, col_q2 = st.columns([1,3])
    
    with col_q1:
        if st.button("🎲 Buat Kuis Baru"):
            if not st.session_state.materi_sekarang: st.error("Materi belum ada.")
            else:
                with st.spinner("Membuat soal..."):
                    p = f"""
                    Dari materi ini: {st.session_state.materi_sekarang[:1500]}...
                    Buat 5 Soal Pilihan Ganda.
                    Output WAJIB JSON Array Murni:
                    [{{"question":"...","options":["A. ..","B. .."],"answer":"A","explanation":"..."}}]
                    """
                    res = ask_the_brain(provider, model_name, api_key, p)
                    data = temukan_json_murni(res)
                    
                    if data:
                        st.session_state.quiz_data = data
                        st.session_state.quiz_id = str(uuid.uuid4()) # Ganti ID agar widget refresh
                    else:
                        st.error("Gagal format JSON.")
    
    if st.session_state.quiz_data:
        # Gunakan Form agar halaman tidak reload setiap klik radio
        with st.form(key=f"quiz_form_{st.session_state.quiz_id}"):
            answers = {}
            for i, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**{i+1}. {q['question']}**")
                # KEY UNIK adalah rahasia anti-error
                answers[i] = st.radio("Jawab:", q['options'], key=f"{st.session_state.quiz_id}_q{i}", label_visibility="collapsed")
                st.markdown("---")
            
            if st.form_submit_button("Cek Nilai"):
                score = 0
                for i, q in enumerate(st.session_state.quiz_data):
                    user_ans = answers[i].split(".")[0].strip() if answers[i] else ""
                    if user_ans == q['answer']:
                        score += 1
                        st.success(f"✅ No {i+1} Benar!")
                    else:
                        st.error(f"❌ No {i+1} Salah. Jawaban: {q['answer']}")
                        st.caption(f"💡 {q['explanation']}")
                st.metric("Nilai Akhir", f"{(score/len(st.session_state.quiz_data))*100:.0f}")

# === TAB 4: CHAT ===
with tab_chat:
    st.header("💬 Diskusi Materi")
    
    # Render History
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["message"])
    
    if q := st.chat_input("Bingung bagian mana?"):
        # 1. User
        st.session_state.chat_history.append({"role":"user", "message":q})
        with st.chat_message("user"): st.markdown(q)
        
        # 2. AI
        with st.chat_message("assistant"):
            with st.spinner("Mengetik..."):
                ctx = st.session_state.materi_sekarang[:3000] if st.session_state.materi_sekarang else ""
                full_prompt = f"Konteks: {ctx}\nUser: {q}\nJawab ringkas & membantu."
                ans = ask_the_brain(provider, model_name, api_key, full_prompt)
                st.markdown(ans)
        
        # 3. Save AI
        st.session_state.chat_history.append({"role":"assistant", "message":ans})
