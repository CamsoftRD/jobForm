import streamlit as st
import streamlit_antd_components as sac
from streamlit_extras.bottom_container import bottom
from app.util import descomponer_codigo
import base64

def buscar_carta_por_id(codigo):
    base_de_datos_simulada = {
        "137216": {
            "codigo": "137216",
            "fecha_emision": "2025-08-02",
            "activo": True,
            "empleado": {
                "nombre": "María González",
                "cedula": "001-1234567-8",
                "puesto": "Analista de Datos",
                "departamento": "TI",
                "genero": "F"
            }
        },
        "xyz789": {
            "codigo": "xyz789",
            "fecha_emision": "2024-12-10",
            "activo": False,
            "empleado": {
                "nombre": "Carlos Ramírez",
                "cedula": "402-9876543-2",
                "puesto": "Supervisor de Producción",
                "departamento": "Operaciones",
                "genero": "M"
            }
        }
    }

    return base_de_datos_simulada.get(codigo)


def validate(code:str):
    

    #gco, comp, emp = str(codigo_validacion).split("-")
    
    def desencriptar_desde_url(encoded_text):
        texto_bytes = base64.urlsafe_b64decode(encoded_text)
        return texto_bytes.decode('utf-8')
    
    descript_code = desencriptar_desde_url(code.split("-")[0])    
    companyName = desencriptar_desde_url(code.split("-")[1])    
    gco, emp,comp  = descomponer_codigo(descript_code)
    st.subheader(companyName)
    
    codigo_validacion = gco+emp+comp
    if not codigo_validacion:
        sac.result(
            label='Código no proporcionado',
            description='Por favor, acceda a esta página desde el código QR de una carta válida.',
            status='warning'
        )
        st.stop()


    # Buscar carta en la base de datos (esto lo defines tú)
    carta = buscar_carta_por_id(codigo_validacion)

    if not carta:
        sac.result(
            label='Carta no encontrada',
            description='No se ha encontrado una carta asociada a este código. Verifique que el enlace sea correcto.',
            status='error'
        )
        st.stop()

    if not carta["activo"]:
        sac.result(
            label='Carta inactiva',
            description='Esta carta fue emitida, pero el empleado ya no labora en la empresa.',
            status='warning'
        )
    else:
        
        sac.result(
            label='Carta válida',
            description=f'La carta {descript_code} ha sido validada exitosamente y pertenece a un empleado activo en la empresa.',
            status='success'
        )


    
    with bottom():
        st.markdown("---")
        st.caption("© 2025 MiEmpresa. Validación electrónica sin necesidad de firma física.")