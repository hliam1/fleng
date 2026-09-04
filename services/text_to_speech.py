"""
Sintesis de voz (TTS).

Proveedores: deepgram, openai, gemini, elevenlabs.

Dos decisiones de diseno importantes:

1. El audio se devuelve en base64 dentro del JSON, no como archivo .wav
   en disco. Elimina un viaje HTTP extra y evita que static/audio/ se
   llene de archivos que nadie borra.

2. synthesize_speech() recibe el idioma. Las voces de Deepgram no son
   multilingues: una voz inglesa leyendo espanol suena mal. El idioma
   decide la voz.
"""
import base64
import io
import time
import wave

from services import clients, config

# Formato del PCM crudo que devuelve Gemini TTS.
PCM_CANALES = 1
PCM_FRECUENCIA = 24000
PCM_ANCHO_MUESTRA = 2

INTENTOS_MAXIMOS = 3
ESPERA_ENTRE_INTENTOS = 1


def synthesize_speech(text, language="en"):
    """
    Convierte texto en audio.

    language: "es" o "en". Decide la voz.
    Devuelve {"audio_base64": "...", "mime_type": "audio/wav"}
    """
    if not text or not text.strip():
        raise ValueError("No hay texto para convertir en voz.")

    proveedor = config.TTS_PROVIDER
    generadores = {
        "deepgram": _deepgram_tts,
        "openai": _openai_tts,
        "gemini": _gemini_tts,
        "elevenlabs": _elevenlabs_tts,
    }

    generador = generadores.get(proveedor)
    if generador is None:
        raise RuntimeError(f"TTS_PROVIDER desconocido: {proveedor}")

    return _con_reintentos(generador, text.strip(), language, proveedor)


def _con_reintentos(generador, text, language, proveedor):
    """
    Reintenta ante fallos temporales, pero no ante errores que reintentar
    no arregla (clave mala, voz inexistente, sin credito).
    """
    ultimo_error = None

    for intento in range(INTENTOS_MAXIMOS):
        try:
            return generador(text, language)
        except RuntimeError as error:
            mensaje = str(error)
            if any(codigo in mensaje for codigo in ("401", "402", "404")):
                raise  # reintentar no lo va a arreglar
            ultimo_error = error
        except Exception as error:
            ultimo_error = error

        if intento < INTENTOS_MAXIMOS - 1:
            time.sleep(ESPERA_ENTRE_INTENTOS * (intento + 1))

    raise RuntimeError(
        f"{proveedor} TTS fallo tras {INTENTOS_MAXIMOS} intentos: {ultimo_error}"
    )


# -------------------------------------------------------------- Deepgram

def _deepgram_tts(text, language):
    parametros = {
        "model": config.voice_for(language),
        "encoding": "linear16",
        "sample_rate": PCM_FRECUENCIA,
        "container": "wav",
    }
    respuesta = clients.http().post(
        f"{clients.DEEPGRAM_BASE}/speak",
        headers={
            "Authorization": f"Token {config.DEEPGRAM_API_KEY}",
            "Content-Type": "application/json",
        },
        params=parametros,
        json={"text": text},
        timeout=clients.TIMEOUT_SECONDS,
    )
    clients.raise_for_status(respuesta, "Deepgram TTS")
    return _empaquetar(respuesta.content, "audio/wav")


# ---------------------------------------------------------------- OpenAI

def _openai_tts(text, language):
    respuesta = clients.http().post(
        f"{clients.OPENAI_BASE}/audio/speech",
        headers=clients.bearer(config.OPENAI_API_KEY),
        json={
            "model": config.MODELS["openai"]["tts"],
            "input": text,
            "voice": config.voice_for(language),
        },
        timeout=clients.TIMEOUT_SECONDS,
    )
    clients.raise_for_status(respuesta, "OpenAI TTS")
    return _empaquetar(respuesta.content, "audio/mpeg")


# ------------------------------------------------------------ ElevenLabs

def _elevenlabs_tts(text, language):
    voz = config.voice_for(language)
    respuesta = clients.http().post(
        f"{clients.ELEVENLABS_BASE}/text-to-speech/{voz}",
        headers={
            "xi-api-key": config.ELEVENLABS_API_KEY,
            "Content-Type": "application/json",
        },
        json={
            "text": text,
            "model_id": config.MODELS["elevenlabs"]["tts"],
            "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
        },
        timeout=clients.TIMEOUT_SECONDS,
    )
    clients.raise_for_status(respuesta, "ElevenLabs TTS")
    return _empaquetar(respuesta.content, "audio/mpeg")


# ---------------------------------------------------------------- Gemini

def _gemini_tts(text, language):
    try:
        from google import genai
        from google.genai import types
    except ImportError as error:
        raise RuntimeError(
            "Para usar Gemini instala su libreria: pip install google-genai"
        ) from error

    cliente = genai.Client(api_key=config.GEMINI_API_KEY)
    respuesta = cliente.models.generate_content(
        model=config.MODELS["gemini"]["tts"],
        contents=text,
        config=types.GenerateContentConfig(
            response_modalities=["AUDIO"],
            speech_config=types.SpeechConfig(
                voice_config=types.VoiceConfig(
                    prebuilt_voice_config=types.PrebuiltVoiceConfig(
                        voice_name=config.voice_for(language)
                    )
                )
            ),
        ),
    )
    pcm = respuesta.candidates[0].content.parts[0].inline_data.data
    return _empaquetar(pcm_a_wav(pcm), "audio/wav")


# ------------------------------------------------------------- utilidades

def _empaquetar(audio_bytes, mime_type):
    """Convierte los bytes de audio en la respuesta que espera el frontend."""
    if not audio_bytes:
        raise RuntimeError("El proveedor devolvio audio vacio.")
    return {
        "audio_base64": base64.b64encode(audio_bytes).decode("utf-8"),
        "mime_type": mime_type,
    }


def pcm_a_wav(pcm_data):
    """Envuelve PCM crudo en una cabecera WAV valida."""
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as archivo_wav:
        archivo_wav.setnchannels(PCM_CANALES)
        archivo_wav.setsampwidth(PCM_ANCHO_MUESTRA)
        archivo_wav.setframerate(PCM_FRECUENCIA)
        archivo_wav.writeframes(pcm_data)
    return buffer.getvalue()
