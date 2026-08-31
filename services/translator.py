"""
Traduccion de texto entre espanol e ingles.
Delega en la capa LLM, asi que respeta LLM_PROVIDER del .env.
"""
from services import config, llm

NOMBRES_IDIOMA = {"es": "espanol", "en": "ingles"}


def translate_text(text, source_lang, target_lang):
    """Traduce un texto. Devuelve un string."""
    if not text or not text.strip():
        return ""
    if source_lang == target_lang:
        return text

    origen = NOMBRES_IDIOMA.get(source_lang, source_lang)
    destino = NOMBRES_IDIOMA.get(target_lang, target_lang)

    instruccion = (
        f"Eres un traductor profesional. Traduce el texto de {origen} a {destino}. "
        "Manten el tono y el registro del original. "
        "Responde unicamente con la traduccion: sin comillas, sin explicaciones, "
        "sin repetir el texto original."
    )

    # La traduccion no puede ser mucho mas larga que el original. El tope
    # evita que el modelo se enrolle si malinterpreta la instruccion.
    return llm.chat(
        instruccion,
        [{"role": "user", "content": text}],
        tier="fast",
        max_tokens=config.MAX_TOKENS["translate"],
    )
