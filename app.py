import streamlit as st
import google.generativeai as genai
from PIL import Image

# 1. Konfigurasi Halaman
st.set_page_config(page_title="Guru Saku AI", page_icon="⚡")

st.title("⚡ Guru Saku AI (Gemini 2.5 Flash)")
st.write("Tanya apa saja, dijawab secepat kilat!")

# 2. Ambil API Key (Otomatis dari Secrets atau Manual)
if "GOOGLE_API_KEY" in st.secrets:
    api_key = st.secrets["GOOGLE_API_KEY"]
else:
    api_key = st.sidebar.text_input("Masukkan API Key:", type="password")

if not api_key:
    st.warning("⚠️ Masukkan API Key dulu ya.")
    st.stop()

# 3. Konfigurasi Model (SUDAH DIUPDATE KE 2.5)
genai.configure(api_key=api_key)

# Kita pakai model yang TERSEDIA di akunmu: 'gemini-2.5-flash'
try:
    model = genai.GenerativeModel('gemini-2.5-flash')
except Exception as e:
    st.error(f"Error memuat model: {e}")
    st.stop()

# 4. Tampilan Menu (Tabs)
tab1, tab2 = st.tabs(["📝 Tanya Teks", "📸 Tanya Gambar"])

# === TAB 1: TEKS ===
with tab1:
    st.header("Mode Chat Cepat")
    pertanyaan = st.text_area("Apa yang ingin kamu ketahui?", height=100, placeholder="Contoh: Buatkan ide konten TikTok tentang kopi...")
    
    if st.button("Kirim Pertanyaan 🚀", key="btn_text"):
        if pertanyaan:
            with st.spinner('Flash sedang berpikir...'):
                try:
                    response = model.generate_content(pertanyaan)
                    st.success("Selesai!")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")
        else:
            st.warning("Jangan lupa ketik pertanyaannya dulu.")

# === TAB 2: GAMBAR ===
with tab2:
    st.header("Mode Analisis Visual")
    uploaded_file = st.file_uploader("Upload fotomu di sini", type=["jpg", "jpeg", "png", "webp"])
    
    if uploaded_file is not None:
        image = Image.open(uploaded_file)
        st.image(image, caption="Preview Gambar", use_container_width=True)
        
        prompt_gambar = st.text_input("Pertanyaan tentang gambar:", placeholder="Jelaskan apa yang ada di gambar ini")
        
        if st.button("Analisis Gambar 📸", key="btn_img"):
            if prompt_gambar:
                with st.spinner('Sedang melihat gambar...'):
                    try:
                        # Mengirim Gambar + Teks
                        response = model.generate_content([prompt_gambar, image])
                        st.markdown("### 💡 Hasil Analisis:")
                        st.markdown(response.text)
                    except Exception as e:
                        st.error(f"Gagal memproses gambar: {e}")
            else:
                st.warning("Berikan instruksi dulu, misal: 'Jelaskan gambar ini'")

# Footer
st.markdown("---")
st.caption("Powered by Google Gemini 2.5 Flash")
