"""
Diagnostico temporal de ElevenLabs.

Hace una llamada REAL de Text-to-Speech y devuelve la respuesta completa
(estado HTTP + cuerpo), para ver el error EXACTO que ElevenLabs regresa
desde el servidor de Railway. No expone la clave.

COMO USAR: abre  /api/diag/elevenlabs  en el navegador.
BORRA este archivo y su ruta en app.py cuando termines de diagnosticar.
"""
from services import clients, config


def probar_elevenlabs():
    voz = config.voice_for("pt")
    modelo = config.MODELS["elevenlabs"]["tts"]
    clave = config.ELEVENLABS_API_KEY or ""

    info = {
        "clave_presente": bool(clave),
        "clave_pista": (clave[:4] + "..." + clave[-4:]) if len(clave) > 8 else "(vacia o muy corta)",
        "voice_id_usada": voz,
        "model_id_usado": modelo,
    }

    try:
        r = clients.http().post(
            f"{clients.ELEVENLABS_BASE}/text-to-speech/{voz}",
            headers={"xi-api-key": clave, "Content-Type": "application/json"},
            json={
                "text": "Ola, bom dia.",
                "model_id": modelo,
                "voice_settings": {"stability": 0.5, "similarity_boost": 0.75},
            },
            timeout=clients.TIMEOUT_SECONDS,
        )
        info["status_http"] = r.status_code
        ctype = r.headers.get("content-type", "")
        if "application/json" in ctype:
            info["respuesta_elevenlabs"] = r.json()
        elif r.status_code < 400:
            info["respuesta_elevenlabs"] = f"OK: audio recibido ({len(r.content)} bytes). La voz SI funciona."
        else:
            info["respuesta_elevenlabs"] = (r.text or "")[:1000]
    except Exception as e:
        info["status_http"] = "sin respuesta"
        info["respuesta_elevenlabs"] = str(e)[:1000]

    return info
