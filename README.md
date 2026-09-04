# Fleng

Aplicacion local para practicar espanol e ingles con IA.
Tres modos: Tutorial, Traductor por voz y Conversacion libre.

## Arrancar

**Windows:** doble clic en `iniciar_fleng.bat`

**Manual:**
```
python -m venv venv
venv\Scripts\activate          (Windows)
source venv/bin/activate       (Mac / Linux)
pip install -r requirements.txt
copy .env.example .env         (Windows)
cp .env.example .env           (Mac / Linux)
```
Abre `.env`, pega tus claves y ejecuta:
```
python app.py
```

## Claves

| Servicio | Donde | Para que |
|---|---|---|
| Groq | https://console.groq.com/keys | Conversar, traducir y transcribir |
| Deepgram | https://console.deepgram.com/signup | Generar la voz (200 USD gratis) |

El Tutorial funciona sin claves: su contenido es texto fijo del servidor.

## Imagenes

Todas las piezas visuales son PNG sueltos en `static/images/`.
Para cambiar cualquiera, sobrescribe el archivo con el mismo nombre.
No hay que tocar codigo.

Obligatorias: `flenglogo.png`, `flengimgbocacerrada.png`, `flengimgbocaabierta.png`
Opcionales: `flengtitulo.png`, `flengfavicon.png`, `flengfeliz.png`,
`flengpensando.png`, `flengbandera-es.png`, `flengbandera-en.png`

Detalles de cada una en `static/images/LEEME.txt`.

## La interfaz

**Barra superior:** el pill "Español ⇄ Inglés" manda sobre los tres modos.
El idioma de la derecha es el que practicas. Un clic lo cambia todo.

**Tutorial:** origen del idioma y conceptos basicos. Cada frase se puede
escuchar y marcar como aprendida. El progreso se guarda por idioma.

**Traductor:** manten pulsada la barra espaciadora y habla. Traduce del
idioma de la izquierda del pill al de la derecha.

**Conversacion:** elige un tema (Libre, Restaurante, Viajes, Trabajo,
Entrevista) y conversa. Al finalizar recibes una evaluacion, que alimenta
el grafico de progreso y el mazo de palabras para repasar.

## Cambiar de proveedor

Todo se hace en `.env`, sin tocar codigo:
```
LLM_PROVIDER=groq        ->  groq | gemini | openai
TTS_PROVIDER=deepgram    ->  deepgram | openai | gemini | elevenlabs
STT_PROVIDER=groq        ->  groq | deepgram | gemini | openai
```

## Estructura

```
app.py                  Servidor y rutas
services/
  config.py             Lee .env y valida la configuracion
  clients.py            Sesion HTTP, errores legibles, medicion de tiempos
  llm.py                Modelo de lenguaje
  speech_to_text.py     Voz -> texto
  text_to_speech.py     Texto -> voz
  translator.py         Traduccion
  conversation.py       Conversacion, temas y evaluacion
  tutorial.py           Contenido de las lecciones (texto fijo)
  imagenes.py           Registro de las piezas visuales
templates/index.html    Interfaz
static/css/styles.css   Estilos
static/js/app.js        Logica del navegador
```

Detalles completos en `INFORME_FLENG.txt`.
Instrucciones paso a paso en `TUTORIAL_FLENG.txt`.
