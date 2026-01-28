import streamlit as st
import google.generativeai as genai

st.title("🔍 Cek Model Gemini")

# Input API Key Manual untuk tes
api_key = st.text_input("Masukkan API Key:", type="password")

if st.button("Cek Model"):
    if api_key:
        genai.configure(api_key=api_key)
        try:
            st.write("Sedang menghubungi Google...")
            # Minta daftar semua model yang tersedia
            for m in genai.list_models():
                if 'generateContent' in m.supported_generation_methods:
                    st.success(f"✅ Model Ditemukan: {m.name}")
        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Masukkan API Key dulu.")
