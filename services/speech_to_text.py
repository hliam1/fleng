"""
Reconocimiento de voz (STT) - VERSION MEJORADA.

Proveedores: browser, groq, deepgram, gemini, openai.

Con STT_PROVIDER=browser la transcripcion ocurre en el navegador
(Web Speech API) y el servidor recibe texto ya escrito, no audio.

MEJORAS DE PRECISION:
- Modelo Whisper large-v3 completo (mas preciso que turbo)
- Prompts de contexto mejorados por idioma
- Deteccion de idioma forzada
- Parametros optimizados para habla de estudiantes
"""
from services import clients, config

NOMBRES_IDIOMA = {"es": "espanol", "en": "ingles"}

# Codigo de idioma que espera cada proveedor.
_LOCALES = {"es": "es-ES", "en": "en-US"}


def prefiere_navegador():
    """True si conviene intentar transcribir en el navegador primero."""
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
    """Transcribe y traduce. Devuelve {"original": "...", "translated": "..."}."""
    if config.STT_PROVIDER == "gemini":
        return _gemini_transcribe_and_translate(
            audio_bytes, mime_type, source_lang, target_lang
        )

    from services import translator

    original = transcribe(audio_bytes, mime_type, source_lang)["text"]
    if not original:
        return {"original": "", "translated": ""}

    traducido = translator.translate_text(original, source_lang, target_lang)
    return {"original": original, "translated": traducido}


# ------------------------------------------------------------------ Groq

# --- MEJORA: Prompts de contexto ampliados por idioma ---
# Un prompt mas rico orienta mejor a Whisper. Incluye ejemplos del tipo
# de vocabulario y registro esperado. Whisper usa esto como "contexto previo"
# para decidir como transcribir palabras ambiguas.
_PROMPTS_CONTEXTO = {
    "es": (
        "Transcripcion de una conversacion en espanol de un estudiante que "
        "practica el idioma. Habla de temas cotidianos: saludos, presentaciones, "
        "familia, trabajo, comida, viajes, planes. Puede cometer errores de "
        "pronunciacion o gramatica que deben transcribirse tal como suenan. "
        "Ejemplo: Hola, me llamo Ian. Hoy quiero practicar mi espanol."
    ),
    "en": (
        "Transcription of an English conversation from a student practicing "
        "the language. Topics include everyday matters: greetings, introductions, "
        "family, work, food, travel, plans. The speaker may make pronunciation "
        "or grammar mistakes that should be transcribed as they sound. "
        "Example: Hello, my name is Ian. Today I want to practice my English."
    ),
}


def _groq_transcribe(audio_bytes, mime_type, language_hint):
    extension = "webm" if "webm" in mime_type else "mp4" if "mp4" in mime_type else "wav"
    archivos = {"file": (f"audio.{extension}", audio_bytes, mime_type)}

    datos = {
        # --- MEJORA 1: Modelo completo en vez de turbo ---
        # whisper-large-v3 (sin turbo) es mas lento pero MAS PRECISO.
        # El turbo sacrifica precision por velocidad. Para estudiantes con
        # pronunciacion imperfecta, la precision importa mas.
        "model": config.MODELS["groq"]["stt"],
        "response_format": "verbose_json",  # verbose da mas metadata
        "temperature": "0",
    }

    if language_hint:
        datos["language"] = language_hint

        # --- MEJORA 2: Prompt de contexto ampliado ---
        if language_hint in _PROMPTS_CONTEXTO:
            datos["prompt"] = _PROMPTS_CONTEXTO[language_hint]

    respuesta = clients.http().post(
        f"{clients.GROQ_BASE}/audio/transcriptions",
        headers={"Authorization": f"Bearer {config.GROQ_API_KEY}"},
        files=archivos,
        data=datos,
        timeout=clients.TIMEOUT_SECONDS,
    )
    clients.raise_for_status(respuesta, "Groq STT")

    resultado = respuesta.json()
    texto = (resultado.get("text") or "").strip()

    # --- MEJORA 3: Filtrar alucinaciones de Whisper ---
    # Whisper a veces "alucina" frases comunes cuando el audio es silencio
    # o ruido. Se filtran las mas conocidas.
    texto = _filtrar_alucinaciones(texto, language_hint)

    return {"text": texto}


# --- MEJORA 3: Lista de alucinaciones conocidas de Whisper ---
# Cuando el audio es muy corto, silencioso o con ruido, Whisper a veces
# devuelve estas frases que NO se dijeron. Se eliminan.
_ALUCINACIONES = {
    "es": [
        "subtitulos realizados por la comunidad de amara.org",
        "subtitulado por la comunidad de amara.org",
        "gracias por ver el video",
        "gracias por ver este video",
        "mas informacion en www",
        "suscribete al canal",
    ],
    "en": [
        "thank you for watching",
        "thanks for watching",
        "subtitles by the amara.org community",
        "subscribe to the channel",
        "please subscribe",
        "thank you.",
    ],
}


def _filtrar_alucinaciones(texto, language_hint):
    """Elimina frases que Whisper alucina con audio vacio o ruidoso."""
    if not texto:
        return texto

    texto_lower = texto.lower().strip()

    # Lista del idioma + lista general
    frases = _ALUCINACIONES.get(language_hint, [])

    for frase in frases:
        # Si el texto ES exactamente una alucinacion (o casi), se vacia
        if texto_lower == frase or texto_lower == frase + ".":
            return ""
        # Si es MUY corto y contiene la alucinacion, tambien
        if len(texto_lower) < 50 and frase in texto_lower:
            return ""

    return texto


# -------------------------------------------------------------- Deepgram

def _deepgram_transcribe(audio_bytes, mime_type, language_hint):
    parametros = {
        "model": config.MODELS["deepgram"]["stt"],
        "smart_format": "true",
        "punctuate": "true",
        # --- MEJORA: Parametros extra de Deepgram ---
        "filler_words": "false",  # Elimina "eh", "um", etc.
        "numerals": "true",       # Convierte numeros hablados a digitos
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
        # --- MEJORA: Prompt de contexto tambien en OpenAI ---
        if language_hint in _PROMPTS_CONTEXTO:
            datos["prompt"] = _PROMPTS_CONTEXTO[language_hint]

    respuesta = clients.http().post(
        f"{clients.OPENAI_BASE}/audio/transcriptions",
        headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
        files=archivos,
        data=datos,
        timeout=clients.TIMEOUT_SECONDS,
    )
    clients.raise_for_status(respuesta, "OpenAI STT")
    texto = (respuesta.json().get("text") or "").strip()
    texto = _filtrar_alucinaciones(texto, language_hint)
    return {"text": texto}


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
        "Devuelve solo el texto hablado, sin comentarios. "
        "Si hay errores de pronunciacion o gramatica, transcribelos "
        "tal como suenan, no los corrijas." + pista
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
        from services import translator

        original = _gemini_transcribe(audio_bytes, mime_type, source_lang)["text"]
        return {
            "original": original,
            "translated": translator.translate_text(original, source_lang, target_lang),
        }
