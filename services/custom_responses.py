"""
Respuestas personalizadas para Fleng.

Este módulo intercepta preguntas clave y devuelve respuestas predefinidas
sin necesidad de llamar a Groq. Esto es más rápido, más barato (sin costo
de API), y garantiza consistencia en las respuestas sobre Fleng mismo.

Uso:
  respuesta = obtener_respuesta_personalizada(pregunta_del_usuario)
  if respuesta:
      return respuesta  # Devolver sin llamar a Groq
  else:
      # Proceder normalmente con Groq
"""

import re


# Base de respuestas personalizadas
RESPUESTAS_PREDEFINIDAS = {
    # Identidad de Fleng
    "identidad": {
        "patrones": [
            r"quien\s+eres",
            r"que\s+eres",
            r"como\s+te\s+llamas",
            r"cual\s+es\s+tu\s+nombre",
            r"who\s+are\s+you",
            r"what\s+are\s+you",
            r"what's\s+your\s+name",
        ],
        "respuesta_es": (
            "¡Soy Fleng! Tu maestro, tutor y asesor de idiomas personalizado. Fui creado por un equipo apasionado "
            "de ingenieros y lingüistas que trabajan para mejorar la práctica del español. Puedo ayudarte de muchas formas: "
            "practicando conversaciones en tiempo real, traduciéndote textos, haciendo dictados interactivos, "
            "evaluando tu nivel y dándote retroalimentación personalizada. Tengo un avatar animado que se mueve sincronizado "
            "con el audio para hacer el aprendizaje más divertido y cercano. ¿Con qué te podría ayudar hoy?"
        ),
        "respuesta_en": (
            "I'm Fleng! Your personalized language teacher, tutor, and advisor. I was created by a passionate team "
            "of engineers and linguists working to improve Spanish practice. I can help you in many ways: practicing "
            "real-time conversations, translating texts, interactive dictation, evaluating your level, and giving you "
            "personalized feedback. I have an animated avatar that moves in sync with the audio to make learning more "
            "fun and engaging. How can I help you today?"
        ),
    },
    # Evento importante hoy
    "evento": {
        "patrones": [
            r"que\s+evento.*hoy",
            r"hay\s+algo\s+especial\s+hoy",
            r"expotech",
            r"what\s+event.*today",
            r"anything\s+special\s+today",
        ],
        "respuesta_es": "¡Hoy es la Expotech 2026 Nasa Edition!",
        "respuesta_en": "Today is the Expotech 2026 Nasa Edition!",
    },
    # Equipo principal
    "equipo": {
        "patrones": [
            r"quien.*equipo.*fleng",
            r"quienes\s+crearon\s+fleng",
            r"equipo\s+principal",
            r"who.*created\s+fleng",
            r"fleng\s+team",
        ],
        "respuesta_es": "Ian Castellón, Kenji Martinez, Stephen Lopez, Héctor Pineda, Daniel Villeda, Milton López",
        "respuesta_en": "Ian Castellón, Kenji Martinez, Stephen Lopez, Héctor Pineda, Daniel Villeda, Milton López",
    },
    # Diseño de Fleng
    "diseño": {
        "patrones": [
            r"quien.*diseno",
            r"diseño.*fleng",
            r"se\s+encargu\s+del\s+diseno",
            r"who\s+designed",
            r"design.*fleng",
        ],
        "respuesta_es": "Stephen Lopez se encargó de todos los diseños de Fleng junto a Kenji Martinez",
        "respuesta_en": "Stephen Lopez was in charge of all of Fleng's designs along with Kenji Martinez",
    },
    # Profesores preferidos del ITEE
    "profesores": {
        "patrones": [
            r"profesores\s+preferidos",
            r"profesores\s+favoritos",
            r"favorite\s+teachers",
            r"preferred\s+teachers",
        ],
        "respuesta_es": "La licenciada Celeste Leiva y el Ing. Miklos Szabo",
        "respuesta_en": "Licenciada Celeste Leiva and Ing. Miklos Szabo",
    },
    # Información del ITEE
    "itee": {
        "patrones": [
            r"que\s+es\s+el?\s+itee",
            r"cual.*itee",
            r"donde.*fleng",
            r"what\s+is\s+itee",
            r"where\s+is\s+fleng",
        ],
        "respuesta_es": (
            "El ITEE es el Instituto Tecnológico de Excelencia Educativa, "
            "la primera institución educativa privada en Honduras en brindar carreras técnicas. "
            "Fundado en 1986-1987, está ubicado en San Pedro Sula, Cortés, Honduras. "
            "Desde sus inicios ha figurado como el centro de formación del profesional idóneo "
            "que Honduras necesita para su desarrollo. Ofrecemos programas en Programación, Diseño, "
            "Robótica, Electrónica, Electromecánica y más, combinando tecnología, creatividad e "
            "innovación. Actualmente celebra 40 años de trayectoria educativa y es reconocido como "
            "'La Mejor Institución Tecnológica de Honduras'. Sitio web: iteesa.edu.hn"
        ),
        "respuesta_en": (
            "The ITEE is the Instituto Tecnológico de Excelencia Educativa, "
            "the first private educational institution in Honduras to offer technical careers. "
            "Founded in 1986-1987, it is located in San Pedro Sula, Cortés, Honduras. "
            "Since its inception, it has been recognized as a center for training the ideal "
            "professional that Honduras needs for its development. We offer programs in Programming, "
            "Design, Robotics, Electronics, Electromechanics and more, combining technology, "
            "creativity and innovation. Currently celebrates 40 years of educational trajectory and "
            "is recognized as 'The Best Technological Institution in Honduras'. Website: iteesa.edu.hn"
        ),
    },
    # Aprender inglés en el ITEE
    "aprender_ingles_itee": {
        "patrones": [
            r"si\s+quiero\s+aprender\s+ingles",
            r"aprender\s+ingles.*itee",
            r"quien\s+enseña\s+ingles",
            r"clases\s+de\s+ingles",
            r"if\s+i\s+want\s+to\s+learn\s+english",
            r"english\s+teacher.*itee",
        ],
        "respuesta_es": "Puedes practicar inglés con la lic. Celeste Leiva o el lic. Miguel Reyes. ¡Recuerda que toda ayuda es bienvenida!",
        "respuesta_en": "You can practice English with Lic. Celeste Leiva or Lic. Miguel Reyes. Remember that all help is welcome!",
    },
    # Aprender español en el ITEE
    "aprender_espanol_itee": {
        "patrones": [
            r"si\s+quiero\s+aprender\s+espanol",
            r"aprender\s+espanol.*itee",
            r"quien\s+enseña\s+espanol",
            r"clases\s+de\s+espanol",
            r"if\s+i\s+want\s+to\s+learn\s+spanish",
            r"spanish\s+teacher.*itee",
        ],
        "respuesta_es": "Puedes practicar español con la lic. Yilari Rivera y la lic. Ana Calix.",
        "respuesta_en": "You can practice Spanish with Lic. Yilari Rivera and Lic. Ana Calix.",
    },
    # Fundador del ITEE
    "fundador_itee": {
        "patrones": [
            r"quien\s+creo\s+el?\s+itee",
            r"quien\s+fundo\s+el?\s+itee",
            r"fundador.*itee",
            r"who\s+founded.*itee",
            r"who\s+created.*itee",
        ],
        "respuesta_es": (
            "El Instituto Tecnológico de Excelencia Educativa (ITEE) fue fundado en 1986 por el ingeniero Raúl Peña Moreno "
            "en San Pedro Sula, Honduras. El ITEE nació con la misión de ser la primera institución educativa privada en "
            "Honduras en brindar carreras técnicas de calidad. Desde entonces, ha sido un centro de formación de profesionales "
            "idóneos que trabajan en tecnología, ingeniería y diseño. El ITEE actualmente celebra más de 40 años de excelencia "
            "educativa y es reconocido como la mejor institución tecnológica del país."
        ),
        "respuesta_en": (
            "The Instituto Tecnológico de Excelencia Educativa (ITEE) was founded in 1986 by engineer Raúl Peña Moreno in "
            "San Pedro Sula, Honduras. The ITEE was born with the mission to be the first private educational institution in "
            "Honduras to offer quality technical careers. Since then, it has been a center for training ideal professionals who "
            "work in technology, engineering, and design. The ITEE currently celebrates over 40 years of educational excellence "
            "and is recognized as the best technological institution in the country."
        ),
    },
    # Carreras de los creadores de Fleng
    "carreras_creadores": {
        "patrones": [
            r"de\s+que\s+carrera.*creadores",
            r"que\s+carreras\s+tienen",
            r"carrera.*fleng.*creators",
            r"what\s+careers.*creators",
        ],
        "respuesta_es": "Ian, Daniel, Héctor, Milton y Kenji son de Programación, mientras que Stephen es de Diseño Gráfico.",
        "respuesta_en": "Ian, Daniel, Héctor, Milton, and Kenji are from Programming, while Stephen is from Graphic Design.",
    },
    # Encargada de consejería
    "encargada_consejeria": {
        "patrones": [
            r"quien.*consejeria",
            r"quien.*consejera",
            r"consejero.*itee",
            r"consejera.*itee",
            r"elia\s+salgado",
            r"who.*counseling",
            r"counselor.*itee",
        ],
        "respuesta_es": "La consejera encargada es Elia Salgado. Si ves algo que no corresponde, ¡dile a ella!",
        "respuesta_en": "The counselor in charge is Elia Salgado. If you see something that doesn't fit, tell her!",
    },
    # Proyectos en Expotech 2026
    "proyectos_expotech": {
        "patrones": [
            r"que\s+proyectos.*expotech",
            r"otros\s+proyectos.*feria",
            r"expotech\s+2026\s+proyectos",
            r"what\s+projects.*expotech",
            r"projects.*fair.*2026",
        ],
        "respuesta_es": "Puedes encontrar proyectos muy interesantes como: Techlife The experience, Hikari y Nous intelligence.",
        "respuesta_en": "You can find very interesting projects like: Techlife The experience, Hikari, and Nous intelligence.",
    },
    # Carreras disponibles en el ITEE
    "carreras_itee": {
        "patrones": [
            r"que\s+carreras.*itee",
            r"carreras\s+disponibles",
            r"programas.*itee",
            r"what\s+careers.*itee",
            r"careers\s+available",
        ],
        "respuesta_es": "Encuentras las carreras de Mecatrónica, Electromecánica, Diseño Gráfico y Programación.",
        "respuesta_en": "You can find the careers in Mechatronics, Electromechanics, Graphic Design, and Programming.",
    },
    # Beta tester original
    "beta_tester": {
        "patrones": [
            r"quien\s+es\s+el\s+beta\s+tester",
            r"beta\s+tester\s+original",
            r"primer\s+beta\s+tester",
            r"who\s+is\s+the\s+beta\s+tester",
            r"original\s+beta\s+tester",
            r"elkin\s+sierra",
        ],
        "respuesta_es": (
            "El beta tester original fue Elkin Sierra. Su retroalimentación fue invaluable durante las primeras fases "
            "de desarrollo de Fleng. Elkin nos ayudó a identificar bugs, sugerir mejoras en la interfaz, y a afinar "
            "la experiencia de aprendizaje. Su contribución como primer usuario fue fundamental para que Fleng llegara "
            "a ser la aplicación que es hoy. ¡Gracias, Elkin!"
        ),
        "respuesta_en": (
            "The original beta tester was Elkin Sierra. His feedback was invaluable during the early stages of Fleng's "
            "development. Elkin helped us identify bugs, suggest interface improvements, and refine the learning experience. "
            "His contribution as our first user was essential for Fleng to become the application it is today. Thank you, Elkin!"
        ),
    },
}


def normalizar_pregunta(texto):
    """
    Normaliza el texto de la pregunta para matching.
    - Convierte a minúsculas
    - Elimina acentos (simplista)
    - Elimina puntuación
    """
    if not texto:
        return ""
    texto = texto.lower()
    # Mapeo simplista de acentos comunes en español
    acentos = {
        "á": "a", "é": "e", "í": "i", "ó": "o", "ú": "u",
        "ñ": "n", "ü": "u",
    }
    for acentuado, sin_acento in acentos.items():
        texto = texto.replace(acentuado, sin_acento)
    # Elimina puntuación
    texto = re.sub(r"[¿?¡!.,;:]", "", texto)
    return texto.strip()


def obtener_respuesta_personalizada(pregunta, idioma="es"):
    """
    Busca si hay una respuesta personalizada para esta pregunta.

    Args:
        pregunta (str): La pregunta del usuario
        idioma (str): 'es' para español, 'en' para inglés

    Returns:
        str: La respuesta personalizada, o None si no hay coincidencia
    """
    if not pregunta or not isinstance(pregunta, str):
        return None

    pregunta_normalizada = normalizar_pregunta(pregunta)
    if not pregunta_normalizada:
        return None

    # Buscar en todas las categorías de respuestas
    for categoria, datos in RESPUESTAS_PREDEFINIDAS.items():
        patrones = datos.get("patrones", [])
        clave_respuesta = f"respuesta_{idioma}"
        respuesta = datos.get(clave_respuesta)

        if not respuesta:
            continue

        # Probar cada patrón regex
        for patron in patrones:
            try:
                if re.search(patron, pregunta_normalizada):
                    return respuesta
            except re.error:
                # Si hay un error en el regex, ignorar
                continue

    return None


# Alias para compatibilidad
obtener_respuesta = obtener_respuesta_personalizada
