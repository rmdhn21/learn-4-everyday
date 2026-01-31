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
    .streamlit-expanderHeader {
        background-color: #f0f2f6;
        color: #004B91;
        font-weight: 700;
        border-radius: 8px;
        border: 1px solid #e0e0e0;
    }
</style>
""", unsafe_allow_html=True)

# ==========================================
# ⚙️ FUNGSI PENDUKUNG (FIXED)
# ==========================================

# 1. VACUUM CLEANER JSON (BARU & CANGGIH) 🧹
def temukan_json_murni(text):
    """
    Mencari array JSON [...] di dalam teks sampah apapun menggunakan Regex.
    """
    try:
        # Cari pola [ ... ] yang isinya bisa apa saja (DOTALL)
        match = re.search(r'\[.*\]', text, re.DOTALL)
        if match:
            json_str = match.group(0)
            return json.loads(json_str)
        else:
            return None
    except:
        return None

# 2. AUDIO MEMORY FIX (UNTUK HP) 📱
def generate_audio_memory(text):
    try:
        mp3_fp = BytesIO()
        tts = gTTS(text=text, lang='id')
        tts.write_to_fp(mp3_fp)
        # PENTING: Kembalikan pointer ke awal file agar bisa dibaca browser HP
        mp3_fp.seek(0) 
        return mp3_fp
    except Exception as e:
        return None

# 3. VISUALISASI GRAPHVIZ
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
        st.caption("💡 **Zoom:** Klik tombol (+) dan (-) di pojok kiri atas diagram.")
    except:
        st.error("Gagal render diagram interaktif. Menampilkan statis.")
        st.graphviz_chart(dot_code)

def bersihkan_kode_dot(text):
    start_index = text.find("digraph")
    if start_index == -1: return None 
    balance = 0; found_first_brace = False; end_index = -1
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
            safety_settings = [{"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"}, {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}]
            time.sleep(1)
            # Temperature 0.1 = SANGAT KONSISTEN
            generation_config = genai.types.GenerationConfig(temperature=0.1, top_p=0.95, top_k=40)
            model = genai.GenerativeModel(model_name, safety_settings=safety_settings, generation_config=generation_config)
            response = model.generate_content(prompt)
            return response.text
        elif provider == "Groq (Super Cepat)":
            client = Groq(api_key=api_key)
            chat_completion = client.chat.completions.create(
                messages=[{"role": "system", "content": "Kamu adalah Sistem Akademik Baku."}, {"role": "user", "content": prompt}],
                model=model_name, 
                temperature=0.1 # Konsisten
            )
            return chat_completion.choices[0].message.content
    except Exception as e:
        if "429" in str(e): return "⛔ **KUOTA HABIS**\n\nTunggu 1 menit atau pakai **Groq**."
        return f"⚠️ ERROR {provider}: {str(e)}"

def render_interactive_content(text):
    sections = re.split(r'(^##\s+.*)', text, flags=re.MULTILINE)
    if sections[0].strip(): st.markdown(sections[0])
    for i in range(1, len(sections), 2):
        if i + 1 < len(sections):
            title = sections[i].replace("##", "").strip()
            content = sections[i+1].strip()
            with st.expander(f"📘 {title}"): st.markdown(content)

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

for k, v in {'kurikulum':[], 'materi_sekarang':"", 'quiz_data':None, 'diagram_code':"", 'topik_saat_ini':"", 'audio_data':None, 'chat_history': []}.items():
    if k not in st.session_state: st.session_state[k] = v

# ==========================================
# 🎛️ SIDEBAR
# ==========================================
with st.sidebar:
    st.title("⚡ Pilih Mesin AI")
    provider = st.radio("Otak:", ["Google Gemini", "Groq (Super Cepat)"])
    api_key = ""; model_name = ""
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

    st.markdown("---"); st.header("🎛️ Kontrol Belajar")
    with st.container(border=True):
        topik_input = st.text_input("Topik:", placeholder="Cth: Geologi")
        gaya_belajar = st.selectbox("Gaya:", ["👶 Pemula", "💡 Visual", "🏫 Akademis (Kuliah)", "🚀 Praktis (Kerja)"])
        if st.button("Buat Kurikulum"):
            if not api_key: st.error("Isi API Key!")
            elif topik_input:
                st.session_state.topik_saat_ini = topik_input
                with st.spinner(f"Menyusun kurikulum..."):
                    p = f"Buat 5 Judul Bab belajar '{topik_input}'. Hanya list bab. Jangan tambahkan kata pengantar. Format konsisten."
                    res = ask_the_brain(provider, model_name, api_key, p)
                    if "⛔" in res or "⚠️" in res: st.error(res) 
                    else:
                        st.session_state.kurikulum = [l.strip().lstrip('1234567890.-* ') for l in res.split('\n') if l.strip()][:5]
                        st.session_state.materi_sekarang = ""; st.session_state.diagram_code = ""; st.session_state.quiz_data = None; st.session_state.audio_data = None; st.session_state.chat_history = [] 
                        st.toast("Siap!")

    if st.session_state.kurikulum:
        st.markdown("---"); st.subheader("📚 Daftar Isi")
        pilihan_bab = st.radio("Bab:", st.session_state.kurikulum, label_visibility="collapsed")
    else: pilihan_bab = None

# ==========================================
# 🖥️ AREA UTAMA
# ==========================================
if not st.session_state.kurikulum:
    st.title("🎓 Guru Saku Ultimate (v45)")
    st.info("Update Fix: Audio Mobile, JSON Parser, Diagram Konsisten.")

tab_belajar, tab_video, tab_kuis, tab_chat = st.tabs(["📚 Materi (Deep)", "🎬 Audio Guru", "📝 Kuis (15 Soal)", "💬 Tanya Guru"])

# === TAB 1: MATERI ===
with tab_belajar:
    if st.session_state.kurikulum and pilihan_bab:
        st.header(f"🎓 {st.session_state.topik_saat_ini}")
        st.caption(f"Bab: {pilihan_bab} | Guru: {model_name}")
        if st.button("✨ Buka Materi Lengkap"):
            if not api_key: st.error("API Key kosong.")
            else:
                with st.spinner("Menulis materi Panjang & Menggambar Diagram..."):
                    p = f"""
                    Saya belajar '{st.session_state.topik_saat_ini}', Bab '{pilihan_bab}'.
                    Gaya: {gaya_belajar}.
                    
                    INSTRUKSI PENULISAN (JANGAN DIUBAH):
                    1. Jelaskan materi secara MENDALAM, PANJANG, dan AKADEMIS (Minimal 800 kata).
                    2. STRUKTUR WAJIB:
                       - Pendahuluan (Tanpa Heading)
                       - ## Definisi & Konsep Dasar
                       - ## Mekanisme / Proses Utama
                       - ## Studi Kasus / Contoh Penerapan
                       - ## Analisis Kelebihan & Kekurangan
                       - ## Kesimpulan
                    
                    INSTRUKSI DIAGRAM: 
                    Buat Graphviz DOT `digraph G {{...}}` di bagian paling akhir. 
                    - Gunakan hanya huruf dan angka untuk ID Node (contoh: A -> B). 
                    - Label boleh pakai spasi. 
                    - Node style fillcolor="lightblue". Rankdir TD.
                    """
                    full = ask_the_brain(provider, model_name, api_key, p)
                    if "⛔" in full or "⚠️" in full: st.error(full)
                    else:
                        kode_dot = bersihkan_kode_dot(full)
                        if kode_dot: st.session_state.diagram_code = kode_dot; idx = full.find("digraph"); st.session_state.materi_sekarang = full[:idx].strip()
                        else: st.session_state.diagram_code = ""; st.session_state.materi_sekarang = full
                        st.session_state.quiz_data = None; st.session_state.audio_data = None 
        
        if st.session_state.diagram_code: st.markdown("### 🧩 Peta Konsep"); render_interactive_graphviz(st.session_state.diagram_code)
        if st.session_state.materi_sekarang: st.markdown("---"); render_interactive_content(st.session_state.materi_sekarang)
        if st.session_state.diagram_code: st.markdown("---"); 
        with st.expander("🔄 Ringkasan Visual"): render_interactive_graphviz(st.session_state.diagram_code)

# === TAB 2: AUDIO (HP FIX) ===
with tab_video:
    st.header("🎬 Audio Guru")
    st.write("Dengarkan penjelasan materi ini (Text-to-Speech).")
    if st.session_state.materi_sekarang:
        if st.button("🎙️ Generate Suara"):
            with st.spinner("Sedang memproses suara..."):
                clean_text = st.session_state.materi_sekarang.replace("#", "").replace("*", "").replace("- ", "")
                # Limit 1500 karakter biar gak error di HP
                audio_buffer = generate_audio_memory(clean_text[:1500])
                if audio_buffer: st.session_state.audio_data = audio_buffer; st.success("Suara berhasil dibuat!")
                else: st.error("Gagal.")
        if st.session_state.audio_data:
            c1, c2 = st.columns(2)
            with c1: 
                st.info("🔊 Putar Audio")
                # Format MPEG lebih aman buat Android/iOS
                st.audio(st.session_state.audio_data, format="audio/mpeg") 
            with c2: st.info("🖼️ Lihat Diagram"); 
            if st.session_state.diagram_code: render_interactive_graphviz(st.session_state.diagram_code)
    else: st.warning("Buka materi dulu.")

# === TAB 3: KUIS (JSON PARSER FIX) ===
with tab_kuis:
    st.header("📝 Kuis (15 Soal)")
    if st.button("🎲 Buat Kuis"):
        if not api_key: st.error("API Key?")
        elif pilihan_bab:
            with st.spinner("Membuat 15 Soal..."):
                p = f"Buat 15 Soal Pilgan tentang '{pilihan_bab}'. Output JSON Murni: [{{'question':'..','options':['A. ..','B. ..'],'answer':'A','explanation':'..'}}] no markdown."
                res = ask_the_brain(provider, model_name, api_key, p)
                
                # --- PANGGIL VACUUM CLEANER JSON ---
                data_kuis = temukan_json_murni(res)
                
                if data_kuis:
                    st.session_state.quiz_data = data_kuis
                else:
                    st.error("Gagal membaca format soal dari AI. Coba klik 'Buat Kuis' lagi.")
                    st.write(res) # Debugging kalau mau lihat output mentah

    if st.session_state.quiz_data:
        with st.form("quiz"):
            ans = {}
            for i, q in enumerate(st.session_state.quiz_data):
                st.markdown(f"**{i+1}. {q['question']}**"); ans[i] = st.radio("Jwb:", q['options'], key=f"q{i}", label_visibility="collapsed")
            if st.form_submit_button("Cek Nilai"):
                sc = 0
                for i, q in enumerate(st.session_state.quiz_data):
                    user_ans_letter = ans[i].split(".")[0].strip()
                    if user_ans_letter == q['answer']: sc += 1; st.success(f"No {i+1}: Benar! ({ans[i]})")
                    else: st.error(f"No {i+1}: Salah. Jawaban: {q['answer']}"); st.caption(f"💡 {q['explanation']}")
                st.metric("SKOR AKHIR", f"{(sc/len(st.session_state.quiz_data))*100:.0f}")

# === TAB 4: CHAT ===
with tab_chat:
    st.header("💬 Tanya Guru")
    for msg in st.session_state.chat_history:
        with st.chat_message(msg["role"]): st.markdown(msg["message"])
    if q := st.chat_input("Ada pertanyaan?"):
        st.session_state.chat_history.append({"role":"user", "message":q})
        with st.chat_message("user"): st.markdown(q)
        with st.chat_message("assistant"):
            with st.spinner("..."):
                ans = ask_the_brain(provider, model_name, api_key, f"Konteks: {st.session_state.materi_sekarang[:3000]}... Pertanyaan: {q}")
                st.markdown(ans)
        st.session_state.chat_history.append({"role":"ai", "message":ans})
