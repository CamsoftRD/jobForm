import streamlit as st
from app.core.api_jobs import fetch_jobs_offers, fetch_jobs_offers_by_group
import streamlit_antd_components as sac
from app.pages.job_detail import job_detail
from streamlit_extras.row import row
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.bottom_container import bottom
from datetime import datetime
import json




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
    
    # Remove default Streamlit top padding
    st.markdown("""
        <style>
               .block-container {
                    padding-top: 2rem !important;
                    padding-bottom: 0rem !important;
                    
                }
        </style>
        """, unsafe_allow_html=True)
    
    if not jobs_original:
        no_jobs()
        st.stop()
        
       
    if not "jobs" in st.session_state:
        st.session_state.jobs = jobs_original
        
        

    # --- REMOVED CALLBACK FUNCTION TO SIMPLIFY LOGIC (Linear Execution) ---
    # We now filter directly based on the current state of widgets during the script run.

    # st.logo(...) 
        
    # Ensure session state structure
    if "jobs" not in st.session_state:
        st.session_state.jobs = jobs_original
        
    if not "detail_index" in st.session_state:
         st.session_state.detail_index = 0
         
    if not "companies" in st.session_state:
        st.session_state["companies"] = list(set(job.company_name for job in jobs_original)) # use jobs_original source
        st.session_state["companies"].insert(0, "Todos")

    
    col_filters,  _ = st.columns([3,1], vertical_alignment="bottom")
    
    # Initialize filter variables
    filtro_texto = ""
    filtro_compania = "Todos"
    filtro_modalidad = "Todos"
    filtro_tipo_contrato = "Todos"

    with col_filters:
        
        add_vertical_space(1)
        
        # Row 2: Chips + Search
        st.markdown("<span style='font-size: 0.9rem; font-weight: 600; color: #555; margin-right: 10px;'>Filtrar por:</span>", unsafe_allow_html=True)
        
        # 3 Columns: Modalidad | Tipo Contrato | Search
        c_chip_1, c_chip_2, c_search = st.columns([1.5, 1.1, 1.5], gap="small", vertical_alignment="bottom")
        
        with c_chip_1:
             # Modalidad
            filtro_modalidad = sac.chip(
                items=[
                    sac.ChipItem('Todos', icon='filter-circle'),
                    sac.ChipItem('Remoto', icon='house-door'),
                    sac.ChipItem('Presencial', icon='building'),
                    sac.ChipItem('Híbrido', icon='shuffle'),
                ],
                label='Modalidad',
                align='start',
                radius='md',
                size='sm',
                variant='light',
                key="filter_modalidad" # Removed callback
            )
        
        with c_chip_2:
            # Tipo Contrato
            filtro_tipo_contrato = sac.chip(
                items=[
                     sac.ChipItem('Todos', icon='filter-circle'),
                     sac.ChipItem('Fijo', icon='briefcase'),
                     sac.ChipItem('Temporal', icon='clock'),
                ],
                label='Tipo Contrato',
                align='start',
                radius='md',
                 size='sm',
                variant='light',
                key="filter_tipo_contrato" # Removed callback
            )
        
        with c_search:
            # Search Input next to chips
            filtro_texto = st.text_input("Buscar", icon=":material/search:", placeholder="🔍 Buscar puesto...", label_visibility="collapsed", key="mi_input")
            if filtro_texto:
                filtro_texto = filtro_texto.lower()
        
        # Ensure filters are not None to avoid AttributeError
        if not filtro_modalidad:
            filtro_modalidad = "Todos"
        if not filtro_tipo_contrato:
            filtro_tipo_contrato = "Todos"

        # Horizontal line for separation
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-top: 1px solid #eee;'>", unsafe_allow_html=True)

    # --- FILTERING LOGIC ---
    # Apply filters immediately using the values captured above
    filtered_jobs = []
    
    # Get company from session state if it exists (though selectbox was removed, we keep this safe in case of re-addition or internal logic)
    # Since selectbox was removed, filtro_compania remains "Todos" by default as initialized above.

    for job in jobs_original:
        # Filtrar por texto (job_title o requirements)
        texto_valido = (
            (job.job_title and filtro_texto in job.job_title.lower()) or
            (job.requirements and filtro_texto in job.requirements.lower())
        ) if filtro_texto else True
        
        # Filtrar por compania (Default Todos since widget removed)
        compania_valida = (filtro_compania == "Todos") or (job.company_name == filtro_compania)
        
        # Filtrar por modalidad
        modalidad_valida = (filtro_modalidad == "Todos") or (
            job.workMode and job.workMode.strip().lower() == filtro_modalidad.strip().lower()
        )
        
        # Filtrar por tipo de contrato
        tipo_contrato_valido = (filtro_tipo_contrato == "Todos") or (
            job.contract_type_name and job.contract_type_name.strip().lower() == filtro_tipo_contrato.strip().lower()
        )
        
        # Si cumple todos los filtros, lo agregamos
        if texto_valido and compania_valida and modalidad_valida and tipo_contrato_valido:
            filtered_jobs.append(job)

    # Update session state for display loop and detail view
    st.session_state.jobs = filtered_jobs


    # --- EMPTY STATE ---
    if not filtered_jobs:
        _, col_msg, _ = st.columns([1, 2, 1])
        with col_msg:
            st.markdown(
                """
                <div style="text-align: center; padding: 40px; color: #666; background-color: #f8f9fa; border-radius: 12px; border: 1px dashed #ccc;">
                    <div style="font-size: 40px; margin-bottom: 10px;">😕</div>
                    <div style="font-size: 18px; font-weight: 500;">No se encontraron vacantes</div>
                    <div style="font-size: 14px;">Intenta ajustar los filtros de búsqueda.</div>
                </div>
                """, unsafe_allow_html=True
            )
        # Placeholder for detail view to keep layout stable
        col_list, col_detail = st.columns([0.3, 0.5])
        with col_detail:
            st.empty() 
            
    else:
        #_, col_list,_, col_detail, _ = st.columns([0.7,3,0.5,3,0.7])
        col_list,col_detail = st.columns([0.3,0.5])
        with col_list:
            #st.title("Grupo Mallén")
            
            keyc = f"container-scroll-hide"

            st.markdown(
                f"""
                <style>
                    .st-key-{keyc} {{
                        overflow: auto !important;
                        scrollbar-width: none;      /* Firefox */
                        padding-right: 10px;        /* Spacing for scrollbar hidden */
                    }}
                    .st-key-{keyc}::-webkit-scrollbar {{
                        display: none;              /* Chrome, Safari, Edge */
                    }}
                </style>
                """,
                unsafe_allow_html=True,
            )



            with st.container(height=900, border=False, key=keyc):
                for i, job in enumerate(st.session_state.jobs):
                    
                    key = f"job-card-{i}"
                    
                    # Inject CSS specific to this card's key to guarantee style application
                    st.markdown(f"""
                    <style>
                    div.st-key-{key} {{
                        background-color: #f0f0f0 !important;

                        border: 1px solid #DEE2E6 !important;
                        border-radius: 12px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
                        transition: all 0.3s ease;
                        margin-bottom: 15px;
                    }}
                    div.st-key-{key}:hover {{
                        box-shadow: 0 8px 16px rgba(0,0,0,0.1);
                        transform: translateY(-2px);
                        border-color: #007bff !important;
                        background-color: #FFFFFF !important;
                    }}
                    /* Internal styles for the card content */
                    .job-card-title {{
                        font-size: 1.15rem;
                        font-weight: 700;
                        color: #1a1a1a;
                        margin-bottom: 2px;
                    }}
                    .job-card-company {{
                        font-size: 0.9rem;
                        color: #666;
                        font-weight: 500;
                        margin-bottom: 12px;
                    }}
                    .job-tags-container {{
                        display: flex;
                        flex-wrap: wrap;
                        gap: 8px;
                        margin-bottom: 12px;
                    }}
                    .job-tag {{
                        background-color: #f8f9fa;
                        color: #4a5568;
                        padding: 4px 10px;
                        border-radius: 20px;
                        font-size: 0.75rem;
                        font-weight: 500;
                        display: flex;
                        align-items: center;
                        gap: 6px;
                        border: 1px solid #e2e8f0;
                    }}
                    .job-tag span {{
                        font-size: 0.9rem;
                    }}
                    .job-card-desc {{
                        font-size: 0.85rem;
                        color: #4a4a4a;
                        line-height: 1.5;
                        margin-bottom: 15px;
                        display: -webkit-box;
                        -webkit-line-clamp: 3;
                        -webkit-box-orient: vertical;
                        overflow: hidden;
                    }}
                    </style>
                    """, unsafe_allow_html=True)
                    
                    # Keyed Container
                    with st.container(border=True, key=key):
                        # Construct HTML for valid values
                        location = job.location if job.location else "No definida"
                        mode = job.workMode if job.workMode else "No definido"
                        contract = job.contract_type_name if job.contract_type_name else "No definido"
                        salary = job.salary if job.salary else "A convenir"

                        # Clean description
                        desc = ""
                        if job.responsibilities:
                            desc = job.responsibilities.replace("\n", " ").strip()
                            if len(desc) > 200:
                                desc = desc[:200] + "..."

                        st.markdown(f"""
                        <div style="padding: 5px;">
                            <div class="job-card-title">{job.job_title}</div>
                            <div class="job-card-company">{job.company_name}</div>
                            <div class="job-tags-container">
                                <div class="job-tag"><span>📍</span> {location}</div>
                                <div class="job-tag"><span>🏠</span> {mode}</div>
                                <div class="job-tag"><span>💼</span> {contract}</div>
                            </div>
                            <div class="job-card-desc">{desc}</div>
                        </div>
                        """.replace("\n", ""), unsafe_allow_html=True)
                             
                        if st.button("Ver detalle ➜", key=f"btn_job_{i}", type="secondary", use_container_width=True):
                            st.session_state.detail_index = i
                        
                    
        with col_detail: 
            add_vertical_space(1)
            key = f"container-render_job_offer"

            st.markdown(
                f"""
                <style>
                    /* Selector para el container con la key específica */
                    .st-key-{key} {{
                        background-color: #f0f0f0 !important;  /* Cambia aquí el color de fondo */
                        border-radius: 1rem; /* Ejemplo de estilo adicional */
                        padding: 1rem;       /* Ejemplo de padding para que el cambio se note */
                    }}
                </style>
                """,
                unsafe_allow_html=True,
            )
            with st.container(border=True, key=key, height=900):    
                if st.session_state.jobs:
                    job_detail(st.session_state.jobs[st.session_state.detail_index]) 
                else:
                    st.write("No hay ofertas de empleos")                          