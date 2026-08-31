"""
Capa de modelo de lenguaje unificada.

Traduccion, conversacion y evaluacion pasan todas por aqui.
Cambiar de LLM = editar LLM_PROVIDER en .env.

tier="fast"  -> modelo rapido y barato (conversacion, traduccion)
tier="smart" -> modelo mas capaz (evaluacion final, se usa una vez)
"""
import json

from services import clients, config


def chat(system_prompt, messages, tier="fast", json_mode=False, max_tokens=None,
         temperature=0.7):
    """
    Genera una respuesta de texto. Devuelve un string.

    max_tokens acota la longitud de la respuesta. Conviene ponerlo siempre:
    es lo que mas reduce la espera del usuario.
    """
    proveedor = config.LLM_PROVIDER

    if proveedor == "groq":
        return _chat_compatible_openai(
            system_prompt, messages, tier, json_mode, max_tokens, temperature,
            base=clients.GROQ_BASE, api_key=config.GROQ_API_KEY,
            modelo=config.MODELS["groq"][tier], etiqueta="Groq",
        )
    if proveedor == "openai":
        return _chat_compatible_openai(
            system_prompt, messages, tier, json_mode, max_tokens, temperature,
            base=clients.OPENAI_BASE, api_key=config.OPENAI_API_KEY,
            modelo=config.MODELS["openai"][tier], etiqueta="OpenAI",
        )
    if proveedor == "gemini":
        return _chat_gemini(system_prompt, messages, tier, json_mode,
                            max_tokens, temperature)

    raise RuntimeError(f"LLM_PROVIDER desconocido: {proveedor}")


def _chat_compatible_openai(system_prompt, messages, tier, json_mode, max_tokens,
                            temperature, base, api_key, modelo, etiqueta):
    """
    Groq y OpenAI comparten el mismo formato de API,
    asi que comparten tambien la misma funcion.
    """
    cuerpo = {
        "model": modelo,
        "messages": [{"role": "system", "content": system_prompt}] + messages,
        "temperature": temperature,
        # on_demand es el nivel de menor latencia. Los otros (flex, batch)
        # son mas baratos a cambio de esperar, que aqui no interesa.
        "service_tier": "on_demand" if etiqueta == "Groq" else None,
    }
    cuerpo = {k: v for k, v in cuerpo.items() if v is not None}

    if max_tokens:
        # max_tokens quedo obsoleto en favor de max_completion_tokens.
        cuerpo["max_completion_tokens"] = max_tokens
    if json_mode:
        cuerpo["response_format"] = {"type": "json_object"}

    # Los GPT-OSS SI razonan (a diferencia de los Llama que sustituyeron).
    # Sin control, gastan tiempo "pensando" antes de responder, lo que en
    # una app de voz se nota. Se fija el esfuerzo de razonamiento al minimo:
    #   - conversar y traducir (fast): "low", respuesta casi inmediata
    #   - evaluar (smart): "medium", que agradece algo mas de analisis
    # A los modelos que no razonan no se les manda este parametro.
    if etiqueta == "Groq" and modelo in config.GROQ_REASONING_MODELS:
        cuerpo["reasoning_effort"] = "medium" if tier == "smart" else "low"

    respuesta = clients.http().post(
        f"{base}/chat/completions",
        headers=clients.bearer(api_key),
        json=cuerpo,
        timeout=clients.TIMEOUT_SECONDS,
    )
    clients.raise_for_status(respuesta, etiqueta)

    datos = respuesta.json()
    try:
        return (datos["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError) as error:
        raise RuntimeError(f"[{etiqueta}] Respuesta inesperada: {datos}") from error


def _chat_gemini(system_prompt, messages, tier, json_mode, max_tokens=None,
                 temperature=0.7):
    try:
        from google import genai
        from google.genai import types
    except ImportError as error:
        raise RuntimeError(
            "Para usar Gemini instala su libreria: pip install google-genai"
        ) from error

    cliente = genai.Client(api_key=config.GEMINI_API_KEY)

    contenidos = [
        types.Content(
            role="model" if m.get("role") == "assistant" else "user",
            parts=[types.Part(text=m.get("content", ""))],
        )
        for m in messages
    ]

    ajustes = {"system_instruction": system_prompt}
    if max_tokens:
        ajustes["max_output_tokens"] = max_tokens
    ajustes["temperature"] = temperature
    if json_mode:
        ajustes["response_mime_type"] = "application/json"
    if tier == "fast":
        ajustes["thinking_config"] = types.ThinkingConfig(thinking_level="minimal")

    respuesta = cliente.models.generate_content(
        model=config.MODELS["gemini"][tier],
        contents=contenidos,
        config=types.GenerateContentConfig(**ajustes),
    )
    return (respuesta.text or "").strip()


def parse_json_response(raw):
    """
    Convierte la respuesta del modelo en un dict.

    Los modelos a veces envuelven el JSON en ```json ... ``` aunque se les
    pida que no lo hagan, asi que se limpia antes de interpretarlo.
    """
    limpio = (raw or "").strip()

    if limpio.startswith("```"):
        lineas = limpio.split("\n")
        lineas = [l for l in lineas if not l.strip().startswith("```")]
        limpio = "\n".join(lineas).strip()
        if limpio.lower().startswith("json"):
            limpio = limpio[4:].strip()

    return json.loads(limpio)
