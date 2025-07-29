import streamlit as st
from app.core.api_jobs import fetch_jobs_offers
from app.pages.job_detail import job_detail
from app.pages.home import home
from app.core.api_educacion import fetch_grades
from urllib.parse import urlparse
from app.fragments.job_apply_frm import apply_job


st.set_page_config(
    page_title="Jobs",
    page_icon="logo.png",
    layout="wide",
)

    
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
if not job_id or not company_id:
    st.session_state.pahe = "home"
      

# CARGO LOS GRADOS ACADEMICOS
if not "grades" in st.session_state:
    grados = fetch_grades()
    st.session_state["grades"] = [f"{g.codigo}-{g.nombre}" for g in grados]
  

if st.session_state.page == "home":
    home(grupo_economico=id_grupo_economico)

elif st.session_state.page == "job":
    with st.spinner():
        job = fetch_jobs_offers(job_id=job_id, company_id=company_id)
        
    job_detail(job, company_id)
    
elif st.session_state.page == "apply":

    apply_job(job_id=job_id, company_id=company_id)
    
else:
     home(grupo_economico=id_grupo_economico)

    
    
        
        
        
        
