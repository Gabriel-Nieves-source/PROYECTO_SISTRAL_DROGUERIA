"""Limitador de intentos fallidos de login (OWASP API4:2023 y API2:2023).

En memoria: suficiente para una sola instancia. Con varias instancias, usar Redis.
"""
import time
from collections import defaultdict, deque


class LoginRateLimiter:

    def __init__(self, max_intentos: int, ventana_segundos: int, reloj=time.monotonic):
        self.max_intentos = max_intentos
        self.ventana = ventana_segundos
        self._reloj = reloj
        self._fallos: dict[str, deque[float]] = defaultdict(deque)

    def _purgar(self, clave: str) -> deque[float]:
        cola = self._fallos[clave]
        limite = self._reloj() - self.ventana
        while cola and cola[0] <= limite:
            cola.popleft()
        return cola

    def bloqueado(self, clave: str) -> bool:
        return len(self._purgar(clave)) >= self.max_intentos

    def registrar_fallo(self, clave: str) -> None:
        self._purgar(clave).append(self._reloj())

    def reiniciar(self, clave: str) -> None:
        self._fallos.pop(clave, None)
