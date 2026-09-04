"""
Registro de imagenes intercambiables.

Todas las piezas visuales de Fleng son archivos PNG sueltos en
static/images/. Para cambiar cualquiera basta con sobrescribir el archivo
con el mismo nombre: no hay que tocar codigo, ni CSS, ni plantillas.

Las que llevan obligatorio=True se avisan si faltan. Las opcionales se
ocultan solas y la interfaz sigue funcionando (por ejemplo, si no pones
flengtitulo.png, la barra superior escribe "Fleng" con tipografia).
"""
import os

CARPETA = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "static", "images",
)

# clave -> (archivo, obligatorio, para que sirve)
RANURAS = {
    # --- Marca -------------------------------------------------------------
    "logo": (
        "flenglogo.png", True,
        "Icono de Fleng. Barra superior, a la izquierda del titulo.",
    ),
    "titulo": (
        "flengtitulo.png", False,
        "Titulo 'Fleng' como imagen. Si falta, se escribe con tipografia.",
    ),
    "favicon": (
        "flengfavicon.png", False,
        "Icono de la pestana del navegador. Si falta, se usa el logo.",
    ),

    # --- Avatar ------------------------------------------------------------
    "boca_cerrada": (
        "flengimgbocacerrada.png", True,
        "Avatar callado. Es el estado normal.",
    ),
    "boca_abierta": (
        "flengimgbocaabierta.png", True,
        "Avatar hablando. Alterna con la anterior segun el volumen.",
    ),
    "feliz": (
        "flengfeliz.png", False,
        "Avatar contento. Aparece al terminar una evaluación con buena nota.",
    ),
    "pensando": (
        "flengpensando.png", False,
        "Avatar mientras se genera la respuesta. Si falta, se usa boca cerrada.",
    ),

    # --- Idiomas -----------------------------------------------------------
    "bandera_es": (
        "flengbandera-es.png", False,
        "Símbolo del español en el selector de idioma.",
    ),
    "bandera_en": (
        "flengbandera-en.png", False,
        "Símbolo del inglés en el selector de idioma.",
    ),
}


def ruta(clave):
    """Ruta absoluta del archivo de una ranura."""
    return os.path.join(CARPETA, RANURAS[clave][0])


def existe(clave):
    return os.path.isfile(ruta(clave))


def disponibles():
    """
    Que ranuras tienen archivo puesto.
    El frontend lo usa para ocultar lo que falte sin romperse.
    """
    return {clave: existe(clave) for clave in RANURAS}


def faltantes_obligatorias():
    """Solo las imagenes sin las que la interfaz se ve mal."""
    return [
        datos[0] for clave, datos in RANURAS.items()
        if datos[1] and not existe(clave)
    ]


def catalogo():
    """Listado legible de todas las ranuras, para el archivo LEEME."""
    return [
        {
            "archivo": datos[0],
            "obligatorio": datos[1],
            "descripcion": datos[2],
            "presente": existe(clave),
        }
        for clave, datos in RANURAS.items()
    ]
