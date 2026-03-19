import streamlit as st
import os
import base64
from app.models.job_model import JobModel
from streamlit_extras.add_vertical_space import add_vertical_space

# Ensure page config is set if accessed directly (though usually inherited)
# st.set_page_config(layout="wide")

def get_base64_image(image_path):
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    return None

def render_job_detail(job: JobModel):
    # Styling for job detail

    st.markdown("""
        <style>
        .block-container {
            padding-top: 3rem !important;
            padding-bottom: 0rem !important;
        }
        div.st-key-job_detail_card {
            background-color: #ffffff;
            padding: 50px !important;
            border-radius: 4px; 
            border: 1px solid #dcdfe6;
            box-shadow: 0 4px 20px rgba(0,0,0,0.08); 
            max-width: 900px; 
            margin: 0 auto; 
        }
        
        .detail-header {
            border-bottom: 2px solid #f0f2f6;
            padding-bottom: 20px;
            margin-bottom: 20px;
        }
        .detail-title-container {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-bottom: 10px;
        }
        .detail-title {
            font-size: 2.2rem;
            font-weight: 700;
            color: #1a1a1a;
            margin: 0;
        }
        .company-logo-detail {
            width: 40px;
            height: 40px;
            object-fit: contain;
            border-radius: 4px;
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
        .detail-text-body {
            font-size: 1rem;
            line-height: 1.6;
            color: #333;
        }
        </style>
    """, unsafe_allow_html=True)

    # Wrap everything in a main styled container using KEY
    with st.container(key="job_detail_card"):
        
        # Logo Logic
        logo_html = ""
        if job.imageUrl and job.imageUrl.startswith("http"):
            logo_html = f'<img src="{job.imageUrl}" class="company-logo-detail">'
        else:
            # Fallback to domain logo
            domain = st.session_state.get("domain_name", "company.com")
            icon_name = domain.split(".")[0]
            icon_path = f"app/assets/{icon_name}.png"
            if not os.path.exists(icon_path):
                icon_path = "app/assets/logo.png"
            
            img_b64 = get_base64_image(icon_path)
            if img_b64:
                logo_html = f'<img src="data:image/png;base64,{img_b64}" class="company-logo-detail">'

        # Header
        st.markdown(f"""
            <div class="detail-header">
                <div class="detail-title-container">
                    {logo_html}
                    <div class="detail-title">{job.job_title}</div>
                </div>
                <div class="detail-company">{job.company_name}</div>
            </div>
        """, unsafe_allow_html=True)
        
        # Metadata chips
        location = job.location if job.location else 'Ubicación no especificada'
        mode = job.workMode if job.workMode else 'No definido'
        contract = job.contract_type_name if job.contract_type_name else 'No definido'
        salary = f"{job.salary:,.2f}" if job.salary else "A convenir"

        st.markdown(f'''
        <div style="display: flex; gap: 15px; flex-wrap: wrap; margin-bottom: 20px;">
            <span style="background:#f0f2f6; padding:5px 10px; border-radius:15px;">📍 {location}</span>
            <span style="background:#f0f2f6; padding:5px 10px; border-radius:15px;">🏠 {mode}</span>
            <span style="background:#f0f2f6; padding:5px 10px; border-radius:15px;">💼 {contract}</span>
            <span style="background:#e6fffa; padding:5px 10px; border-radius:15px; color:#047857;">💰 {salary}</span>
        </div>
        ''', unsafe_allow_html=True)
 
        st.markdown('<div class="detail-section-title">Acerca del empleo</div>', unsafe_allow_html=True)
        
        desc = job.job_description if job.job_description else "No hay descripción disponible."
        st.markdown(f'<div class="detail-text">{desc}</div>', unsafe_allow_html=True)
        
        add_vertical_space(1)
        
        
        # Helper for apply navigation
        def go_to_apply(job_obj):
            # Extract ID and Company ID robustly (handle both dict and object)
            j_id = None
            c_id = None
            
            if isinstance(job_obj, dict):
                j_id = job_obj.get("id")
                c_id = job_obj.get("company_id")
            else:
                j_id = getattr(job_obj, "id", None)
                c_id = getattr(job_obj, "company_id", None)

            if j_id:
                st.query_params["job_id"] = str(j_id)
                if c_id:
                    st.query_params["comp"] = str(c_id)
                
                # Usar query_param para asegurar que app.py reconozca la navegación
                st.query_params["page"] = "apply"
                st.session_state.page = "apply"
        
        # Apply Button
        st.button("Aplicar ahora", icon=":material/send:", type="primary", use_container_width=True, on_click=go_to_apply, args=(job,))

        if job.requirements:
            st.markdown('<div class="detail-section-title">Requisitos</div>', unsafe_allow_html=True)
            # Formatting requirements as a list if they look like one, otherwise just text
            reqs = job.requirements.replace("\n", "<br>")
            st.markdown(f'<div class="detail-text-body">{reqs}</div>', unsafe_allow_html=True)
        
        if job.responsibilities:
            st.markdown('<div class="detail-section-title">Responsabilidades</div>', unsafe_allow_html=True)
            resps = job.responsibilities.replace("\n", "<br>")
            st.markdown(f'<div class="detail-text-body">{resps}</div>', unsafe_allow_html=True)

    add_vertical_space(2)


# --- Page Execution ---

# --- Page Execution ---
def job_detail_page():
    # 1. Back Button
    if st.button("⬅ Volver a ofertas", type="tertiary"):
        st.query_params.clear()
        st.query_params["page"] = "home"
        st.session_state.page = "home"
        st.rerun()

    # 2. Check Session State
    if "selected_job" in st.session_state and st.session_state.selected_job:
        render_job_detail(st.session_state.selected_job)
    else:
        # Fallback / Error state
        st.warning("No se ha seleccionado ninguna oferta o la sesión ha expirado.")
        st.info("Por favor, regresa al listado de ofertas.")