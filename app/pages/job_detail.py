import streamlit as st
from app.models.job_model import JobModel



def get_job(job_id) -> JobModel:
    # This function would typically fetch job details from a database or API
    # For this example, we will return a mock job detail
    return JobModel(
        id=job_id,
        job_title="Software Engineer",
        company_name="Tech Solutions",
        job_description="We are looking for a skilled software engineer to join our team.",
        position_name="Software Engineer",
        department_name="Engineering",
        contract_type_name="Full-time",
        creation_date="2023-01-01",
        closing_date="2023-12-31",
        supervisor_name="John Doe",
        requirements="Bachelor's degree in Computer Science or related field.",
        responsibilities="Develop and maintain software applications.",
        available_positions=5,
        workMode_code=1,  # 1 for remote, 2 for on-site
        workMode="Remote",
        salary=60000.00,
        customData='[{"label":"Tiene Vehículo propio","fieldName":"vehiculopropio","type":3,"typename":"select_multiple","placeHolder":"Seleccione Si o No dependiendo de si tiene o no un vehiculo","required":false,"options":[{"value":"Si","text":"Si"},{"value":"No","text":"No"}],"validationRules":{},"order":1,"value":[]}]'
    )

    

def job_detail(job:JobModel):
    

    st.header(job.job_title)
    st.caption(f"América Latina · {job.workMode} · {job.contract_type_name} · {job.salary} DOP$/Mes")


    st.subheader("Acerca del empleo")
    #st.image("https://images.unsplash.com/photo-1504384308090-c894fdcc538d?ixlib=rb-1.2.1&ixid=MnwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHx8&auto=format&fit=crop&w=1470&q=80", use_container_width=True)
    st.caption(f"América Latina · {job.workMode} · {job.contract_type_name} · {job.salary} DOP$/Mes")

    
    st.markdown(f"###### {job.job_description}")
    
    st.link_button("Aplicar al empleo", url=f"/apply?job_id={job.id}&comp={job.company_id}", icon=":material/send:", type="primary")
    # if st.button("Aplicar al empleo", icon=":material/send:", type="primary"):
        
     
    #     # del st.session_state["payload"]
    #     # del st.session_state["grades"]
    #     # del st.session_state["cv_loaded"]
    #     # del st.session_state["customFields"]

                
    #     #job.customData='[{"label":"Tiene Vehículo propio","fieldName":"vehiculopropio","type":3,"typename":"select_multiple","placeHolder":"Seleccione Si o No dependiendo de si tiene o no un vehiculo","required":false,"options":[{"value":"Si","text":"Si"},{"value":"No","text":"No"}],"validationRules":{},"order":1,"value":[]}]'
    #     from app.fragments.job_apply_frm import apply_job
    #     apply_job(job=job.__dict__, company_id=company_id)
        
    #     #st.switch_page("job_form.py")
        
    st.markdown("##### Requisitos")
    if job.requirements:
        st.write(job.requirements.replace("\n", ""))
    else:
        st.write("No se especificaron requisitos.")
    st.empty()
    
    st.markdown("##### Responsabilidades")
    
    if job.responsibilities:
        st.write(job.responsibilities.replace("\n", ""))
    else:
        st.write("No se especificaron responsabilidades.")
        

    

    # sac.buttons([
    #     sac.ButtonsItem(label='Solicitar', icon='send', color="blue")
    # ], align='start')


        
#     st.subheader("Quiénes somos")
#     with st.container(border=True):
#         col_logo, col_header = st.columns([1, 4], vertical_alignment="bottom")
#         with col_logo:
#             st.image("Mallen_Logo_Footer.png", width=200)
#         with col_header:
#             st.subheader(job.company_name)
#         st.write("""Somos un grupo de empresas dedicadas a la representación, distribución y promoción de productos Farmacéuticos, Salud y Belleza y Salud Animal con cobertura en toda la República Dominicana.

# Desde el año 1948, nos hemos caracterizado por contar con un equipo de profesionales de amplia experiencia en los sectores que incidimos. Ofrecemos infraestructuras óptimas para garantizar cada uno de los servicios prestados a nivel nacional.

# Nuestra filosofía de negocio es EL CLIENTE, contando con un excelente servicio de distribución, atención al cliente y buenas relaciones humanas.""")
#         st.link_button("Visitar sitio web", url="https://grupomallen.com/quienes-somos/")
        
        
        
        #requ -> shared - jobs.triple.com.do/?comp=2&req=2&client=cliente1
        # {{baseUrl}}/external/requisicion/compania/2
        # {{baseUrl}}/External/SolicitudEmpleo
        # {{baseUrl}}/reclutamiento/SolicitudEmpleo/requisicion/2

        