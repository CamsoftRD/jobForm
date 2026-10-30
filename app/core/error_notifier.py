"""
Módulo de notificación automática de errores a JIRA por correo electrónico para jobForm.

Captura eventos de logging de nivel ERROR o CRITICAL y despacha una notificación por correo a:
- administrador@camsoft.com.do
- epaniagua@camsoft.com.do

Características clave:
1. Prevención estricta de recursión infinita (Thread-local recursion guard).
2. Rate-limiting / Throttling en memoria para evitar saturación de correos/tickets ante caídas de backend.
3. Despacho asíncrono en segundo plano (Daemon Thread) para evitar demoras en la interfaz de usuario.
4. Enmascaramiento de datos sensibles (JWTs, tokens, passwords, API keys).
5. Extracción segura de contexto de sesión de Streamlit (usuario, empresa, dominio, ambiente, versión).
"""

import sys
import time
import re
import html
import logging
import threading
import traceback
from datetime import datetime
from typing import List, Optional, Dict, Any

try:
    import pytz
except ImportError:
    pytz = None

# Recipientes obligatorios por defecto
DEFAULT_RECIPIENTS = [
    "administrador@camsoft.com.do",
    "epaniagua@camsoft.com.do"
]

# Destinatario que debe recibir la notificación en texto plano sin HTML (creación de tickets en JIRA)
PLAIN_TEXT_RECIPIENT = "administrador@camsoft.com.do"

DEFAULT_SUBJECT_PREFIX = "JOBFORM:"
DEFAULT_COOLDOWN_SECONDS = 900  # 15 minutos entre errores idénticos

# Lista de patrones o códigos de error que no deben notificarse a JIRA
IGNORED_ERROR_PATTERNS = [
    "SRH601089",
    "Error buscando detalle de Documentos",
    "602302",
    "602266",
    "autorizacion/cancelar",
    "FMK24",
    "El parámetro Password es incorrecto",
    "usuarioautorizaciones",
]

# Control de reentrada por hilo para evitar bucles infinitos
_thread_local = threading.local()

# Cache en memoria para throttling de errores {error_signature: timestamp}
_throttle_cache: Dict[str, float] = {}
_throttle_lock = threading.Lock()


def mask_sensitive_data(text: str) -> str:
    """
    Enmascara datos sensibles como tokens JWT, cabeceras Bearer, contraseñas y API keys.
    """
    if not text:
        return ""
    
    # Enmascarar Bearer tokens
    text = re.sub(
        r'(?i)bearer\s+[A-Za-z0-9_\-\.]+',
        'Bearer [TOKEN_ENMASCARADO]',
        text
    )

    # Enmascarar tokens JWT (ej. eyJhbGciOi...)
    text = re.sub(
        r'ey[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}',
        '[TOKEN_JWT_ENMASCARADO]',
        text
    )
    
    # Enmascarar contraseñas o secrets en JSON / key-value
    text = re.sub(
        r'(?i)(["\']?(?:password|contrase[ñn]a|secret|x-api-key|token|cookies_password)["\']?\s*[:=]\s*["\'])([^"\'\s]+)(["\']?)',
        r'\1[ENMASCARADO]\3',
        text
    )
    
    return text


def get_safe_session_context() -> Dict[str, Any]:
    """
    Extrae información contextual de la sesión de Streamlit de forma segura
    sin lanzar excepciones si se ejecuta en un hilo secundario o sin contexto.
    """
    context: Dict[str, Any] = {
        "user_name": "No autenticado / Desconocido",
        "employee_id": "N/A",
        "employee_name": "N/A",
        "company_name": "N/A",
        "domain_name": "N/A",
        "enviroment": "desconocido",
        "version": "v1.0.5",
        "current_url": "N/A"
    }

    try:
        import streamlit as st

        # Secrets
        if hasattr(st, "secrets"):
            try:
                context["enviroment"] = st.secrets.get("enviroment", "desconocido")
                context["version"] = st.secrets.get("version", "v1.0.5")
                default_domain = st.secrets.get("default_domain")
                if default_domain:
                    context["domain_name"] = default_domain
            except Exception:
                pass

        # Session state
        if hasattr(st, "session_state"):
            try:
                if "enviroment" in st.session_state and st.session_state.enviroment:
                    context["enviroment"] = st.session_state.enviroment

                if "domain_name" in st.session_state and st.session_state.domain_name:
                    context["domain_name"] = st.session_state.domain_name

                if "page" in st.session_state and st.session_state.page:
                    context["page"] = str(st.session_state.page)

                # Candidato / Solicitante si está en proceso de postulación
                applicant = st.session_state.get("applicant_obj")
                if applicant:
                    first_name = getattr(applicant, "primer_Nombre", "") or ""
                    last_name = getattr(applicant, "primer_Apellido", "") or ""
                    applicant_email = getattr(applicant, "email", "") or ""
                    full_name = f"{first_name} {last_name}".strip()
                    if full_name:
                        context["user_name"] = f"{full_name} <{applicant_email}>" if applicant_email else full_name
                    elif applicant_email:
                        context["user_name"] = applicant_email

                # Usuario autenticado
                user = st.session_state.get("user")
                if user:
                    if isinstance(user, dict):
                        context["user_name"] = user.get("userName") or user.get("nombre") or str(user)
                    else:
                        context["user_name"] = getattr(user, "userName", getattr(user, "nombre", str(user)))

                # Datos del empleado
                me = st.session_state.get("me")
                if me:
                    if isinstance(me, dict):
                        context["employee_id"] = str(me.get("id") or me.get("codigo") or "N/A")
                        context["employee_name"] = me.get("fullName") or me.get("nombre") or "N/A"
                        context["company_name"] = me.get("company_name") or me.get("empresa") or "N/A"
                    else:
                        context["employee_id"] = str(getattr(me, "id", getattr(me, "codigo", "N/A")))
                        context["employee_name"] = getattr(me, "fullName", getattr(me, "nombre", "N/A"))
                        context["company_name"] = getattr(me, "company_name", getattr(me, "empresa", "N/A"))
            except Exception:
                pass

        # Contexto de URL/Headers si está disponible
        if hasattr(st, "context") and hasattr(st.context, "headers"):
            try:
                host = st.context.headers.get("Host") or st.context.headers.get("host")
                if host:
                    context["current_url"] = host
            except Exception:
                pass

    except Exception:
        pass

    return context


def _clean_throttle_cache(now: float, cooldown: float) -> None:
    """Limpia entradas antiguas de la caché para evitar crecimiento indefinido de memoria."""
    stale_keys = [k for k, timestamp in _throttle_cache.items() if now - timestamp > (cooldown * 2)]
    for k in stale_keys:
        _throttle_cache.pop(k, None)


def _should_throttle(error_signature: str, cooldown: float) -> bool:
    """Verifica y actualiza la tasa de emisión para evitar ráfagas masivas."""
    now = time.time()
    with _throttle_lock:
        _clean_throttle_cache(now, cooldown)
        last_time = _throttle_cache.get(error_signature)
        if last_time is not None and (now - last_time) < cooldown:
            return True
        _throttle_cache[error_signature] = now
        return False


def _build_error_signature(record: logging.LogRecord) -> str:
    """Genera una firma compacta para identificar errores idénticos."""
    clean_msg = re.sub(r'\d+', 'N', record.getMessage()[:120])
    return f"{record.module}:{record.lineno}:{clean_msg}"


def _format_timestamp() -> str:
    """Formatea la fecha actual en hora local dominicana (America/Santo_Domingo) o local del sistema."""
    if pytz:
        try:
            tz = pytz.timezone("America/Santo_Domingo")
            return datetime.now(tz).strftime("%Y-%m-%d %H:%M:%S (%Z)")
        except Exception:
            pass
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _build_email_subject(prefix: str, environment: str, record: logging.LogRecord) -> str:
    """
    Construye el asunto del correo optimizado para filtrado e indexación en JIRA.
    Ejemplo: 'JOBFORM: [apis_qa] Error al procesar solicitud...'
    """
    msg_summary = record.getMessage().splitlines()[0] if record.getMessage() else "Error no especificado"
    msg_summary = mask_sensitive_data(msg_summary).strip()
    
    # Limitar longitud para compatibilidad con clientes de correo
    if len(msg_summary) > 90:
        msg_summary = msg_summary[:87] + "..."
        
    env_tag = f"[{environment}] " if environment and environment != "desconocido" else ""
    return f"{prefix} {env_tag}{msg_summary}"


def _build_email_body_text(
    record: logging.LogRecord,
    context: Dict[str, Any],
    timestamp_str: str,
    stack_trace: Optional[str]
) -> str:
    """
    Construye el cuerpo del correo en texto plano sin HTML,
    optimizado para creación de incidencias en JIRA sin etiquetas web.
    """
    raw_msg = mask_sensitive_data(record.getMessage())
    user_info = f"{context.get('user_name')} (Empleado ID: {context.get('employee_id')} - {context.get('employee_name')})"
    location = f"{record.pathname}:{record.lineno} ({record.funcName})"

    lines = [
        "⚠️ Notificación Automática de Error - JobForm",
        "Este correo ha sido generado automáticamente para la creación y seguimiento de issues en JIRA.",
        "",
        f"Nivel: {record.levelname}",
        f"Mensaje: {raw_msg}",
        "",
        "Información del Contexto:",
        f"- Fecha y Hora: {timestamp_str}",
        f"- Ambiente: {context.get('enviroment')}",
        f"- Versión: {context.get('version')}",
        f"- Dominio / Tenant: {context.get('domain_name')}",
        f"- Empresa: {context.get('company_name')}",
        f"- Usuario en Sesión: {user_info}",
        f"- Archivo / Línea: {location}",
    ]

    if stack_trace:
        st_clean = mask_sensitive_data(stack_trace).strip()
        lines.append("")
        lines.append("Stack Trace / Detalle Técnico:")
        lines.append(st_clean)

    lines.append("")
    lines.append("Generado automáticamente por el manejador de incidencias de jobForm para JIRA.")

    return "\n".join(lines)


def _build_email_body_html(
    record: logging.LogRecord,
    context: Dict[str, Any],
    timestamp_str: str,
    stack_trace: Optional[str]
) -> str:
    """
    Construye el cuerpo del correo en HTML enriquecido, limpio y compatible con JIRA.
    """
    error_message_escaped = html.escape(mask_sensitive_data(record.getMessage()))
    
    stack_trace_section = ""
    if stack_trace:
        st_escaped = html.escape(mask_sensitive_data(stack_trace))
        stack_trace_section = f"""
        <div style="margin-top: 20px;">
            <h3 style="color: #1e293b; font-size: 15px; margin-bottom: 8px; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px;">
                Stack Trace / Detalle Técnico
            </h3>
            <pre style="background-color: #0f172a; color: #f8fafc; padding: 14px; border-radius: 6px; font-family: Consolas, 'Courier New', monospace; font-size: 12px; line-height: 1.5; overflow-x: auto; white-space: pre-wrap; word-break: break-all;">{st_escaped}</pre>
        </div>
        """

    html_content = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #334155; line-height: 1.6; background-color: #f8fafc; padding: 20px; margin: 0;">
    <div style="max-width: 720px; margin: 0 auto; background: #ffffff; border-radius: 8px; border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); overflow: hidden;">
        
        <!-- Header -->
        <div style="background-color: #dc2626; color: #ffffff; padding: 16px 24px;">
            <h2 style="margin: 0; font-size: 18px; font-weight: 600; letter-spacing: -0.01em;">
                ⚠️ Notificación Automática de Error - JobForm
            </h2>
            <p style="margin: 4px 0 0 0; font-size: 13px; opacity: 0.9;">
                Este correo ha sido generado automáticamente para la creación y seguimiento de issues en JIRA.
            </p>
        </div>

        <div style="padding: 24px;">
            
            <!-- Resumen del Error -->
            <div style="background-color: #fef2f2; border-left: 4px solid #ef4444; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px;">
                <strong style="color: #991b1b; font-size: 14px; display: block; margin-bottom: 4px;">
                    Nivel: {record.levelname} | Mensaje:
                </strong>
                <span style="color: #7f1d1d; font-size: 14px; word-break: break-word;">
                    {error_message_escaped}
                </span>
            </div>

            <!-- Tabla de Metadatos -->
            <h3 style="color: #1e293b; font-size: 15px; margin-bottom: 8px; border-bottom: 2px solid #e2e8f0; padding-bottom: 4px;">
                Información del Contexto
            </h3>
            <table style="width: 100%; border-collapse: collapse; font-size: 13px; margin-bottom: 15px;">
                <tbody>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 8px 12px; font-weight: 600; color: #64748b; width: 30%;">Fecha y Hora:</td>
                        <td style="padding: 8px 12px; color: #0f172a;">{timestamp_str}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9; background-color: #f8fafc;">
                        <td style="padding: 8px 12px; font-weight: 600; color: #64748b;">Ambiente:</td>
                        <td style="padding: 8px 12px; color: #0f172a;"><span style="background-color: #e0e7ff; color: #3730a3; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: 500;">{context.get('enviroment')}</span></td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 8px 12px; font-weight: 600; color: #64748b;">Versión:</td>
                        <td style="padding: 8px 12px; color: #0f172a;">{context.get('version')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9; background-color: #f8fafc;">
                        <td style="padding: 8px 12px; font-weight: 600; color: #64748b;">Dominio / Tenant:</td>
                        <td style="padding: 8px 12px; color: #0f172a;">{context.get('domain_name')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 8px 12px; font-weight: 600; color: #64748b;">Empresa:</td>
                        <td style="padding: 8px 12px; color: #0f172a;">{context.get('company_name')}</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9; background-color: #f8fafc;">
                        <td style="padding: 8px 12px; font-weight: 600; color: #64748b;">Usuario en Sesión:</td>
                        <td style="padding: 8px 12px; color: #0f172a;">{context.get('user_name')} (Empleado ID: {context.get('employee_id')} - {context.get('employee_name')})</td>
                    </tr>
                    <tr style="border-bottom: 1px solid #f1f5f9;">
                        <td style="padding: 8px 12px; font-weight: 600; color: #64748b;">Archivo / Línea:</td>
                        <td style="padding: 8px 12px; color: #0f172a;">{record.pathname}:{record.lineno} ({record.funcName})</td>
                    </tr>
                </tbody>
            </table>

            <!-- Stack Trace -->
            {stack_trace_section}

            <div style="margin-top: 24px; padding-top: 12px; border-top: 1px solid #e2e8f0; font-size: 11px; color: #94a3b8; text-align: center;">
                Generado automáticamente por el manejador de incidencias de <strong>jobForm</strong> para JIRA.
            </div>
        </div>
    </div>
</body>
</html>
"""
    return html_content


class JiraEmailErrorHandler(logging.Handler):
    """
    Handler de logging de Python que envía correos electrónicos a JIRA
    cuando ocurre un error (ERROR o CRITICAL).
    """

    def __init__(
        self,
        recipients: Optional[List[str]] = None,
        subject_prefix: str = DEFAULT_SUBJECT_PREFIX,
        cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
        enabled: bool = True,
        ignored_patterns: Optional[List[str]] = None
    ):
        super().__init__(level=logging.ERROR)
        self.recipients = recipients or list(DEFAULT_RECIPIENTS)
        self.subject_prefix = subject_prefix
        self.cooldown_seconds = cooldown_seconds
        self.enabled = enabled
        self.ignored_patterns = ignored_patterns if ignored_patterns is not None else list(IGNORED_ERROR_PATTERNS)

    def emit(self, record: logging.LogRecord) -> None:
        # 1. Verificar si el handler está habilitado
        if not self.enabled:
            return

        # 2. Protección estricta contra recursión infinita
        if getattr(_thread_local, "is_sending_error", False):
            return

        # 3. Filtrar logs que provengan del propio módulo para evitar ciclos
        if record.name == __name__ or record.module == "error_notifier":
            return

        # 4. Filtrar errores de negocio conocidos o esperados que no deben crear tickets en JIRA
        msg = record.getMessage()
        if any(pattern in msg for pattern in self.ignored_patterns):
            return

        try:
            # 5. Verificar Throttling (cooldown)
            signature = _build_error_signature(record)
            if _should_throttle(signature, self.cooldown_seconds):
                return

            # 6. Extraer contexto de sesión actual
            context = get_safe_session_context()

            # 6. Extraer stack trace si existe
            stack_trace = None
            if record.exc_info:
                stack_trace = "".join(traceback.format_exception(*record.exc_info))
            elif getattr(record, "stack_info", None):
                stack_trace = str(record.stack_info)

            # 7. Obtener configuración dinámica si está definida en secrets
            recipients = self.recipients
            subject_prefix = self.subject_prefix
            try:
                import streamlit as st
                if hasattr(st, "secrets") and "error_reporting" in st.secrets:
                    cfg = st.secrets["error_reporting"]
                    if not cfg.get("enabled", True):
                        return
                    if "recipients" in cfg and cfg["recipients"]:
                        recipients = list(cfg["recipients"])
                    if "subject_prefix" in cfg and cfg["subject_prefix"]:
                        subject_prefix = cfg["subject_prefix"]
            except Exception:
                pass

            # 8. Despachar en hilo de fondo asíncrono
            self._dispatch_async(record, context, stack_trace, recipients, subject_prefix)

        except Exception:
            # No propagar excepciones generadas por el propio handler
            pass

    def _dispatch_async(
        self,
        record: logging.LogRecord,
        context: Dict[str, Any],
        stack_trace: Optional[str],
        recipients: List[str],
        subject_prefix: str
    ) -> None:
        """Lanza el envío en un Daemon Thread no bloqueante."""
        worker_thread = threading.Thread(
            target=self._send_worker,
            args=(record, context, stack_trace, recipients, subject_prefix),
            daemon=True,
            name=f"JiraEmailSender-{int(time.time())}"
        )

        # Si estamos dentro de Streamlit, adjuntar el contexto de ejecución
        try:
            from streamlit.runtime.scriptrunner import add_script_run_ctx, get_script_run_ctx
            ctx = get_script_run_ctx()
            if ctx:
                add_script_run_ctx(worker_thread, ctx)
        except Exception:
            pass

        worker_thread.start()

    def _send_worker(
        self,
        record: logging.LogRecord,
        context: Dict[str, Any],
        stack_trace: Optional[str],
        recipients: List[str],
        subject_prefix: str
    ) -> None:
        """Trabajo de fondo que construye el correo y llama a send_email."""
        # Activar el flag de exclusión en este hilo
        _thread_local.is_sending_error = True
        try:
            timestamp_str = _format_timestamp()
            subject = _build_email_subject(subject_prefix, context.get("enviroment", ""), record)

            # Importación diferida para evitar dependencias circulares
            from app.core import send_email

            # Asegurar claves mínimas en session_state si se ejecuta en un contexto no inicializado
            try:
                import streamlit as st
                if hasattr(st, "session_state"):
                    if "enviroment" not in st.session_state or not st.session_state.enviroment:
                        st.session_state.enviroment = st.secrets.get("enviroment", "apis_qa") if hasattr(st, "secrets") else "apis_qa"
                    if "is_auth" not in st.session_state:
                        st.session_state.is_auth = str(False)
                    if "token" not in st.session_state:
                        st.session_state.token = ""

                    # Si no hay token de usuario en sesión pero existen credenciales de servicio configuradas en secrets, autenticarse
                    if not st.session_state.get("token") and hasattr(st, "secrets") and "error_reporting" in st.secrets:
                        cfg = st.secrets["error_reporting"]
                        s_user = cfg.get("service_user")
                        s_pwd = cfg.get("service_password")
                        if s_user and s_pwd:
                            from app.core import sign_in
                            auth_data = sign_in(s_user, s_pwd)
                            if isinstance(auth_data, dict) and "access_Token" in auth_data:
                                st.session_state.token = auth_data["access_Token"]
                                st.session_state.is_auth = str(True)
            except Exception:
                pass

            # Clasificar destinatarios: texto plano sin HTML (administrador@camsoft.com.do) vs plantilla HTML
            raw_recipients = [recipients] if isinstance(recipients, str) else list(recipients or [])
            plain_recipients: List[str] = []
            html_recipients: List[str] = []

            for r in raw_recipients:
                if not r or not isinstance(r, str):
                    continue
                clean_email = r.strip()
                if clean_email.lower() == PLAIN_TEXT_RECIPIENT.lower():
                    plain_recipients.append(clean_email)
                else:
                    html_recipients.append(clean_email)

            # Deduplicar preservando el orden
            plain_recipients = list(dict.fromkeys(plain_recipients))
            html_recipients = list(dict.fromkeys(html_recipients))

            # Envío 1 (independiente): texto plano sin HTML para administrador@camsoft.com.do (JIRA)
            if plain_recipients:
                try:
                    body_text = _build_email_body_text(record, context, timestamp_str, stack_trace)
                    send_email(
                        email=plain_recipients,
                        subject=subject,
                        body=body_text
                    )
                except Exception as e_plain:
                    sys.stderr.write(f"[JiraEmailErrorHandler] Error al enviar notificación en texto plano: {e_plain}\n")

            # Envío 2 (independiente): plantilla HTML para los demás destinatarios
            if html_recipients:
                try:
                    body_html = _build_email_body_html(record, context, timestamp_str, stack_trace)
                    send_email(
                        email=html_recipients,
                        subject=subject,
                        body=body_html
                    )
                except Exception as e_html:
                    sys.stderr.write(f"[JiraEmailErrorHandler] Error al enviar notificación con plantilla HTML: {e_html}\n")
        except Exception as e:
            # Escribir directamente a stderr como fallback de depuración sin invocar logging
            sys.stderr.write(f"[JiraEmailErrorHandler] Error al enviar notificación: {e}\n")
        finally:
            _thread_local.is_sending_error = False


def setup_error_notifier(
    recipients: Optional[List[str]] = None,
    subject_prefix: str = DEFAULT_SUBJECT_PREFIX,
    cooldown_seconds: float = DEFAULT_COOLDOWN_SECONDS,
    enabled: bool = True
) -> JiraEmailErrorHandler:
    """
    Inicializa y registra el JiraEmailErrorHandler en el logger raíz de Python.
    Es idempotente: si ya existe un handler registrado, no lo duplica.
    """
    root_logger = logging.getLogger()

    # Verificar si ya existe una instancia de este handler para no duplicar en re-runs de Streamlit
    existing_handler = next(
        (h for h in root_logger.handlers if isinstance(h, JiraEmailErrorHandler)),
        None
    )
    if existing_handler:
        return existing_handler

    # Intentar leer configuración desde secrets si no se proveyó
    actual_recipients = recipients or list(DEFAULT_RECIPIENTS)
    actual_prefix = subject_prefix
    actual_cooldown = cooldown_seconds
    actual_enabled = enabled

    try:
        import streamlit as st
        if hasattr(st, "secrets") and "error_reporting" in st.secrets:
            cfg = st.secrets["error_reporting"]
            actual_enabled = cfg.get("enabled", actual_enabled)
            if "recipients" in cfg and cfg["recipients"]:
                actual_recipients = list(cfg["recipients"])
            if "subject_prefix" in cfg and cfg["subject_prefix"]:
                actual_prefix = cfg["subject_prefix"]
            if "cooldown_seconds" in cfg:
                actual_cooldown = float(cfg["cooldown_seconds"])
    except Exception:
        pass

    handler = JiraEmailErrorHandler(
        recipients=actual_recipients,
        subject_prefix=actual_prefix,
        cooldown_seconds=actual_cooldown,
        enabled=actual_enabled
    )

    root_logger.addHandler(handler)
    return handler
