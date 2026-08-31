"""
Genera un PDF de evaluacion detallada con recomendaciones concretas por area.

Usa las poses del personaje Fleng como decoracion de cada seccion:
  · Pronunciacion -> pensando (con puntero)
  · Fluidez       -> corriendo (en movimiento)
  · Gramatica     -> confundida (signos de interrogacion)
  · Vocabulario   -> sentado apuntando (con puntero diagonal)
  · Nota alta     -> feliz/emocionada

Los colores siguen la paleta de la aplicacion (oscuro + naranja + magenta).
"""
import io
import os
from datetime import datetime

from reportlab.lib.pagesizes import LETTER
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                 Image, Table, TableStyle, HRFlowable)

# --- Rutas de imagenes -------------------------------------------------------

CARPETA_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
POSES = os.path.join(CARPETA_BASE, "static", "images", "poses")
LOGO = os.path.join(CARPETA_BASE, "static", "images", "flenglogo.png")

POSE_SECCION = {
    "pronunciation": "flengpensando.png",
    "fluency": "FLENG_CUERPO_Corriendo_.png",
    "grammar": "FLENG_CUERPO_Confundida_.png",
    "vocabulary": "FLENG_CUERPO_Sentado_Apuntando_.png",
    "good": "FLENG_CUERPO_Emocionada_.png",
}

# --- Paleta (mismos colores que la app) --------------------------------------

NAVY = colors.HexColor("#0e0e26")
NAVY_PANEL = colors.HexColor("#1a1a3e")
ORANGE = colors.HexColor("#f57e22")
MAGENTA = colors.HexColor("#c01f63")
WHITE = colors.HexColor("#ffffff")
INK_100 = colors.HexColor("#e8e8f0")
INK_300 = colors.HexColor("#b0b0c8")
INK_500 = colors.HexColor("#6e6e8a")
SKY = colors.HexColor("#4bb4e5")
DANGER = colors.HexColor("#e53935")

# --- Estilos -----------------------------------------------------------------

st_title = ParagraphStyle("T", fontName="Helvetica-Bold", fontSize=26,
    textColor=WHITE, leading=30, alignment=TA_CENTER)
st_subtitle = ParagraphStyle("ST", fontName="Helvetica", fontSize=13,
    textColor=INK_300, alignment=TA_CENTER, leading=16)
st_section = ParagraphStyle("S", fontName="Helvetica-Bold", fontSize=18,
    textColor=ORANGE, leading=22, spaceBefore=10, spaceAfter=4)
st_body = ParagraphStyle("B", fontName="Helvetica", fontSize=13,
    textColor=INK_100, leading=18, spaceAfter=4, wordWrap="CJK")
st_tip = ParagraphStyle("Tip", fontName="Helvetica", fontSize=12,
    textColor=INK_300, leading=16, leftIndent=18, spaceBefore=1, spaceAfter=1)
st_score_big = ParagraphStyle("SB", fontName="Helvetica-Bold", fontSize=52,
    textColor=WHITE, alignment=TA_CENTER, leading=56)
st_score_label = ParagraphStyle("SL", fontName="Helvetica", fontSize=12,
    textColor=INK_500, alignment=TA_CENTER, leading=15)
st_footer = ParagraphStyle("F", fontName="Helvetica", fontSize=9,
    textColor=INK_500, alignment=TA_CENTER, leading=11)

ESC = lambda t: (str(t).replace("&", "&amp;").replace("<", "&lt;")
                        .replace(">", "&gt;"))


def _pose_image(key, ancho=3.8 * cm):
    """Carga una pose si existe; si no, devuelve None."""
    nombre = POSE_SECCION.get(key, "")
    ruta = os.path.join(POSES, nombre)
    if not os.path.isfile(ruta):
        return None
    try:
        img = Image(ruta)
        ratio = img.imageWidth / img.imageHeight if img.imageHeight else 1
        img.drawWidth = ancho
        img.drawHeight = ancho / ratio
        return img
    except Exception:
        return None


def _logo_image():
    if not os.path.isfile(LOGO):
        return None
    try:
        img = Image(LOGO)
        img.drawWidth = 1.2 * cm
        img.drawHeight = 1.2 * cm
        return img
    except Exception:
        return None


def _color_nota(score):
    if score >= 80:
        return SKY
    if score >= 60:
        return ORANGE
    return DANGER


def generar_pdf(evaluacion, idioma, turnos=0):
    """
    Genera un PDF en memoria con la evaluacion detallada.

    evaluacion: dict con score, pronunciation, fluency, grammar, vocabulary,
                problem_words, common_errors, corrections, recommendations.
    idioma: 'es' o 'en'
    turnos: cuantos turnos tuvo la conversacion

    Devuelve bytes del PDF.
    """
    buf = io.BytesIO()
    score = int(evaluacion.get("score") or 0)
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M")
    nombre_idioma = "Inglés" if idioma == "en" else "Español"

    doc = SimpleDocTemplate(buf, pagesize=LETTER,
        topMargin=1.5 * cm, bottomMargin=1.5 * cm,
        leftMargin=2 * cm, rightMargin=2 * cm,
        title="Fleng - Evaluación detallada",
        author="Fleng")

    historia = []

    # ========================= CABECERA ======================================

    # Logo + titulo
    logo = _logo_image()
    if logo:
        historia.append(logo)
        historia.append(Spacer(1, 8))

    historia.append(Paragraph("Evaluación detallada", st_title))
    historia.append(Paragraph(
        f"{nombre_idioma} · {turnos} turnos · {fecha}", st_subtitle))
    historia.append(Spacer(1, 8))

    # Nota grande
    historia.append(Paragraph(str(score), st_score_big))
    historia.append(Paragraph("de 100 puntos", st_score_label))
    historia.append(Spacer(1, 6))
    historia.append(HRFlowable(width="60%", thickness=1, color=INK_500,
                               hAlign="CENTER", spaceBefore=6, spaceAfter=14))

    # ========================= SECCIONES =====================================

    secciones = [
        ("pronunciation", "Pronunciación",
         evaluacion.get("pronunciation") or "Sin datos suficientes."),
        ("fluency", "Fluidez",
         evaluacion.get("fluency") or "Sin datos suficientes."),
        ("grammar", "Gramática",
         evaluacion.get("grammar") or "Sin datos suficientes."),
        ("vocabulary", "Vocabulario",
         evaluacion.get("vocabulary") or "Sin datos suficientes."),
    ]

    for key, titulo, texto in secciones:
        pose = _pose_image(key)

        if pose:
            # Titulo + texto juntos en la celda izquierda, ilustración a la
            # derecha. Así no hay espacio en blanco entre título y texto.
            celda_izq = [
                Paragraph(ESC(titulo), st_section),
                Paragraph(ESC(texto), st_body),
            ]
            tabla = Table(
                [[celda_izq, pose]],
                colWidths=[doc.width - 4.5 * cm, 4 * cm],
            )
            tabla.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (0, -1), 12),
                ("RIGHTPADDING", (1, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
            ]))
            historia.append(tabla)
        else:
            historia.append(Paragraph(ESC(titulo), st_section))
            historia.append(Paragraph(ESC(texto), st_body))

    # ========================= RECOMENDACIONES ===============================

    recomendaciones = evaluacion.get("recommendations") or []
    if isinstance(recomendaciones, str):
        recomendaciones = [recomendaciones]
    if recomendaciones:
        historia.append(Spacer(1, 8))
        historia.append(HRFlowable(width="100%", thickness=0.5, color=INK_500,
                                   spaceBefore=6, spaceAfter=10))

        historia.append(Paragraph("Recomendaciones", st_section))

        for rec in recomendaciones[:6]:
            historia.append(Paragraph("→  " + ESC(str(rec)), st_tip))

    # ========================= PALABRAS PROBLEMATICAS ========================

    palabras = evaluacion.get("problem_words") or []
    if palabras:
        historia.append(Spacer(1, 10))
        historia.append(Paragraph("Palabras o expresiones a repasar", st_section))
        for palabra in palabras[:8]:
            historia.append(Paragraph("·  " + ESC(str(palabra)), st_tip))

    # ========================= FRASES CORREGIDAS =============================

    correcciones = evaluacion.get("corrections") or []
    if correcciones:
        historia.append(Spacer(1, 10))
        historia.append(Paragraph("Frases corregidas", st_section))
        for corr in correcciones[:6]:
            historia.append(Paragraph("·  " + ESC(str(corr)), st_tip))

    # ========================= PIE ===========================================

    historia.append(Spacer(1, 20))
    historia.append(HRFlowable(width="100%", thickness=0.5, color=INK_500,
                               spaceBefore=6, spaceAfter=8))
    historia.append(Paragraph(f"Generado por Fleng · {fecha}", st_footer))

    # Si la nota es alta y hay pose de celebracion, ponerla al final
    if score >= 70:
        pose_final = _pose_image("good", ancho=5 * cm)
        if pose_final:
            historia.append(Spacer(1, 8))
            t = Table([[pose_final]], colWidths=[doc.width])
            t.setStyle(TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER")]))
            historia.append(t)

    # ========================= FONDO OSCURO ==================================

    def fondo_oscuro(canvas, doc):
        canvas.saveState()
        canvas.setFillColor(NAVY)
        canvas.rect(0, 0, LETTER[0], LETTER[1], fill=1, stroke=0)
        canvas.restoreState()

    doc.build(historia, onFirstPage=fondo_oscuro, onLaterPages=fondo_oscuro)
    return buf.getvalue()
