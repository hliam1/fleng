"""
Reconocimiento de voz (STT).

Proveedores: browser, groq, deepgram, gemini, openai.

Con STT_PROVIDER=browser la transcripcion ocurre en el navegador
(Web Speech API) y el servidor recibe texto ya escrito, no audio.
"""
from services import clients, config

NOMBRES_IDIOMA = {"es": "espanol", "en": "ingles"}

# Codigo de idioma que espera cada proveedor.
_LOCALES = {"es": "es-ES", "en": "en-US"}


def prefiere_navegador():
    """
    True si conviene intentar transcribir en el navegador primero.

    Es solo una preferencia, no una obligacion: el servidor siempre sabe
    transcribir. Si el navegador no puede (Firefox no trae la API; Brave y
    los demas derivados de Chromium no llevan la clave privada de Google y
    dan error de red siempre), el frontend cambia solo a enviar el audio.
    """
    return config.STT_PREFER_BROWSER


def transcribe(audio_bytes, mime_type, language_hint=None):
    """Transcribe audio a texto. Devuelve {"text": "..."}."""
    proveedor = config.STT_PROVIDER

    if proveedor == "groq":
        return _groq_transcribe(audio_bytes, mime_type, language_hint)
    if proveedor == "deepgram":
        return _deepgram_transcribe(audio_bytes, mime_type, language_hint)
    if proveedor == "gemini":
        return _gemini_transcribe(audio_bytes, mime_type, language_hint)
    if proveedor == "openai":
        return _openai_transcribe(audio_bytes, mime_type, language_hint)
    raise RuntimeError(f"STT_PROVIDER desconocido: {proveedor}")


def transcribe_and_translate(audio_bytes, mime_type, source_lang, target_lang):
    """
    Transcribe y traduce. Devuelve {"original": "...", "translated": "..."}.

    Gemini es multimodal: hace las dos cosas en UNA llamada (~600 ms menos).
    El resto de proveedores necesitan dos pasos: transcribir y luego traducir.
    """
    if config.STT_PROVIDER == "gemini":
        return _gemini_transcribe_and_translate(
            audio_bytes, mime_type, source_lang, target_lang
        )

    from services import translator  # import aqui para evitar ciclo de imports

    original = transcribe(audio_bytes, mime_type, source_lang)["text"]
    if not original:
        return {"original": "", "translated": ""}

    traducido = translator.translate_text(original, source_lang, target_lang)
    return {"original": original, "translated": traducido}


# ------------------------------------------------------------------ Groq

def _groq_transcribe(audio_bytes, mime_type, language_hint):
    extension = "webm" if "webm" in mime_type else "mp4" if "mp4" in mime_type else "wav"
    archivos = {"file": (f"audio.{extension}", audio_bytes, mime_type)}
    datos = {"model": config.MODELS["groq"]["stt"], "response_format": "json"}

    # Temperatura 0: la transcripcion debe ser consistente, no creativa.
    # Sin esto Whisper a veces inventa o junta palabras con habla rapida.
    datos["temperature"] = "0"

    if language_hint:
        datos["language"] = language_hint
        # El prompt de contexto orienta a Whisper hacia el idioma y el
        # registro esperado. Mejora mucho el manejo de habla continua y
        # rapida, que era el sintoma que reportaba el usuario en Brave.
        prompts = {
            "es": "Transcripcion de una conversacion en espanol. El hablante practica espanol.",
            "en": "Transcription of a conversation in English. The speaker is practicing English.",
        }
        if language_hint in prompts:
            datos["prompt"] = prompts[language_hint]

    respuesta = clients.http().post(
        f"{clients.GROQ_BASE}/audio/transcriptions",
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
        files=archivos,
        data=datos,
        timeout=clients.TIMEOUT_SECONDS,
    )
    clients.raise_for_status(respuesta, "Groq STT")
    return {"text": (respuesta.json().get("text") or "").strip()}


# -------------------------------------------------------------- Deepgram

def _deepgram_transcribe(audio_bytes, mime_type, language_hint):
    parametros = {
        "model": config.MODELS["deepgram"]["stt"],
        "smart_format": "true",
        "punctuate": "true",
    }
    if language_hint:
        parametros["language"] = language_hint

    cabeceras = clients.token_auth(config.DEEPGRAM_API_KEY)
    cabeceras["Content-Type"] = mime_type

    respuesta = clients.http().post(
        f"{clients.DEEPGRAM_BASE}/listen",
        headers=cabeceras,
        params=parametros,
        data=audio_bytes,
        timeout=clients.TIMEOUT_SECONDS,
    )
    clients.raise_for_status(respuesta, "Deepgram STT")

    try:
        alternativa = respuesta.json()["results"]["channels"][0]["alternatives"][0]
        return {"text": (alternativa.get("transcript") or "").strip()}
    except (KeyError, IndexError):
        return {"text": ""}


# ---------------------------------------------------------------- OpenAI

def _openai_transcribe(audio_bytes, mime_type, language_hint):
    extension = "webm" if "webm" in mime_type else "mp4" if "mp4" in mime_type else "wav"
    archivos = {"file": (f"audio.{extension}", audio_bytes, mime_type)}
    datos = {"model": config.MODELS["openai"]["stt"]}
    if language_hint:
        datos["language"] = language_hint

    respuesta = clients.http().post(
        f"{clients.OPENAI_BASE}/audio/transcriptions",
        headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
        files=archivos,
        data=datos,
        timeout=clients.TIMEOUT_SECONDS,
    )
    clients.raise_for_status(respuesta, "OpenAI STT")
    return {"text": (respuesta.json().get("text") or "").strip()}


# ---------------------------------------------------------------- Gemini

def _cliente_gemini():
    try:
        from google import genai
    except ImportError as error:
        raise RuntimeError(
            "Para usar Gemini instala su libreria: pip install google-genai"
        ) from error
    return genai


def _gemini_transcribe(audio_bytes, mime_type, language_hint):
    genai = _cliente_gemini()
    from google.genai import types

    idioma = NOMBRES_IDIOMA.get(language_hint, "")
    pista = f" El audio esta en {idioma}." if idioma else ""
    instruccion = (
        "Transcribe exactamente lo que se dice en este audio. "
        "Devuelve solo el texto hablado, sin comentarios." + pista
    )

    cliente = genai.Client(api_key=config.GEMINI_API_KEY)
    respuesta = cliente.models.generate_content(
        model=config.MODELS["gemini"]["fast"],
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            instruccion,
        ],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_level="minimal")
        ),
    )
    return {"text": (respuesta.text or "").strip()}


def _gemini_transcribe_and_translate(audio_bytes, mime_type, source_lang, target_lang):
    """Transcribe y traduce en una sola llamada aprovechando que es multimodal."""
    genai = _cliente_gemini()
    from google.genai import types
    import json

    origen = NOMBRES_IDIOMA.get(source_lang, source_lang)
    destino = NOMBRES_IDIOMA.get(target_lang, target_lang)

    instruccion = (
        f"El audio esta en {origen}. Haz dos cosas:\n"
        f"1. Transcribe exactamente lo que se dice.\n"
        f"2. Traduce esa transcripcion a {destino}.\n"
        'Responde solo con JSON: {"original": "...", "translated": "..."}'
    )

    cliente = genai.Client(api_key=config.GEMINI_API_KEY)
    respuesta = cliente.models.generate_content(
        model=config.MODELS["gemini"]["fast"],
        contents=[
            types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
            instruccion,
        ],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            thinking_config=types.ThinkingConfig(thinking_level="minimal"),
        ),
    )

    try:
        datos = json.loads((respuesta.text or "").strip())
        return {
            "original": (datos.get("original") or "").strip(),
            "translated": (datos.get("translated") or "").strip(),
        }
    except json.JSONDecodeError:
        # Si el modelo no devolvio JSON valido, se hace en dos pasos.
        from services import translator

        original = _gemini_transcribe(audio_bytes, mime_type, source_lang)["text"]
        return {
            "original": original,
            "translated": translator.translate_text(original, source_lang, target_lang),
        }
