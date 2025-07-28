import streamlit as st
from app.core.api_jobs import fetch_jobs_offers
from app.pages.job_detail import job_detail
from app.pages.home import home
from app.core.api_educacion import fetch_grades

st.set_page_config(
    page_title="Job Details",
    page_icon=":briefcase:",
    layout="wide",
)

job_id = st.query_params.get("job_id", None)
company_id = st.query_params.get("comp", 6)
id_grupo_economico = st.query_params.get("geco", 1)
cliente_id = st.query_params.get("client", "rrhh")



#http://localhost:8501/?job_id=1089&comp=6
    
if not "page" in st.session_state:
    st.session_state.page = "home"

if not "grades" in st.session_state:
    grados = fetch_grades()
    st.session_state["grades"] = [f"{g.codigo}-{g.nombre}" for g in grados]
  
  

if job_id:
    
    with st.spinner():
        job = fetch_jobs_offers(job_id=job_id, company_id=company_id)
        
    job_detail(job, company_id)
else:
    
    if st.session_state.page == "home":
        home(company_id=company_id, grupo_economico=id_grupo_economico)
