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
import time

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
    .stSelectbox, .stTextInput { margin-bottom: 15px; }
    .graphviz-box {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        background-color: white;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ FUNGSI BEDAH KODE (THE SURGEON)
# ==========================================
def bersihkan_kode_dot(text):
    """
    Mengambil kode digraph G { ... } dari respon AI dengan presisi tinggi.
    """
    start_index = text.find("digraph")
    if start_index == -1:
        return None 

    balance = 0
    found_first_brace = False
    end_index = -1

    for i in range(start_index, len(text)):
        char = text[i]
        if char == '{':
            balance += 1
            found_first_brace = True
        elif char == '}':
            balance -= 1
        
        if found_first_brace and balance == 0:
            end_index = i + 1
            break
    
    if end_index != -1:
        return text[start_index:end_index]
    else:
        return None

# ==========================================
# 🧠 MESIN KECERDASAN (AI BRAIN)
# ==========================================
def ask_the_brain(provider, model_name, api_key, prompt):
    try:
        if provider == "Google Gemini":
            genai.configure(api_key=api_key)
            safety_settings = [
                {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
            ]
            time.sleep(1)
            model = genai.GenerativeModel(model_name, safety_settings=safety_settings)
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
        error_msg = str(e)
        if "404" in error_msg:
            return f"⛔ **MODEL ERROR (404)**\n\nModel `{model_name}` bermasalah. Coba ganti ke `gemini-2.0-flash`."
        elif "429" in error_msg:
            return "⛔ **KUOTA HABIS (Limit 429)**\n\nGoogle Gemini 2.5 membatasi kecepatan. \n👉 **Solusi:** Tunggu 1 menit atau pakai **Groq**."
        else:
            return f"⚠️ ERROR {provider}: {error_msg}"

# ==========================================
# ⚙️ FUNGSI PENDUKUNG LAIN
# ==========================================
def generate_audio(text):
    try:
        tts = gTTS(text=text, lang='id')
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
            tts.save(fp.name)
            return fp.name
    except: return None

def get_clean_image_url(prompt, style_model):
    safe_prompt = re.sub(r'[^a-zA-Z0-9 ]', '', prompt)
    encoded_prompt = urllib.parse.quote(safe_prompt)
    seed = random.randint(1, 999999)
    return f"https://pollinations.ai/p/{encoded_prompt}?width=1024&height=768&seed={seed}&model={style_model}&nologo=true"

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
    'diagram_code':"", 
    'topik_saat_ini':"", 'audio_path':None,
    'current_image_url': None 
}.items():
    if k not in st.session_state: st.session_state[k] = v

# ==========================================
# 🎛️ SIDEBAR
# ==========================================
with st.sidebar:
    st.title("⚡ Pilih Mesin AI")
    provider = st.radio("Otak:", ["Google Gemini", "Groq (Super Cepat)"])
    
    api_key = ""
    model_name = ""

    if provider == "Google Gemini":
        st.caption("Pilihan Model:")
        model_name = st.selectbox("Versi:", [
            "gemini-2.5-flash", 
            "gemini-2.5-pro",
            "gemini-2.0-flash"
        ])
        if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]; st.caption("✅ API Key Ready")
        else: api_key = st.text_input("Gemini Key:", type="password")

    elif provider == "Groq (Super Cepat)":
        st.caption("Model Llama 3:")
        model_name = st.selectbox("Versi:", [
            "llama-3.3-70b-versatile",
            "llama-3.1-8b-instant",
            "mixtral-8x7b-32768"
        ])
        if "GROQ_API_KEY" in st.secrets: api_key = st.secrets["GROQ_API_KEY"]; st.caption("✅ API Key Ready")
        else: api_key = st.text_input("Groq Key:", type="password")

    st.markdown("---")
    st.header("🎛️ Kontrol Belajar")
    with st.container(border=True):
        topik_input = st.text_input("Topik:", placeholder="Cth: Dinosaurus")
        gaya_belajar = st.selectbox("Gaya:", ["👶 Pemula", "💡 Visual", "🏫 Akademis", "🚀 Praktis"])
        
        with st.expander("ℹ️ Penjelasan 4 Gaya Belajar", expanded=False):
            st.markdown("""
            1. **👶 Pemula:** Penjelasan simpel.
            2. **💡 Visual:** Banyak analogi.
            3. **🏫 Akademis:** Formal dan detail.
            4. **🚀 Praktis:** To-the-point.
            """)

        if st.button("Buat Kurikulum"):
            if not api_key: st.error("Isi API Key!")
            elif topik_input:
                st.session_state.topik_saat_ini = topik_input
                with st.spinner(f"Menyusun kurikulum..."):
                    p = f"Buat 5 Judul Bab belajar '{topik_input}'. Hanya list bab."
                    res = ask_the_brain(provider, model_name, api_key, p)
                    
                    if "⛔" in res or "⚠️" in res: 
                        st.error(res) 
                    else:
                        st.session_state.kurikulum = [l.strip().lstrip('1234567890.-* ') for l in res.split('\n') if l.strip()][:5]
                        st.session_state.materi_sekarang = ""; st.session_state.diagram_code = ""; st.session_state.quiz_data = None; st.session_state.current_image_url = None
                        st.toast("Siap!")

    if st.session_state.kurikulum:
        st.markdown("---"); st.subheader("📚 Daftar Isi")
        pilihan_bab = st.radio("Bab:", st.session_state.kurikulum, label_visibility="collapsed")
    else: pilihan_bab = None

# ==========================================
# 🖥️ AREA UTAMA
# ==========================================
if not st.session_state.kurikulum:
    st.title("🎓 Guru Saku Ultimate (v36)")
    st.info("Fitur Diagram Graphviz dikembalikan & muncul di akhir!")

# --- 4 TAB OUTPUT ---
tab_belajar, tab_video, tab_gambar, tab_kuis = st.tabs(["📚 Materi & Diagram", "🎬 Video AI", "🎨 Ilustrasi AI", "📝 Kuis"])

# === TAB 1: MATERI ===
with tab_belajar:
    if st.session_state.kurikulum and pilihan_bab:
        st.header(f"🎓 {st.session_state.topik_saat_ini}")
        st.caption(f"Bab: {pilihan_bab} | Guru: {model_name}")
        
        if st.button("✨ Buka Materi"):
            if not api_key: st.error("API Key kosong.")
            else:
                with st.spinner("Menulis & Menggambar Diagram (Graphviz)..."):
                    p = f"""
                    Saya belajar '{st.session_state.topik_saat_ini}', Bab '{pilihan_bab}'.
                    Gaya: {gaya_belajar}.
                    
                    Tugas 1: Jelaskan materi lengkap (Markdown).
                    
                    Tugas 2: Buat DIAGRAM Peta Konsep (Graphviz DOT).
                    - Gunakan `digraph G {{ ... }}`.
                    - Node style: `node [style="filled", fillcolor="lightblue", shape="box", fontname="Arial"]`.
                    - Rankdir: LR (Kiri ke Kanan).
                    - Pastikan kodenya valid.
                    """
                    full = ask_the_brain(provider, model_name, api_key, p)
                    
                    if "⛔" in full or "⚠️" in full: 
                        st.error(full)
                    else:
                        kode_dot = bersihkan_kode_dot(full)
                        if kode_dot:
                            st.session_state.diagram_code = kode_dot
                            idx = full.find("digraph")
                            st.session_state.materi_sekarang = full[:idx].strip()
                        else:
                            st.session_state.diagram_code = ""
                            st.session_state.materi_sekarang = full
                            
                        st.session_state.quiz_data = None; st.session_state.audio_path = None
        
        # --- POSISI 1: DIAGRAM DI ATAS (PREVIEW) ---
        if st.session_state.diagram_code:
            st.markdown("### 🧩 Peta Konsep (Awal)")
            st.caption("💡 Tips: Hover mouse di atas diagram lalu klik tombol 'Fullscreen' (tanda panah dua arah) yang muncul di pojok kanan atas diagram untuk **Zoom In/Out**.")
            try:
                st.graphviz_chart(st.session_state.diagram_code, use_container_width=True)
            except Exception as e:
                st.error("Gagal merender diagram.")

        # --- MATERI ---
        if st.session_state.materi_sekarang:
            st.markdown("---")
            st.markdown(st.session_state.materi_sekarang)

        # --- POSISI 2: DIAGRAM DI AKHIR (REVIEW) ---
        if st.session_state.diagram_code:
            st.markdown("---")
            st.markdown("### 🔄 Ringkasan Visual (Akhir)")
            try:
                st.graphviz_chart(st.session_state.diagram_code, use_container_width=True)
            except: pass

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
                st.info("🖼️ Lihat Diagram")
                if st.session_state.diagram_code:
                    st.graphviz_chart(st.session_state.diagram_code, use_container_width=True)
    else: st.warning("Buka materi di Tab 1 dulu.")

# === TAB 3: GAMBAR (HTML CLIENT SIDE) ===
with tab_gambar:
    st.header("🎨 Ilustrasi AI (Gratis)")
    
    col_input, col_style = st.columns([3, 1])
    with col_input:
        default_prompt = f"Illustration of {pilihan_bab} in {st.session_state.topik_saat_ini}, educational style, detailed, 8k" if pilihan_bab else "A cute robot teacher"
        prompt_gambar = st.text_input("Prompt Gambar:", value=default_prompt)
    with col_style:
        gaya_gambar = st.selectbox("Gaya:", ["flux", "turbo", "midjourney", "anime", "3d-model"])

    if st.button("🖌️ Lukis Sekarang"):
        url_gambar = get_clean_image_url(prompt_gambar, gaya_gambar)
        st.session_state.current_image_url = url_gambar
        st.success("Memuat gambar...")

    if st.session_state.current_image_url:
        st.markdown(f'''
            <div style="text-align: center;">
                <img src="{st.session_state.current_image_url}" style="max-width: 100%; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <br><br>
                <a href="{st.session_state.current_image_url}" target="_blank">
                    <button style="background-color:#4CAF50; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer;">
                        ⬇️ Buka Penuh / Simpan
                    </button>
                </a>
            </div>
        ''', unsafe_allow_html=True)

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
