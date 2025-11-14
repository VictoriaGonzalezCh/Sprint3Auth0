import re
import time

from django.http import HttpResponse


# Patrones simples de SQL injection que queremos bloquear
SUSPICIOUS_SQL_PATTERNS = [
    r";\s*delete\s",      # ;DELETE ...
    r";\s*drop\s",        # ;DROP ...
    r";\s*update\s",      # ;UPDATE ...
    r"--",                # comentario SQL
    r"'\s*or\s+1=1",      # ' OR 1=1
]


class SqlInjectionProtectionMiddleware:
    """
    Middleware muy simple para el experimento de integridad:
    - Inspecciona path, query string y body en busca de patrones de SQL injection.
    - Si encuentra algo sospechoso, devuelve 403 inmediatamente,
      con un mensaje de acceso no autorizado y el tiempo de detección.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.compiled_patterns = [
            re.compile(pat, re.IGNORECASE) for pat in SUSPICIOUS_SQL_PATTERNS
        ]

    def __call__(self, request):
        start = time.time()

        # Construimos una cadena con todo lo relevante de la petición
        raw_parts = [
            request.path,
            request.META.get("QUERY_STRING", ""),
        ]

        if request.body:
            try:
                body_text = request.body.decode("utf-8", errors="ignore")
            except Exception:
                body_text = ""
            raw_parts.append(body_text)

        raw = " ".join(raw_parts)

        # Si alguno de los patrones hace match -> bloqueamos
        if any(pattern.search(raw) for pattern in self.compiled_patterns):
            elapsed_ms = (time.time() - start) * 1000.0
            content = (
                "Acceso no autorizado - intento de inyección SQL bloqueado. "
                f"Tiempo de detección: {elapsed_ms:.2f} ms"
            )
            response = HttpResponse(content, status=403)
            response["X-Detection-Time-ms"] = f"{elapsed_ms:.2f}"
            return response

        # Si no se detecta nada raro, continuamos el flujo normal
        response = self.get_response(request)
        return response
