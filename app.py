"""
Fleng - Servidor Flask.

Rutas:
  GET  /                            interfaz
  GET  /api/status                  configuracion y avisos de instalacion
  POST /api/translate               traducir (texto o audio) + voz
  POST /api/speak                   solo voz (para repetir del historial)
  POST /api/conversation            turno de conversacion libre
  POST /api/conversation/evaluate   evaluacion final

El audio siempre viaja en base64 dentro del JSON. No se guardan archivos.
"""
import io
import json
import logging
import os
import webbrowser
from concurrent.futures import ThreadPoolExecutor
from threading import Timer

from flask import Flask, jsonify, render_template, request, send_file

from services import (clients, config, conversation, imagenes, pdf_evaluation,
                      speech_to_text,
                      text_to_speech, translator, tutorial)

app = Flask(__name__)

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
logger = logging.getLogger("fleng")

CARPETA_BASE = os.path.dirname(os.path.abspath(__file__))

IDIOMAS_VALIDOS = ("es", "en")
DIRECCIONES_VALIDAS = ("es-en", "en-es")

# Limite de audio subido: 25 MB. Sin esto, una peticion enorme tumba el server.
app.config["MAX_CONTENT_LENGTH"] = 25 * 1024 * 1024


def imagenes_faltantes():
    """Imagenes obligatorias que el usuario todavia no ha colocado."""
    return imagenes.faltantes_obligatorias()


def _error(mensaje, codigo):
    return jsonify({"error": mensaje}), codigo


def _revisar_configuracion():
    """Devuelve una respuesta de error si falta configuracion, o None."""
    problemas = config.config_errors()
    if problemas:
        return _error(" · ".join(problemas), 400)
    return None


# ------------------------------------------------------------------ rutas

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/status")
def api_status():
    """La interfaz llama a esto al abrir para avisar de lo que falta."""
    return jsonify({
        "config": config.active_summary(),
        "config_errors": config.config_errors(),
        "missing_images": imagenes_faltantes(),
        # Si el frontend deberia intentar transcribir el primero. Es solo
        # una preferencia: si no puede, manda el audio y transcribe el
        # servidor.
        "prefer_browser": speech_to_text.prefiere_navegador(),
        "server_stt": config.STT_PROVIDER,
        # Que imagenes hay puestas. El frontend oculta las que falten en
        # vez de mostrar iconos rotos.
        "images": imagenes.disponibles(),
        "topics": list(conversation.TEMAS.keys()),
    })


@app.route("/api/tutorial")
def api_tutorial():
    """
    Contenido del tutorial de un idioma: origen y conceptos basicos.

    Es texto fijo, no pasa por ninguna API, asi que no necesita claves ni
    gasta cuota. Responde al instante.
    """
    idioma = request.args.get("language", "en")
    if idioma not in IDIOMAS_VALIDOS:
        return _error("Idioma invalido.", 400)
    return jsonify(tutorial.para_idioma(idioma))


@app.route("/api/translate", methods=["POST"])
def api_translate():
    """
    Traduce y devuelve la voz de la traduccion.

    Acepta texto ya transcrito por el navegador (campo 'text')
    o un archivo de audio para transcribir en el servidor (campo 'audio').
    """
    fallo = _revisar_configuracion()
    if fallo:
        return fallo

    direccion = request.form.get("direction", "es-en")
    if direccion not in DIRECCIONES_VALIDAS:
        return _error("Direccion de traduccion invalida.", 400)
    idioma_origen, idioma_destino = direccion.split("-")

    sw = clients.Stopwatch()

    try:
        texto_original = (request.form.get("text") or "").strip()

        if texto_original:
            # El navegador ya transcribio: solo hay que traducir.
            with sw.stage("translate"):
                texto_traducido = translator.translate_text(
                    texto_original, idioma_origen, idioma_destino
                )
        else:
            archivo = request.files.get("audio")
            if archivo is None:
                return _error("No se recibio ni texto ni audio.", 400)

            with sw.stage("stt_and_translate"):
                resultado = speech_to_text.transcribe_and_translate(
                    archivo.read(),
                    archivo.mimetype or "audio/webm",
                    idioma_origen,
                    idioma_destino,
                )
            texto_original = resultado["original"]
            texto_traducido = resultado["translated"]

        if not texto_original:
            return _error("No se reconocio ninguna voz. Intenta de nuevo.", 422)

        with sw.stage("tts"):
            voz = text_to_speech.synthesize_speech(texto_traducido, idioma_destino)

        sw.log("POST /api/translate")

        return jsonify({
            "original_text": texto_original,
            "translated_text": texto_traducido,
            "source_lang": idioma_origen,
            "target_lang": idioma_destino,
            "audio_base64": voz["audio_base64"],
            "audio_mime": voz["mime_type"],
            "timings": sw.as_dict(),
        })

    except Exception as error:
        logger.error("/api/translate: %s", error)
        return _error(str(error)[:200], 502)


@app.route("/api/speak", methods=["POST"])
def api_speak():
    """
    Genera voz de un texto que ya existe.

    Sirve para el boton de repetir del historial. Gracias a esta ruta el
    historial guarda solo texto y no audio en base64, que llenaba la cuota
    de almacenamiento del navegador a las pocas decenas de traducciones.
    """
    fallo = _revisar_configuracion()
    if fallo:
        return fallo

    datos = request.get_json(silent=True) or {}
    texto = (datos.get("text") or "").strip()
    idioma = datos.get("language", "en")

    if not texto:
        return _error("No hay texto que leer.", 400)
    if idioma not in IDIOMAS_VALIDOS:
        return _error("Idioma invalido.", 400)

    sw = clients.Stopwatch()
    try:
        with sw.stage("tts"):
            voz = text_to_speech.synthesize_speech(texto, idioma)
        sw.log("POST /api/speak")
        return jsonify({
            "audio_base64": voz["audio_base64"],
            "audio_mime": voz["mime_type"],
            "timings": sw.as_dict(),
        })
    except Exception as error:
        logger.error("/api/speak: %s", error)
        return _error(str(error)[:200], 502)


@app.route("/api/conversation", methods=["POST"])
def api_conversation():
    """Un turno de conversacion: mensaje del usuario -> respuesta con voz."""
    fallo = _revisar_configuracion()
    if fallo:
        return fallo

    idioma_practica = request.form.get("practice_language", "en")
    if idioma_practica not in IDIOMAS_VALIDOS:
        return _error("Idioma invalido.", 400)

    tema = request.form.get("topic", "libre")
    if tema not in conversation.TEMAS:
        tema = "libre"

    try:
        historial = json.loads(request.form.get("history", "[]"))
        if not isinstance(historial, list):
            historial = []
    except json.JSONDecodeError:
        historial = []

    sw = clients.Stopwatch()

    try:
        texto_usuario = (request.form.get("text") or "").strip()

        if not texto_usuario:
            archivo = request.files.get("audio")
            if archivo is None:
                return _error("No se recibio ni texto ni audio.", 400)
            with sw.stage("stt"):
                texto_usuario = speech_to_text.transcribe(
                    archivo.read(),
                    archivo.mimetype or "audio/webm",
                    idioma_practica,
                )["text"]

        if not texto_usuario:
            return _error("No se reconocio ninguna voz. Intenta de nuevo.", 422)

        historial.append({"role": "user", "content": texto_usuario})

        with sw.stage("llm_response"):
            texto_ia = conversation.get_ai_response(
                historial, idioma_practica, tema
            )

        historial.append({"role": "assistant", "content": texto_ia})

        idioma_referencia = "es" if idioma_practica == "en" else "en"

        # Traducir y generar la voz solo dependen de texto_ia, no la una de
        # la otra. Encadenarlas hacia esperar al usuario la suma de las dos
        # (~350 ms + ~850 ms). Lanzadas a la vez, se paga solo la mas lenta.
        # Son esperas de red, asi que los hilos sirven: mientras una espera
        # respuesta, la otra avanza.
        with sw.stage("translate_and_tts"):
            with ThreadPoolExecutor(max_workers=2) as pool:
                futuro_traduccion = pool.submit(
                    translator.translate_text,
                    texto_ia, idioma_practica, idioma_referencia,
                )
                futuro_voz = pool.submit(
                    text_to_speech.synthesize_speech, texto_ia, idioma_practica,
                )
                # La voz importa mas que la traduccion de referencia: si la
                # traduccion falla, se sigue adelante sin ella en vez de
                # tumbar el turno entero.
                voz = futuro_voz.result()
                try:
                    texto_referencia = futuro_traduccion.result()
                except Exception as error:
                    logger.warning("Traduccion de referencia fallida: %s", error)
                    texto_referencia = ""

        sw.log("POST /api/conversation")

        return jsonify({
            "user_text": texto_usuario,
            "ai_text": texto_ia,
            "translated_text": texto_referencia,
            "audio_base64": voz["audio_base64"],
            "audio_mime": voz["mime_type"],
            "history": historial,
            "timings": sw.as_dict(),
        })

    except Exception as error:
        logger.error("/api/conversation: %s", error)
        return _error(str(error)[:200], 502)


@app.route("/api/dictation", methods=["POST"])
def api_dictation():
    """
    Modo dictado: el usuario dicta una frase, se corrige y se lee en voz
    alta la version correcta.

    A diferencia de la conversacion, no hay ida y vuelta ni traduccion: solo
    transcribir -> corregir -> leer la correccion. El avatar pronuncia la
    frase corregida para que el usuario oiga como deberia sonar.
    """
    fallo = _revisar_configuracion()
    if fallo:
        return fallo

    idioma_practica = request.form.get("practice_language", "en")
    if idioma_practica not in IDIOMAS_VALIDOS:
        return _error("Idioma invalido.", 400)

    sw = clients.Stopwatch()

    try:
        texto_usuario = (request.form.get("text") or "").strip()

        if not texto_usuario:
            archivo = request.files.get("audio")
            if archivo is None:
                return _error("No se recibio ni texto ni audio.", 400)
            with sw.stage("stt"):
                texto_usuario = speech_to_text.transcribe(
                    archivo.read(),
                    archivo.mimetype or "audio/webm",
                    idioma_practica,
                )["text"]

        if not texto_usuario:
            return _error("No se reconocio ninguna voz. Intenta de nuevo.", 422)

        with sw.stage("correct"):
            resultado = conversation.correct_dictation(
                texto_usuario, idioma_practica
            )

        # El avatar lee la version CORREGIDA, que es la que el usuario debe
        # aprender a decir.
        with sw.stage("tts"):
            voz = text_to_speech.synthesize_speech(
                resultado["correccion"], idioma_practica
            )

        sw.log("POST /api/dictation")

        return jsonify({
            "user_text": texto_usuario,
            "correction": resultado["correccion"],
            "explanation": resultado["explicacion"],
            "no_errors": resultado["sin_errores"],
            "audio_base64": voz["audio_base64"],
            "audio_mime": voz["mime_type"],
            "timings": sw.as_dict(),
        })

    except Exception as error:
        logger.error("/api/dictation: %s", error)
        return _error(str(error)[:200], 502)


@app.route("/api/conversation/evaluate", methods=["POST"])
def api_evaluate():
    """Evaluacion final de la conversacion."""
    fallo = _revisar_configuracion()
    if fallo:
        return fallo

    datos = request.get_json(silent=True) or {}
    historial = datos.get("history", [])
    idioma_practica = datos.get("practice_language", "en")

    if not historial:
        return _error("No hay conversacion que evaluar.", 400)
    if idioma_practica not in IDIOMAS_VALIDOS:
        return _error("Idioma invalido.", 400)

    sw = clients.Stopwatch()
    try:
        with sw.stage("evaluate"):
            evaluacion = conversation.evaluate_conversation(
                historial, idioma_practica
            )
        sw.log("POST /api/conversation/evaluate")
        evaluacion["timings"] = sw.as_dict()
        return jsonify(evaluacion)
    except Exception as error:
        logger.error("/api/conversation/evaluate: %s", error)
        return _error(str(error)[:200], 502)


@app.route("/api/evaluation/pdf", methods=["POST"])
def api_evaluation_pdf():
    """
    Genera un PDF de evaluacion detallada a partir de los datos de una
    evaluacion ya realizada.
    """
    try:
        datos = request.get_json(silent=True) or {}
        evaluacion = datos.get("evaluation", {})
        idioma = datos.get("language", "en")
        turnos = datos.get("turns", 0)

        if not evaluacion or "score" not in evaluacion:
            return _error("No se recibieron datos de evaluacion.", 400)

        pdf_bytes = pdf_evaluation.generar_pdf(evaluacion, idioma, turnos)

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=f"fleng_evaluacion_{idioma}.pdf",
        )
    except Exception as error:
        logger.error("/api/evaluation/pdf: %s", error)
        return _error(str(error)[:200], 502)


# ------------------------------------------------------------- errores

@app.errorhandler(404)
def no_encontrado(_excepcion):
    return _error("Recurso no encontrado.", 404)


@app.errorhandler(413)
def demasiado_grande(_excepcion):
    return _error("El audio es demasiado grande. Habla menos tiempo seguido.", 413)


@app.errorhandler(500)
def error_servidor(_excepcion):
    return _error("Error interno del servidor.", 500)


# ------------------------------------------------------------- arranque

def _mostrar_arranque(puerto):
    print("\n" + "=" * 58)
    print("  FLENG")
    print("=" * 58)
    resumen = config.active_summary()
    print(f"  Voz -> texto : {resumen['stt']}")
    print(f"  Modelo       : {resumen['llm']}")
    print(f"  Texto -> voz : {resumen['tts']}")
    print("-" * 58)

    problemas = config.config_errors()
    if problemas:
        for problema in problemas:
            print(f"  [!] {problema}")
    else:
        print("  [ok] Claves configuradas")

    faltan = imagenes_faltantes()
    if faltan:
        print(f"  [!] Faltan imagenes en static/images/: {', '.join(faltan)}")
    else:
        print("  [ok] Imagenes obligatorias completas")

    opcionales = [
        datos["archivo"] for datos in imagenes.catalogo()
        if not datos["obligatorio"] and not datos["presente"]
    ]
    if opcionales:
        print(f"  [--] Opcionales sin poner: {', '.join(opcionales)}")

    print("-" * 58)
    print(f"  Abre: http://127.0.0.1:{puerto}")
    print("  Para detener el servidor: Ctrl + C")
    print("=" * 58 + "\n")


if __name__ == "__main__":
    PUERTO = int(os.getenv("PORT", "5000"))
    _mostrar_arranque(PUERTO)

    Timer(1.0, lambda: webbrowser.open(f"http://127.0.0.1:{PUERTO}")).start()
    app.run(host="127.0.0.1", port=PUERTO, debug=False, use_reloader=False)
