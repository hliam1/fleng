"""
Conversacion libre con IA y evaluacion del desempeno del usuario.
"""
from services import config, llm

NOMBRES_IDIOMA = {"es": "espanol", "en": "ingles"}

TEMAS = {
    "libre": "",
    "restaurante": (
        "La conversacion ocurre en un restaurante. Tu haces de camarero: "
        "recomienda platos, toma el pedido, pregunta por bebidas y postre. "
        "Usa vocabulario de comida, cantidades y formas de pago."
    ),
    "viajes": (
        "La conversacion ocurre durante un viaje. Tu haces de recepcionista "
        "de hotel o de persona local que ayuda: da indicaciones, habla de "
        "transporte, reservas, equipaje y sitios que visitar."
    ),
    "trabajo": (
        "La conversacion ocurre en un entorno de trabajo. Hablad de tareas, "
        "reuniones, plazos y companeros. Usa un registro profesional pero "
        "cercano."
    ),
    "entrevista": (
        "Tu haces de entrevistador en una entrevista de trabajo. Pregunta "
        "por la experiencia, las fortalezas, por que quiere el puesto y "
        "donde se ve en el futuro. Una pregunta cada vez."
    ),
}

# Cuantos turnos recientes se mandan al modelo para conversar.
MAX_TURNOS_CONTEXTO = 10

# --- FIX: Recortar mensajes individuales excesivamente largos ---
# Si un turno tiene una transcripcion enorme (error de STT, o el usuario
# hablo mucho), se recorta. Es proteccion contra prompts gigantes por
# UN mensaje, NO se pierde historial.
MAX_CARACTERES_POR_TURNO = 800

ESQUEMA_EVALUACION = (
    "Responde UNICAMENTE con JSON valido, sin markdown y sin texto alrededor:\n"
    "{\n"
    '  "score": numero entero de 0 a 100,\n'
    '  "pronunciation": "una o dos frases",\n'
    '  "fluency": "una o dos frases",\n'
    '  "problem_words": ["palabra", "..."],\n'
    '  "common_errors": ["error", "..."],\n'
    '  "corrected_phrases": ["lo que dijo -> como se dice mejor", "..."],\n'
    '  "recommendations": ["recomendacion", "..."]\n'
    "}"
)


def get_ai_response(history, practice_language, topic="libre"):
    """Genera la siguiente respuesta del companero de conversacion."""
    idioma = NOMBRES_IDIOMA.get(practice_language, practice_language)
    contexto = TEMAS.get(topic, "")

    instruccion = (
        f"Eres un companero amigable para practicar {idioma}. "
        f"Responde SIEMPRE en {idioma}, pase lo que pase. "
        "Usa un tono natural y cercano. "
        "Respuestas MUY breves: 2 o 3 frases como maximo, nunca mas. "
        "Haz preguntas de vez en cuando para mantener la conversacion viva. "
        "Si el usuario comete un error grave, corrigelo con suavidad y sigue."
    )

    if contexto:
        instruccion += " " + contexto

    reciente = history[-MAX_TURNOS_CONTEXTO:]
    return llm.chat(
        instruccion, reciente, tier="fast", max_tokens=config.MAX_TOKENS["chat"]
    )


def evaluate_conversation(history, practice_language):
    """
    Evalua TODA la conversacion. Devuelve un dict con el esquema completo.

    FIX: Mantiene TODO el historial. Solo aplica mejoras defensivas:
    - Recorta mensajes individuales excesivamente largos (proteccion contra
      transcripciones erroneas de STT que a veces dan miles de caracteres).
    - Aumenta max_tokens de respuesta para JSON completo.
    - Rescata JSON malformado si el modelo trunca la respuesta.
    - Fallback util si TODO falla, en vez de error 502.
    """
    idioma = NOMBRES_IDIOMA.get(practice_language, practice_language)

    # --- FIX: Recortar mensajes individuales muy largos ---
    # SOLO turnos individuales gigantes (proteccion contra bugs de STT),
    # NO se elimina ningun turno del historial.
    def _recortar(texto):
        if len(texto) > MAX_CARACTERES_POR_TURNO:
            return texto[:MAX_CARACTERES_POR_TURNO] + "... [mensaje recortado]"
        return texto

    # Transcripcion COMPLETA (todos los turnos)
    transcripcion = "\n".join(
        f"{'Usuario' if m.get('role') == 'user' else 'IA'}: {_recortar(m.get('content', ''))}"
        for m in history
    )

    # Nota informativa sobre longitud
    nota_longitud = ""
    if len(history) > 20:
        nota_longitud = (
            f"\n\n(Conversacion completa de {len(history)} turnos. "
            f"Evalua el desempeno GLOBAL del estudiante a traves de "
            f"toda la charla.)"
        )

    instruccion = (
        f"Evalua el desempeno de un estudiante practicando {idioma}. "
        "Fijate SOLO en los mensajes del Usuario; los de la IA son contexto. "
        "La evaluacion es aproximada: se basa en texto transcrito, "
        "no en un analisis fonetico real. "
        "Escribe los comentarios en español. " + ESQUEMA_EVALUACION
    )

    # --- FIX: Escalar tokens segun longitud de conversacion ---
    # Conversaciones largas → evaluacion mas detallada → mas tokens necesarios
    # para el JSON de respuesta (mas problem_words, mas correcciones, etc.)
    # Base: 1500 tokens. Añade 50 tokens por cada 10 turnos extra.
    turnos_extra = max(0, len(history) - 10)
    tokens_extra = (turnos_extra // 10) * 50
    max_tokens_evaluacion = max(config.MAX_TOKENS["evaluate"], 1500 + tokens_extra)
    # Cap en 3000 para no dispararse
    max_tokens_evaluacion = min(max_tokens_evaluacion, 3000)

    crudo = llm.chat(
        instruccion,
        [{"role": "user", "content": transcripcion + nota_longitud}],
        tier="smart",
        json_mode=True,
        max_tokens=max_tokens_evaluacion,
        temperature=0.2,
    )

    # --- FIX: Manejo robusto de JSON malformado ---
    try:
        datos_parseados = llm.parse_json_response(crudo)
    except Exception as error:
        import logging
        logging.error("Error parseando evaluacion JSON: %s", error)
        logging.error("Respuesta cruda (primeros 300 chars): %s", (crudo or "")[:300])

        # Intento de rescate: reparar JSON truncado
        rescatado = _intentar_rescatar_json(crudo)
        if rescatado:
            logging.info("JSON rescatado exitosamente")
            datos_parseados = rescatado
        else:
            # Ultimo recurso: fallback util (no rompe el frontend)
            datos_parseados = {
                "score": 0,
                "pronunciation": "No se pudo procesar la evaluacion completa.",
                "fluency": "El servicio de evaluacion tuvo un problema temporal.",
                "problem_words": [],
                "common_errors": [],
                "corrected_phrases": [],
                "recommendations": [
                    "Intenta finalizar de nuevo en unos segundos.",
                ],
            }

    return _normalizar(datos_parseados)


def _intentar_rescatar_json(crudo):
    """
    Si el JSON viene truncado, intenta rescatar lo que se pueda.
    Cierra llaves/corchetes que quedaron abiertos.
    """
    import json

    if not crudo or not isinstance(crudo, str):
        return None

    limpio = crudo.strip()

    # Limpiar markdown wrapper si el modelo lo puso
    if limpio.startswith("```"):
        lineas = limpio.split("\n")
        lineas = [l for l in lineas if not l.strip().startswith("```")]
        limpio = "\n".join(lineas).strip()
        if limpio.lower().startswith("json"):
            limpio = limpio[4:].strip()

    # Intentar parseo directo primero
    try:
        return json.loads(limpio)
    except (json.JSONDecodeError, ValueError):
        pass

    # Reparacion: buscar ultimo caracter valido y cerrar estructuras
    for i in range(len(limpio) - 1, -1, -1):
        if limpio[i] in (',', '"', ']', '}'):
            candidato = limpio[:i+1]
            abiertas = candidato.count('{') - candidato.count('}')
            corchetes = candidato.count('[') - candidato.count(']')

            if candidato.endswith(','):
                candidato = candidato[:-1]

            candidato += ']' * corchetes + '}' * abiertas

            try:
                return json.loads(candidato)
            except (json.JSONDecodeError, ValueError):
                continue

    return None


def _normalizar(datos):
    """
    Garantiza que estan todas las claves del esquema y con el tipo correcto.
    Sin esto, un campo que el modelo omita revienta el frontend.
    """
    if not isinstance(datos, dict):
        datos = {}

    limpio = {}

    try:
        puntuacion = int(float(datos.get("score", 0)))
    except (TypeError, ValueError):
        puntuacion = 0
    limpio["score"] = max(0, min(100, puntuacion))

    for campo in ("pronunciation", "fluency"):
        valor = datos.get(campo)
        limpio[campo] = valor.strip() if isinstance(valor, str) else ""

    for campo in ("problem_words", "common_errors", "corrected_phrases",
                  "recommendations"):
        valor = datos.get(campo)
        if isinstance(valor, list):
            limpio[campo] = [str(x).strip() for x in valor if str(x).strip()]
        elif isinstance(valor, str) and valor.strip():
            limpio[campo] = [valor.strip()]
        else:
            limpio[campo] = []

    return limpio


def correct_dictation(text, practice_language):
    """Corrige una frase dictada por el usuario en el idioma que practica."""
    idioma = NOMBRES_IDIOMA.get(practice_language, practice_language)
    idioma_base = "ingles" if practice_language == "es" else "espanol"

    instruccion = (
        f"Eres un profesor de {idioma}. El usuario esta practicando y te "
        f"dicta una frase. Devuelve SOLO un objeto JSON con estas claves:\n"
        f'  "correccion": la frase corregida y natural en {idioma}. Si ya '
        f"estaba bien, repitela igual.\n"
        f'  "explicacion": explica en {idioma_base}, en una o dos frases '
        f"breves, que corregiste y por que. Si no habia errores, felicita "
        f"brevemente.\n"
        f'  "sin_errores": true si la frase original ya era correcta, false '
        f"si tuviste que cambiar algo.\n"
        f"No anadas nada fuera del JSON."
    )

    crudo = llm.chat(
        instruccion,
        [{"role": "user", "content": text}],
        tier="smart",
        json_mode=True,
        max_tokens=config.MAX_TOKENS["evaluate"],
        temperature=0.2,
    )

    return _normalizar_dictado(crudo, text)


def _normalizar_dictado(crudo, original):
    """Convierte la respuesta del modelo en un dict fiable."""
    import json

    datos = {}
    if isinstance(crudo, str):
        try:
            datos = json.loads(crudo)
        except (json.JSONDecodeError, ValueError):
            datos = {}
    elif isinstance(crudo, dict):
        datos = crudo

    correccion = str(datos.get("correccion") or original).strip()
    explicacion = str(datos.get("explicacion") or "").strip()
    sin_errores = bool(datos.get("sin_errores", False))

    if not correccion:
        correccion = original.strip()

    return {
        "correccion": correccion,
        "explicacion": explicacion,
        "sin_errores": sin_errores,
    }
