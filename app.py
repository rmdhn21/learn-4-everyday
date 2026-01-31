import streamlit as st
import google.generativeai as genai
from groq import Groq
import json
import streamlit.components.v1 as components
import re
from gtts import gTTS
import tempfile
import requests
from PIL import Image
from io import BytesIO
import random
import urllib.parse

# --- 1. KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="Guru Saku AI Ultimate",
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
    /* Styling container */
    .stSelectbox, .stTextInput { margin-bottom: 15px; }
</style>
""", unsafe_allow_html=True)

# ==========================================
# 🧠 DUAL ENGINE (GEMINI & GROQ)
# ==========================================
def ask_the_brain(provider, model_name, api_key, prompt):
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=api_key)
            # Pastikan nama model bersih
            model = genai.GenerativeModel(model_name)
            response = model.generate_content(prompt)
            return response.text

        elif provider == "Groq (Super Cepat)":
            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Kamu adalah guru ahli yang ramah."},
                    {"role": "user", "content": prompt},
                ],
                model=model_name,
                temperature=0.7,
            )
            return chat_completion.choices[0].message.content
    except Exception as e:
        return f"⚠️ ERROR {provider}: {str(e)}"

# ==========================================
# ⚙️ FUNGSI PENDUKUNG
# ==========================================
def render_mermaid(code):
    html_code = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>mermaid.initialize({{startOnLoad:true, theme:'base', securityLevel:'loose'}});</script>
        <style>body{{background:white;}} #diagram{{display:flex;justify-content:center;}}</style>
    </head>
    <body><div class="mermaid" id="diagram">{code}</div></body>
    </html>
    """
    components.html(html_code, height=450, scrolling=True)

def extract_mermaid_code(text):
    match = re.search(r'```mermaid(.*?)```', text, re.DOTALL)
    if match: return match.group(1).strip()
    keywords = ["graph TD", "graph LR", "mindmap", "sequenceDiagram"]
    for key in keywords:
        if key in text:
            return text[text.find(key):].split('```')[0].strip()
    return None

def generate_audio(text):
    try:
        tts = gTTS(text=text, lang='id')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            return fp.name
    except: return None

def generate_image_pollinations(prompt, style_model):
    try:
        encoded_prompt = urllib.parse.quote(prompt)
        seed = random.randint(1, 100000)
        url = f"[https://pollinations.ai/p/](https://pollinations.ai/p/){encoded_prompt}?width=1024&height=768&seed={seed}&model={style_model}&nologo=true"
        response = requests.get(url)
        if response.status_code == 200:
            return Image.open(BytesIO(response.content))
        else: return None
    except: return None

# ==========================================
# 🔒 LOGIN & STATE
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
    st.stop()

# Init State
for k, v in {
    'kurikulum':[], 'materi_sekarang':"", 'quiz_data':None, 
    'mermaid_code':"", 'topik_saat_ini':"", 'audio_path':None,
    'last_image': None
}.items():
    if k not in st.session_state: st.session_state[k] = v

# ==========================================
# 🎛️ SIDEBAR (DUAL ENGINE)
# ==========================================
with st.sidebar:
    st.title("⚡ Pilih Mesin AI")
    provider = st.radio("Otak:", ["Google Gemini", "Groq (Super Cepat)"])
    
    api_key = ""
    model_name = ""

    # --- UPDATE DAFTAR MODEL SESUAI LOG KAMU ---
    if provider == "Google Gemini":
        st.caption("🚀 Menggunakan Model Terbaru (Bleeding Edge)")
        # Saya pilihkan yang paling relevan untuk Chat & Text Generation
        model_name = st.selectbox("Model:", [
            "gemini-2.5-flash",        # Super Cepat & Baru
            "gemini-2.5-pro",          # Paling Pintar
            "gemini-2.0-flash",        # Standar Baru
            "gemini-3-pro-preview",    # Masa Depan (Eksperimental)
            "gemini-flash-latest",     # Selalu update otomatis
            "gemini-pro-latest"
        ])
        
        if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]; st.success("API Key Ready.")
        else: api_key = st.text_input("Gemini Key:", type="password")

    elif provider == "Groq (Super Cepat)":
        model_name = st.selectbox("Model:", ["llama3-70b-8192", "mixtral-8x7b-32768", "llama3-8b-8192"])
        if "GROQ_API_KEY" in st.secrets: api_key = st.secrets["GROQ_API_KEY"]; st.success("API Key Ready.")
        else: api_key = st.text_input("Groq Key:", type="password")

    st.markdown("---")
    st.header("🎛️ Kontrol Belajar")
    with st.container(border=True):
        topik_input = st.text_input("Topik:", placeholder="Cth: Teknologi Nano")
        gaya_belajar = st.selectbox("Gaya:", ["👶 Pemula", "💡 Visual", "🏫 Akademis", "🚀 Praktis"])
        
        with st.expander("ℹ️ Bedanya apa?", expanded=False):
            st.markdown("""
            **👶 Pemula (ELI5):** Penjelasan super simpel.
            **💡 Visual (Analogi):** Banyak perumpamaan.
            **🏫 Akademis (Kuliah):** Formal & Teoritis.
            **🚀 Praktis (To-the-point):** Langsung penerapan.
            """)

        if st.button("Buat Kurikulum"):
            if not api_key: st.error("Isi API Key!")
            elif topik_input:
                st.session_state.topik_saat_ini = topik_input
                with st.spinner(f"Menyusun kurikulum dengan {model_name}..."):
                    p = f"Buat 5 Judul Bab belajar '{topik_input}'. Hanya list bab."
                    res = ask_the_brain(provider, model_name, api_key, p)
                    if "ERROR" in res: st.error(res)
                    else:
                        st.session_state.kurikulum = [l.strip().lstrip('1234567890.-* ') for l in res.split('\n') if l.strip()][:5]
                        st.session_state.materi_sekarang = ""; st.session_state.mermaid_code = ""; st.session_state.quiz_data = None; st.session_state.last_image = None
                        st.toast("Siap!")

    if st.session_state.kurikulum:
        st.markdown("---"); st.subheader("📚 Daftar Isi")
        pilihan_bab = st.radio("Bab:", st.session_state.kurikulum, label_visibility="collapsed")
    else: pilihan_bab = None

# ==========================================
# 🖥️ AREA UTAMA
# ==========================================
if not st.session_state.kurikulum:
    st.title("🎓 Guru Saku Ultimate (v18)")
    st.info("Pilih Topik di kiri. Support Gemini 2.5 & 3.0 Preview!")

# TABS
tab_belajar, tab_video, tab_gambar, tab_kuis = st.tabs(["📚 Materi & Diagram", "🎬 Video AI", "🎨 Ilustrasi AI", "📝 Kuis"])

# === TAB 1: MATERI ===
with tab_belajar:
    if st.session_state.kurikulum and pilihan_bab:
        st.header(f"🎓 {st.session_state.topik_saat_ini}")
        st.caption(f"Bab: {pilihan_bab} | Guru: {model_name}")
        
        if st.button("✨ Buka Materi"):
            if not api_key: st.error("API Key kosong.")
            else:
                with st.spinner("Menulis & Menggambar Diagram..."):
                    p = f"""
                    Jelaskan '{pilihan_bab}' ({gaya_belajar}).
                    WAJIB: Buat Diagram Mermaid JS (graph TD/mindmap).
                    Kode diagram dalam blok ```mermaid ... ```.
                    """
                    full = ask_the_brain(provider, model_name, api_key, p)
                    if "ERROR" in full: st.error(full)
                    else:
                        mm = extract_mermaid_code(full)
                        if mm:
                            st.session_state.mermaid_code = mm
                            st.session_state.materi_sekarang = full.replace(f"```mermaid\n{mm}\n```", "").replace(mm, "").strip()
                        else: st.session_state.mermaid_code = ""; st.session_state.materi_sekarang = full
                        st.session_state.quiz_data = None; st.session_state.audio_path = None
        
        if st.session_state.materi_sekarang:
            if st.session_state.mermaid_code:
                st.markdown("### 🧩 Peta Konsep"); render_mermaid(st.session_state.mermaid_code)
            st.markdown("---"); st.markdown(st.session_state.materi_sekarang)

# === TAB 2: VIDEO ===
with tab_video:
    st.header("🎬 Studio Video")
    if st.session_state.materi_sekarang:
        if st.button("🎙️ Buat Suara Guru"):
            aud = generate_audio(st.session_state.materi_sekarang[:1000])
            if aud: st.session_state.audio_path = aud; st.success("Selesai!")
        
        if st.session_state.audio_path:
            c1, c2 = st.columns(2)
            with c1: st.info("🔊 Dengar"); st.audio(st.session_state.audio_path)
            with c2: 
                st.info("🖼️ Lihat")
                if st.session_state.mermaid_code: render_mermaid(st.session_state.mermaid_code)
    else: st.warning("Buka materi di Tab 1 dulu.")

# === TAB 3: GAMBAR ===
with tab_gambar:
    st.header("🎨 Ilustrasi AI (Gratis)")
    st.write("Buat gambar pendukung belajar secara instan.")
    
    col_input, col_style = st.columns([3, 1])
    with col_input:
        default_prompt = f"Illustration of {pilihan_bab} in {st.session_state.topik_saat_ini}, educational style, detailed, 8k" if pilihan_bab else "A cute robot teacher"
        prompt_gambar = st.text_input("Prompt Gambar (Inggris lebih baik):", value=default_prompt)
    with col_style:
        gaya_gambar = st.selectbox("Gaya:", ["flux", "turbo", "midjourney", "anime", "3d-model"])

    if st.button("🖌️ Lukis Sekarang"):
        with st.spinner("Sedang melukis..."):
            img = generate_image_pollinations(prompt_gambar, gaya_gambar)
            if img:
                st.session_state.last_image = img
                st.success("Jadi!")
            else: st.error("Gagal.")

    if st.session_state.last_image:
        st.image(st.session_state.last_image, caption="Hasil Generasi AI", use_container_width=True)
        buf = BytesIO()
        st.session_state.last_image.save(buf, format="PNG")
        st.download_button("⬇️ Download Gambar", data=buf.getvalue(), file_name="guru_saku_img.png", mime="image/png")

# === TAB 4: KUIS ===
with tab_kuis:
    st.header("📝 Kuis")
    if st.button("🎲 Buat Kuis"):
        if not api_key: st.error("API Key?")
        elif pilihan_bab:
            with st.spinner("Bikin soal..."):
                p = f"5 Soal Pilgan '{pilihan_bab}'. JSON murni: [{{'question':'..','options':['A'],'answer':'A','explanation':'..'}}] no markdown."
                res = ask_the_brain(provider, model_name, api_key, p)
                try:
                    clean = res.replace("```json","").replace("```","").strip()
                    if '[' in clean and ']' in clean:
                        clean = clean[clean.find('['):clean.rfind(']')+1]
                        st.session_state.quiz_data = json.loads(clean)
                except: st.error("Gagal format JSON.")

    if st.session_state.quiz_data:
        with st.form("quiz"):
            ans = {}
            for i, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**{i+1}. {q['question']}**"); ans[i] = st.radio("Jwb:", q['options'], key=f"q{i}", label_visibility="collapsed")
            if st.form_submit_button("Cek"):
                sc=0
                for i,q in enumerate(st.session_state.quiz_data):
                    if ans[i]==q['answer']: sc+=1; st.success(f"No {i+1}: Benar!")
                    else: st.error(f"No {i+1}: Salah. ({q['answer']})")
                st.metric("Skor", f"{sc/len(st.session_state.quiz_data)*100:.0f}")
