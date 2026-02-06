import streamlit as st
import os
import pandas as pd
import time
import requests
import base64
import json
from datetime import datetime

# Configuración de la página
st.set_page_config(page_title="Ofertas de Empleo", layout="wide")


global df_ofertas
df_ofertas = pd.DataFrame()
  

relative_path = './logo.png' 
full_path = os.path.join(os.getcwd(), relative_path)
path = os.path.abspath(full_path)


_, col2, _= st.columns([0.3, 1, 0.3])

    
@st.cache_data(ttl=60*60)
def get_jobs():
    #df = pd.read_json("./sample.json")
    #return df
    baseUrl = "http://rrhh.administracionapi.camsoft.com.do:8086"
    x_api_key = "AJEFTSLBSUXBTIILJPQKSNNXTETCMFRRWHQSLIHBDJQVBFELRO"
    
    #baseUrl = os.getenv("RRHH_BASE_URL")
    #x_api_key = os.getenv("RRHH_API_KEY")
    url = f"{baseUrl}/ApiGateway/api/v1/requisitions/"
    
    x_ui_culture = "es-DO"
    headers = {
        "Content-type": "application/json",
        "x-api-key": x_api_key,
        "x-ui-culture": x_ui_culture
    }
   
    response = requests.get(url=url, headers=headers)
    
    if response.status_code == 200:
        result = response.json()["result"]
        return pd.DataFrame(result)
    else:
        return None
    


# Definir el estado de la sesión para la navegación
if "page" not in st.session_state:
    st.session_state.page = "home"  # Página inicial
    

if "jobid" in st.query_params and st.session_state.page != "form":
    st.session_state.jobRequisitionId = st.query_params.jobid
    st.session_state.page = "detail"
    

    
# Función para cambiar de página
def switch_page(page_name):
    st.session_state.page = page_name


# Función para convertir el archivo subido a Base64
def file_to_base64(file):
    return base64.b64encode(file.read()).decode("utf-8")
   
def send_request(data):
    baseUrl = os.getenv("RRHH_BASE_URL")
    x_api_key = os.getenv("RRHH_API_KEY")
    
    baseUrl = "http://rrhh.administracionapi.camsoft.com.do:8086"
    x_api_key = "AJEFTSLBSUXBTIILJPQKSNNXTETCMFRRWHQSLIHBDJQVBFELRO"
    
    url = f"{baseUrl}/ApiGateway/api/v1/applications/"
    x_ui_culture = "es-DO"
    

    
    headers = {
        "Content-type": "application/json",
        "x-api-key": x_api_key,
        "x-ui-culture": x_ui_culture
    }
    
    
    response = requests.post(url=url, headers=headers, json=data)
    if response.status_code == 201:
        return True    
    else:
        response.text
        return False    
        



# Función para renderizar los campos dentro de un contenedor
def render_custom_fields_in_container(fields):
    fields = sorted(fields, key=lambda x: x['order'])  # Ordenar por el campo "order"
    form_data = {}
    


    container = st.container()  # Crear un contenedor
    with container:
        for field in fields:
            fieldName =  field.get("fieldName")
            field_type = field.get("typename", "")
            label = field.get("label")
            value = field.get("value", "")
            placeholder = field.get("placeHolder", "")
            options = field.get("options", [])
            required = field.get("required", False)

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

with col2:


    # Navegación basada en el estado de la sesión
    if st.session_state.page == "home":
        st.title("Ofertas de Empleo")
        df_ofertas = get_jobs() 
        
        if df_ofertas is not None:
            
            colf, colf2, _= st.columns([1, 1, 0.3])
            
            # Filtro por ubicación
            ubicaciones = ["Todos"] + df_ofertas["companyName"].unique().tolist()
            with colf:
                filtro_ubicacion = st.selectbox("Filtrar por Empresa", ubicaciones)

                # Filtrar las ofertas
                if filtro_ubicacion != "Todos":
                    df_ofertas = df_ofertas[df_ofertas["companyName"] == filtro_ubicacion]



            # Filtro por departamento
            departmentName = ["Todos"] + df_ofertas["departmentName"].unique().tolist()
            with colf2:
                filtro_departmentName = st.selectbox("Filtrar por departamento", departmentName)

                # Filtrar las ofertas
                if filtro_departmentName != "Todos":
                    df_ofertas = df_ofertas[df_ofertas["departmentName"] == filtro_departmentName]
                
  
           
            # Mostrar las ofertas
            for h, oferta in df_ofertas.iterrows():
                container = st.container(border=True, key=h)
                with container:
                    colt, _, colbutton= st.columns([1, 1.1, 0.2])
                    with colt:
                        st.markdown(f"##### {oferta['jobTitle']}")

                        
                    with colbutton:
                        if st.button(key=f"{h}2{oferta['id']}", label=":blue[Aplicar]", type="tertiary"):
                            st.session_state.jobRequisitionId = oferta['id']
                            st.query_params.jobid = oferta['id']
                            switch_page("detail")
                            st.rerun()
                                        
        else:
            st.write("No hay ofertas de empleos")
            
    elif st.session_state.page == "detail":
        col, _, _ = st.columns([0.5, 1.1, 0.2])
        with col:
            if st.button(":blue[< Atrás]", type="tertiary"):
                st.query_params.clear()
                switch_page("home")
                st.rerun()
                
                
        df = get_jobs()
        job = df[df["id"] == int(st.session_state.jobRequisitionId)]
        if not job.empty:
            st.title(job["jobTitle"].values[0])
            st.subheader(f"**Empresa:** {job['companyName'].values[0]}")
            st.write(f"**Descripción**")
            st.write(job['description'].values[0])

            st.write("**Responsabilidades**")
            st.markdown(job['responsibilities'].values[0])
            st.write()
            st.write("**Requisitos**")
            st.markdown(job['requirements'].values[0])

            if st.button(label=":red[Aplicar a Vacante]"):
                st.session_state.jobRequisitionId = job['id'].values[0]
                switch_page("form")
                st.rerun()

            st.write("---") 
        else:
            st.query_params.clear()
            switch_page("home")
            st.rerun()
            
    elif st.session_state.page == "form":
        customFields = []
        df = get_jobs() 
        df = df[df["id"] == int(st.session_state.jobRequisitionId)]
        if st.button(":blue[< Atrás]", type="tertiary"):
            switch_page("detail")  
            st.rerun()
        st.subheader(df["jobTitle"].values[0])
        
        if "customData" in df.columns:
            if df["customData"].values[0]:
                strdata = str(df["customData"].values[0])
                customFields= json.loads(strdata)
        
        paises = (
                    "1-Republica Dominicana",
                    "2-Estados Unidos",
                    "3-México",
                    "4-Colombia",
                    "5-Venezuela",
                    "6-Argentina",
                    "7-Chile",
                    "8-Perú",
                    "9-Brasil",
                    "10-Cuba",
                    "11-Canadá",
                    "12-España",
                    "13-Francia",
                    "14-Alemania",
                    "15-Italia",
                    "16-Inglaterra",
                    "17-Japón",
                    "18-China",
                    "19-Corea del Sur",
                    "20-Haití"
                )
        nacionalidades = (
                    "1-Dominicana",
                    "2-Estadounidense",
                    "3-Mexicana",
                    "4-Colombiana",
                    "5-Venezolana",
                    "6-Argentina",
                    "7-Chilena",
                    "8-Peruana",
                    "9-Brasileña",
                    "10-Cubana",
                    "11-Canadiense",
                    "12-Española",
                    "13-Francesa",
                    "14-Alemana",
                    "15-Italiana",
                    "16-Inglesa",
                    "17-Japonesa",
                    "18-China",
                    "19-Coreana",
                    "20-Haitiana"
                )

        grados_academicos = (
            "1-Secundaria",
            "2-Bachillerato",
            "3-Técnico",
            "4-Licenciatura",
            "5-Maestría",
            "6-Doctorado",
        )
        
        # Botón para volver a la página principal
        
            
        with st.form("my_form"):
        
            # Información Personal
            st.caption("Información Personal")
            f, m = st.columns(2)
            l, s = st.columns(2)
            
            firstName = f.text_input(":red[*] Primer Nombre", placeholder="ej. Jhon")
            middleName = m.text_input("Segundo Nombre", placeholder="ej. Alexander")
            lastName = l.text_input(":red[*] Primer Apellido", placeholder="ej. Doe")
            surname = s.text_input("Segundo Apellido", placeholder="ej. Smith")
            
            #gender = st.selectbox(":red[*] Género", ("1-Masculino", "2-Femenino"))
            birthDate = st.date_input(":red[*] Fecha de Nacimiento")
            #maritalStatus = st.selectbox("Estado Civil", ("Soltero", "Casado", "Unión Libre"))

            # Identificación
            st.caption("Identificación")
            identificationType = st.selectbox("Tipo de identificación", ("1-Cédula", "5-Pasaporte"))
            identificationNumber = st.text_input(":red[*] Número de Identificación", placeholder="ej. 00100013305")

            # Educación

            # educationLevelId = st.selectbox(":red[*] Nivel Educativo", grados_academicos)
            mobilePhone = st.text_input(":red[*] Teléfono Celular", placeholder="ej. 18090009999")
            email = st.text_input("Correo Electrónico", placeholder="ej. ejemplo@correo.com")
            uploaded_file = st.file_uploader(":red[*] Resume/CV", type=['doc', 'pdf', 'docx', "png", "jpg", "txt", "bmp"])

            if customFields:    
                container = render_custom_fields_in_container(customFields)

            
            #st.write(form_data)
                    


            # Every form must have a submit button.
            submitted = st.form_submit_button("Submit")
            
            if submitted:
                for i, field in enumerate(customFields):
                    ssession_data = json.loads(st.session_state.customFields)
                    if field['fieldName'] in ssession_data:
                        customFields[i]["value"] = ssession_data[field['fieldName']]

                data = {
                    "jobRequisitionId": int(st.session_state.jobRequisitionId),
                    "identificationType": int(identificationType.split("-")[0]),
                    "identificationNumber": identificationNumber,
                    "firstName": firstName.capitalize(),
                    "middleName": middleName.capitalize(),
                    "lastName": lastName.capitalize(),
                    "surname": surname.capitalize(),
                    "mobilePhone": mobilePhone,
                    "attachedDocument": None,
                    "fileExtension": "",
                    "email": email,
                    "customData": json.dumps(customFields)
                }
                
                st.json(data)
                
                # Campos requeridos con nombres descriptivos
                required_fields = {
                    "jobRequisitionId": "Job Requisition ID",
                    "identificationType": "Identification Type",
                    "identificationNumber": "Número de Identificación",
                    "firstName": "Primer Nombre",
                    "lastName": "Segundo Nombre",
                    "mobilePhone": "📱 Teléfono Celular",
                    "email": "Correo Electrónico",
                    "attachedDocument": "Resumen CV"
                }
                
                if uploaded_file is not None:
                    
                    # Convertir archivo a base64
                    file_base64 = file_to_base64(uploaded_file)
                    data["attachedDocument"] = file_base64
                    data["fileExtension"] = uploaded_file.type.split("/")[1]
                    
                
                
                # Validación de campos requeridos
                error = None
                

                
                for field, field_name in required_fields.items():
                    if field_name == "customData":
                        for item in data["customData"]:
                            val = item["value"]
                            st.write(item)
                            if item["required"] and (val is None or (isinstance(val, str) and not val.strip())):
                                error = f"{item['fieldName']} es requerido."
                                break
                    else:
                        value = data.get(field)
                        if value is None or (isinstance(value, str) and not value.strip()):
                            error = f"{field_name} es requerido."
                            break
                   
                    
                if error:
                    st.error(error)  
                else:
                    msg = st.toast('Enviando...')
                    
                   
                    if send_request(data):
                        msg.toast('Solicitud enviada exitosamente...', icon="✅")
                        time.sleep(3)
                        st.session_state.page = "home"
                        st.rerun()
                    else:
                        msg.toast('Se presentó un error al envíar la solicitud. Por favor intente de nuevo.!', icon = "😰")
                        time.sleep(1)
                        st.error("Se presentó un error al envíar la solicitud. Por favor intente de nuevo.")
                        
            


