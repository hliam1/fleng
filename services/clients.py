"""
Utilidades compartidas por todos los proveedores:
sesion HTTP reutilizable, errores legibles y medicion de tiempos.
"""
import logging
import time
from contextlib import contextmanager
from functools import lru_cache

import requests

logger = logging.getLogger("fleng")

TIMEOUT_SECONDS = 60

GROQ_BASE = "https://api.groq.com/openai/v1"
DEEPGRAM_BASE = "https://api.deepgram.com/v1"
OPENAI_BASE = "https://api.openai.com/v1"
ELEVENLABS_BASE = "https://api.elevenlabs.io/v1"


@lru_cache(maxsize=1)
def http():
    """
    Sesion HTTP unica y reutilizada.
    Mantiene viva la conexion TLS: ahorra ~100-200 ms por llamada.
    """
    session = requests.Session()
    adapter = requests.adapters.HTTPAdapter(pool_connections=4, pool_maxsize=8)
    session.mount("https://", adapter)
    return session


def bearer(api_key):
    """Cabecera de autenticacion tipo Bearer (Groq, OpenAI)."""
    return {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}


def token_auth(api_key):
    """Cabecera de autenticacion tipo Token (Deepgram)."""
    return {"Authorization": f"Token {api_key}"}


def raise_for_status(response, proveedor=""):
    """Convierte un error HTTP en un mensaje que se entiende."""
    if response.status_code < 400:
        return

    detalle = ""
    try:
        data = response.json()
        if isinstance(data, dict):
            error = data.get("error") or data.get("err_msg") or data.get("message")
            if isinstance(error, dict):
                detalle = error.get("message", str(error))
            elif error:
                detalle = str(error)
    except Exception:
        detalle = (response.text or "")[:200]

    etiqueta = f"[{proveedor}] " if proveedor else ""
    codigo = response.status_code

    if codigo == 401:
        raise RuntimeError(
            f"{etiqueta}Clave de API rechazada (401). "
            f"Revisa la clave en el archivo .env. {detalle}"
        )
    if codigo == 402:
        raise RuntimeError(f"{etiqueta}Sin credito disponible (402). {detalle}")
    if codigo == 404:
        raise RuntimeError(
            f"{etiqueta}Modelo o voz no encontrado (404). "
            f"Actualiza el nombre en services/config.py o en .env. {detalle}"
        )
    if codigo == 429:
        raise RuntimeError(
            f"{etiqueta}Limite de uso alcanzado (429). Espera un momento. {detalle}"
        )
    raise RuntimeError(f"{etiqueta}Error {codigo}: {detalle}")


class Stopwatch:
    """
    Mide cuanto tarda cada etapa de una peticion.

    Uso:
        sw = Stopwatch()
        with sw.stage("tts"):
            ...
        sw.as_dict()  ->  {"tts": 812, "total": 830}

    El resultado viaja en el JSON de respuesta para poder documentar
    la latencia real en el informe.
    """

    def __init__(self):
        self._stages = {}
        self._start = time.perf_counter()

    @contextmanager
    def stage(self, name):
        inicio = time.perf_counter()
        try:
            yield
        finally:
            transcurrido = (time.perf_counter() - inicio) * 1000
            self._stages[name] = round(self._stages.get(name, 0) + transcurrido)

    def total_ms(self):
        return round((time.perf_counter() - self._start) * 1000)

    def as_dict(self):
        datos = dict(self._stages)
        datos["total"] = self.total_ms()
        return datos

    def log(self, etiqueta):
        """Escribe los tiempos en la consola del servidor."""
        datos = self.as_dict()
        detalle = "  ".join(f"{k}={v}ms" for k, v in datos.items())
        logger.info("%s  %s", etiqueta, detalle)
