import time
import logging
import unittest
from unittest.mock import patch, MagicMock

from app.core.error_notifier import (
    JiraEmailErrorHandler,
    setup_error_notifier,
    mask_sensitive_data,
    get_safe_session_context,
    _build_error_signature,
    _should_throttle,
    _throttle_cache,
    _thread_local,
    _build_email_body_text,
    DEFAULT_RECIPIENTS,
    DEFAULT_SUBJECT_PREFIX,
    PLAIN_TEXT_RECIPIENT
)


class TestJobFormErrorNotifier(unittest.TestCase):

    def test_default_recipients(self):
        """Verifica que los destinatarios por defecto incluyan a administrador y a epaniagua."""
        self.assertIn("administrador@camsoft.com.do", DEFAULT_RECIPIENTS)
        self.assertIn("epaniagua@camsoft.com.do", DEFAULT_RECIPIENTS)
        self.assertEqual(PLAIN_TEXT_RECIPIENT, "administrador@camsoft.com.do")
        self.assertEqual(DEFAULT_SUBJECT_PREFIX, "JOBFORM:")

    def test_mask_sensitive_data(self):
        """Verifica que contraseñas, bearer tokens y JWTs sean enmascarados."""
        sample_text = (
            'Authorization: Bearer myBearerToken12345 '
            'raw_token: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.doNotLeakThis '
            'password: "SuperSecretPassword123" and x-api-key: "ABC123XYZ"'
        )
        masked = mask_sensitive_data(sample_text)
        self.assertNotIn("SuperSecretPassword123", masked)
        self.assertNotIn("doNotLeakThis", masked)
        self.assertNotIn("ABC123XYZ", masked)
        self.assertIn("[TOKEN_JWT_ENMASCARADO]", masked)
        self.assertIn("Bearer [TOKEN_ENMASCARADO]", masked)
        self.assertIn("[ENMASCARADO]", masked)

    def test_throttling_logic(self):
        """Verifica que errores idénticos dentro del cooldown sean bloqueados."""
        _throttle_cache.clear()
        sig = "test_module:42:Error_de_base_de_datos"
        cooldown = 10.0

        # Primer error: debe pasar
        self.assertFalse(_should_throttle(sig, cooldown))

        # Segundo error idéntico inmediato: debe ser bloqueado por throttling
        self.assertTrue(_should_throttle(sig, cooldown))

        # Error diferente: debe pasar
        self.assertFalse(_should_throttle("other_module:10:Different_error", cooldown))

    def test_safe_session_context_empty(self):
        """Verifica que get_safe_session_context no falle aun si no hay contexto Streamlit."""
        context = get_safe_session_context()
        self.assertIsInstance(context, dict)
        self.assertIn("user_name", context)
        self.assertIn("enviroment", context)
        self.assertIn("domain_name", context)

    def test_handler_emit_invokes_send_email(self):
        """Verifica que al emitir un log de ERROR se realicen dos envíos independientes: texto plano y plantilla HTML."""
        _throttle_cache.clear()

        handler = JiraEmailErrorHandler(
            recipients=["administrador@camsoft.com.do", "epaniagua@camsoft.com.do"],
            subject_prefix="JOBFORM:",
            cooldown_seconds=300,
            enabled=True
        )

        logger = logging.getLogger("test_jira_logger")
        logger.setLevel(logging.ERROR)
        logger.handlers.clear()
        logger.addHandler(handler)

        record = logger.makeRecord(
            name="test_jira_logger",
            level=logging.ERROR,
            fn="test_file.py",
            lno=100,
            msg="Error al procesar solicitud de usuario: NullReferenceException",
            args=(),
            exc_info=None
        )

        with patch("app.core.send_email") as mock_send_email:
            context = {
                "enviroment": "apis_qa",
                "version": "v1.0.0",
                "domain_name": "jobs.triple.com.do",
                "user_name": "Juan Perez <juan@example.com>",
                "company_name": "Triple",
                "page": "job_apply"
            }
            handler._send_worker(
                record=record,
                context=context,
                stack_trace=None,
                recipients=handler.recipients,
                subject_prefix=handler.subject_prefix
            )

            self.assertTrue(mock_send_email.called)
            self.assertEqual(mock_send_email.call_count, 2)

            # 1. Primer envío: administrador@camsoft.com.do en texto plano sin HTML
            call_plain_kwargs = mock_send_email.call_args_list[0][1]
            self.assertEqual(call_plain_kwargs["email"], ["administrador@camsoft.com.do"])
            self.assertTrue(call_plain_kwargs["subject"].startswith("JOBFORM: [apis_qa]"))
            self.assertIn("NullReferenceException", call_plain_kwargs["subject"])
            body_plain = call_plain_kwargs["body"]
            self.assertIn("⚠️ Notificación Automática de Error - JobForm", body_plain)
            self.assertIn("jobs.triple.com.do", body_plain)
            self.assertIn("Juan Perez", body_plain)
            # Validar ausencia estricta de HTML
            self.assertNotIn("<html", body_plain)
            self.assertNotIn("<table", body_plain)
            self.assertNotIn("<div", body_plain)
            self.assertNotIn("<span", body_plain)
            self.assertNotIn("&quot;", body_plain)

            # 2. Segundo envío: epaniagua@camsoft.com.do con plantilla HTML
            call_html_kwargs = mock_send_email.call_args_list[1][1]
            self.assertEqual(call_html_kwargs["email"], ["epaniagua@camsoft.com.do"])
            self.assertTrue(call_html_kwargs["subject"].startswith("JOBFORM: [apis_qa]"))
            body_html = call_html_kwargs["body"]
            self.assertIn("<!DOCTYPE html>", body_html)
            self.assertIn("<table", body_html)
            self.assertIn("⚠️ Notificación Automática de Error", body_html)

    def test_handler_emit_only_plain_text_recipient(self):
        """Verifica que si solo está configurado administrador@camsoft.com.do solo se realice un envío de texto plano."""
        _throttle_cache.clear()
        handler = JiraEmailErrorHandler(recipients=["administrador@camsoft.com.do"])
        record = logging.LogRecord(
            name="test_logger", level=logging.ERROR, pathname="test.py", lineno=1,
            msg="Error individual", args=(), exc_info=None
        )

        with patch("app.core.send_email") as mock_send_email:
            context = {"enviroment": "prod", "version": "v1.0.0", "domain_name": "camsoft.com.do", "user_name": "admin"}
            handler._send_worker(record, context, None, handler.recipients, "JOBFORM:")

            self.assertEqual(mock_send_email.call_count, 1)
            call_kwargs = mock_send_email.call_args[1]
            self.assertEqual(call_kwargs["email"], ["administrador@camsoft.com.do"])
            self.assertNotIn("<html", call_kwargs["body"])
            self.assertIn("Error individual", call_kwargs["body"])

    def test_handler_emit_only_html_recipient(self):
        """Verifica que si solo hay destinatarios diferentes a administrador@camsoft.com.do solo se envíe la plantilla HTML."""
        _throttle_cache.clear()
        handler = JiraEmailErrorHandler(recipients=["soporte@empresa.com", "dev@empresa.com"])
        record = logging.LogRecord(
            name="test_logger", level=logging.ERROR, pathname="test.py", lineno=1,
            msg="Error html", args=(), exc_info=None
        )

        with patch("app.core.send_email") as mock_send_email:
            context = {"enviroment": "prod", "version": "v1.0.0", "domain_name": "camsoft.com.do", "user_name": "soporte"}
            handler._send_worker(record, context, None, handler.recipients, "JOBFORM:")

            self.assertEqual(mock_send_email.call_count, 1)
            call_kwargs = mock_send_email.call_args[1]
            self.assertEqual(call_kwargs["email"], ["soporte@empresa.com", "dev@empresa.com"])
            self.assertIn("<!DOCTYPE html>", call_kwargs["body"])

    def test_send_worker_independent_resilience(self):
        """Verifica que si el envío en texto plano falla con una excepción, el envío HTML continúe y se complete."""
        _throttle_cache.clear()
        handler = JiraEmailErrorHandler(recipients=["administrador@camsoft.com.do", "epaniagua@camsoft.com.do"])
        record = logging.LogRecord(
            name="test_logger", level=logging.ERROR, pathname="test.py", lineno=1,
            msg="Error de resiliencia", args=(), exc_info=None
        )

        with patch("app.core.send_email", side_effect=[Exception("Error de red con JIRA"), {"result": "ok"}]) as mock_send_email:
            context = {"enviroment": "qa", "version": "v1.0.0", "domain_name": "triple.com.do", "user_name": "epaniagua"}
            handler._send_worker(record, context, None, handler.recipients, "JOBFORM:")

            self.assertEqual(mock_send_email.call_count, 2)
            call_2 = mock_send_email.call_args_list[1][1]
            self.assertEqual(call_2["email"], ["epaniagua@camsoft.com.do"])
            self.assertIn("<!DOCTYPE html>", call_2["body"])

    def test_build_email_body_text_formatting(self):
        """Verifica que _build_email_body_text formatee correctamente el texto plano y enmascare datos sensibles."""
        record = logging.LogRecord(
            name="test_logger",
            level=logging.ERROR,
            pathname="app/test.py",
            lineno=42,
            msg='Conexión fallida con token Bearer secretToken123 y password: "myPassword"',
            args=(),
            exc_info=None
        )
        context = {
            "enviroment": "production",
            "version": "v1.2.3",
            "domain_name": "empresa.com",
            "company_name": "Mi Empresa",
            "user_name": "jdoe",
            "page": "job_detail"
        }
        stack_trace = 'Traceback (most recent call last):\n  File "test.py", line 42, in test\n    raise ValueError("test")'

        body = _build_email_body_text(record, context, "2026-10-30 08:00:00", stack_trace)

        self.assertNotIn("secretToken123", body)
        self.assertNotIn("myPassword", body)
        self.assertIn("Bearer [TOKEN_ENMASCARADO]", body)
        self.assertIn("[ENMASCARADO]", body)

        self.assertNotIn("<", body)
        self.assertNotIn(">", body)
        self.assertNotIn("html", body.lower())

        self.assertIn("Nivel: ERROR", body)
        self.assertIn("Ambiente: production", body)
        self.assertIn("Versión: v1.2.3", body)
        self.assertIn("Dominio / Tenant: empresa.com", body)
        self.assertIn("Stack Trace / Detalle Técnico:", body)
        self.assertIn('raise ValueError("test")', body)

    def test_anti_recursion_guard(self):
        """Verifica que si send_email o el worker fallan, no ocurra recursión infinita."""
        _throttle_cache.clear()
        handler = JiraEmailErrorHandler(enabled=True)

        record = logging.LogRecord(
            name="app.core",
            level=logging.ERROR,
            pathname="app/core/__init__.py",
            lineno=50,
            msg="Error de red al llamar a EnviarEmail",
            args=(),
            exc_info=None
        )

        _thread_local.is_sending_error = True
        try:
            with patch.object(handler, "_dispatch_async") as mock_dispatch:
                handler.emit(record)
                self.assertFalse(mock_dispatch.called)
        finally:
            _thread_local.is_sending_error = False

    def test_setup_error_notifier_idempotent(self):
        """Verifica que llamar varias veces a setup_error_notifier no duplique el handler."""
        root_logger = logging.getLogger()
        
        h1 = setup_error_notifier()
        self.assertTrue(any(isinstance(h, JiraEmailErrorHandler) for h in root_logger.handlers))

        h2 = setup_error_notifier()
        self.assertIs(h1, h2)

        count = sum(1 for h in root_logger.handlers if isinstance(h, JiraEmailErrorHandler))
        self.assertEqual(count, 1)

    def test_ignored_error_patterns_not_dispatched(self):
        """Verifica que errores ignorados (como FMK24, SRH601089, etc.) sean filtrados sin enviar correo a JIRA."""
        handler = JiraEmailErrorHandler(enabled=True)
        record = logging.LogRecord(
            name="app.core",
            level=logging.ERROR,
            pathname="app/core/__init__.py",
            lineno=223,
            msg="API Business Error: {'errorCode': 'SRH601089', 'message': 'Error buscando detalle de Documentos'}",
            args=(),
            exc_info=None
        )

        with patch.object(handler, "_dispatch_async") as mock_dispatch:
            handler.emit(record)
            self.assertFalse(mock_dispatch.called)

        record_fmk24 = logging.LogRecord(
            name="app.core",
            level=logging.ERROR,
            pathname="app/core/__init__.py",
            lineno=227,
            msg="API Error: {'errorCode': 'FMK24', 'errorId': 24, 'message': 'El parámetro Password es incorrecto'}",
            args=(),
            exc_info=None
        )

        with patch.object(handler, "_dispatch_async") as mock_dispatch:
            handler.emit(record_fmk24)
            self.assertFalse(mock_dispatch.called)


if __name__ == "__main__":
    unittest.main()
