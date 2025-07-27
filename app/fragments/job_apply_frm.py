import streamlit as st
import json, os
from openai import OpenAI
import time
from app.util import render_custom_fields_in_container, leer_pdf, file_to_base64
from app.core.api_jobs import apply_job_offert
from app.core.api_educacion import fetch_grades
from streamlit_extras.row import row

openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key)  # or set OPENAI_API_KEY in your environment

if not "grades" in st.session_state:
    grados = fetch_grades()
    st.session_state["grades"] = [f"{g.codigo}-{g.nombre}" for g in grados]


                        
prompt= f"""Con los datos de este texto:

Si la información proporcionada **no corresponde claramente a un currículum vitae (hoja de vida)**, genera exclusivamente el siguiente diccionario JSON:
"error": "La información proporcionada no corresponde a una hoja de vida"

Si la información **sí corresponde a un currículum vitae**, genera un diccionario JSON que siga estrictamente esta estructura de claves sin modificarlas:


    "tipo_Identificacion": null,
    "identificacion": null,
    "id_Compania": null,
    "primer_Nombre": "",
    "segundo_Nombre": "",
    "primer_Apellido": "",
    "segundo_Apellido": "",
    "nombre_Completo": "",
    "comentario": "",
    "email": "",
    "telefono": "",
    "etiqueta": "",
    "id_GradoAcademico: "",
    "apreciacion": 0


Llena los valores con los datos que correspondan del currículum (por ejemplo, nombre, teléfono, correo). 
Para el campo "etiqueta" agrega alguna cualidad(hashstag separados por comas, ej: #liderazgo, ) destacada del solicitante basada en su perfil profesional. 

Completa el campo id_GradoAcademico basándote en la información académica proporcionada en el currículum vitae.
Por ejemplo, si el candidato posee un título de Licenciatura, selecciona el valor correspondiente de este listado:
    {st.session_state.grades}


Instrucciones para asignar el valor de tipo_Identificacion (entero):
    Si el campo identificacion contiene una cédula dominicana válida de 11 dígitos, con o sin guiones (por ejemplo, 001-20324456-5 o 001203244565), asignar el valor entero 1 a tipo_Identificacion.
    Si identificacion corresponde a un pasaporte, asignar el valor entero 5 a tipo_Identificacion.
    Si identificacion está vacío o es nulo, asignar el valor null a tipo_Identificacion


No cambies las claves ni agregues nuevas. 

En el campo "apreciación", compara detalladamente los datos del currículum del candidato con los requisitos del puesto al que está aplicando. Evalúa considerando los siguientes criterios:
    Educación y formación relacionadas con el puesto
    Experiencia relevante y específica en funciones similares
    Habilidades técnicas y competencias clave requeridas por la vacante

Evalúa y asigna una puntuación de 1 a 5 estrellas según la siguiente escala:
    1 Sin coincidencia o perfil inadecuado respecto a los requisitos.
    2 Muy poca adecuación; no cumple los requisitos básicos.
    3 Adecuación limitada; cumple algunos requisitos mínimos.
    4 Adecuación media; cumple la mayoría de los requisitos clave y posee 1-2 años de experiencia laboral en el puesto solicitado.
    5 Alta adecuación; cumple todos los requisitos y tiene 3 o más años de experiencia laboral en el  puesto solicitado.

Llena el campo "comentario" tomando en cuenta la apreciación anterior. Finaliza el comentario con:
"...✅" si la apreciación es positiva (4 o 5 estrellas)
"...❌" si la apreciación es 2 estrellas o menos.


Si algún dato no está disponible, deja el valor como null.
**La respuesta debe contener únicamente el diccionario JSON solicitado, sin sugerencias, explicaciones ni datos adicionales.**
"""



def preguntar_al_modelo(texto, prompt_usuario, job):
    respuesta = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Eres un asistente útil que analiza documentos."},
            {"role": "user", "content": f"{prompt_usuario}\n\nContenido del documento:\n{texto}\n\n Requisitos del empleo:{job}"}
        ]
    )
    return respuesta.choices[0].message.content





def generate_response(some_long_response):
    for line in some_long_response:
        yield line
        time.sleep(0.01)  # Optional delay for effect
        
        
        
        
@st.dialog("Aplicar al empleo", width="large")
def apply_job(job, company_id):
    """
    Function to handle job application logic.
    This function would typically interact with an API to submit the job application.
    """
    
    st.subheader(job["job_title"])
    st.write(job["job_description"].capitalize())
    
    payload_temp = {}
    customFields = []
    
    if not "cv_loaded" in st.session_state:
        st.session_state.cv_loaded = False
        
        
    if not "payload" in st.session_state:
        st.session_state.payload = {}
        

    uploaded_file = st.file_uploader(f"Adjunta tu CV para que gestionemos tu postulación al empleo de forma automática.", type=['pdf'], accept_multiple_files=False)
    
  
    
    if uploaded_file is not None:
       
        
        if not st.session_state.payload:
            texto_extraido = leer_pdf(uploaded_file)
            
            if not st.session_state.cv_loaded:
                with st.spinner("Procesando el CV..."):
                    respuesta = preguntar_al_modelo(texto_extraido, prompt, job)
                    
                    #convertir la respuesta a un diccionario
                    st.session_state.payload = json.loads(respuesta)
                    
                    if not isinstance(st.session_state.payload, dict):
                        st.warning("Hubo un error al procesar el CV. Por favor, asegúrate de que el archivo sea un currículum vitae válido.")
                        return
                    
                   
            
        if "error" in st.session_state.payload:
            st.write_stream(generate_response(st.session_state.payload["error"]))
            st.session_state.cv_loaded = False
        else:
            
            #valoracion y comentario del candidato
            with st.chat_message("ai"):
                st.markdown("### Valoración:")
                if not st.session_state.cv_loaded:
                    st.write_stream(generate_response(st.session_state.payload['comentario']))
                else:
                    st.write(st.session_state.payload['comentario'])
                
                if "feedback" not in st.session_state:
                    st.session_state.feedback = st.session_state.payload["apreciacion"] -1
    
                st.caption("Resultado de la valoración del perfil para esta posición")
                st.feedback("stars", key="feedback", disabled=True)
                
            
            #validar los campos del dict que son null y solicitarlos al usuario
            st.write_stream(generate_response("Campos obligatorios que faltan en tu CV"))
            for i, key in enumerate(st.session_state.payload.keys()):
               
                if st.session_state.payload[key] is None or st.session_state.payload[key] == "":
                    if key == "tipo_Identificacion":
                        st.session_state.payload[key] = int(st.selectbox("Tipo de identificación", ("1-Cédula", "5-Pasaporte"), key=f"{i}_req_{key}").split("-")[0])
                        
                    elif key == "id_GradoAcademico":
                        st.session_state.payload[key] = st.selectbox(":red[*] Nivel Educativo", st.session_state.grades, key=f"{i}_req_{key}")
                    else:
                        if not key in ["segundo_Nombre", "segundo_Apellido", "etiqueta", "id_Compania", "nombre_Completo", "nombre_Supervisor", "nombre_Departamento", "id_Departamento", "id_Requisicion", "comentario", "apreciacion"]:
                            st.session_state.payload[key] = st.text_input(f"Ingrese el valor para {key}:", value=st.session_state.payload[key], key=f"{i}_req_{key}")
            
            # Resumen de los datos cargados desde el cv
            with st.expander("Resumen de datos cargados"):
                 for i, key in enumerate(st.session_state.payload.keys()):            
                    if not st.session_state.payload[key] is None and not st.session_state.payload[key] == "":
                        if key == "tipo_Identificacion":
                            st.session_state.payload[key] = int(st.selectbox("Tipo de identificación", ("1-Cédula", "5-Pasaporte"), key=f"{i}_complete_{key}").split("-")[0])
                        elif key == "id_GradoAcademico":
                            st.session_state.payload[key] = st.selectbox(":red[*] Nivel Educativo", st.session_state.grades,  key=f"{i}_complete_{key}")
                        else:
                            if not key in ["etiqueta", "id_Compania", "nombre_Completo", "nombre_Supervisor", "nombre_Departamento", "id_Departamento", "id_Requisicion", "comentario", "apreciacion"]:
                                st.session_state.payload[key] = st.text_input(f"Ingrese el valor para {key}:", value=st.session_state.payload[key], key=f"{i}_complete_{key}")
                
            
                
            if "customData" in job:
                if job["customData"]:
                    strdata = str(job["customData"])
                    customFields= json.loads(strdata)
            
                    if customFields:    
                        render_custom_fields_in_container(customFields, requeridos=False)     
            
            
            if "customData" in job:
                if job["customData"]:
                    strdata = str(job["customData"])
                    customFields= json.loads(strdata)
                    print(customFields)
           
            
                

                    
            st.session_state.cv_loaded = True
            
                
                


            
    #st.json(st.session_state.payload)
    row_btn = row([0.5,0.5], vertical_align="bottom")
    
    # if row_btn.button("Cancelar"):
    #      for key in st.session_state.keys():
    #         del st.session_state[key]
            
    #         time.sleep(2)
    #         st.rerun()
    
    
    if row_btn.button(f"Enviar solicitud", type="primary"):
        
        for i, field in enumerate(customFields):
            ssession_data = json.loads(st.session_state.customFields)
            if field['fieldName'] in ssession_data:
                customFields[i]["value"] = ssession_data[field['fieldName']]
                
        st.session_state.payload["id_Requisicion"] = job["id"]
        st.session_state.payload["id_Compania"] = int(company_id)
        st.session_state.payload["id_Departamento"] = job["department_id"]
        st.session_state.payload["nombre_Departamento"] = job["department_name"]
        st.session_state.payload["nombre_Supervisor"] = job["supervisor_name"]
        st.session_state.payload["ExtraCustomData"] = json.dumps(customFields)
   
    
        
                    
        # Convertir archivo a base64
        file_base64 = file_to_base64(uploaded_file)
        file = {}
        file["attachedDocument"] = file_base64
        file["fileExtension"] = uploaded_file.type.split("/")[1]

        
        

        #st.json(st.session_state.payload)
        response = None
        with st.spinner("Porfavor espere ..."):
            response = apply_job_offert(data=st.session_state.payload, file=file)
            
            
        if response.get("error"):
            st.error(response.get("message", "No fue posible enviar la solicitud. Por favor, inténtalo nuevamente."))
        else:
            st.success("Solicitud enviada correctamente. Nuestro equipo revisará tu perfil y te contactará pronto.")
            if st.button("Cerrar"):
                for key in st.session_state.keys():
                    del st.session_state[key]
                
                time.sleep(2)
                st.rerun()
        # data = json.dumps(customFields)
        # for item in data:
        #    val = item["value"]
        #    st.write(item)

                
                
                