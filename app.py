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
    
    /* Styling Header Expander */
    .streamlit-expanderHeader {
        background-color: #f0f2f6;
        color: #0068C9;
        font-weight: bold;
        border-radius: 8px;
    }
    
    /* Chat Bubble Style */
    .chat-user {
        background-color: #e6f3ff;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: right;
    }
    .chat-ai {
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 10px;
        margin-bottom: 10px;
        text-align: left;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ FUNGSI PENDUKUNG
# ==========================================
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
                        svgPanZoom(svgElement, {{ zoomEnabled: true, controlIconsEnabled: true, fit: true, center: true, minZoom: 0.5, maxZoom: 10 }});
                    }});
                }};
            </script>
        </body>
        </html>
        """
        components.html(html_code, height=500, scrolling=False)
        st.caption("💡 **Tips:** Gunakan tombol **(+)** dan **(-)** di pojok diagram untuk Zoom.")
    except:
        st.graphviz_chart(dot_code)

def bersihkan_kode_dot(text):
    start_index = text.find("digraph")
    if start_index == -1: return None 
    balance = 0
    found_first_brace = False
    end_index = -1
    for i in range(start_index, len(text)):
        char = text[i]
        if char == '{': balance += 1; found_first_brace = True
        elif char == '}': balance -= 1
        if found_first_brace and balance == 0: end_index = i + 1; break
    return text[start_index:end_index] if end_index != -1 else None

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
                messages=[{"role": "system", "content": "Kamu adalah guru ahli."}, {"role": "user", "content": prompt}],
                model=model_name, temperature=0.7
            )
            return chat_completion.choices[0].message.content
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg: return "⛔ **KUOTA HABIS**\n\nTunggu 1 menit atau pakai **Groq**."
        return f"⚠️ ERROR {provider}: {error_msg}"

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

def render_interactive_content(text):
    sections = re.split(r'(^##\s+.*)', text, flags=re.MULTILINE)
    if sections[0].strip(): st.markdown(sections[0])
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            title = sections[i].replace("##", "").strip()
            content = sections[i+1].strip()
            with st.expander(f"👉 {title}"): st.markdown(content)

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

# Init State (Tambah chat_history)
for k, v in {
    'kurikulum':[], 'materi_sekarang':"", 'quiz_data':None, 'diagram_code':"", 
    'topik_saat_ini':"", 'audio_path':None, 'current_image_url': None,
    'chat_history': [] # 💬 History Chat Baru
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
        model_name = st.selectbox("Versi:", ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-2.0-flash"])
        if "GOOGLE_API_KEY" in st.secrets: api_key = st.secrets["GOOGLE_API_KEY"]; st.caption("✅ API Key Ready")
        else: api_key = st.text_input("Gemini Key:", type="password")

    elif provider == "Groq (Super Cepat)":
        st.caption("Model Llama 3:")
        model_name = st.selectbox("Versi:", ["llama-3.3-70b-versatile", "llama-3.1-8b-instant", "mixtral-8x7b-32768"])
        if "GROQ_API_KEY" in st.secrets: api_key = st.secrets["GROQ_API_KEY"]; st.caption("✅ API Key Ready")
        else: api_key = st.text_input("Groq Key:", type="password")

    st.markdown("---")
    st.header("🎛️ Kontrol Belajar")
    with st.container(border=True):
        topik_input = st.text_input("Topik:", placeholder="Cth: Dinosaurus")
        gaya_belajar = st.selectbox("Gaya:", ["👶 Pemula", "💡 Visual", "🏫 Akademis", "🚀 Praktis"])
        
        if st.button("Buat Kurikulum"):
            if not api_key: st.error("Isi API Key!")
            elif topik_input:
                st.session_state.topik_saat_ini = topik_input
                with st.spinner(f"Menyusun kurikulum..."):
                    p = f"Buat 5 Judul Bab belajar '{topik_input}'. Hanya list bab."
                    res = ask_the_brain(provider, model_name, api_key, p)
                    if "⛔" in res or "⚠️" in res: st.error(res) 
                    else:
                        st.session_state.kurikulum = [l.strip().lstrip('1234567890.-* ') for l in res.split('\n') if l.strip()][:5]
                        st.session_state.materi_sekarang = ""; st.session_state.diagram_code = ""; st.session_state.quiz_data = None; st.session_state.current_image_url = None
                        st.session_state.chat_history = [] # Reset chat kalau ganti topik
                        st.toast("Siap!")

    if st.session_state.kurikulum:
        st.markdown("---"); st.subheader("📚 Daftar Isi")
        pilihan_bab = st.radio("Bab:", st.session_state.kurikulum, label_visibility="collapsed")
    else: pilihan_bab = None

# ==========================================
# 🖥️ AREA UTAMA
# ==========================================
if not st.session_state.kurikulum:
    st.title("🎓 Guru Saku Ultimate (v40)")
    st.info("Fitur Baru: Chatbot Guru! Bisa tanya jawab langsung.")

# --- 5 TAB OUTPUT (TAB 5 BARU) ---
tab_belajar, tab_video, tab_gambar, tab_kuis, tab_chat = st.tabs(["📚 Materi", "🎬 Video", "🎨 Ilustrasi", "📝 Kuis", "💬 Tanya Guru"])

# === TAB 1: MATERI ===
with tab_belajar:
    if st.session_state.kurikulum and pilihan_bab:
        st.header(f"🎓 {st.session_state.topik_saat_ini}")
        st.caption(f"Bab: {pilihan_bab} | Guru: {model_name}")
        
        if st.button("✨ Buka Materi"):
            if not api_key: st.error("API Key kosong.")
            else:
                with st.spinner("Menulis materi & Menggambar Diagram..."):
                    p = f"""
                    Saya belajar '{st.session_state.topik_saat_ini}', Bab '{pilihan_bab}'.
                    Gaya: {gaya_belajar}.
                    TUGAS 1: Jelaskan materi. WAJIB: Gunakan Heading 2 (##) untuk Sub-Bab.
                    TUGAS 2: Buat DIAGRAM Graphviz DOT. Gunakan `digraph G {{ ... }}`. Rankdir TD.
                    """
                    full = ask_the_brain(provider, model_name, api_key, p)
                    if "⛔" in full or "⚠️" in full: st.error(full)
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
        
        if st.session_state.diagram_code:
            st.markdown("### 🧩 Peta Konsep"); render_interactive_graphviz(st.session_state.diagram_code)
        if st.session_state.materi_sekarang:
            st.markdown("---"); render_interactive_content(st.session_state.materi_sekarang)
        if st.session_state.diagram_code:
            st.markdown("---"); 
            with st.expander("🔄 Ringkasan Visual"): render_interactive_graphviz(st.session_state.diagram_code)

# === TAB 2: VIDEO ===
with tab_video:
    st.header("🎬 Studio Video")
    if st.session_state.materi_sekarang:
        if st.button("🎙️ Buat Suara Guru"):
            clean_text = st.session_state.materi_sekarang.replace("#", "").replace("*", "")
            aud = generate_audio(clean_text[:1000])
            if aud: st.session_state.audio_path = aud; st.success("Selesai!")
        if st.session_state.audio_path:
            c1, c2 = st.columns(2)
            with c1: st.info("🔊 Dengar"); st.audio(st.session_state.audio_path)
            with c2: st.info("🖼️ Lihat Diagram"); 
            if st.session_state.diagram_code: render_interactive_graphviz(st.session_state.diagram_code)
    else: st.warning("Buka materi di Tab 1 dulu.")

# === TAB 3: GAMBAR ===
with tab_gambar:
    st.header("🎨 Ilustrasi AI")
    col_input, col_style = st.columns([3, 1])
    with col_input:
        default_prompt = f"Illustration of {pilihan_bab} in {st.session_state.topik_saat_ini}, educational style, detailed, 8k" if pilihan_bab else "A cute robot teacher"
        prompt_gambar = st.text_input("Prompt Gambar:", value=default_prompt)
    with col_style:
        gaya_gambar = st.selectbox("Gaya:", ["flux", "turbo", "midjourney", "anime", "3d-model"])
    if st.button("🖌️ Lukis"):
        url_gambar = get_clean_image_url(prompt_gambar, gaya_gambar)
        st.session_state.current_image_url = url_gambar; st.success("Memuat...")
    if st.session_state.current_image_url:
        st.markdown(f'<div style="text-align: center;"><img src="{st.session_state.current_image_url}" style="max-width: 100%; border-radius: 10px;"><br><br><a href="{st.session_state.current_image_url}" target="_blank"><button style="background-color:#4CAF50; color:white; padding:10px 20px; border:none; border-radius:5px; cursor:pointer;">⬇️ Buka Penuh</button></a></div>', unsafe_allow_html=True)

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

# === TAB 5: CHATBOT GURU (FITUR BARU) ===
with tab_chat:
    st.header("💬 Tanya Guru")
    st.caption("Diskusikan materi ini lebih dalam dengan AI.")
    
    # Tampilkan History Chat
    for chat in st.session_state.chat_history:
        role_class = "chat-user" if chat["role"] == "user" else "chat-ai"
        align = "right" if chat["role"] == "user" else "left"
        st.markdown(f'<div style="text-align: {align};"><span class="{role_class}">{chat["message"]}</span></div>', unsafe_allow_html=True)
        st.write("") # Spacer

    # Input User
    user_question = st.chat_input("Tanya sesuatu tentang bab ini...")
    
    if user_question:
        # 1. Tambah pertanyaan user ke history
        st.session_state.chat_history.append({"role": "user", "message": user_question})
        
        # 2. Kirim ke AI (Sertakan konteks materi)
        context_prompt = f"""
        Konteks Materi: {st.session_state.materi_sekarang[:2000]}... (dan seterusnya).
        Pertanyaan Siswa: {user_question}
        
        Jawablah sebagai guru yang ramah dan membantu. Pendek dan jelas saja.
        """
        
        with st.spinner("Guru sedang mengetik..."):
            answer = ask_the_brain(provider, model_name, api_key, context_prompt)
        
        # 3. Tambah jawaban AI ke history
        st.session_state.chat_history.append({"role": "ai", "message": answer})
        
        # 4. Rerun agar chat muncul
        st.rerun()
