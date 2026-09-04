"""
Contenido de la pestana Tutorial.

Es texto fijo, no generado por IA: asi carga al instante, no gasta cuota y
dice siempre lo mismo. Para anadir una leccion basta con sumar una entrada
a la lista "conceptos" del idioma correspondiente.

Cada concepto tiene entradas con la forma:
    (lo que se dice en el idioma que se practica, su equivalente)
El boton de escuchar de la interfaz lee el primer elemento del par.
"""

CONTENIDO = {
    "en": {
        # El origen del ingles, en los dos idiomas. Se muestra el que
        # coincide con el idioma de la INTERFAZ (el que el usuario ya sabe):
        # practicando ingles, la interfaz va en espanol -> "origen".
        "origen": (
            "El inglés nació de los dialectos germánicos que llegaron a "
            "Britania hace más de 1400 años. Hoy lo hablan cerca de 1500 "
            "millones de personas, la mayoría como segunda lengua. Curiosidad: "
            "casi el 60 % de su vocabulario viene del latín y del francés, "
            "herencia de la conquista normanda de 1066."
        ),
        "origen_alt": (
            "English grew out of the Germanic dialects that reached Britain "
            "more than 1400 years ago. Today around 1.5 billion people speak "
            "it, most as a second language. Fun fact: nearly 60% of its "
            "vocabulary comes from Latin and French, a legacy of the Norman "
            "conquest of 1066."
        ),
        "conceptos": [
            {
                "id": "saludos",
                "nombre": "Saludos",
                "icono": "saludo",
                "entradas": [
                    ("Hello", "Hola"),
                    ("Good morning", "Buenos dias"),
                    ("Good afternoon", "Buenas tardes"),
                    ("Good night", "Buenas noches"),
                    ("How are you?", "Como estas?"),
                    ("Nice to meet you", "Encantado de conocerte"),
                    ("See you later", "Hasta luego"),
                    ("Goodbye", "Adios"),
                ],
            },
            {
                "id": "numeros",
                "nombre": "Números",
                "icono": "numero",
                "entradas": [
                    ("One", "Uno"),
                    ("Two", "Dos"),
                    ("Three", "Tres"),
                    ("Four", "Cuatro"),
                    ("Five", "Cinco"),
                    ("Ten", "Diez"),
                    ("Twenty", "Veinte"),
                    ("One hundred", "Cien"),
                ],
            },
            {
                "id": "cortesia",
                "nombre": "Cortesía",
                "icono": "cortesia",
                "entradas": [
                    ("Please", "Por favor"),
                    ("Thank you", "Gracias"),
                    ("You're welcome", "De nada"),
                    ("Excuse me", "Disculpe"),
                    ("I'm sorry", "Lo siento"),
                    ("May I?", "Puedo?"),
                ],
            },
            {
                "id": "verbo-to-be",
                "nombre": "Verbo to be",
                "icono": "gramatica",
                "entradas": [
                    ("I am", "Yo soy / estoy"),
                    ("You are", "Tu eres / estas"),
                    ("He is", "El es / esta"),
                    ("She is", "Ella es / esta"),
                    ("We are", "Nosotros somos / estamos"),
                    ("They are", "Ellos son / estan"),
                ],
            },
            {
                "id": "preguntas",
                "nombre": "Preguntas",
                "icono": "pregunta",
                "entradas": [
                    ("What?", "Que?"),
                    ("Where?", "Donde?"),
                    ("When?", "Cuando?"),
                    ("Who?", "Quien?"),
                    ("Why?", "Por que?"),
                    ("How much?", "Cuanto?"),
                ],
            },
            {
                "id": "frases-utiles",
                "nombre": "Frases útiles",
                "icono": "frase",
                "entradas": [
                    ("I don't understand", "No entiendo"),
                    ("Could you repeat that?", "Puede repetirlo?"),
                    ("How do you say...?", "Como se dice...?"),
                    ("I'm learning English", "Estoy aprendiendo inglés"),
                    ("Speak slower, please", "Hable mas despacio, por favor"),
                ],
            },
        ],
    },

    "es": {
        # Practicando espanol, la interfaz va en ingles -> se usa "origen_alt".
        "origen": (
            "El español viene del latín vulgar que hablaban los soldados y "
            "colonos romanos en la península ibérica. Se empezó a escribir "
            "hacia el siglo X y hoy lo hablan unos 600 millones de personas. "
            "Curiosidad: cerca de 4000 palabras suyas vienen del árabe, como "
            "almohada, aceite u ojalá."
        ),
        "origen_alt": (
            "Spanish comes from the Vulgar Latin spoken by Roman soldiers and "
            "settlers on the Iberian Peninsula. It began to be written around "
            "the 10th century and today about 600 million people speak it. "
            "Fun fact: roughly 4000 of its words come from Arabic, such as "
            "almohada (pillow), aceite (oil) and ojalá (hopefully)."
        ),
        "conceptos": [
            {
                "id": "saludos",
                "nombre": "Saludos",
                "icono": "saludo",
                "entradas": [
                    ("Hola", "Hello"),
                    ("Buenos días", "Good morning"),
                    ("Buenas tardes", "Good afternoon"),
                    ("Buenas noches", "Good night"),
                    ("Cómo estás?", "How are you?"),
                    ("Mucho gusto", "Nice to meet you"),
                    ("Hasta luego", "See you later"),
                    ("Adiós", "Goodbye"),
                ],
            },
            {
                "id": "numeros",
                "nombre": "Números",
                "icono": "numero",
                "entradas": [
                    ("Uno", "One"),
                    ("Dos", "Two"),
                    ("Tres", "Three"),
                    ("Cuatro", "Four"),
                    ("Cinco", "Five"),
                    ("Diez", "Ten"),
                    ("Veinte", "Twenty"),
                    ("Cien", "One hundred"),
                ],
            },
            {
                "id": "cortesia",
                "nombre": "Cortesía",
                "icono": "cortesia",
                "entradas": [
                    ("Por favor", "Please"),
                    ("Gracias", "Thank you"),
                    ("De nada", "You're welcome"),
                    ("Disculpe", "Excuse me"),
                    ("Lo siento", "I'm sorry"),
                    ("¿Puedo?", "May I?"),
                ],
            },
            {
                "id": "verbos-ser-estar",
                "nombre": "Ser y estar",
                "icono": "gramatica",
                "entradas": [
                    ("Yo soy", "I am (permanente)"),
                    ("Yo estoy", "I am (temporal)"),
                    ("Tú eres", "You are"),
                    ("Él está", "He is"),
                    ("Nosotros somos", "We are"),
                    ("Ellos están", "They are"),
                ],
            },
            {
                "id": "preguntas",
                "nombre": "Preguntas",
                "icono": "pregunta",
                "entradas": [
                    ("Qué?", "What?"),
                    ("Dónde?", "Where?"),
                    ("Cuándo?", "When?"),
                    ("Quién?", "Who?"),
                    ("Por qué?", "Why?"),
                    ("Cuánto?", "How much?"),
                ],
            },
            {
                "id": "frases-utiles",
                "nombre": "Frases útiles",
                "icono": "frase",
                "entradas": [
                    ("No entiendo", "I don't understand"),
                    ("¿Puede repetirlo?", "Could you repeat that?"),
                    ("Cómo se dice...?", "How do you say...?"),
                    ("Estoy aprendiendo español", "I'm learning Spanish"),
                    ("Hable más despacio, por favor", "Speak slower, please"),
                ],
            },
        ],
    },
}


def para_idioma(idioma):
    """
    Devuelve el contenido del tutorial de un idioma.

    Incluye el texto de origen en DOS versiones:
      origen             el origen escrito en el idioma que se practica
      origen_referencia  el mismo, en el otro idioma (el de la interfaz)

    Asi el frontend puede mostrar la descripcion del idioma en la lengua
    que el usuario ya conoce, en vez de en la que esta aprendiendo.
    """
    datos = CONTENIDO.get(idioma)
    if datos is None:
        return {"origen": "", "origen_referencia": "", "conceptos": []}

    # El texto de origen describe el idioma que se practica, y se ofrece en
    # los dos idiomas para que el frontend muestre el que coincide con la
    # interfaz (la lengua que el usuario ya conoce). Para el idioma que se
    # practica, "origen" ya esta en la lengua de referencia y "origen_alt"
    # en la que se practica; se etiquetan por idioma para que el cliente
    # elija sin ambiguedad.
    if idioma == "en":
        # origen del ingles: "origen" en espanol, "origen_alt" en ingles
        origen_es = datos["origen"]
        origen_en = datos.get("origen_alt", datos["origen"])
    else:
        # origen del espanol: "origen" en espanol, "origen_alt" en ingles
        origen_es = datos["origen"]
        origen_en = datos.get("origen_alt", datos["origen"])

    return {
        "origen": datos["origen"],
        "origen_es": origen_es,
        "origen_en": origen_en,
        "conceptos": [
            {
                "id": c["id"],
                "nombre": c["nombre"],
                "icono": c["icono"],
                "total": len(c["entradas"]),
                "entradas": [
                    {"texto": texto, "traduccion": traduccion}
                    for texto, traduccion in c["entradas"]
                ],
            }
            for c in datos["conceptos"]
        ],
    }
