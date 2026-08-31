"""
Configuracion centralizada de proveedores.

Cambiar de API = editar .env, no el codigo.
Cada capacidad (STT, LLM, TTS) usa un proveedor independiente.
"""
import os
from dotenv import load_dotenv

load_dotenv()


def _get(name, default=""):
    """Lee una variable de entorno y limpia espacios accidentales."""
    value = (os.getenv(name) or default).strip()
    # Tolera que el usuario deje los parentesis del .env.example puestos.
    if value.startswith("(") and value.endswith(")"):
        return ""
    return value


# ---------------------------------------------------------------- proveedores

# Quien transcribe en el SERVIDOR. Siempre debe haber uno configurado:
# es la red de seguridad cuando el navegador no puede transcribir.
STT_PROVIDER = _get("STT_PROVIDER", "groq").lower()
LLM_PROVIDER = _get("LLM_PROVIDER", "groq").lower()
TTS_PROVIDER = _get("TTS_PROVIDER", "deepgram").lower()

def _es_verdadero(valor):
    return valor.lower() in ("1", "true", "si", "yes", "on")

# Intentar primero el reconocimiento del navegador: es gratis e instantaneo.
# Si falla (Firefox no lo tiene; Brave, Chromium y derivados no llevan la
# clave privada de Google y siempre dan error de red), la aplicacion pasa
# sola a transcribir en el servidor con STT_PROVIDER.
STT_PREFER_BROWSER = _es_verdadero(_get("STT_PREFER_BROWSER", "true"))

# Compatibilidad: antes STT_PROVIDER=browser significaba "transcribe el
# navegador y el servidor no sabe hacerlo". Eso dejaba la aplicacion sin
# alternativa cuando el navegador fallaba. Ahora se traduce a la nueva
# forma: preferir el navegador, pero con Groq detras por si acaso.
if STT_PROVIDER == "browser":
    STT_PREFER_BROWSER = True
    STT_PROVIDER = "groq"

# ------------------------------------------------------------------- claves

GROQ_API_KEY = _get("GROQ_API_KEY")
DEEPGRAM_API_KEY = _get("DEEPGRAM_API_KEY")
OPENAI_API_KEY = _get("OPENAI_API_KEY")
GEMINI_API_KEY = _get("GEMINI_API_KEY")
ELEVENLABS_API_KEY = _get("ELEVENLABS_API_KEY")

# ------------------------------------------------------------------ modelos

# Modelos de Groq que SI razonan y aceptan reasoning_effort. A los demas
# (los Llama, ya retirados) no se les debe mandar ese parametro.
GROQ_REASONING_MODELS = ("openai/gpt-oss-20b", "openai/gpt-oss-120b")

MODELS = {
    "groq": {
        # Groq retiro los modelos Llama (llama-3.1-8b-instant y
        # llama-3.3-70b-versatile) el 17 de junio de 2026. Sus reemplazos
        # oficiales son los GPT-OSS, que ademas son mas rapidos y baratos.
        # Si vuelven a cambiar, se ajustan aqui o en el .env sin tocar nada mas.
        "fast": _get("GROQ_FAST_MODEL", "openai/gpt-oss-20b"),
        "smart": _get("GROQ_SMART_MODEL", "openai/gpt-oss-120b"),
        "stt": _get("GROQ_STT_MODEL", "whisper-large-v3-turbo"),
    },
    "deepgram": {
        "stt": _get("DEEPGRAM_STT_MODEL", "nova-2"),
        # Aura NO es multilingue: cada voz habla un solo idioma.
        # Por eso hay una voz por idioma en vez de una sola global.
        "voice_en": _get("DEEPGRAM_VOICE_EN", "aura-2-thalia-en"),
        "voice_es": _get("DEEPGRAM_VOICE_ES", "aura-2-celeste-es"),
    },
    "openai": {
        "fast": _get("OPENAI_FAST_MODEL", "gpt-4o-mini"),
        "smart": _get("OPENAI_SMART_MODEL", "gpt-4o"),
        "stt": _get("OPENAI_STT_MODEL", "whisper-1"),
        "tts": _get("OPENAI_TTS_MODEL", "tts-1"),
        # Las voces de OpenAI si son multilingues: una sirve para ambos idiomas.
        "voice_en": _get("OPENAI_VOICE", "nova"),
        "voice_es": _get("OPENAI_VOICE", "nova"),
    },
    "gemini": {
        "fast": _get("GEMINI_FAST_MODEL", "gemini-3.1-flash-lite"),
        "smart": _get("GEMINI_SMART_MODEL", "gemini-3.5-flash"),
        "tts": _get("GEMINI_TTS_MODEL", "gemini-3.1-flash-tts-preview"),
        "voice_en": _get("GEMINI_VOICE", "Kore"),
        "voice_es": _get("GEMINI_VOICE", "Kore"),
    },
    "elevenlabs": {
        "tts": _get("ELEVENLABS_TTS_MODEL", "eleven_flash_v2_5"),
        "voice_en": _get("ELEVENLABS_VOICE", "21m00Tcm4TlvDq8ikWAM"),
        "voice_es": _get("ELEVENLABS_VOICE", "21m00Tcm4TlvDq8ikWAM"),
    },
}

# Que clave necesita cada proveedor. "browser" no necesita ninguna.
_KEY_FOR_PROVIDER = {
    "groq": ("GROQ_API_KEY", GROQ_API_KEY),
    "deepgram": ("DEEPGRAM_API_KEY", DEEPGRAM_API_KEY),
    "openai": ("OPENAI_API_KEY", OPENAI_API_KEY),
    "gemini": ("GEMINI_API_KEY", GEMINI_API_KEY),
    "elevenlabs": ("ELEVENLABS_API_KEY", ELEVENLABS_API_KEY),
}

# Que proveedores son validos para cada capacidad.
VALID_PROVIDERS = {
    "stt": ("groq", "deepgram", "gemini", "openai"),
    "llm": ("groq", "gemini", "openai"),
    "tts": ("deepgram", "openai", "gemini", "elevenlabs"),
}


def voice_for(language):
    """Devuelve la voz del proveedor TTS activo para el idioma dado."""
    key = "voice_es" if language == "es" else "voice_en"
    return MODELS[TTS_PROVIDER][key]


def config_errors():
    """
    Devuelve una lista de problemas de configuracion en texto plano.
    Vacia = todo bien. Se muestra en el banner de la interfaz.
    """
    problemas = []

    for capacidad, proveedor in (
        ("stt", STT_PROVIDER),
        ("llm", LLM_PROVIDER),
        ("tts", TTS_PROVIDER),
    ):
        validos = VALID_PROVIDERS[capacidad]
        if proveedor not in validos:
            problemas.append(
                f"{capacidad.upper()}_PROVIDER='{proveedor}' no es valido. "
                f"Opciones: {', '.join(validos)}"
            )
            continue

        nombre_clave, valor_clave = _KEY_FOR_PROVIDER[proveedor]
        if nombre_clave and not valor_clave:
            falta = f"Falta {nombre_clave} en el archivo .env"
            if falta not in problemas:
                problemas.append(falta)

    return problemas


def missing_keys():
    """Alias historico. Se mantiene para no romper codigo que ya lo usaba."""
    return config_errors()


# Tope de longitud de respuesta.
#
# Es la palanca de velocidad mas efectiva que tenemos. No solo acorta la
# generacion del texto: como la sintesis de voz tarda en proporcion a los
# caracteres, una respuesta a la mitad de larga tambien se convierte en voz
# en la mitad de tiempo. Recorta en los dos sitios a la vez.
MAX_TOKENS = {
    "chat": int(_get("MAX_TOKENS_CHAT", "160") or 160),
    "translate": int(_get("MAX_TOKENS_TRANSLATE", "300") or 300),
    "evaluate": int(_get("MAX_TOKENS_EVALUATE", "900") or 900),
}


def active_summary():
    """Resumen legible de la configuracion activa."""
    return {
        "stt": STT_PROVIDER,
        "llm": LLM_PROVIDER,
        "tts": TTS_PROVIDER,
        "prefer_browser": STT_PREFER_BROWSER,
    }
