import streamlit as st
from app.core.api_jobs import fetch_jobs_offers, fetch_jobs_offers_by_group
import streamlit_antd_components as sac
from app.pages.job_detail import job_detail
from streamlit_extras.row import row
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.bottom_container import bottom

@st.fragment()
def no_jobs():
    import base64

    # Simulando que no hay ofertas
    ofertas = []

    #st.set_page_config(page_title="Portal de Empleo", page_icon="💼", layout="centered")
    
    

    # Función para convertir imagen a Base64 e incrustarla en HTML
    def get_base64_image(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()

    image_base64 = get_base64_image("abeja_mallen.png")

    st.markdown(
        """
        <style>
        .empty-container {
            text-align: center;
            padding: 60px 20px;
            color: #555;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, sans-serif;
        }
        .empty-icon img {
            width: 120px;
            margin-bottom: 20px;
            opacity: 0.9;
        }
        .empty-title {
            font-size: 26px;
            font-weight: 600;
            margin-bottom: 10px;
        }
        .empty-subtitle {
            font-size: 14px;
            color: #777;
            margin-bottom: 10px;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    if not ofertas:
        st.markdown(
            f"""
            <div class="empty-container">
                <div class="empty-icon">
                    <img src="data:image/png;base64,{image_base64}" alt="Sin vacantes">
                </div>
                <div class="empty-company-name">Grupo Mallén</div>
                <div class="empty-title">No hay vacantes disponibles</div>
                <div class="empty-subtitle">
                    Nuestro equipo está creciendo, pero en este momento no tenemos oportunidades abiertas.<br>
                    Déjanos tu correo y te avisaremos cuando publiquemos nuevas vacantes.
                </div>
            </div>
            <style>
                .empty-company-name {{
                    font-size: 2rem;
                    font-weight: 600;
                    color: #2c3e50;
                    margin: 10px 0;
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                }}
            </style>
            """,
            unsafe_allow_html=True
        )

        _, col2, _ = st.columns([2.5, 4, 2.5])  # [izquierda, centro, derecha]
        with col2:  # Centro
            email = st.text_input("Tu correo electrónico", placeholder="ejemplo@correo.com")
            if st.button("Enviar", type="primary"):
                st.success("✅ ¡Gracias! Te avisaremos cuando haya una vacante disponible.")
                
        with bottom():
            _, col3, _ = st.columns([2.5, 4, 2.5])  # [izquierda, centro, derecha]
            with col3:  # Centro
                st.caption("Euclides Morillo Nº 53 Arroyo Hondo Viejo Santo Domingo, República Dominicana. T.809 683 7000 F.809 732 4748 E.info@mallengroup.com")

def home(grupo_economico):
    
 
      #with st.spinner():
    #jobs_original = fetch_jobs_offers(company_id=company_id)
    jobs_original = fetch_jobs_offers_by_group(id_grupo_economico=grupo_economico)
    
    if not jobs_original:
        no_jobs()
        st.stop()
        
       
    if not "jobs" in st.session_state:
        st.session_state.jobs = jobs_original
        
        

    def callback():
        # Obtenemos el filtro de texto, lo pasamos a minúsculas para búsqueda case-insensitive
        filtro_texto = st.session_state.mi_input.lower() if st.session_state.mi_input else ""
        filtro_compania = st.session_state.get("filter_compania", "Todos")
        filtro_modalidad = st.session_state.get("filter_modalidad", "Todos")
        filtro_tipo_contrato = st.session_state.get("filter_tipo_contrato", "Todos")  # si tienes esa key
        filtro_nivel_academico = st.session_state.get("filter_nivel_academico", "Todos")
        
        # Aplicar filtros combinados sobre jobs_original
        filtered_jobs = []
        for job in jobs_original:
            # Filtrar por texto (job_title o requirements)
            texto_valido = (
                (job.job_title and filtro_texto in job.job_title.lower()) or
                (job.requirements and filtro_texto in job.requirements.lower())
            ) if filtro_texto else True
            
            # Filtrar por compania
            compania_valida = (filtro_compania == "Todos") or (job.company_name == filtro_compania)
            
            # Filtrar por modalidad
            modalidad_valida = (filtro_modalidad == "Todos") or (job.workMode == filtro_modalidad)
            
            # Filtrar por tipo de contrato
            tipo_contrato_valido = (filtro_tipo_contrato == "Todos") or (job.contract_type_name == filtro_tipo_contrato)
            
            # Filtrar por nivel académico
            nivel_academico_valido = (filtro_nivel_academico == "Todos") or (job.nivel_academico == filtro_nivel_academico)
            
            # Si cumple todos los filtros, lo agregamos
            if texto_valido and compania_valida and modalidad_valida and tipo_contrato_valido and nivel_academico_valido:
                filtered_jobs.append(job)
                
        st.session_state.jobs = filtered_jobs
        # Reiniciar índice detalle para evitar errores IndexError
        st.session_state.detail_index = 0

    
    
    # st.logo(
    #     "https://grupomallen.com/wp-content/uploads/2016/09/Mallen_Logo_Footer.jpg",
    #     size="large",
    #     link="https://grupomallen.com",
    #     icon_image="https://grupomallen.com/wp-content/uploads/2016/09/Mallen_Logo_Footer.jpg",
    # )
        
    if st.session_state.jobs is not None:
        
        if not "detail_index" in st.session_state:
             st.session_state.detail_index = 0
             
        # Obtener una lista de las compañías disponibles.
        
        if not "companies" in st.session_state:
            st.session_state["companies"] = list(set(job.company_name for job in st.session_state.jobs))
            st.session_state["companies"].insert(0, "Todos")

        
        
    
        _, col_filters,  _ = st.columns([0.5,3,0.5], vertical_alignment="bottom")
        
        with col_filters:
            
            row2 = row([2, 2, 2, 3], vertical_align="bottom")
            row2.selectbox("Compañía", st.session_state.companies, on_change=callback, key="filter_compania")
            row2.selectbox("Modalidad", ["Todos", "Remoto", "Presencial", "Híbrido"], key="filter_modalidad", on_change=callback)
            row2.selectbox("Tipo Contrato", ["Todos", "Fijo", "Temporal"], key="filter_tipo_contrato", on_change=callback)
            #row2.selectbox("Nivel Academico", grados_academicos, key="filter_nivel_academico",  on_change=callback)
            row2.text_input("Buscar", icon=":material/search:", placeholder="Buscar por posición o palabra clave", label_visibility="collapsed",  key="mi_input", on_change=callback)
            
                    
        st.divider()

        _, col_list,_, col_detail, _ = st.columns([0.7,3,0.5,3,0.7])
        
        with col_list:
            st.title("Grupo Mallén")


            with st.container(height=900, border=False):
                for i, job in enumerate(st.session_state.jobs):
                    with st.container(border=True):
                        st.markdown(f"##### {job.job_title}")
                        st.markdown(f"###### {job.company_name}")
                        #st.caption(f"América Latina · {job.workMode} · {job.contract_type_name} · {job.salary} DOP$/Mes")
                        add_vertical_space(1)
                        
                        row_tags = row([1,1,1,1], vertical_align="bottom")
                        row_tags.badge("América Latina", icon=":material/location_on:", color="blue")
                        row_tags.badge(job.workMode, icon=":material/home:", color="orange")
                        row_tags.badge(job.contract_type_name, icon=":material/business_center:", color="green")
                        row_tags.badge(job.salary if job.salary else "No definido", icon=":material/paid:", color="violet")
                        
                        # sac.tags([
                        #     sac.Tag(label='América Latina', icon='geo-alt-fill', color="blue"),
                        #     sac.Tag(label=job.workMode, icon='house', color="orange"),
                        #     sac.Tag(label=job.contract_type_name, icon='briefcase-fill', color="geekblue"),
                        #     sac.Tag(label=job.salary if job.salary else "A discutir", icon='cash-coin'),
                        # ], align='start', key=f"{i}tags")


                        st.write(job.job_description.capitalize())
                        if job.responsibilities:
                            st.write(job.responsibilities.replace("\n", "")[0:400] + "...")
                            
                        if st.button("Ver mas detalle", key=i):
                            st.session_state.detail_index = i
                        
                    
        with col_detail: 
            if st.session_state.jobs:
                job_detail(st.session_state.jobs[st.session_state.detail_index]) 
            else:
                 st.write("No hay ofertas de empleos")                          
    else:
        st.write("No hay ofertas de empleos")