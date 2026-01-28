import streamlit as st
from app.models.job_model import JobModel
from streamlit_extras.add_vertical_space import add_vertical_space



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
    

    # Styling for job detail
    st.markdown("""
        <style>
        .detail-header {
            border-bottom: 2px solid #f0f2f6;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }
        .detail-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1a1a1a;
            margin-bottom: 10px;
        }
        .detail-company {
            font-size: 1.2rem;
            color: #555;
            font-weight: 500;
        }
        .detail-section-title {
            font-size: 1.3rem;
            font-weight: 600;
            color: #2c3e50;
            margin-top: 25px;
            margin-bottom: 15px;
            border-left: 4px solid #ff4b4b;
            padding-left: 10px;
        }
        .detail-text {
            font-size: 1rem;
            line-height: 1.6;
            color: #333;
        }
        </style>
    """, unsafe_allow_html=True)

    with st.container():
        st.markdown(f"""
            <div class="detail-header">
                <div class="detail-title">{job.job_title}</div>
                <div class="detail-company">{job.company_name}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Metadata chips
        st.markdown('<div style="display: flex; gap: 10px; flex-wrap: wrap; margin-bottom: 20px;">', unsafe_allow_html=True)
        
        st.caption(f"📍 {job.location if job.location else 'Ubicación no especificada'} • 🏠 {job.workMode} • 💼 {job.contract_type_name} • 💰 {job.salary} DOP$/Mes")
        
        st.markdown('</div>', unsafe_allow_html=True)

    with st.container():
        st.markdown('<div class="detail-section-title">Acerca del empleo</div>', unsafe_allow_html=True)
        st.markdown(f'<div class="detail-text">{job.job_description}</div>', unsafe_allow_html=True)
        
        add_vertical_space(1)
        st.link_button("Aplicar ahora", url=f"/apply?job_id={job.id}&comp={job.company_id}", icon=":material/send:", type="primary", use_container_width=True)

    with st.container():
        if job.requirements:
            st.markdown('<div class="detail-section-title">Requisitos</div>', unsafe_allow_html=True)
            # Formatting requirements as a list if they look like one, otherwise just text
            reqs = job.requirements.replace("\n", "<br>")
            st.markdown(f'<div class="detail-text">{reqs}</div>', unsafe_allow_html=True)
        
        if job.responsibilities:
            st.markdown('<div class="detail-section-title">Responsabilidades</div>', unsafe_allow_html=True)
            resps = job.responsibilities.replace("\n", "<br>")
            st.markdown(f'<div class="detail-text">{resps}</div>', unsafe_allow_html=True)

    add_vertical_space(2)


        
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

        