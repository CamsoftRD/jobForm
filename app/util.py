import streamlit as st
from datetime import datetime
import pdfplumber
import json
import base64
import re


def leer_pdf(file_obj) -> str:
    texto = ""
    with pdfplumber.open(file_obj) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text() + "\n"
    return texto



def leer_pdf_from_path(path):
    texto = ""
    with pdfplumber.open(path) as pdf:
        for pagina in pdf.pages:
            texto += pagina.extract_text() + "\n"
    return texto



def file_to_base64(file):
    return base64.b64encode(file.read()).decode("utf-8")
   
   
# Función para renderizar los campos dentro de un contenedor
def render_custom_fields_in_container(fields, requeridos=False):
    fields = sorted(fields, key=lambda x: x['order'])  # Ordenar por el campo "order"
    form_data = {}
    
    container = st.container()  # Crear un contenedor
    with container:
        for field in fields:
            required = field.get("required", False)
            if requeridos:
                if not required:
                    continue
       
            
            fieldName =  field.get("fieldName")
            field_type = field.get("typename", "")
            label = field.get("label")
            value = field.get("value", "")
            placeholder = field.get("placeHolder", "")
            options = field.get("options", [])
            

            if field_type == "text_input":
                form_data[field["fieldName"]] = st.text_input(
                    key= fieldName,
                    label=label,
                    value=value if value else None,
                    placeholder=placeholder,
                    help="Este campo es requerido" if required else None
                )
            elif field_type == "text_area":
                form_data[field["fieldName"]] = st.text_area(
                    key= fieldName,
                    label=label,
                    value=value if value else None,
                    placeholder=placeholder,
                    help="Este campo es requerido" if required else None
                )
            elif field_type == "number_input":
                form_data[field["fieldName"]] = st.number_input(
                    key= fieldName,
                    label=label,
                    value=value if value else 0,
                    step=1,
                    placeholder=placeholder,
                    help="Este campo es requerido" if required else None
                )
            elif field_type == "select":
                opc = [x['value'] for x in options]
                form_data[field["fieldName"]] = st.selectbox(
                    key= fieldName,
                    label=label,
                    options=opc,
                    index=opc.index(value) if value in opc else 0,
                    help="Este campo es requerido" if required else None,
                )
            elif field_type == "select_multiple":
                opc = [x['value'] for x in options]
                form_data[field["fieldName"]] = st.multiselect(
                    key= fieldName,
                    label=label,
                    options=opc,
                    help="Este campo es requerido" if required else None,
                )
            elif field_type == "date":
                form_data[field["fieldName"]] = st.text_input(
                    key= fieldName,
                    label=label,
                    value= datetime.today().strftime("%d-%m-%Y"),
                    placeholder="dd-mm-yyyy ej. 31-12-2025",
                    help="Este campo es requerido" if required else None,
                )
                
        st.session_state.customFields = json.dumps(form_data)
       
    return container



def desencriptar(texto):
    resultado = ""
    for char in texto:
        if char in "ABCDEFGHIJ":
            num = ord(char) - ord('A')
            original = (num + 1) % 10
            resultado += str(original)
        else:
            resultado += char
    return resultado




def descomponer_codigo(codigo):
    # Busca: inicio con dígitos, luego letras, luego termina con dígitos
    match = re.match(r'^(\d+)([A-Za-z]+)(\d+)$', codigo)
    if match:
        grupo_economico = match.group(1)
        codigo_usuario = match.group(2)
        compania = match.group(3)
        resultado = {
            "grupo_economico": grupo_economico,
            "codigo_usuario": codigo_usuario,
            "compania": compania
        }
        
        codigo_emp = desencriptar(resultado['codigo_usuario'])
        
        return resultado['grupo_economico'], codigo_emp, resultado['compania'],
        
    else:
        raise ValueError("El código no tiene el formato esperado")


def render_error_page(title, message, button_text="Volver al inicio"):
    """
    Muestra una página de error elegante y vibrante utilizando st.html para máxima compatibilidad.
    """
    
    error_html = f"""
    <div style="font-family: sans-serif; display: flex; flex-direction: column; align-items: center; justify-content: center; padding: 40px 20px; width: 100%;">
        <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;600;700&display=swap" rel="stylesheet">
        <div style="background: white; border-radius: 32px; padding: 48px 32px; text-align: center; max-width: 550px; width: 100%; box-shadow: 0 30px 60px rgba(0,0,0,0.12); border: 1px solid #f0f0f0; position: relative; overflow: hidden; font-family: 'Outfit', sans-serif;">
            <div style="position: absolute; top: 0; left: 0; right: 0; height: 6px; background: linear-gradient(90deg, #FF4B4B, #FF8E53);"></div>
            <div style="width: 90px; height: 90px; background: linear-gradient(135deg, #FFF5F5 0%, #FFE3E3 100%); border-radius: 24px; display: flex; align-items: center; justify-content: center; margin: 0 auto 28px; color: #FF4B4B; box-shadow: 0 15px 30px rgba(255, 75, 75, 0.15); transform: rotate(-5deg); margin-left: auto; margin-right: auto;">
                <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                    <circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/>
                </svg>
            </div>
            <div style="font-size: 32px; font-weight: 700; color: #1A1A1A; margin-bottom: 16px; letter-spacing: -0.5px;">{title}</div>
            <div style="font-size: 18px; color: #4A5568; line-height: 1.6; margin-bottom: 30px;">{message}</div>
        </div>
    </div>
    """
    st.html(error_html)
    
    # El botón se mantiene fuera de la tarjeta para usar st.button nativo
    _, col, _ = st.columns([1, 1, 1])
    with col:
        if st.button(button_text, type="primary", use_container_width=True):
            st.query_params.clear()
            st.query_params["page"] = "home"
            st.session_state.page = "home"
            st.rerun()