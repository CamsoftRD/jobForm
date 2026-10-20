import streamlit as st
import json
import os
import logging
import time as t
import re
from openai import OpenAI
from streamlit_extras.row import row
from streamlit_extras.add_vertical_space import add_vertical_space
import streamlit_antd_components as sac

from app.util import render_custom_fields_in_container, leer_pdf, file_to_base64, render_error_page
from app.core.api_jobs import apply_job_offert, fetch_jobs_offers
from app.core.api_educacion import fetch_grades
from app.fragments.captcha_frg import validate_captcha
from app.models.applicant_model import ApplicantModel

openai_api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(api_key=openai_api_key) if openai_api_key else None

# Prompt extendido para extraer la mayor cantidad de datos útiles del CV
PROMPT_ANALISIS_CV = """Con los datos de este texto:

Si la información proporcionada **no corresponde claramente a un currículum vitae (hoja de vida)**, genera exclusivamente el siguiente diccionario JSON:
"error": "La información proporcionada no corresponde a una hoja de vida"

Si la información **sí corresponde a un currículum vitae**, genera un diccionario JSON que siga estrictamente esta estructura de claves:

{
    "tipo_Identificacion": null,
    "identificacion": null,
    "primer_Nombre": "",
    "segundo_Nombre": "",
    "primer_Apellido": "",
    "segundo_Apellido": "",
    "email": "",
    "telefono": "",
    "ciudad": "",
    "carrera": "",
    "institucion": "",
    "experiencia_Total": "",
    "etiqueta": "",
    "comentario": "",
    "apreciacion": 0
}

Instrucciones para asignar el valor de tipo_Identificacion (entero):
    - Si identificacion contiene una cédula dominicana de 11 dígitos, asignar 1 a tipo_Identificacion.
    - Si identificacion corresponde a un pasaporte, asignar 5 a tipo_Identificacion.
    - Si no se encuentra, asignar null.

Instrucciones para campos adicionales:
    - ciudad: Ciudad o provincia de residencia si se menciona.
    - carrera: Carrera, profesión o especialidad principal del candidato.
    - institucion: Universidad, instituto o centro educativo principal.
    - experiencia_Total: Estimación de años de experiencia total (ej: "1-2 años", "3-5 años", "+5 años").
    - etiqueta: Hashtags con cualidades destacadas (ej: #liderazgo-#proactivo).
    - apreciacion: Evalúa del 1 al 5 según adecuación a los requisitos del puesto (1 bajo, 5 excelente).
    - comentario: Resumen conciso de la evaluación que finalice con "...✅" si es 4-5 estrellas o "...❌" si es 2 o menos.

Responde ÚNICAMENTE con el diccionario JSON sin explicaciones adicionales.
"""


def preguntar_al_modelo(texto: str, prompt_usuario: str, job: dict) -> str:
    """Analiza un CV usando OpenAI GPT-4."""
    if not client:
        return json.dumps({
            "error": "El servicio de OpenAI no está configurado (falta OPENAI_API_KEY). Puedes llenar el formulario manualmente."
        })
    try:
        max_cv_chars = 12000
        if len(texto) > max_cv_chars:
            texto = texto[:max_cv_chars] + "\n\n[Texto truncado por límite de tamaño]"

        job_info = {
            "titulo": job.get("job_title", ""),
            "descripcion": job.get("job_description", "")[:500],
            "requisitos": job.get("requirements", "")[:500],
            "responsabilidades": job.get("responsabilidades", "")[:500]
        }
        job_info_str = json.dumps(job_info, ensure_ascii=False)

        respuesta = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un asistente de reclutamiento que analiza CVs con precisión y extrae datos en formato JSON."},
                {"role": "user", "content": f"{prompt_usuario}\n\nContenido del documento:\n{texto}\n\nRequisitos del empleo:\n{job_info_str}"}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        return respuesta.choices[0].message.content
    except Exception as e:
        logging.error(f"Error al procesar CV con OpenAI: {e}")
        return json.dumps({
            "error": f"No se pudo procesar el CV automáticamente ({str(e)[:90]}). Completa los campos manualmente."
        })


def get_academic_grades_list():
    """Obtiene la lista de grados académicos desde la API con fallback seguro."""
    try:
        grados = fetch_grades()
        if isinstance(grados, list) and len(grados) > 0:
            return [(g.codigo, g.nombre) for g in grados if g.nombre]
    except Exception as e:
        logging.warning(f"No fue posible cargar grados académicos desde la API: {e}")

    # Fallback oficial estándar de República Dominicana
    return [
        (1, "Básica / Primaria"),
        (2, "Secundaria / Bachillerato"),
        (3, "Técnico Medio / Vocacional"),
        (4, "Técnico Superior / Tecnólogo"),
        (5, "Grado / Licenciatura / Ingeniería"),
        (6, "Postgrado / Especialidad"),
        (7, "Maestría"),
        (8, "Doctorado")
    ]


def init_applicant_session():
    """Inicializa el estado del solicitante y del stepper."""
    if "applicant_obj" not in st.session_state:
        st.session_state.applicant_obj = ApplicantModel()

    if "applicant_step" not in st.session_state:
        st.session_state.applicant_step = 0

    if "attached_cv_file" not in st.session_state:
        st.session_state.attached_cv_file = None

    if "attached_cv_name" not in st.session_state:
        st.session_state.attached_cv_name = None

    if "cv_autofilled" not in st.session_state:
        st.session_state.cv_autofilled = False

    if "valid_captcha" not in st.session_state:
        st.session_state["valid_captcha"] = True

    if "send_pressed" not in st.session_state:
        st.session_state["send_pressed"] = False

    # Valores iniciales para widgets con key (evita doble asignación de default_value)
    widget_defaults = {
        "app_tipo_identificacion": "1-Cédula",
        "app_identificacion": "",
        "app_primer_nombre": "",
        "app_segundo_nombre": "",
        "app_primer_apellido": "",
        "app_segundo_apellido": "",
        "app_genero": "No especificado",
        "app_fecha_nacimiento": "",
        "app_nacionalidad": "Dominicana",
        "app_telefono": "",
        "app_telefono_alt": "",
        "app_email": "",
        "app_ciudad": "",
        "app_direccion": "",
        "app_carrera": "",
        "app_institucion": "",
        "app_estado_estudios": "Graduado",
        "app_experiencia_total": "1 a 2 años",
        "app_expectativa_salarial": "",
        "app_disponibilidad": "Inmediata",
        "app_linkedin": "",
    }
    for k, v in widget_defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def populate_session_from_dict(data: dict):
    """Puebla el objeto ApplicantModel y las claves de widgets de Streamlit."""
    app: ApplicantModel = st.session_state.applicant_obj

    if data.get("primer_Nombre"):
        app.primer_Nombre = data["primer_Nombre"]
        st.session_state["app_primer_nombre"] = data["primer_Nombre"]

    if data.get("segundo_Nombre"):
        app.segundo_Nombre = data["segundo_Nombre"]
        st.session_state["app_segundo_nombre"] = data["segundo_Nombre"]

    if data.get("primer_Apellido"):
        app.primer_Apellido = data["primer_Apellido"]
        st.session_state["app_primer_apellido"] = data["primer_Apellido"]

    if data.get("segundo_Apellido"):
        app.segundo_Apellido = data["segundo_Apellido"]
        st.session_state["app_segundo_apellido"] = data["segundo_Apellido"]

    if data.get("identificacion"):
        app.identificacion = str(data["identificacion"])
        st.session_state["app_identificacion"] = str(data["identificacion"])

    if data.get("tipo_Identificacion") in [1, 5]:
        app.tipo_Identificacion = int(data["tipo_Identificacion"])
        st.session_state["app_tipo_identificacion"] = "1-Cédula" if data["tipo_Identificacion"] == 1 else "5-Pasaporte"

    if data.get("email"):
        app.email = data["email"]
        st.session_state["app_email"] = data["email"]

    if data.get("telefono"):
        app.telefono = data["telefono"]
        st.session_state["app_telefono"] = data["telefono"]

    if data.get("ciudad"):
        app.ciudad = data["ciudad"]
        st.session_state["app_ciudad"] = data["ciudad"]

    if data.get("carrera"):
        app.carrera = data["carrera"]
        st.session_state["app_carrera"] = data["carrera"]

    if data.get("institucion"):
        app.institucion = data["institucion"]
        st.session_state["app_institucion"] = data["institucion"]

    if data.get("experiencia_Total"):
        app.experiencia_Total = data["experiencia_Total"]
        st.session_state["app_experiencia_total"] = data["experiencia_Total"]

    if data.get("etiqueta"):
        app.etiqueta = data["etiqueta"]

    if data.get("comentario"):
        app.comentario = data["comentario"]

    if data.get("apreciacion"):
        app.apreciacion = int(data["apreciacion"])

    st.session_state.cv_autofilled = True


def sync_current_step_to_model(step_idx: int):
    """Sincroniza los valores ingresados en los widgets hacia el objeto ApplicantModel."""
    app: ApplicantModel = st.session_state.applicant_obj
    if step_idx == 0:
        if "app_primer_nombre" in st.session_state and st.session_state["app_primer_nombre"]:
            app.primer_Nombre = st.session_state["app_primer_nombre"]
        if "app_segundo_nombre" in st.session_state:
            app.segundo_Nombre = st.session_state["app_segundo_nombre"]
        if "app_primer_apellido" in st.session_state and st.session_state["app_primer_apellido"]:
            app.primer_Apellido = st.session_state["app_primer_apellido"]
        if "app_segundo_apellido" in st.session_state:
            app.segundo_Apellido = st.session_state["app_segundo_apellido"]
        if "app_identificacion" in st.session_state and st.session_state["app_identificacion"]:
            app.identificacion = st.session_state["app_identificacion"]
        if "app_tipo_identificacion" in st.session_state:
            app.tipo_Identificacion = int(st.session_state["app_tipo_identificacion"].split("-")[0])
        if "app_genero" in st.session_state:
            app.genero = st.session_state["app_genero"]
        if "app_fecha_nacimiento" in st.session_state:
            app.fecha_Nacimiento = st.session_state["app_fecha_nacimiento"]
        if "app_nacionalidad" in st.session_state:
            app.nacionalidad = st.session_state["app_nacionalidad"]

    elif step_idx == 1:
        if "app_telefono" in st.session_state and st.session_state["app_telefono"]:
            app.telefono = st.session_state["app_telefono"]
        if "app_telefono_alt" in st.session_state:
            app.telefono_Alternativo = st.session_state["app_telefono_alt"]
        if "app_email" in st.session_state and st.session_state["app_email"]:
            app.email = st.session_state["app_email"]
        if "app_ciudad" in st.session_state:
            app.ciudad = st.session_state["app_ciudad"]
        if "app_direccion" in st.session_state:
            app.direccion = st.session_state["app_direccion"]

    elif step_idx == 2:
        if "app_grado_academico" in st.session_state:
            app.grado_Nombre = st.session_state["app_grado_academico"]
        if "app_carrera" in st.session_state:
            app.carrera = st.session_state["app_carrera"]
        if "app_institucion" in st.session_state:
            app.institucion = st.session_state["app_institucion"]
        if "app_estado_estudios" in st.session_state:
            app.estado_Estudios = st.session_state["app_estado_estudios"]
        if "app_experiencia_total" in st.session_state:
            app.experiencia_Total = st.session_state["app_experiencia_total"]
        if "app_expectativa_salarial" in st.session_state:
            app.expectativa_Salarial = st.session_state["app_expectativa_salarial"]
        if "app_disponibilidad" in st.session_state:
            app.disponibilidad = st.session_state["app_disponibilidad"]
        if "app_linkedin" in st.session_state:
            app.linkedin_Url = st.session_state["app_linkedin"]


def validate_step(step_idx: int) -> bool:
    """Valida los campos obligatorios del paso actual antes de permitir avanzar."""
    sync_current_step_to_model(step_idx)
    app: ApplicantModel = st.session_state.applicant_obj

    if step_idx == 0:
        if not app.primer_Nombre.strip():
            st.error("El campo **Primer Nombre** es obligatorio.")
            return False
        if not app.primer_Apellido.strip():
            st.error("El campo **Primer Apellido** es obligatorio.")
            return False
        if not app.identificacion.strip():
            st.error("El campo **Número de Identificación** es obligatorio.")
            return False

    elif step_idx == 1:
        if not app.telefono.strip():
            st.error("El campo **Teléfono móvil / WhatsApp** es obligatorio.")
            return False
        if not app.email.strip():
            st.error("El campo **Correo Electrónico** es obligatorio.")
            return False
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", app.email.strip()):
            st.error("Por favor introduce un **Correo Electrónico** válido (ejemplo@correo.com).")
            return False

    return True


def apply_job(job_id, company_id):
    """Componente principal de aplicación a vacante con Stepper y captura extendida."""
    init_applicant_session()

    _, colmain, _ = st.columns([0.5, 3.5, 0.5])
    with colmain:
        with st.spinner("Cargando información del puesto..."):
            response = fetch_jobs_offers(company_id, job_id)

        if not response:
            render_error_page("¡Ups! Vacante no disponible", "No fue posible encontrar la información del empleo solicitado.")
            st.stop()

        if isinstance(response, dict) and response.get("error"):
            render_error_page("¡Ups! Algo salió mal", response.get("error"))
            st.stop()

        job = response if isinstance(response, dict) else response.__dict__

        # Botón volver
        if st.button("⬅ Volver a las ofertas", type="tertiary"):
            st.query_params.clear()
            st.query_params["page"] = "home"
            st.session_state.page = "home"
            st.rerun()

        # Cabecera de la postulación
        st.markdown(
            f"""
            <div style="background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); padding: 24px 28px; border-radius: 14px; color: white; margin-bottom: 24px; box-shadow: 0 4px 14px rgba(0,0,0,0.12);">
                <span style="background: #3b82f6; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px;">Postulación a Empleo</span>
                <h2 style="color: white; margin-top: 10px; margin-bottom: 6px; font-size: 1.8rem;">{job.get('job_title', 'Vacante')}</h2>
                <div style="color: #94a3b8; font-size: 0.95rem;">🏢 {job.get('company_name', '')} &nbsp;|&nbsp; 📍 {job.get('location', 'República Dominicana')} &nbsp;|&nbsp; 💼 {job.get('contract_type_name', 'Fijo')}</div>
            </div>
            """,
            unsafe_allow_html=True
        )

        # -------------------------------------------------------------
        # SECCIÓN DE AUTOCOMPLETADO INTELIGENTE (ASISTENTE IA)
        # -------------------------------------------------------------
        with st.expander("✨ ¿Deseas autocompletar este formulario con tu CV? (Recomendado)", expanded=not st.session_state.cv_autofilled):
            st.markdown(
                "Sube tu currículum en formato **PDF** para que nuestro asistente inteligente pre-llene automáticamente tus datos personales, de contacto y formación. **Podrás revisar y modificar cualquier campo antes de enviar.**"
            )
            cv_upload = st.file_uploader(
                "Selecciona tu CV (PDF)",
                type=["pdf"],
                key="cv_autofill_uploader",
                help="El archivo será procesado para autocompletar el formulario y adjuntado a tu postulación."
            )

            if cv_upload is not None:
                # Guardar referencia del archivo
                st.session_state.attached_cv_file = cv_upload
                st.session_state.attached_cv_name = cv_upload.name

                if not st.session_state.cv_autofilled:
                    with st.spinner("Analizando CV con Inteligencia Artificial..."):
                        try:
                            texto_pdf = leer_pdf(cv_upload)
                            if texto_pdf and len(texto_pdf.strip()) >= 40:
                                raw_json = preguntar_al_modelo(texto_pdf, PROMPT_ANALISIS_CV, job)
                                parsed_data = json.loads(raw_json)
                                if "error" in parsed_data:
                                    st.warning(parsed_data["error"])
                                else:
                                    populate_session_from_dict(parsed_data)
                                    st.success("¡Datos extraídos con éxito! Revisa cada paso a continuación.")
                                    t.sleep(1)
                                    st.rerun()
                            else:
                                st.warning("No se pudo extraer texto legible del PDF. Puedes continuar llenando el formulario manualmente.")
                        except Exception as e:
                            logging.error(f"Error procesando CV: {e}")
                            st.warning("No se pudo completar el análisis automático. Por favor, ingresa tus datos en los campos a continuación.")

        if st.session_state.attached_cv_name:
            st.info(f"📄 **CV adjunto:** `{st.session_state.attached_cv_name}` (Listo para ser enviado con tu solicitud)")

        st.markdown("---")

        # -------------------------------------------------------------
        # STEPPER DE NAVEGACIÓN
        # -------------------------------------------------------------
        step_items = [
            sac.StepsItem(title="1. Personal", subtitle="Nombre e ID", icon="person"),
            sac.StepsItem(title="2. Contacto", subtitle="Teléfono y correo", icon="telephone"),
            sac.StepsItem(title="3. Perfil & Estudios", subtitle="Grado y experiencia", icon="mortarboard"),
            sac.StepsItem(title="4. Preguntas & Envío", subtitle="Requisitos y envío", icon="send-check"),
        ]

        stepper_value = sac.steps(
            items=step_items,
            index=st.session_state.applicant_step,
            return_index=True,
            size="sm",
            color="blue",
            key="application_steps_widget"
        )

        # Si el usuario hace clic directo en un paso del stepper
        if stepper_value != st.session_state.applicant_step:
            sync_current_step_to_model(st.session_state.applicant_step)
            st.session_state.applicant_step = stepper_value
            st.rerun()

        current_step = st.session_state.applicant_step
        app: ApplicantModel = st.session_state.applicant_obj

        # -------------------------------------------------------------
        # CONTENIDO DE CADA PASO
        # -------------------------------------------------------------
        with st.container(border=True):

            # === PASO 0: DATOS PERSONALES ===
            if current_step == 0:
                st.subheader("Paso 1: Información Personal e Identificación")
                st.caption("Ingresa tus datos personales tal como figuran en tu documento de identidad.")

                col_id1, col_id2 = st.columns([1, 2])
                with col_id1:
                    tipo_id_options = ["1-Cédula", "5-Pasaporte"]
                    tipo_selected = st.selectbox(
                        "Tipo de Identificación *",
                        tipo_id_options,
                        key="app_tipo_identificacion"
                    )
                    app.tipo_Identificacion = int(tipo_selected.split("-")[0])

                with col_id2:
                    app.identificacion = st.text_input(
                        "Número de Identificación *",
                        placeholder="Ej. 001-20324456-5 o Pasaporte",
                        key="app_identificacion"
                    )

                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    app.primer_Nombre = st.text_input(
                        "Primer Nombre *",
                        placeholder="Ej. Juan",
                        key="app_primer_nombre"
                    )
                with col_n2:
                    app.segundo_Nombre = st.text_input(
                        "Segundo Nombre",
                        placeholder="Ej. Carlos",
                        key="app_segundo_nombre"
                    )

                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    app.primer_Apellido = st.text_input(
                        "Primer Apellido *",
                        placeholder="Ej. Pérez",
                        key="app_primer_apellido"
                    )
                with col_a2:
                    app.segundo_Apellido = st.text_input(
                        "Segundo Apellido",
                        placeholder="Ej. Gómez",
                        key="app_segundo_apellido"
                    )

                col_extra1, col_extra2, col_extra3 = st.columns([1.2, 1.2, 1.2])
                with col_extra1:
                    generos = ["No especificado", "Masculino", "Femenino"]
                    app.genero = st.selectbox("Género", generos, key="app_genero")

                with col_extra2:
                    app.fecha_Nacimiento = st.text_input(
                        "Fecha de Nacimiento",
                        placeholder="DD/MM/AAAA",
                        key="app_fecha_nacimiento"
                    )

                with col_extra3:
                    nacionalidades = ["Dominicana", "Extranjera con permiso", "Otra"]
                    app.nacionalidad = st.selectbox("Nacionalidad", nacionalidades, key="app_nacionalidad")

            # === PASO 1: CONTACTO Y UBICACIÓN ===
            elif current_step == 1:
                st.subheader("Paso 2: Datos de Contacto y Ubicación")
                st.caption("A través de estos medios te contactaremos para el proceso de selección.")

                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    app.telefono = st.text_input(
                        "Teléfono móvil / WhatsApp *",
                        placeholder="Ej. 809-555-1234",
                        key="app_telefono"
                    )
                with col_c2:
                    app.telefono_Alternativo = st.text_input(
                        "Teléfono alternativo o residencial",
                        placeholder="Ej. 809-555-5678",
                        key="app_telefono_alt"
                    )

                app.email = st.text_input(
                    "Correo Electrónico *",
                    placeholder="Ej. tu.nombre@correo.com",
                    key="app_email"
                )

                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    app.ciudad = st.text_input(
                        "Ciudad / Provincia de residencia",
                        placeholder="Ej. Santo Domingo, Santiago, etc.",
                        key="app_ciudad"
                    )
                with col_u2:
                    app.direccion = st.text_input(
                        "Sector o Dirección residencial",
                        placeholder="Ej. Ensanche Naco, Bella Vista, etc.",
                        key="app_direccion"
                    )

            # === PASO 2: FORMACIÓN Y EXPERIENCIA ===
            elif current_step == 2:
                st.subheader("Paso 3: Formación Académica y Perfil Laboral")
                st.caption("Completa tu formación académica y trayectoria profesional.")

                grados_list = get_academic_grades_list()
                grados_nombres = [g[1] for g in grados_list]

                # Asegurar valor en session_state si aún no existe
                if "app_grado_academico" not in st.session_state or st.session_state["app_grado_academico"] not in grados_nombres:
                    st.session_state["app_grado_academico"] = grados_nombres[0] if grados_nombres else ""

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    grado_sel_name = st.selectbox(
                        "Nivel Académico Máximo Alcanzado *",
                        grados_nombres,
                        key="app_grado_academico"
                    )
                    # Guardar código y nombre seleccionado
                    for cod, nom in grados_list:
                        if nom == grado_sel_name:
                            app.id_GradoAcademico = cod
                            app.grado_Nombre = nom
                            break

                with col_g2:
                    estados = ["Graduado", "En curso", "Incompleto / Pausado"]
                    app.estado_Estudios = st.selectbox("Estado de los estudios", estados, key="app_estado_estudios")

                col_f1, col_f2 = st.columns(2)
                with col_f1:
                    app.carrera = st.text_input(
                        "Carrera, Profesión o Área de Estudio",
                        placeholder="Ej. Licenciatura en Contabilidad, Ing. de Sistemas...",
                        key="app_carrera"
                    )
                with col_f2:
                    app.institucion = st.text_input(
                        "Institución / Universidad / Centro Educativo",
                        placeholder="Ej. UASD, INTEC, PUCMM, ITLA, etc.",
                        key="app_institucion"
                    )

                st.markdown("---")
                st.markdown("##### Experiencia y Expectativas")

                col_exp1, col_exp2 = st.columns(2)
                with col_exp1:
                    rangos_exp = ["Sin experiencia laboral", "Menos de 1 año", "1 a 2 años", "3 a 5 años", "Más de 5 años"]
                    app.experiencia_Total = st.selectbox("Años de experiencia laboral en áreas afines", rangos_exp, key="app_experiencia_total")

                with col_exp2:
                    app.expectativa_Salarial = st.text_input(
                        "Expectativa Salarial pretendida (RD$)",
                        placeholder="Ej. 45,000 - 55,000 o A convenir",
                        key="app_expectativa_salarial"
                    )

                col_disp1, col_disp2 = st.columns(2)
                with col_disp1:
                    disponibilidades = ["Inmediata", "En 15 días", "En 1 mes", "A convenir"]
                    app.disponibilidad = st.selectbox("Disponibilidad para iniciar", disponibilidades, key="app_disponibilidad")

                with col_disp2:
                    app.linkedin_Url = st.text_input(
                        "Enlace a LinkedIn o Portafolio Web (Opcional)",
                        placeholder="https://linkedin.com/in/tu-perfil",
                        key="app_linkedin"
                    )

            # === PASO 3: PREGUNTAS DE VACANTE Y ENVÍO ===
            elif current_step == 3:
                st.subheader("Paso 4: Preguntas del Puesto y Confirmación de Envío")
                st.caption("Responde las preguntas específicas de la vacante y confirma tu solicitud.")

                # Preguntas específicas de la vacante (customData de la requisición)
                customFields = []
                if "customData" in job and job["customData"]:
                    try:
                        strdata = str(job["customData"])
                        customFields = json.loads(strdata)
                    except Exception as e:
                        logging.warning(f"Error parseando customData del empleo: {e}")

                if customFields:
                    st.markdown("**Preguntas requeridas por la empresa para este puesto:**")
                    with st.container(border=True):
                        render_custom_fields_in_container(customFields, requeridos=False)
                    st.markdown("---")

                # Subida de CV si aún no lo ha subido
                if not st.session_state.attached_cv_file:
                    st.markdown("**Adjuntar Curriculum Vitae (Obligatorio para la revisión final):**")
                    final_cv_upload = st.file_uploader(
                        "Adjunta tu CV en formato PDF",
                        type=["pdf"],
                        key="final_cv_uploader"
                    )
                    if final_cv_upload is not None:
                        st.session_state.attached_cv_file = final_cv_upload
                        st.session_state.attached_cv_name = final_cv_upload.name
                        st.success(f"Archivo adjuntado: `{final_cv_upload.name}`")

                # Resumen previo al envío
                st.markdown("##### Resumen de tu Postulación")
                st.markdown(
                    f"""
                    - **Candidato:** {app.nombre_Completo or 'No especificado'}
                    - **Documento:** {('Cédula' if app.tipo_Identificacion == 1 else 'Pasaporte')}: `{app.identificacion or 'No especificada'}`
                    - **Contacto:** 📞 {app.telefono or 'No especificado'} &nbsp;|&nbsp; ✉️ {app.email or 'No especificado'}
                    - **Nivel Académico:** {app.grado_Nombre or 'No seleccionado'} {f'en {app.carrera}' if app.carrera else ''}
                    - **Experiencia:** {app.experiencia_Total or 'No especificada'}
                    - **Disponibilidad:** {app.disponibilidad or 'Inmediata'}
                    - **CV adjunto:** {f'`{st.session_state.attached_cv_name}`' if st.session_state.attached_cv_name else '⚠️ No adjuntado'}
                    """
                )

        # -------------------------------------------------------------
        # BOTONES DE NAVEGACIÓN (ANTERIOR / SIGUIENTE / ENVIAR)
        # -------------------------------------------------------------
        col_nav_prev, _, col_nav_next = st.columns([1, 1.5, 1.2])

        with col_nav_prev:
            if current_step > 0:
                if st.button("⬅ Anterior", use_container_width=True, type="secondary"):
                    sync_current_step_to_model(current_step)
                    st.session_state.applicant_step -= 1
                    st.rerun()

        with col_nav_next:
            if current_step < 3:
                if st.button("Siguiente ➔", use_container_width=True, type="primary"):
                    sync_current_step_to_model(current_step)
                    if validate_step(current_step):
                        st.session_state.applicant_step += 1
                        st.rerun()
            else:
                # Botón final de envío
                puede_enviar = bool(st.session_state.attached_cv_file)
                if st.button(
                    "Enviar Solicitud 🚀",
                    use_container_width=True,
                    type="primary",
                    disabled=not puede_enviar,
                    help="Debes adjuntar tu CV para poder enviar la solicitud" if not puede_enviar else None
                ):
                    sync_current_step_to_model(current_step)
                    st.session_state["send_pressed"] = True

        # -------------------------------------------------------------
        # PROCESO DE ENVÍO DE LA SOLICITUD
        # -------------------------------------------------------------
        if st.session_state.get("send_pressed"):
            st.session_state["send_pressed"] = False

            # Validar pasos anteriores por seguridad
            if not validate_step(0) or not validate_step(1):
                st.session_state.applicant_step = 0
                st.error("Por favor completa los campos obligatorios del Paso 1 y Paso 2.")
                st.rerun()

            # Capturar respuestas de customFields si existen
            custom_data_str = "[]"
            if "customData" in job and job["customData"]:
                try:
                    raw_fields = json.loads(str(job["customData"]))
                    if "customFields" in st.session_state:
                        session_data = json.loads(st.session_state.customFields)
                        for i, field in enumerate(raw_fields):
                            if field.get("fieldName") in session_data:
                                raw_fields[i]["value"] = session_data[field["fieldName"]]
                        custom_data_str = json.dumps(raw_fields)
                except Exception as e:
                    logging.warning(f"Error procesando customFields para envío: {e}")

            # Construir payload de la solicitud
            payload_data = app.to_solicitud_dict(job, custom_fields_json=custom_data_str)

            with st.spinner("Enviando tu postulación... Por favor espera un momento."):
                file_dict = None
                cv_file = st.session_state.get("attached_cv_file")
                if cv_file:
                    file_b64 = file_to_base64(cv_file)
                    file_dict = {
                        "attachedDocument": file_b64,
                        "fileExtension": cv_file.type.split("/")[-1] if "/" in cv_file.type else "pdf"
                    }

                response = apply_job_offert(data=payload_data, file=file_dict)

                if response.get("error"):
                    st.error(response.get("message", "No fue posible enviar la solicitud. Por favor intenta nuevamente."))
                else:
                    st.balloons()
                    st.success("🎉 ¡Tu postulación ha sido enviada exitosamente! Nuestro equipo de Recursos Humanos revisará tu perfil y te contactará pronto.")
                    t.sleep(4)
                    # Limpiar estado y redirigir
                    st.query_params.clear()
                    st.query_params["page"] = "home"
                    st.session_state.page = "home"
                    st.rerun()