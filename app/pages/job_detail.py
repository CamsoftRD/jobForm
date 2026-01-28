import streamlit as st
from app.models.job_model import JobModel
from streamlit_extras.add_vertical_space import add_vertical_space

# Ensure page config is set if accessed directly (though usually inherited)
# st.set_page_config(layout="wide")

def render_job_detail(job: JobModel):
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
        .detail-text-body {
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

    with st.container():
        st.markdown('<div class="detail-section-title">Acerca del empleo</div>', unsafe_allow_html=True)
        
        desc = job.job_description if job.job_description else "No hay descripción disponible."
        st.markdown(f'<div class="detail-text">{desc}</div>', unsafe_allow_html=True)
        
        add_vertical_space(1)
        
        # Apply Button
        st.link_button("Aplicar ahora", url=f"/apply?job_id={job.id}&comp={job.company_id}", icon=":material/send:", type="primary", use_container_width=True)

    with st.container():
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
    if st.button("⬅ Volver a ofertas", type="secondary"):
        st.session_state.page = "home"
        st.rerun()

    # 2. Check Session State
    if "selected_job" in st.session_state and st.session_state.selected_job:
        render_job_detail(st.session_state.selected_job)
    else:
        # Fallback / Error state
        st.warning("No se ha seleccionado ninguna oferta o la sesión ha expirado.")
        st.info("Por favor, regresa al listado de ofertas.")