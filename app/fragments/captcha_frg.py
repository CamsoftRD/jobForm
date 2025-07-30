import streamlit as st
from captcha.image import ImageCaptcha
import random
import string
from io import BytesIO
from app.core.api_jobs import apply_job_offert

    
if not "valid_captcha" in st.session_state:
    st.session_state['valid_captcha'] = False


    

def generate_captcha_text(length=5):
    letters = string.ascii_letters + string.digits
    return ''.join(random.choice(letters) for i in range(length))

def generate_captcha_image(text):
    image = ImageCaptcha()
    data = image.generate(text)
    return data

@st.dialog("Verificación de seguridad", width="large")
def validate_captcha():
    st.title("Verificación de seguridad")
    
    if not "valid_captcha" in st.session_state:
        st.session_state['valid_captcha'] = False
        

    if 'captcha_text' not in st.session_state:
        st.session_state.captcha_text = generate_captcha_text()

    captcha_image_data = generate_captcha_image(st.session_state.captcha_text)

    st.image(captcha_image_data, caption="Por favor, introduce el texto que ves en la imagen")

    user_input = st.text_input("Introduce el texto mostrado")
    #st.write(st.session_state.captcha_text)
    if st.button("Validar"):
        if user_input == st.session_state.captcha_text:
            
            st.session_state['valid_captcha'] = True
            st.session_state.captcha_text = generate_captcha_text()  # renovar captcha
            st.rerun()
  
        else:
            st.session_state['valid_captcha'] = False
            st.error("El texto ingresado no coincide, por favor inténtalo de nuevo.")



