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
    "genero": "",
    "fecha_Nacimiento": "",
    "email": "",
    "telefono": "",
    "ciudad": "",
    "direccion": "",
    "carrera": "",
    "institucion": "",
    "periodo_Estudio": "",
    "experiencia_Total": "",
    "experiencias_Laborales": [
        {
            "empresa": "",
            "puesto": "",
            "duracion": "",
            "funciones": ""
        }
    ],
    "expectativa_Salarial": "",
    "etiqueta": "",
    "comentario": "",
    "apreciacion": 0
}

Instrucciones para asignar el valor de tipo_Identificacion (entero):
    - Si identificacion contiene una cédula dominicana de 11 dígitos, asignar 1 a tipo_Identificacion.
    - Si identificacion corresponde a un pasaporte, asignar 5 a tipo_Identificacion.
    - Si no se encuentra, asignar null.

Instrucciones para campos adicionales:
    - genero: "Masculino" o "Femenino" si se puede deducir del perfil, de lo contrario null.
    - fecha_Nacimiento: Fecha de nacimiento en formato DD/MM/AAAA si está disponible.
    - ciudad: Ciudad o provincia de residencia si se menciona.
    - direccion: Sector, barrio o dirección de residencia si se menciona.
    - carrera: Carrera, profesión o especialidad principal del candidato.
    - institucion: Universidad, instituto o centro educativo principal.
    - periodo_Estudio: Años o período en los que cursó los estudios (ej: "2018 - 2022").
    - experiencia_Total: Estimación de años de experiencia total (ej: "1 a 2 años", "3 a 5 años", "Más de 5 años").
    - experiencias_Laborales: Lista con las experiencias laborales que aparecen en el CV (máximo 4 más recientes). Para cada una extraer:
        * empresa: Nombre de la empresa o institución.
        * puesto: Cargo o posición desempeñada.
        * duracion: Tiempo o fechas en el puesto (ej: "Ene 2021 - Dic 2023" o "2 años").
        * funciones: Resumen conciso de responsabilidades y tareas principales.
    - expectativa_Salarial: Expectativa salarial pretendida si se menciona.
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
            max_tokens=1200
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


def format_cedula(value: str) -> str:
    """Formatea una cédula dominicana de 11 dígitos al formato estándar 001-0000000-0."""
    if not value:
        return ""
    digits = re.sub(r"\D", "", value)[:11]
    if len(digits) > 10:
        return f"{digits[:3]}-{digits[3:10]}-{digits[10]}"
    elif len(digits) > 3:
        return f"{digits[:3]}-{digits[3:]}"
    return digits


def format_pasaporte(value: str) -> str:
    """Formatea un pasaporte limpiando caracteres no alfanuméricos y en mayúsculas."""
    if not value:
        return ""
    return re.sub(r"[^A-Za-z0-9]", "", value).upper()[:20]


def init_applicant_session():
    """Inicializa el estado del solicitante y del stepper."""
    if "applicant_obj" not in st.session_state:
        st.session_state.applicant_obj = ApplicantModel()

    if not hasattr(st.session_state.applicant_obj, "experiencias_Laborales") or st.session_state.applicant_obj.experiencias_Laborales is None:
        st.session_state.applicant_obj.experiencias_Laborales = []

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


def populate_session_from_dict(data: dict):
    """Puebla el objeto ApplicantModel con los datos extraídos por la IA."""
    app: ApplicantModel = st.session_state.applicant_obj

    if data.get("primer_Nombre"):
        app.primer_Nombre = str(data["primer_Nombre"]).strip()
    if data.get("segundo_Nombre"):
        app.segundo_Nombre = str(data["segundo_Nombre"]).strip()
    if data.get("primer_Apellido"):
        app.primer_Apellido = str(data["primer_Apellido"]).strip()
    if data.get("segundo_Apellido"):
        app.segundo_Apellido = str(data["segundo_Apellido"]).strip()

    if data.get("tipo_Identificacion") in [1, 5]:
        app.tipo_Identificacion = int(data["tipo_Identificacion"])

    if data.get("identificacion"):
        raw_id = str(data["identificacion"])
        app.identificacion = format_cedula(raw_id) if app.tipo_Identificacion == 1 else format_pasaporte(raw_id)

    if data.get("genero"):
        gen_str = str(data["genero"]).strip().capitalize()
        if gen_str in ["Masculino", "Hombre"]:
            app.genero = "Masculino"
        elif gen_str in ["Femenino", "Mujer"]:
            app.genero = "Femenino"

    if data.get("fecha_Nacimiento"):
        app.fecha_Nacimiento = str(data["fecha_Nacimiento"]).strip()

    if data.get("email"):
        app.email = str(data["email"]).strip()
    if data.get("telefono"):
        app.telefono = str(data["telefono"]).strip()
    if data.get("ciudad"):
        app.ciudad = str(data["ciudad"]).strip()
    if data.get("direccion"):
        app.direccion = str(data["direccion"]).strip()
    if data.get("carrera"):
        app.carrera = str(data["carrera"]).strip()
    if data.get("institucion"):
        app.institucion = str(data["institucion"]).strip()
    if data.get("periodo_Estudio"):
        app.periodo_Estudio = str(data["periodo_Estudio"]).strip()
    if data.get("experiencia_Total"):
        app.experiencia_Total = str(data["experiencia_Total"]).strip()

    if data.get("experiencias_Laborales") and isinstance(data["experiencias_Laborales"], list):
        parsed_exps = []
        for exp in data["experiencias_Laborales"]:
            if isinstance(exp, dict):
                parsed_exps.append({
                    "empresa": str(exp.get("empresa", "")).strip(),
                    "puesto": str(exp.get("puesto", "")).strip(),
                    "duracion": str(exp.get("duracion", "")).strip(),
                    "funciones": str(exp.get("funciones", "")).strip()
                })
        if parsed_exps:
            app.experiencias_Laborales = parsed_exps

    if data.get("expectativa_Salarial"):
        app.expectativa_Salarial = str(data["expectativa_Salarial"]).strip()
    if data.get("etiqueta"):
        app.etiqueta = str(data["etiqueta"]).strip()
    if data.get("comentario"):
        app.comentario = str(data["comentario"]).strip()
    if data.get("apreciacion"):
        try:
            app.apreciacion = int(data["apreciacion"])
        except Exception:
            app.apreciacion = 0

    st.session_state.cv_autofilled = True


def validate_step(step_idx: int) -> bool:
    """Valida los campos obligatorios del paso actual antes de permitir avanzar."""
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

        if app.tipo_Identificacion == 1:
            digits = re.sub(r"\D", "", app.identificacion)
            if len(digits) != 11:
                st.error("La **Cédula de Identidad** debe contener exactamente 11 dígitos (ejemplo: 001-2032445-6).")
                return False
        else:
            if len(app.identificacion.strip()) < 5:
                st.error("El **Pasaporte** debe contener al menos 5 caracteres alfanuméricos.")
                return False

        if not app.genero or app.genero not in ["Masculino", "Femenino"]:
            st.error("El campo **Género** es obligatorio.")
            return False

        dob = app.fecha_Nacimiento.strip()
        if not dob:
            st.error("El campo **Fecha de Nacimiento** es obligatorio.")
            return False
        date_match = re.match(r"^\d{1,2}[/-]\d{1,2}[/-]\d{4}$", dob) or re.match(r"^\d{4}[/-]\d{1,2}[/-]\d{1,2}$", dob)
        if not date_match and len(dob) < 6:
            st.error("Por favor introduce una **Fecha de Nacimiento** válida (ejemplo: DD/MM/AAAA).")
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
        if not app.direccion.strip():
            st.error("El campo **Sector o Dirección residencial** es obligatorio.")
            return False

    elif step_idx == 2:
        if not app.id_GradoAcademico:
            st.error("El campo **Nivel Académico Máximo Alcanzado** es obligatorio.")
            return False
        if not app.expectativa_Salarial.strip():
            st.error("El campo **Expectativa Salarial pretendida (RD$)** es obligatorio.")
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
            <div style="background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 14px; padding: 24px 28px; margin-bottom: 24px; box-shadow: 0 2px 8px rgba(0,0,0,0.04);">
                <span style="background: #e2e8f0; color: #475569; padding: 4px 12px; border-radius: 20px; font-size: 0.8rem; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; display: inline-block;">Postulación a Empleo</span>
                <h2 style="color: #0f172a; margin-top: 10px; margin-bottom: 6px; font-size: 1.8rem; font-weight: 700;">{job.get('job_title', 'Vacante')}</h2>
                <div style="color: #64748b; font-size: 0.95rem; font-weight: 500;">🏢 {job.get('company_name', '')} &nbsp;|&nbsp; 📍 {job.get('location', 'República Dominicana')} &nbsp;|&nbsp; 💼 {job.get('contract_type_name', 'Fijo')}</div>
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
        # STEPPER DE NAVEGACIÓN Y VALIDACIONES DE ESTADO
        # -------------------------------------------------------------
        current_step = st.session_state.applicant_step
        app: ApplicantModel = st.session_state.applicant_obj

        # Función para verificar si un paso tiene todos sus campos requeridos llenos
        def is_step_completed(step_num: int) -> bool:
            if step_num == 0:
                return bool(
                    app.primer_Nombre.strip()
                    and app.primer_Apellido.strip()
                    and app.identificacion.strip()
                    and app.genero in ["Masculino", "Femenino"]
                    and app.fecha_Nacimiento.strip()
                )
            elif step_num == 1:
                return bool(
                    app.telefono.strip()
                    and app.email.strip()
                    and app.direccion.strip()
                )
            elif step_num == 2:
                return bool(
                    app.id_GradoAcademico
                    and app.expectativa_Salarial.strip()
                )
            elif step_num == 3:
                return bool(st.session_state.get("attached_cv_file"))
            return False

        # Retorna el icono con color azuloso (#2563eb) cuando el paso esté completado o activo
        def get_step_icon(step_num: int, base_icon: str):
            if is_step_completed(step_num) or step_num < current_step:
                return sac.BsIcon(name=base_icon, color="#2563eb")
            elif step_num == current_step:
                return sac.BsIcon(name=base_icon, color="#2563eb")
            return sac.BsIcon(name=base_icon, color="#94a3b8")

        # Parsear customData de la vacante para determinar si contiene preguntas personalizadas
        customFields = []
        raw_custom_data = job.get("customData")
        if raw_custom_data:
            try:
                if isinstance(raw_custom_data, str):
                    customFields = json.loads(raw_custom_data)
                elif isinstance(raw_custom_data, list):
                    customFields = raw_custom_data
            except Exception as e:
                logging.warning(f"Error parseando customData del empleo: {e}")

        if isinstance(customFields, list):
            customFields = [
                f for f in customFields
                if isinstance(f, dict) and (f.get("fieldName") or f.get("label"))
            ]
        else:
            customFields = []

        has_custom_questions = len(customFields) > 0

        step4_title = "4. Preguntas & Envío" if has_custom_questions else "4. Confirmación"
        step4_subtitle = "Requisitos y envío" if has_custom_questions else "Resumen y envío"
        step4_icon_name = "send-check" if has_custom_questions else "clipboard-check"

        step_items = [
            sac.StepsItem(title="1. Personal", subtitle="Nombre e ID", icon=get_step_icon(0, "person")),
            sac.StepsItem(title="2. Contacto", subtitle="Teléfono y correo", icon=get_step_icon(1, "telephone")),
            sac.StepsItem(title="3. Perfil & Estudios", subtitle="Grado y experiencia", icon=get_step_icon(2, "mortarboard")),
            sac.StepsItem(title=step4_title, subtitle=step4_subtitle, icon=get_step_icon(3, step4_icon_name)),
        ]

        # Usar clave dinámica vinculada al paso para evitar que sac.steps bloquee el avance de paso
        stepper_value = sac.steps(
            items=step_items,
            index=st.session_state.applicant_step,
            return_index=True,
            size="sm",
            color="blue",
            key=f"stepper_nav_{st.session_state.applicant_step}"
        )

        # Si el usuario hace clic directo en un paso del stepper
        if stepper_value is not None and stepper_value != st.session_state.applicant_step:
            if stepper_value > st.session_state.applicant_step:
                if not validate_step(st.session_state.applicant_step):
                    st.rerun()
            st.session_state.applicant_step = stepper_value
            st.rerun()

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
                    current_tipo_idx = 0 if app.tipo_Identificacion == 1 else 1
                    tipo_selected = st.selectbox(
                        "Tipo de Identificación *",
                        tipo_id_options,
                        index=current_tipo_idx,
                        key=f"step0_tipo_id_{st.session_state.applicant_step}"
                    )
                    new_tipo = int(tipo_selected.split("-")[0])
                    if new_tipo != app.tipo_Identificacion:
                        app.tipo_Identificacion = new_tipo
                        if app.identificacion:
                            app.identificacion = format_cedula(app.identificacion) if new_tipo == 1 else format_pasaporte(app.identificacion)
                        st.rerun()

                is_cedula = app.tipo_Identificacion == 1
                placeholder_id = "001-2032445-6" if is_cedula else "Ej. A12345678"
                label_id = "Cédula de Identidad *" if is_cedula else "Número de Pasaporte *"
                help_id = "Formato dominicano de 11 dígitos: 001-XXXXXXX-X" if is_cedula else "Alfanumérico (letras y números sin espacios)"
                max_chars_id = 13 if is_cedula else 20

                with col_id2:
                    raw_id = st.text_input(
                        label_id,
                        value=app.identificacion,
                        placeholder=placeholder_id,
                        max_chars=max_chars_id,
                        help=help_id,
                        key=f"step0_identificacion_{st.session_state.applicant_step}"
                    )
                    app.identificacion = format_cedula(raw_id) if is_cedula else format_pasaporte(raw_id)

                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    app.primer_Nombre = st.text_input(
                        "Primer Nombre *",
                        value=app.primer_Nombre,
                        placeholder="Ej. Juan",
                        key=f"step0_primer_nombre_{st.session_state.applicant_step}"
                    )
                with col_n2:
                    app.segundo_Nombre = st.text_input(
                        "Segundo Nombre",
                        value=app.segundo_Nombre,
                        placeholder="Ej. Carlos",
                        key=f"step0_segundo_nombre_{st.session_state.applicant_step}"
                    )

                col_a1, col_a2 = st.columns(2)
                with col_a1:
                    app.primer_Apellido = st.text_input(
                        "Primer Apellido *",
                        value=app.primer_Apellido,
                        placeholder="Ej. Pérez",
                        key=f"step0_primer_apellido_{st.session_state.applicant_step}"
                    )
                with col_a2:
                    app.segundo_Apellido = st.text_input(
                        "Segundo Apellido",
                        value=app.segundo_Apellido,
                        placeholder="Ej. Gómez",
                        key=f"step0_segundo_apellido_{st.session_state.applicant_step}"
                    )

                col_extra1, col_extra2, col_extra3 = st.columns([1.2, 1.2, 1.2])
                with col_extra1:
                    generos = ["Seleccione una opción...", "Masculino", "Femenino"]
                    gen_idx = generos.index(app.genero) if app.genero in ["Masculino", "Femenino"] else 0
                    sel_gen = st.selectbox(
                        "Género *",
                        generos,
                        index=gen_idx,
                        key=f"step0_genero_{st.session_state.applicant_step}"
                    )
                    app.genero = sel_gen if sel_gen in ["Masculino", "Femenino"] else ""

                with col_extra2:
                    app.fecha_Nacimiento = st.text_input(
                        "Fecha de Nacimiento *",
                        value=app.fecha_Nacimiento,
                        placeholder="DD/MM/AAAA",
                        help="Ejemplo: 15/05/1995",
                        key=f"step0_fecha_nacimiento_{st.session_state.applicant_step}"
                    )

                with col_extra3:
                    nacionalidades = ["Dominicana", "Extranjera con permiso", "Otra"]
                    nac_idx = nacionalidades.index(app.nacionalidad) if app.nacionalidad in nacionalidades else 0
                    app.nacionalidad = st.selectbox(
                        "Nacionalidad",
                        nacionalidades,
                        index=nac_idx,
                        key=f"step0_nacionalidad_{st.session_state.applicant_step}"
                    )

            # === PASO 1: CONTACTO Y UBICACIÓN ===
            elif current_step == 1:
                st.subheader("Paso 2: Datos de Contacto y Ubicación")
                st.caption("A través de estos medios te contactaremos para el proceso de selección.")

                col_c1, col_c2 = st.columns(2)
                with col_c1:
                    app.telefono = st.text_input(
                        "Teléfono móvil / WhatsApp *",
                        value=app.telefono,
                        placeholder="Ej. 809-555-1234",
                        key=f"step1_telefono_{st.session_state.applicant_step}"
                    )
                with col_c2:
                    app.telefono_Alternativo = st.text_input(
                        "Teléfono alternativo o residencial",
                        value=app.telefono_Alternativo,
                        placeholder="Ej. 809-555-5678",
                        key=f"step1_telefono_alt_{st.session_state.applicant_step}"
                    )

                app.email = st.text_input(
                    "Correo Electrónico *",
                    value=app.email,
                    placeholder="Ej. tu.nombre@correo.com",
                    key=f"step1_email_{st.session_state.applicant_step}"
                )

                col_u1, col_u2 = st.columns(2)
                with col_u1:
                    app.ciudad = st.text_input(
                        "Ciudad / Provincia de residencia",
                        value=app.ciudad,
                        placeholder="Ej. Santo Domingo, Santiago, etc.",
                        key=f"step1_ciudad_{st.session_state.applicant_step}"
                    )
                with col_u2:
                    app.direccion = st.text_input(
                        "Sector o Dirección residencial *",
                        value=app.direccion,
                        placeholder="Ej. Ensanche Naco, Bella Vista, etc.",
                        key=f"step1_direccion_{st.session_state.applicant_step}"
                    )

            # === PASO 2: FORMACIÓN Y EXPERIENCIA ===
            elif current_step == 2:
                st.subheader("Paso 3: Formación Académica y Perfil Laboral")
                st.caption("Completa tu formación académica y trayectoria profesional.")

                grados_list = get_academic_grades_list()
                grados_nombres = [g[1] for g in grados_list]

                default_grado_idx = 0
                if app.id_GradoAcademico:
                    for i, (cod, nom) in enumerate(grados_list):
                        if cod == app.id_GradoAcademico:
                            default_grado_idx = i
                            break

                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    grado_sel_name = st.selectbox(
                        "Nivel Académico Máximo Alcanzado *",
                        grados_nombres,
                        index=default_grado_idx,
                        key=f"step2_grado_{st.session_state.applicant_step}"
                    )
                    for cod, nom in grados_list:
                        if nom == grado_sel_name:
                            app.id_GradoAcademico = cod
                            app.grado_Nombre = nom
                            break

                with col_g2:
                    estados = ["Graduado", "En curso", "Incompleto / Pausado"]
                    est_idx = estados.index(app.estado_Estudios) if app.estado_Estudios in estados else 0
                    app.estado_Estudios = st.selectbox("Estado de los estudios", estados, index=est_idx, key=f"step2_estado_{st.session_state.applicant_step}")

                col_f1, col_f2, col_f3 = st.columns([1.4, 1.4, 1.2])
                with col_f1:
                    app.carrera = st.text_input(
                        "Carrera, Profesión o Área de Estudio",
                        value=app.carrera,
                        placeholder="Ej. Licenciatura en Contabilidad, Ing. de Sistemas...",
                        key=f"step2_carrera_{st.session_state.applicant_step}"
                    )
                with col_f2:
                    app.institucion = st.text_input(
                        "Institución / Universidad / Centro Educativo",
                        value=app.institucion,
                        placeholder="Ej. UASD, INTEC, PUCMM, ITLA, etc.",
                        key=f"step2_institucion_{st.session_state.applicant_step}"
                    )
                with col_f3:
                    app.periodo_Estudio = st.text_input(
                        "Años cursados / Período",
                        value=app.periodo_Estudio,
                        placeholder="Ej. 2018 - 2022",
                        help="Años de inicio y fin o año de graduación",
                        key=f"step2_periodo_{st.session_state.applicant_step}"
                    )

                st.markdown("---")
                st.markdown("##### Historial de Experiencias Laborales (Opcional)")
                st.caption("Si posees experiencia previa, puedes registrar una o más empresas donde hayas laborado, el tiempo y tus funciones principales.")

                if not hasattr(app, "experiencias_Laborales") or app.experiencias_Laborales is None:
                    app.experiencias_Laborales = []

                if len(app.experiencias_Laborales) == 0:
                    app.experiencias_Laborales.append({
                        "empresa": "",
                        "puesto": "",
                        "duracion": "",
                        "funciones": ""
                    })

                indices_to_remove = []
                for i, exp in enumerate(app.experiencias_Laborales):
                    with st.container(border=True):
                        col_hdr1, col_hdr2 = st.columns([4, 1])
                        with col_hdr1:
                            st.markdown(f"💼 **Experiencia #{i + 1}**")
                        with col_hdr2:
                            if len(app.experiencias_Laborales) > 1 or (exp.get("empresa") or exp.get("puesto") or exp.get("funciones")):
                                if st.button("🗑️ Quitar", key=f"btn_remove_exp_{i}_{st.session_state.applicant_step}"):
                                    indices_to_remove.append(i)

                        col_e1, col_e2, col_e3 = st.columns([1.5, 1.5, 1.2])
                        with col_e1:
                            exp["empresa"] = st.text_input(
                                f"Empresa / Institución #{i+1}",
                                value=exp.get("empresa", ""),
                                placeholder="Ej. Banco BHD, Claro, etc.",
                                key=f"exp_empresa_{i}_{st.session_state.applicant_step}"
                            )
                        with col_e2:
                            exp["puesto"] = st.text_input(
                                f"Cargo o Puesto desempeñado #{i+1}",
                                value=exp.get("puesto", ""),
                                placeholder="Ej. Analista de Sistemas, Contador...",
                                key=f"exp_puesto_{i}_{st.session_state.applicant_step}"
                            )
                        with col_e3:
                            exp["duracion"] = st.text_input(
                                f"Tiempo en el puesto / Período #{i+1}",
                                value=exp.get("duracion", ""),
                                placeholder="Ej. Ene 2021 - Dic 2023 (2 años)",
                                key=f"exp_duracion_{i}_{st.session_state.applicant_step}"
                            )

                        exp["funciones"] = st.text_area(
                            f"Funciones y responsabilidades principales #{i+1}",
                            value=exp.get("funciones", ""),
                            placeholder="Describe brevemente tus principales responsabilidades, tareas y logros en este puesto...",
                            rows=2,
                            key=f"exp_funciones_{i}_{st.session_state.applicant_step}"
                        )

                if indices_to_remove:
                    for idx in sorted(indices_to_remove, reverse=True):
                        app.experiencias_Laborales.pop(idx)
                    st.rerun()

                if st.button("➕ Agregar otra experiencia laboral", key=f"btn_add_exp_{st.session_state.applicant_step}"):
                    app.experiencias_Laborales.append({
                        "empresa": "",
                        "puesto": "",
                        "duracion": "",
                        "funciones": ""
                    })
                    st.rerun()

                st.markdown("---")
                st.markdown("##### Expectativas y Disponibilidad")

                col_exp1, col_exp2 = st.columns(2)
                with col_exp1:
                    rangos_exp = ["Sin experiencia laboral", "Menos de 1 año", "1 a 2 años", "3 a 5 años", "Más de 5 años"]
                    exp_idx = rangos_exp.index(app.experiencia_Total) if app.experiencia_Total in rangos_exp else 1
                    app.experiencia_Total = st.selectbox("Años de experiencia laboral en áreas afines", rangos_exp, index=exp_idx, key=f"step2_exp_{st.session_state.applicant_step}")

                with col_exp2:
                    app.expectativa_Salarial = st.text_input(
                        "Expectativa Salarial pretendida (RD$) *",
                        value=app.expectativa_Salarial,
                        placeholder="Ej. 45,000 - 55,000",
                        key=f"step2_expectativa_{st.session_state.applicant_step}"
                    )

                col_disp1, col_disp2 = st.columns(2)
                with col_disp1:
                    disponibilidades = ["Inmediata", "En 15 días", "En 1 mes", "A convenir"]
                    disp_idx = disponibilidades.index(app.disponibilidad) if app.disponibilidad in disponibilidades else 0
                    app.disponibilidad = st.selectbox("Disponibilidad para iniciar", disponibilidades, index=disp_idx, key=f"step2_disp_{st.session_state.applicant_step}")

                with col_disp2:
                    app.linkedin_Url = st.text_input(
                        "Enlace a LinkedIn o Portafolio Web (Opcional)",
                        value=app.linkedin_Url,
                        placeholder="https://linkedin.com/in/tu-perfil",
                        key=f"step2_linkedin_{st.session_state.applicant_step}"
                    )

            # === PASO 3: PREGUNTAS DE VACANTE Y ENVÍO ===
            elif current_step == 3:
                if has_custom_questions:
                    st.subheader("Paso 4: Preguntas del Puesto y Confirmación de Envío")
                    st.caption("Responde las preguntas específicas de la vacante y confirma tu postulación.")
                    st.markdown("**Preguntas requeridas por la empresa para este puesto:**")
                    with st.container(border=True):
                        render_custom_fields_in_container(customFields, requeridos=False)
                    st.markdown("---")
                else:
                    st.subheader("Paso 4: Resumen y Confirmación de Envío")
                    st.caption("Verifica el resumen de tu postulación antes de realizar el envío definitivo.")

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
                exps_validas_list = [
                    e for e in app.experiencias_Laborales 
                    if isinstance(e, dict) and (e.get("empresa") or e.get("puesto"))
                ]
                exps_texto = f"{len(exps_validas_list)} empleo(s) registrado(s)" if exps_validas_list else "Sin empleos previos registrados"
                periodo_txt = f" ({app.periodo_Estudio})" if app.periodo_Estudio else ""

                st.markdown(
                    f"""
                    - **Candidato:** {app.nombre_Completo or 'No especificado'}
                    - **Documento:** {('Cédula' if app.tipo_Identificacion == 1 else 'Pasaporte')}: `{app.identificacion or 'No especificada'}`
                    - **Género:** {app.genero or 'No especificado'} &nbsp;|&nbsp; **Fecha Nac.:** {app.fecha_Nacimiento or 'No especificada'}
                    - **Contacto:** 📞 {app.telefono or 'No especificado'} &nbsp;|&nbsp; ✉️ {app.email or 'No especificado'}
                    - **Dirección:** {app.direccion or 'No especificada'} {f'({app.ciudad})' if app.ciudad else ''}
                    - **Nivel Académico:** {app.grado_Nombre or 'No seleccionado'} {f'en {app.carrera}' if app.carrera else ''}{periodo_txt}
                    - **Historial Laboral:** {exps_texto} &nbsp;|&nbsp; **Rango general:** {app.experiencia_Total or 'N/A'}
                    - **Expectativa:** {app.expectativa_Salarial or 'A convenir'} &nbsp;|&nbsp; **Disponibilidad:** {app.disponibilidad or 'Inmediata'}
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
                    st.session_state.applicant_step -= 1
                    st.rerun()

        with col_nav_next:
            if current_step < 3:
                if st.button("Siguiente ➔", use_container_width=True, type="primary"):
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
                    st.session_state["send_pressed"] = True

        # -------------------------------------------------------------
        # PROCESO DE ENVÍO DE LA SOLICITUD
        # -------------------------------------------------------------
        if st.session_state.get("send_pressed"):
            st.session_state["send_pressed"] = False

            if not validate_step(0):
                st.session_state.applicant_step = 0
                st.error("Por favor completa los campos obligatorios del Paso 1 (Personal).")
                st.rerun()
            elif not validate_step(1):
                st.session_state.applicant_step = 1
                st.error("Por favor completa los campos obligatorios del Paso 2 (Contacto y Ubicación).")
                st.rerun()
            elif not validate_step(2):
                st.session_state.applicant_step = 2
                st.error("Por favor completa los campos obligatorios del Paso 3 (Formación y Expectativas).")
                st.rerun()

            custom_data_str = "[]"
            if has_custom_questions and "customFields" in st.session_state:
                try:
                    session_data = json.loads(st.session_state.customFields)
                    for i, field in enumerate(customFields):
                        if field.get("fieldName") in session_data:
                            customFields[i]["value"] = session_data[field["fieldName"]]
                    custom_data_str = json.dumps(customFields)
                except Exception as e:
                    logging.warning(f"Error procesando customFields para envío: {e}")

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
                    st.query_params.clear()
                    st.query_params["page"] = "home"
                    st.session_state.page = "home"
                    st.rerun()