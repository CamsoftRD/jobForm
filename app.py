import streamlit as st
from app.core.api_jobs import fetch_jobs_offers
from app.pages.job_detail import job_detail_page
from app.pages.home import home

from app.pages.letter_validator import validate
from app.core.api_educacion import fetch_grades
from urllib.parse import urlparse
from app.fragments.job_apply_frm import apply_job


st.set_page_config(
    page_title="Jobs",
    page_icon="logo.png",
    layout="wide",
)


enviroment = st.secrets["enviroment"]

if not "enviroment"  in st.session_state or st.session_state.enviroment != enviroment:
    st.session_state.enviroment = enviroment

    
tabla_relacion_db = st.secrets["domain"]  
if "domain_name" not in st.session_state:
    # Obtener el dominio sin protocolo
    url = st.context.url.replace("https://", "").replace("http://", "")

    # Buscar en el diccionario proveniente del TOML
    mapped = tabla_relacion_db.get(url)

    if mapped:
        st.session_state.domain_name = mapped
    else:
        # Si no existe, usar el dominio actual como fallback
        #st.session_state.domain_name = url
        st.session_state.domain_name = "demo.triple.com.do"


if not "page" in st.session_state:
    st.session_state.page = "home"


job_id = st.query_params.get("job_id", None)
company_id = st.query_params.get("comp", None)
id_grupo_economico = st.query_params.get("geco", 1)


# DETERMINAR CUAL ES LA PAGE QUE ESTAN LLAMANDO 
url = st.context.url #obtener el page de la url
parsed_url = urlparse(url) # Parsear la URL
page = parsed_url.path.rstrip('/').split('/')[-1] # Obtener el path y extraer la última parte
if page:
    st.session_state.page = page
  
# Si no hay datos para acceder a las paginas de detalle, redirecciono al home page

st.session_state.grades = []   

# CARGO LOS GRADOS ACADEMICOS
# if not "grades" in st.session_state:
#     grados = fetch_grades()
#     if grados:
#         st.session_state["grades"] = [f"{g.codigo}-{g.nombre}" for g in grados]
  

if st.session_state.page == "home":
    home(grupo_economico=id_grupo_economico)
    
elif st.session_state.page == "validate":
    validator_id = st.query_params.get("id", None)
    if validator_id:
        validate(validator_id)
    else:
        home(grupo_economico=id_grupo_economico)

elif st.session_state.page == "job":
    # Only fetch if params exist (Deep link), otherwise use existing state
    if job_id and company_id:
        with st.spinner():
            job = fetch_jobs_offers(job_id=job_id, company_id=company_id)
        st.session_state.selected_job = job
    
    job_detail_page()
    
elif st.session_state.page == "apply":

    apply_job(job_id=job_id, company_id=company_id)
    
else:
     home(grupo_economico=id_grupo_economico)

    
    
        
        
        
        
