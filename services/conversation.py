"""
Conversacion libre con IA y evaluacion del desempeno del usuario.
"""
from services import config, llm

NOMBRES_IDIOMA = {"es": "espanol", "en": "ingles"}

# Temas de conversacion. Cada uno anade una situacion al system prompt para
# orientar el vocabulario, en vez de dejar la charla sin rumbo.
# "libre" no anade nada: es el comportamiento de siempre.
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

# Cuantos turnos recientes se mandan al modelo.
#
# Cuanto mas largo el contexto, mas tarda el modelo en soltar el primer
# token. Diez turnos bastan para que la conversacion tenga sentido y
# mantienen la peticion pequena.
MAX_TURNOS_CONTEXTO = 10

ESQUEMA_EVALUACION = (
    "Responde UNICAMENTE con JSON valido, sin markdown y sin texto alrededor:\n"
    "{\n"
    '  "score": numero entero de 0 a 100,\n'
    '  "pronunciation": "una o dos frases",\n'
    '  "fluency": "una o dos frases",\n'
    '  "problem_words": ["palabra", "..."],\n'
    '  "common_errors": ["error", "..."],\n'
    '  "corrected_phrases": ["lo que dijo -> como se dice mejor", "..."],\n'
    '  "recommendations": ["consejo", "..."]\n'
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
        # La brevedad no es un capricho de estilo: el texto que genera el
        # modelo hay que convertirlo despues en voz, y la sintesis tarda en
        # proporcion a los caracteres. Una respuesta corta llega antes por
        # partida doble.
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
    """Evalua la conversacion. Devuelve un dict con el esquema completo."""
    idioma = NOMBRES_IDIOMA.get(practice_language, practice_language)

    transcripcion = "\n".join(
        f"{'Usuario' if m.get('role') == 'user' else 'IA'}: {m.get('content', '')}"
        for m in history
    )

    instruccion = (
        f"Evalua el desempeno de un estudiante practicando {idioma}. "
        "Fijate SOLO en los mensajes del Usuario; los de la IA son contexto. "
        "La evaluacion es aproximada: se basa en texto transcrito, "
        "no en un analisis fonetico real. "
        "Escribe los comentarios en español. " + ESQUEMA_EVALUACION
    )

    crudo = llm.chat(
        instruccion,
        [{"role": "user", "content": transcripcion}],
        tier="smart",
        json_mode=True,
        max_tokens=config.MAX_TOKENS["evaluate"],
        # Temperatura baja: la evaluacion debe ser CONSISTENTE. Con la
        # temperatura de conversar (0.7) el modelo improvisa y la misma
        # conversacion daba notas distintas cada vez. Con 0.2 la nota es
        # estable entre evaluaciones repetidas.
        temperature=0.2,
    )
    return _normalizar(llm.parse_json_response(crudo))


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
    """
    Corrige una frase dictada por el usuario en el idioma que practica.

    A diferencia de la conversacion, aqui no se responde ni se sigue el
    hilo: solo se devuelve la version correcta de lo que dijo, con una
    explicacion breve de que se cambio y por que. Es practica de
    pronunciacion y gramatica, no charla.

    Devuelve un dict:
      correccion : la frase corregida (lo que leera el avatar en voz alta)
      explicacion: que se cambio, en el idioma que el usuario ya conoce
      sin_errores: True si la frase ya estaba bien
    """
    idioma = NOMBRES_IDIOMA.get(practice_language, practice_language)
    # La explicacion se da en el idioma que el usuario YA sabe, para que la
    # entienda; la correccion va en el idioma que practica.
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
        # Consistencia: corregir la misma frase debe dar el mismo resultado.
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

    # Si el modelo no devolvio correccion util, se queda la original.
    if not correccion:
        correccion = original.strip()

    return {
        "correccion": correccion,
        "explicacion": explicacion,
        "sin_errores": sin_errores,
    }
