import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="Guru Saku AI", page_icon="🎓")

st.title("🎓 Guru Saku AI")
st.write("Asisten belajar cerdas: Bisa tanya teks atau tanya dari foto!")

# Cek API Key di Secrets atau Sidebar
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Masukkan Gemini API Key", type="password")

if not api_key:
    st.warning("⚠️ Masukkan API Key dulu agar saya bisa bekerja.")
    st.stop()

genai.configure(api_key=api_key)
model = genai.GenerativeModel('gemini-1.5-flash')

tab1, tab2 = st.tabs(["📝 Tanya Teks", "📸 Tanya Gambar"])

# TAB 1: TEKS
with tab1:
    st.header("Mode Teks")
    pertanyaan = st.text_area("Tulis pertanyaanmu:", placeholder="Contoh: Buatkan jadwal belajar...")

    if st.button("Jawab", key="btn_text"):
        if pertanyaan:
            with st.spinner('Sedang berpikir...'):
                try:
                    response = model.generate_content(pertanyaan)
                    st.success("Selesai!")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Error: {e}")

# TAB 2: GAMBAR
with tab2:
    st.header("Mode Gambar")
    uploaded_file = st.file_uploader("Upload foto", type=["jpg", "png", "jpeg"])

    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Gambar diupload", use_container_width=True)
        prompt_gambar = st.text_input("Pertanyaan tentang gambar:", placeholder="Jelaskan gambar ini")

        if st.button("Analisis", key="btn_img"):
            if prompt_gambar:
                with st.spinner('Menganalisis...'):
                    try:
                        response = model.generate_content([prompt_gambar, image])
                        st.markdown("### Hasil:")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"Error: {e}")
