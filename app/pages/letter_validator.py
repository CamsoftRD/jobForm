import streamlit as st
import streamlit_antd_components as sac
from streamlit_extras.bottom_container import bottom
from app.util import descomponer_codigo
import base64
from app.core import validate_employee


def validate(code:str):
    
    def desencriptar_desde_url(encoded_text: str) -> str:
        try:
            texto_bytes = base64.urlsafe_b64decode(encoded_text)
            return texto_bytes.decode('utf-8')
        except (base64.binascii.Error, UnicodeDecodeError):
            #st.error("Error al desencriptar el texto.")
            return ""

    def procesar_codigo(code: str):
        try:
            partes = code.split("-")
            if len(partes) < 2:
                st.error("Formato de código inválido.")
                return None, None, None, None, None, None

            encrypted_code, encrypted_company = partes[0], partes[1]
            descript_code = desencriptar_desde_url(encrypted_code)
            company_name = desencriptar_desde_url(encrypted_company)

            if not descript_code or not company_name:
                return None, None, None, None, None, None

            gco, emp, comp = descomponer_codigo(descript_code)


            codigo_validacion = f"{gco}{emp}{comp}"
            return gco, emp, comp,company_name, codigo_validacion, descript_code

        except Exception as e:
            st.error(f"Error al procesar el código: {e}")
            return None, None, None, None, None, None

    # Uso
    gco, emp, comp, company_name, codigo_validacion, codigo_en_carta = procesar_codigo(code)
    
    
   
        
    
    if not codigo_validacion:
        sac.result(
            label='Carta Inválida',
            description='Por favor, acceda a esta página desde el código QR de una carta válida.',
            status='error'
        )
        st.stop()


    # Buscar carta en la base de datos (esto lo defines tú)
    status = validate_employee(employee_id=int(emp), employee_company=int(comp))


    if status['activo'] == None:
        sac.result(
            label='Carta no encontrada',
            description='No se ha encontrado una carta asociada a este código. Verifique que el enlace sea correcto.',
            status='error'
        )
        st.stop()

    if status['activo'] == False:
        sac.result(
            label='Carta inactiva',
            description='Esta carta fue emitida, pero el empleado ya no labora en la empresa.',
            status='warning'
        )
    else:
        sac.result(
            label='Carta válida',
            description=f'La carta {codigo_en_carta} ha sido validada exitosamente y pertenece a un empleado activo en la empresa.',
            status='success'
        )


    
    with bottom():
        st.markdown("---")
        st.caption(f"© 2025 {company_name}. Validación electrónica sin necesidad de firma física.")