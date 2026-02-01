import streamlit as st
from app.core.api_jobs import fetch_jobs_offers, fetch_jobs_offers_by_group
from st_keyup import st_keyup
import streamlit_antd_components as sac

from streamlit_extras.row import row
from streamlit_extras.add_vertical_space import add_vertical_space
from streamlit_extras.bottom_container import bottom
from datetime import datetime
import json, os




@st.fragment()
def no_jobs():
    import base64
    
    # Custom CSS for the modern look
    st.markdown("""
        <style>
        /* General styling for the page background if needed, 
           but we focus on the card */
           
        .company-logo-container {
            width: 100px;
            height: 100px;
            background: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05);
            margin: 0 auto 1.5rem auto; /* Center horizontally */
            padding: 0.8rem;
            border: 1px solid #f0f0f0;
        }
        
        .company-logo-img {
            max-width: 80%;
            max-height: 80%;
            object-fit: contain;
        }
        
        div[data-testid="stVerticalBlockBorderWrapper"] {
             background-color: #ffffff;
             border-radius: 16px;
             border: 1px solid #e5e7eb;
             box-shadow: 0 10px 40px -10px rgba(0,0,0,0.08);
             padding: 2rem;
             max-width: 700px;
             margin: 2rem auto;
        }
        
        /* Hide default border if we want to override completely 
           (Streamlit v1.30+ might behave differently, but usually this targets the border=True container)
        */
        
        .no-jobs-header {
            text-align: center;
            margin-bottom: 2rem;
        }
        
        .no-jobs-title {
            font-family: 'Inter', system-ui, sans-serif;
            font-size: 1.8rem;
            font-weight: 700;
            color: #111827;
            margin-bottom: 0.5rem;
        }
        
        .no-jobs-subtitle {
            font-family: 'Inter', system-ui, sans-serif;
            font-size: 1rem;
            color: #6b7280;
            line-height: 1.5;
            max-width: 90%;
            margin: 0 auto;
        }
        
        .subscription-section {
            margin-top: 2rem;
            padding-top: 2rem;
            border-top: 1px dashed #e5e7eb;
        }
        
        .footer-text {
            text-align: center;
            color: #9ca3af;
            font-size: 0.75rem;
            margin-top: 2rem;
        }

        </style>
    """, unsafe_allow_html=True)

    # Get Company Info safely
    domain = st.session_state.get("domain_name", "company.com")
    if domain:
        icon_name = domain.split(".")[0]
        company_name = icon_name.replace("-", " ").title()
    else:
        icon_name = "logo"
        company_name = "Nuestra Empresa"
    
    # Logic for Image
    def get_base64_image(image_path):
        if os.path.exists(image_path):
             with open(image_path, "rb") as img_file:
                return base64.b64encode(img_file.read()).decode()
        return None

    icon_path = f"app/assets/{icon_name}.png"
    if not os.path.exists(icon_path):
        icon_path = "app/assets/logo.png" # Fallback
        
    img_b64 = get_base64_image(icon_path)
    
    # Main Unified Card
    with st.container(border=True):
        
        # 1. Branding Header (HTML)
        st.markdown(f"""
            <div class="no-jobs-header">
                <div class="company-logo-container">
                    <img src="data:image/png;base64,{img_b64}" class="company-logo-img" alt="{company_name}">
                </div>
                <div class="no-jobs-title">No hay vacantes disponibles</div>
                <div class="no-jobs-subtitle">
                    En este momento <strong>{company_name}</strong> no tiene procesos de selección activos.
                    <br>Únete a nuestra base de talentos para ser contactado en el futuro.
                </div>
            </div>
            <div class="subscription-section"></div>
        """, unsafe_allow_html=True)
        
        # 2. Subscription Form (Native Widgets) - Centered
        # Use columns to constrain width inside the card
        c_fill_l, c_content, c_fill_r = st.columns([1, 4, 1])
        
        with c_content:
            st.markdown("##### 📩 Mantente informado")
            st.markdown("<div style='margin-bottom: 8px; font-size: 0.9rem; color: #555;'>Déjanos tu correo para recibir alertas de nuevas vacantes.</div>", unsafe_allow_html=True)
            
            email = st.text_input("Correo electrónico", placeholder="nombre@ejemplo.com", label_visibility="collapsed")
            
            if st.button("Unirme a la lista de espera", type="primary", use_container_width=True):
                 if email and "@" in email:
                     # Here you would typically save to DB
                     st.balloons()
                     st.success("¡Gracias! Hemos guardado tu contacto exitosamente.")
                 else:
                     st.error("Por favor ingresa un correo electrónico válido.")

        # 3. Footer (HTML)
        st.markdown(
            f"""
            <div class="footer-text">
                &copy; {datetime.now().year} {company_name} • Powered by Triple
            </div>
            """, 
            unsafe_allow_html=True
        )

def home(grupo_economico):
    
    # ------------------------------
    # Detectar dispositivo PRIMERO
    # ------------------------------
    try:
        user_agent = st.context.headers.get("user-agent", "").lower()
        if "mobile" in user_agent:
            dispositivo = "movil"
        elif "android" in user_agent and "mobile" not in user_agent:
            dispositivo = "tablet"
        elif "ipad" in user_agent or "tablet" in user_agent:
            dispositivo = "tablet"
        else:
            dispositivo = "pc"
    except:
        dispositivo = "pc"
    
    is_mobile = dispositivo == "movil"
    is_mobile=True
    
    # DEBUG: Validating mobile state
    # st.write(f"DEBUG: is_mobile={is_mobile}, device={dispositivo}")
 
    #with st.spinner():
    #jobs_original = fetch_jobs_offers(company_id=company_id)
    jobs_original = fetch_jobs_offers_by_group(id_grupo_economico=grupo_economico)
    
    # Responsive CSS based on device type
    if is_mobile:
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 3rem !important;
                    padding-left: 0.5rem !important;
                    padding-right: 0.5rem !important;
                    padding-bottom: 0rem !important;
                }
                
                /* Reducir espacio entre elementos en móvil */
                .element-container {
                    margin-bottom: 0.1rem !important;
                }
                
                /* Asegurar que no haya scroll horizontal */
                .main {
                    overflow-x: hidden !important;
                }
                
                /* Reducir altura del search input en móvil */
                iframe[title="st_keyup.st_keyup"] {
                    height: 38px !important;
                    min-height: 38px !important;
                }
            </style>
            """, unsafe_allow_html=True)
    else:
        # Desktop CSS
        st.markdown("""
            <style>
                .block-container {
                    padding-top: 3rem !important;
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

    if "mobile_show_detail" not in st.session_state:
        st.session_state.mobile_show_detail = False

    # --- HEADER SECTION (Logo & Filters) ---
    
    # Get icon name for both layouts
    icon_name = st.session_state['domain_name'].split('.')[0]
    icon_path = f"app/assets/{icon_name}.png" if os.path.exists(f"app/assets/{icon_name}.png") else "app/assets/logo.png"
    
    if is_mobile:
        # Mobile: Logo + Search en la misma fila
        col_logo, col_search = st.columns([0.4, 0.6], vertical_alignment="bottom")
        
        with col_logo:
            st.image(icon_path, width=40)
        
        with col_search:
            filtro_texto = st_keyup(
                "Buscar", 
                value="",
                placeholder="🔍 Buscar empleos...", 
                label_visibility="collapsed", 
                key="mi_input",
                debounce=400
            )
            if filtro_texto and len(filtro_texto) < 3:
                filtro_texto = ""
            elif filtro_texto:
                filtro_texto = filtro_texto.lower()
        
        st.markdown("<div style='margin-bottom: 0.3rem;'></div>", unsafe_allow_html=True)
    else:
        # Desktop: Original layout with both logos
        c_logo, c_filters_container, c_triple = st.columns([0.05, 0.95, 0.08], vertical_alignment="top")
        
        with c_logo:
            st.image(icon_path, width=60)

        with c_triple:
            st.image("app/assets/logo_triple.png", width=120) 

    # Initialize filter variables
    filtro_texto = ""
    filtro_compania = "Todos"
    filtro_modalidad = "Todos"
    filtro_tipo_contrato = "Todos"

    if is_mobile:
        # MOBILE LAYOUT: Chips apilados verticalmente sin header para ahorrar espacio
        filtro_modalidad = sac.chip(
            items=[
                sac.ChipItem('Todos', icon='filter-circle'),
                sac.ChipItem('Remoto', icon='house-door'),
                sac.ChipItem('Presencial', icon='building'),
            ],
            label='Modalidad',
            index=0,
            align='start',
            radius='sm',
            size='xs',
            variant='light',
            key="filter_modalidad"
        )
        
        filtro_tipo_contrato = sac.chip(
            items=[
                sac.ChipItem('Todos', icon='filter-circle'),
                sac.ChipItem('Fijo', icon='briefcase'),
                sac.ChipItem('Temporal', icon='clock'),
            ],
            label='Tipo Contrato',
            index=0,
            align='start',
            radius='sm',
            size='xs',
            variant='light',
            key="filter_tipo_contrato"
        )
        
        # Ensure filters are not None
        if not filtro_modalidad:
            filtro_modalidad = "Todos"
        if not filtro_tipo_contrato:
            filtro_tipo_contrato = "Todos"
            
        # Minimal spacing
        st.markdown("<div style='margin-bottom: 0.2rem;'></div>", unsafe_allow_html=True)
        
    else:
        # DESKTOP LAYOUT: Original horizontal layout
        with c_filters_container:
            # Row 2: Chips + Search
            st.markdown("<span style='font-size: 0.9rem; font-weight: 600; color: #555; margin-right: 10px;'>Filtrar por:</span>", unsafe_allow_html=True)
            
            # 3 Columns: Modalidad | Tipo Contrato | Search
            c_chip_1, c_chip_2, c_search = st.columns([0.35, 0.35, 0.3], vertical_alignment="bottom")
            
            with c_chip_1:
                # Modalidad
                filtro_modalidad = sac.chip(
                    items=[
                        sac.ChipItem('Todos', icon='filter-circle'),
                        sac.ChipItem('Remoto', icon='house-door'),
                        sac.ChipItem('Presencial', icon='building'),
                    ],
                    label='Modalidad',
                    index=0,
                    align='start',
                    radius='md',
                    size='sm',
                    variant='light',
                    key="filter_modalidad"
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
                    index=0,
                    align='start',
                    radius='md',
                    size='sm',
                    variant='light',
                    key="filter_tipo_contrato"
                )
            
            with c_search:
                # CSS HACK: Force the iframe height to be smaller
                st.markdown("""
                <style>
                iframe[title="st_keyup.st_keyup"] {
                    height: 40px !important;
                    min-height: 40px !important;
                }
                </style>
                """, unsafe_allow_html=True)

                # Search Input next to chips
                filtro_texto = st_keyup(
                    "Buscar", 
                    value="",
                    placeholder="🔍 Buscar...", 
                    label_visibility="collapsed", 
                    key="mi_input",
                    debounce=400
                )

                # Logic: If text length < 3, treat as empty (no filter)
                if filtro_texto and len(filtro_texto) < 3:
                    filtro_texto = ""
                elif filtro_texto:
                    filtro_texto = filtro_texto.lower()
            
            # Ensure filters are not None to avoid AttributeError
            if not filtro_modalidad:
                filtro_modalidad = "Todos"
            if not filtro_tipo_contrato:
                filtro_tipo_contrato = "Todos"
    
    # ... (Filtering Logic skips here) ...
    
    # --- PROCESSING FILTER LOGIC ---
    filtered_jobs = []
    
    # Get company from session state if it exists (though selectbox was removed, we keep this safe in case of re-addition or internal logic)
    # Since selectbox was removed, filtro_compania remains "Todos" by default as initialized above.

    for job in jobs_original:
        # Filtrar por texto (Search across multiple fields)
        search_corpus = [
            job.job_title,
            job.job_description,
            job.requirements,
            job.responsibilities,
            job.company_name,
            job.location,
            job.workMode,
            job.contract_type_name
        ]
        # Join all valid strings into one lower-case block for easy searching
        full_text = " ".join([str(s).lower() for s in search_corpus if s])
        
        texto_valido = (filtro_texto in full_text) if filtro_texto else True
        
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
            
    else:
        # Main List View (Full Width)
        col_list_container = st.container()

        with col_list_container:
                # Logo removed from here (it was lines 290-293)
                
                keyc = f"container-scroll-hide"


                st.markdown(
                    f"""
                    <style>
                        .st-key-{keyc} {{
                            overflow: auto !important;
                            scrollbar-width: none;
                            padding-right: 10px;
                        }}
                        .st-key-{keyc}::-webkit-scrollbar {{
                            display: none;
                        }}
                    </style>
                    """,
                    unsafe_allow_html=True,
                )

                # Helper to handle navigation
                def nav_to_detail(job_obj):

                    # Fetch full details to ensure we have description/requirements not truncated by list view
                    with st.spinner("Cargando detalles..."):
                        # Ensure company_id is valid (not None) before API call
                        if hasattr(job_obj, 'id') and hasattr(job_obj, 'company_id') and job_obj.company_id:
                            try:
                                full_job = fetch_jobs_offers(company_id=job_obj.company_id, job_id=job_obj.id)
                                
                                # Check for error dict or empty result
                                if isinstance(full_job, dict) and "error" in full_job:
                                    print(f"Error fetching detail: {full_job['error']}")
                                    st.session_state.selected_job = job_obj # Fallback
                                elif full_job:
                                    # Handle list vs object return
                                    if isinstance(full_job, list):
                                        st.session_state.selected_job = full_job[0] if len(full_job) > 0 else job_obj
                                    else:
                                        st.session_state.selected_job = full_job
                                else:
                                    st.session_state.selected_job = job_obj # Fallback if None
                            except Exception as e:
                                print(f"Exception in nav_to_detail: {e}")
                                st.session_state.selected_job = job_obj
                        else:
                             print("Missing company_id or id, using basic object")
                             st.session_state.selected_job = job_obj
                    
                    # Clear params LAST to avoid interrupting the logic above if it triggers reruns
                    st.query_params.clear()
                    st.session_state.page = "job"
                    
                # Apply helper
                def apply_action(job_obj):
                    if hasattr(job_obj, 'id'):
                        st.query_params["job_id"] = str(job_obj.id)
                        if hasattr(job_obj, 'company_id'):
                            st.query_params["comp"] = str(job_obj.company_id)
                        st.session_state.page = "apply"

                # Responsive container height
                container_height = 600 if is_mobile else 900
                
                with st.container(height=container_height, border=False, key=keyc):
                    for i, job in enumerate(st.session_state.jobs):
                        
                        key = f"job-card-{i}"
                        
                        # Responsive CSS based on device
                        if is_mobile:
                            # MOBILE CSS: Optimized for small screens
                            st.markdown(f"""
                            <style>
                            div.st-key-{key} {{
                                background-color: #fafafa !important;
                                border: 1px solid #e1e1e1 !important;
                                border-radius: 10px;
                                padding: 0.75rem !important;
                                margin-bottom: 15px !important;
                                box-shadow: none !important;
                            }}
                            div.st-key-{key}:hover {{
                                background-color: #F3F6F8 !important;
                                border-color: #ccc !important;
                            }}
                            
                            .job-title-aldaba {{
                                font-family: Arial, Helvetica, sans-serif;
                                font-size: 16px !important;
                                font-weight: 700;
                                color: #000;
                                margin-bottom: 10px !important;
                                margin-top: 0px !important;
                                line-height: 1.3;
                            }}
                            
                            .company-row {{
                                display: flex;
                                flex-direction: column !important;
                                align-items: flex-start !important;
                                gap: 6px !important;
                                font-family: Arial, sans-serif;
                                font-size: 12px !important;
                                color: #666;
                                margin-bottom: 12px !important;
                            }}
                            
                            .verified-badge {{
                                color: #72b028;
                                font-weight: 700;
                                display: flex;
                                align-items: center;
                                gap: 4px;
                            }}

                            .location-text {{
                                color: #666;
                                font-weight: 600;
                                display: flex;
                                align-items: center;
                                gap: 4px;
                            }}

                            .meta-right {{
                                margin-left: 0 !important;
                                display: flex;
                                gap: 10px;
                            }}
                            
                            .job-desc-aldaba {{
                                font-family: Arial, sans-serif;
                                font-size: 12px !important;
                                color: #000;
                                line-height: 1.4;
                                margin-bottom: 15px !important;
                                display: -webkit-box;
                                -webkit-line-clamp: 2 !important;
                                -webkit-box-orient: vertical;
                                overflow: hidden;
                            }}
                            
                            /* Mobile button styling - full width and touch-friendly */
                            .stButton > button {{
                                width: 100% !important;
                                height: 44px !important;
                                font-size: 14px !important;
                                padding: 10px !important;
                                border-radius: 8px !important;
                                font-weight: 600 !important;
                                margin-bottom: 8px !important;
                            }}
                            </style>
                            """, unsafe_allow_html=True)
                        else:
                            # DESKTOP CSS: Original styling
                            st.markdown(f"""
                            <style>
                            div.st-key-{key} {{
                                background-color: #fafafa !important;
                                border: 1px solid #e1e1e1 !important;
                                border-radius: 12px;
                                padding: 0px !important;
                                margin-bottom: 25px;
                                box-shadow: none !important; 
                                padding: 1rem !important;
                            }}
                            div.st-key-{key}:hover {{
                                background-color: #F3F6F8 !important;
                                border-color: #ccc !important;
                            }}
                            
                            .job-title-aldaba {{
                                font-family: Arial, Helvetica, sans-serif;
                                font-size: 18px;
                                font-weight: 700;
                                color: #000;
                                margin-bottom: 8px;
                                margin-top: 5px;
                            }}
                            
                            .company-row {{
                                display: flex;
                                align-items: center;
                                gap: 15px;
                                font-family: Arial, sans-serif;
                                font-size: 13px;
                                color: #666;
                                margin-bottom: 15px;
                            }}
                            
                            .verified-badge {{
                                color: #72b028;
                                font-weight: 700;
                                display: flex;
                                align-items: center;
                                gap: 4px;
                            }}

                            .location-text {{
                                color: #666;
                                font-weight: 700; 
                                display: flex;
                                align-items: center;
                                gap: 4px;
                            }}

                            .meta-right {{
                                margin-left: auto; 
                                display: flex;
                                gap: 15px;
                            }}
                            
                            .job-desc-aldaba {{
                                font-family: Arial, sans-serif;
                                font-size: 13px;
                                color: #000;
                                line-height: 1.5;
                                margin-bottom: 20px;
                                display: -webkit-box;
                                -webkit-line-clamp: 4; 
                                -webkit-box-orient: vertical;
                                overflow: hidden;
                            }}
                            
                            .action-row {{
                                display: flex;
                                align-items: center;
                                gap: 20px;
                                font-family: Arial, sans-serif;
                                font-size: 11px;
                                color: #333;
                                padding-top: 10px;
                                border-top: 0px solid #eee; 
                            }}
                            
                            .date-text {{
                                color: #666;
                                font-weight: 400;
                                margin-right: 15px;
                            }}
                            
                            /* Custom Button/Link Styling */
                            .stButton > button {{
                                border: none !important;
                                background: transparent !important;
                                color: #000 !important;
                                padding: 0px !important;
                                font-size: 11px !important;
                                height: auto !important;
                                font-weight: normal !important;
                                text-decoration: none !important;
                            }}
                            .stButton > button:hover {{
                                 color: #e33b1e !important;
                                 text-decoration: underline !important;
                            }}
                            
                            .bold-link > div > button {{
                                font-weight: 700 !important;
                            }}
                            
                            </style>
                            """, unsafe_allow_html=True)
                        
                        # Content Logic
                        location = job.location if job.location else "Distrito Nacional"
                        # Handle long location names
                        if len(location) > 30:
                            location = location[:30] + "..."
                            
                        mode = job.workMode if job.workMode else "Completa"
                        contract = job.contract_type_name if job.contract_type_name else "Fijo"
                        
                        company_display = job.company_name if job.company_name else "Confidencial"
                        # Logic: If confidential, show Verified badge + Confidencial. Else show Company Name + Verified.
                        # For exact match to image "Operador de CCTV" example: "✔ Confidencial ... Distrito Nacional ... Completa ... Técnico"
                        
                        # Date
                        date_str = "27-01-2026"
                        if job.creation_date:
                            try:
                                date_str = str(job.creation_date).split("T")[0]
                                # Reformat to DD-MM-YYYY
                                parts = date_str.split("-")
                                if len(parts) == 3:
                                    date_str = f"{parts[2]}-{parts[1]}-{parts[0]}"
                            except:
                                pass

                        desc = ""
                        if job.responsibilities:
                            desc = " ".join(job.responsibilities.split())
                        elif job.job_description:
                            desc = " ".join(job.job_description.split())
                        
                        # Truncate visually but provide enough text
                        if len(desc) > 600:
                            desc = desc[:600] + " [...]"

                        # Keyed Container
                        with st.container(border=True, key=key):
                            
                            st.markdown(f"""
<div style="padding: 25px 25px 10px 25px;">
<div class="job-title-aldaba">{job.job_title}</div>
<div class="company-row">
<div class="verified-badge">✔ {company_display}</div>
<div class="location-text"><span style="color:#999; margin-right:4px;">🏢</span> {location}</div>
<div class="meta-right">
<span>{mode}</span>
<span>{contract}</span>
</div>
</div>
<div class="job-desc-aldaba">{desc}</div>
</div>
""", unsafe_allow_html=True)
                            
                            
                            # Responsive button layout
                            if is_mobile:
                                # MOBILE: Stacked buttons for better touch experience
                                st.button(
                                    "📄 Ver detalles completos", 
                                    key=f"btn_detail_{i}", 
                                    on_click=nav_to_detail, 
                                    args=(job,), 
                                    use_container_width=True, 
                                    type="primary"
                                )
                                
                                st.button(
                                    "✉️ Enviar currículum", 
                                    key=f"btn_apply_{i}", 
                                    on_click=apply_action, 
                                    args=(job,),
                                    use_container_width=True, 
                                    type="secondary"
                                )
                                
                                # Date at the end, as caption
                                st.caption(f"📅 Publicado: {date_str}")
                                
                            else:
                                # DESKTOP: Original horizontal layout
                                # Columns: Date (narrow) | Enviar (fit) | Mas Info (fit) | Contactar (fit)
                                _, c_date, c_b1, c_b2, c_b3, _ = st.columns([0.03, 0.15, 0.2, 0.2, 0.3, 0.5])
                                
                                with c_date:
                                    st.button(f"**{date_str}**", key=f"btn_date_{i}", type="tertiary")

                                with c_b1:
                                    st.button("Enviar currículum", key=f"btn_apply_{i}", on_click=apply_action, args=(job,), type="tertiary")

                                with c_b2:
                                    st.button("Más información", key=f"btn_more_{i}", on_click=nav_to_detail, args=(job,))
                                
                                with c_b3:
                                    st.button("Contactar empresa", key=f"btn_contact_{i}", disabled=True)
                            
        # Footer
        with bottom():
             st.markdown(
                "<div style='text-align: center; color: #aaa; font-size: 11px; padding: 10px;'>Powered by <strong>Tirple</strong></div>",
                unsafe_allow_html=True
            )
                          