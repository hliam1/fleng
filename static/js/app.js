/* ==========================================================================
   Fleng - Logica de frontend
   ========================================================================== */

document.addEventListener('DOMContentLoaded', () => {

  /* ------------------------------ Referencias DOM ------------------------------ */

  const setupBannerEl = document.getElementById('setup-banner');
  const modeTabs = Array.from(document.querySelectorAll('.mode-tab'));
  const translatorViewEl = document.getElementById('translator-view');
  const conversationViewEl = document.getElementById('conversation-view');

  const avatarImgEl = document.getElementById('avatar-img');
  const avatarStageEl = document.querySelector('.avatar-stage');
  const avatarAudioEl = document.getElementById('avatar-audio');
  const waveformBars = Array.from(document.querySelectorAll('.waveform-bar'));
  const globalStatusEl = document.getElementById('global-status');
  const repeatBtn = document.getElementById('repeat-audio-btn');
  const toastContainerEl = document.getElementById('toast-container');

  const tutorialViewEl = document.getElementById('tutorial-view');
  const brandLogoEl = document.getElementById('brand-logo');
  const brandTitleEl = document.getElementById('brand-title');
  const brandNameEl = document.getElementById('brand-name');
  const faviconEl = document.getElementById('favicon');

  // Dos botones separados en vez de un pill: el usuario ve de un vistazo
  // en qué idioma esta practicando.
  const langButtons = Array.from(document.querySelectorAll('.lang-btn'));
  const micDirectionEl = document.getElementById('mic-direction');

  const streakDaysEl = document.getElementById('streak-days');
  const streakTurnsEl = document.getElementById('streak-turns');
  const streakScoreEl = document.getElementById('streak-score');

  const originTitleEl = document.getElementById('origin-title');
  const originTextEl = document.getElementById('origin-text');
  const conceptGridEl = document.getElementById('concept-grid');
  const lessonPanelEl = document.getElementById('lesson-panel');
  const lessonTitleEl = document.getElementById('lesson-title');
  const lessonCountEl = document.getElementById('lesson-count');
  const lessonEntriesEl = document.getElementById('lesson-entries');
  const lessonBackBtn = document.getElementById('lesson-back');
  const resetTutorialBtn = document.getElementById('reset-tutorial-btn');

  const topicSwitchEl = document.getElementById('topic-switch');

  const dictationViewEl = document.getElementById('dictation-view');
  const dictationMicBtn = document.getElementById('dictation-mic-btn');
  const dictationHistoryEl = document.getElementById('dictation-history');
  const clearDictationBtn = document.getElementById('clear-dictation-btn');
  const translatorTextForm = document.getElementById('translator-text-row');
  const translatorTextInput = document.getElementById('translator-text-input');
  const dictationTextForm = document.getElementById('dictation-text-row');
  const dictationTextInput = document.getElementById('dictation-text-input');
  const translatorMicBtn = document.getElementById('translator-mic-btn');
  const translationHistoryEl = document.getElementById('translation-history');
  const clearHistoryBtn = document.getElementById('clear-history-btn');

  const conversationMicBtn = document.getElementById('conversation-mic-btn');
  const chatMessagesEl = document.getElementById('chat-messages');
  const chatInputRowEl = document.getElementById('chat-input-row');
  const conversationTextInputEl = document.getElementById('conversation-text-input');
  const conversationSendBtn = document.getElementById('conversation-send-btn');
  const finishConversationBtn = document.getElementById('finish-conversation-btn');
  const evaluationPanelEl = document.getElementById('evaluation-panel');

  // Rutas del avatar. Se derivan de la imagen que ya trae el HTML, asi que
  // basta con cambiar los archivos de static/images/ para cambiar el avatar.
  const IMAGES_BASE = avatarImgEl.getAttribute('src')
    .replace('flengimgbocacerrada.png', '');
  const MOUTH_CLOSED_SRC = IMAGES_BASE + 'flengimgbocacerrada.png';
  const MOUTH_OPEN_SRC = IMAGES_BASE + 'flengimgbocaabierta.png';
  const HAPPY_SRC = IMAGES_BASE + 'flengfeliz.png';
  const THINKING_SRC = IMAGES_BASE + 'flengpensando.png';

  const HISTORY_STORAGE_KEY = 'fleng_translation_history';
  const DICTATION_STORAGE_KEY = 'fleng_dictation_history';
  const EVAL_STORAGE_KEY = 'fleng_evaluations';
  const REVIEW_STORAGE_KEY = 'fleng_review_words';
  const TUTORIAL_STORAGE_KEY = 'fleng_tutorial_progress';
  const STATS_STORAGE_KEY = 'fleng_stats';
  const LANG_STORAGE_KEY = 'fleng_language';

  /* --------------------------------- Estado --------------------------------- */

  // La pestana Tutorial es la primera, asi que es la que se abre al entrar.
  let currentMode = 'tutorial';

  // UN SOLO estado de idioma para los tres modos.
  // practiceLanguage = el idioma que se esta practicando (derecha del pill).
  // referenceLanguage = el idioma conocido (izquierda del pill).
  // En el traductor eso significa traducir DE referencia A practica.
  let practiceLanguage = loadLanguage();
  let currentTopic = 'libre';
  let availableTopics = ['libre'];
  let conversationHistory = [];
  let lastEvaluation = null;
  let translationHistory = loadTranslationHistory();
  let isProcessing = false;
  let avatarThinking = false;   // el avatar muestra la pose de "pensando"
  let avatarImagesReady = true;
  let preferBrowserStt = true;   // lo confirma /api/status al arrancar
  let browserSttBroken = false;  // se activa si el navegador demuestra que no puede
  let imagenesDisponibles = {};  // que ranuras de static/images tienen archivo

  // Las piezas visuales opcionales se activan solas si el archivo existe.
  // Asi se puede cambiar la marca sin tocar codigo: basta con poner o
  // quitar un PNG en static/images/.
  function aplicarImagenes() {
    // El titulo como imagen sustituye al texto. Si no esta, se escribe.
    const hayTitulo = Boolean(imagenesDisponibles.titulo);
    brandTitleEl.classList.toggle('hidden', !hayTitulo);
    brandNameEl.classList.toggle('hidden', hayTitulo);

    if (imagenesDisponibles.favicon) {
      faviconEl.href = IMAGES_BASE + 'flengfavicon.png';
    }

    // Si falta el logo se oculta en vez de dejar el icono roto.
    brandLogoEl.classList.toggle('hidden', !imagenesDisponibles.logo);
  }

  const LANG_NAMES = { es: 'Español', en: 'Inglés' };

  /* ============================================================
     INTERNACIONALIZACION DE LA INTERFAZ

     La interfaz se muestra en el idioma que el usuario YA SABE, no en
     el que practica: si practica ingles, la app le habla en espanol
     (su lengua base); si practica espanol, la app va en ingles.

     Asi, el idioma de la interfaz es SIEMPRE el de referencia, el
     contrario al que se practica.

     La conversacion y el dictado en si van siempre en el idioma que se
     practica: eso no lo toca applyLocale.
     ============================================================ */

  const UI_STRINGS = {
    es: {
      tab_tutorial: 'Tutorial', tab_translator: 'Traductor',
      tab_dictation: 'Dictado', tab_conversation: 'Conversación',
      origin_title: 'Origen del idioma', basic_concepts: 'Conceptos básicos',
      reset_progress: 'Reiniciar progreso', history: 'Historial',
      clear_history: 'Limpiar historial', talk_about: 'Sobre qué quieres hablar',
      finish_conversation: 'Finalizar conversación', send: 'Enviar',
      conversation_empty: 'Escribe o habla para comenzar una conversación.',
      type_message: 'Escribe tu mensaje…', repeat_audio: 'Repetir audio',
      ready: 'Listo', listen: 'Escuchar',
      dictation_hint: 'Mantén presionado y di una frase. Fleng la corregirá y la leerá bien.',
      dictation_history: 'Frases corregidas',
      dictation_empty: 'Di una frase y Fleng te la corregirá.',
      dic_said: 'Dijiste', dic_fixed: 'Correcto', dic_perfect: '¡Perfecto! Sin errores.',
      concept_done: 'Completo', concept_start: 'Sin empezar',
      concept_of: 'de', lesson_learned: 'aprendidas',
      aria_practicing: 'Estás practicando', aria_switch: 'Cambiar a',
      origin_of: 'Origen del', tutorial_loading: 'Cargando…',
      tutorial_load_error: 'No se pudo cargar el tutorial.',
      tutorial_conn_error: 'No se pudo conectar con el servidor.',
      lang_es: 'español', lang_en: 'inglés',
      mark_learned: 'Marcar como aprendida',
      confirm_reset: '¿Reiniciar tu progreso del tutorial en',
      back_conversation: 'Volver a la conversación',
      detailed_pdf: 'Evaluación detallada (PDF)',
      generating_pdf: 'Generando PDF…',
      new_conversation: 'Nueva conversación',
      eval_disclaimer: 'Esta evaluación es aproximada: se basa en la transcripción de la conversación, no en un análisis fonético profesional.',
      eval_pronunciation: 'Pronunciación (aproximada)',
      eval_fluency: 'Fluidez',
      eval_problem_words: 'Palabras o expresiones problemáticas',
      eval_common_errors: 'Errores frecuentes',
      eval_corrections: 'Frases corregidas',
      eval_recommendations: 'Recomendaciones',
      type_to_translate: 'O escribe aquí para traducir…', translate_btn: 'Traducir',
      type_to_correct: 'O escribe una frase para corregir…', correct_btn: 'Corregir',
      topic_libre: 'Libre', topic_restaurante: 'Restaurante', topic_viajes: 'Viajes',
      topic_trabajo: 'Trabajo', topic_entrevista: 'Entrevista',
      status_listening: 'Escuchando…', status_processing: 'Procesando audio…',
      status_translating: 'Traduciendo…', status_speaking: 'Generando voz…',
      status_thinking: 'Pensando…', status_correcting: 'Corrigiendo…',
      help_title: 'Cómo elegir tu idioma',
      help_practicing: 'Inglés', help_practicing_label: '↑ practicas',
      help_know: 'Español', help_know_label: '↑ ya lo sabes',
      help_step1: 'El botón <b>relleno</b> es el idioma que estás practicando.',
      help_step2: 'El botón <b>apagado</b> es el idioma que ya sabes.',
      help_step3: 'Pulsa el apagado para cambiar: se intercambian al instante.',
      help_ok: 'Entendido',
      toast_lang_changed: 'Cambiaste de idioma, se reinició la conversación.',
      confirm_lang: 'Cambiar de idioma reiniciará la conversación actual. ¿Continuar?',
    },
    en: {
      tab_tutorial: 'Tutorial', tab_translator: 'Translator',
      tab_dictation: 'Dictation', tab_conversation: 'Conversation',
      origin_title: 'Language origin', basic_concepts: 'Basic concepts',
      reset_progress: 'Reset progress', history: 'History',
      clear_history: 'Clear history', talk_about: 'What do you want to talk about',
      finish_conversation: 'End conversation', send: 'Send',
      conversation_empty: 'Type or speak to start a conversation.',
      type_message: 'Type your message…', repeat_audio: 'Repeat audio',
      ready: 'Ready', listen: 'Listen',
      dictation_hint: 'Hold and say a sentence. Fleng will correct it and read it back.',
      dictation_history: 'Corrected sentences',
      dictation_empty: 'Say a sentence and Fleng will correct it.',
      dic_said: 'You said', dic_fixed: 'Correct', dic_perfect: 'Perfect! No mistakes.',
      concept_done: 'Complete', concept_start: 'Not started',
      concept_of: 'of', lesson_learned: 'learned',
      aria_practicing: 'You are practicing', aria_switch: 'Switch to',
      origin_of: 'Origin of', tutorial_loading: 'Loading…',
      tutorial_load_error: 'Could not load the tutorial.',
      tutorial_conn_error: 'Could not connect to the server.',
      lang_es: 'Spanish', lang_en: 'English',
      mark_learned: 'Mark as learned',
      confirm_reset: 'Reset your tutorial progress in',
      back_conversation: 'Back to conversation',
      detailed_pdf: 'Detailed evaluation (PDF)',
      generating_pdf: 'Generating PDF…',
      new_conversation: 'New conversation',
      eval_disclaimer: 'This evaluation is approximate: it is based on the conversation transcript, not on a professional phonetic analysis.',
      eval_pronunciation: 'Pronunciation (approximate)',
      eval_fluency: 'Fluency',
      eval_problem_words: 'Problematic words or expressions',
      eval_common_errors: 'Common errors',
      eval_corrections: 'Corrected sentences',
      eval_recommendations: 'Recommendations',
      type_to_translate: 'Or type here to translate…', translate_btn: 'Translate',
      type_to_correct: 'Or type a sentence to correct…', correct_btn: 'Correct',
      topic_libre: 'Free', topic_restaurante: 'Restaurant', topic_viajes: 'Travel',
      topic_trabajo: 'Work', topic_entrevista: 'Interview',
      status_listening: 'Listening…', status_processing: 'Processing audio…',
      status_translating: 'Translating…', status_speaking: 'Generating voice…',
      status_thinking: 'Thinking…', status_correcting: 'Correcting…',
      help_title: 'How to choose your language',
      help_practicing: 'Spanish', help_practicing_label: '↑ practicing',
      help_know: 'English', help_know_label: '↑ you know this',
      help_step1: 'The <b>filled</b> button is the language you are practicing.',
      help_step2: 'The <b>dimmed</b> button is the language you already know.',
      help_step3: 'Tap the dimmed one to switch: they swap instantly.',
      help_ok: 'Got it',
      toast_lang_changed: 'Language changed, the conversation was reset.',
      confirm_lang: 'Changing the language will reset the current conversation. Continue?',
    },
  };

  // El idioma de la interfaz es el de referencia (el que el usuario ya
  // sabe), no el que practica.
  function uiLang() {
    return referenceLanguage();
  }

  function t(clave) {
    const juego = UI_STRINGS[uiLang()] || UI_STRINGS.es;
    return juego[clave] !== undefined ? juego[clave] : clave;
  }

  // Reasigna todos los textos marcados con data-i18n al idioma actual.
  function applyLocale() {
    const juego = UI_STRINGS[uiLang()] || UI_STRINGS.es;

    document.querySelectorAll('[data-i18n]').forEach((el) => {
      const clave = el.dataset.i18n;
      if (juego[clave] !== undefined) el.innerHTML = juego[clave];
    });
    document.querySelectorAll('[data-i18n-placeholder]').forEach((el) => {
      const clave = el.dataset.i18nPlaceholder;
      if (juego[clave] !== undefined) el.placeholder = juego[clave];
    });

    // Idioma del documento, para lectores de pantalla y correctores.
    document.documentElement.lang = uiLang();
  }

  function referenceLanguage() {
    return practiceLanguage === 'en' ? 'es' : 'en';
  }

  const lockableControls = [
    translatorMicBtn, conversationMicBtn, conversationSendBtn,
    conversationTextInputEl, clearHistoryBtn, dictationMicBtn, translatorTextInput, dictationTextInput,
    clearDictationBtn, ...modeTabs, ...langButtons,
  ];

  /* ------------------------------- Utilidades ------------------------------- */

  function setStatus(text) { globalStatusEl.textContent = text; }

  function showToast(message, isError) {
    const toast = document.createElement('div');
    toast.className = 'toast' + (isError ? ' toast-error' : '');
    toast.textContent = message;
    toastContainerEl.appendChild(toast);
    setTimeout(() => toast.remove(), 5000);
  }

  /*
    Pose de "pensando" mientras se genera la respuesta.

    Dos precauciones que importan:

    · Solo se aplica si el usuario puso flengpensando.png. Es una imagen
      opcional; si no esta, el avatar se queda como estaba en vez de
      mostrar un icono roto.

    · No debe pisar la animacion de la boca. El audio empieza a sonar
      ANTES de que termine el procesamiento, asi que al salir del estado
      solo se restaura la boca cerrada si no hay nada sonando; si ya esta
      hablando, manda la animacion.
  */
  function setAvatarThinking(value) {
    if (!avatarImagesReady || !imagenesDisponibles.pensando) return;

    if (value) {
      if (!avatarAudioEl.paused) return;   // ya esta hablando: no interrumpir
      avatarThinking = true;
      avatarImgEl.src = THINKING_SRC;
      return;
    }

    if (!avatarThinking) return;
    avatarThinking = false;
    if (avatarAudioEl.paused) avatarImgEl.src = MOUTH_CLOSED_SRC;
  }

  function setProcessing(value) {
    isProcessing = value;
    lockableControls.forEach((el) => { if (el) el.disabled = value; });
    setAvatarThinking(value);
    updateFinishButtonState();
  }

  function isEditableElement(el) {
    if (!el) return false;
    return el.tagName === 'INPUT' || el.tagName === 'TEXTAREA' || el.isContentEditable;
  }

  avatarImgEl.addEventListener('error', () => { avatarImagesReady = false; });

  /* -------------------------- Estado inicial del servidor -------------------------- */

  async function checkStatus() {
    try {
      const response = await fetch('/api/status');
      const data = await response.json();
      preferBrowserStt = Boolean(data.prefer_browser);
      imagenesDisponibles = data.images || {};
      aplicarImagenes();

      if (Array.isArray(data.topics) && data.topics.length > 0) {
        availableTopics = data.topics;
        renderTemas();
      }

      const messages = [];
      if (data.config_errors && data.config_errors.length > 0) {
        messages.push(...data.config_errors);
      }
      if (data.missing_images && data.missing_images.length > 0) {
        messages.push('Faltan imágenes del avatar en static/images/: ' + data.missing_images.join(', '));
      }
      // Firefox no trae la Web Speech API. Ya no es un problema: el
      // servidor transcribe. Solo se anota en la consola.
      if (preferBrowserStt && !browserSttAvailable) {
        console.info('Este navegador no reconoce voz. Transcribirá el servidor ('
          + (data.server_stt || 'servidor') + ').');
      }
      if (messages.length > 0) {
        setupBannerEl.textContent = messages.join('  ·  ');
        setupBannerEl.classList.remove('hidden');
      }
    } catch (err) {
      console.error('No se pudo verificar el estado del servidor', err);
    }
  }

  /* ------------------------------ Cambio de modo ------------------------------ */

  modeTabs.forEach((tab) => {
    tab.addEventListener('click', () => {
      if (isProcessing || tab.dataset.mode === currentMode) return;
      currentMode = tab.dataset.mode;
      modeTabs.forEach((t) => {
        const active = t === tab;
        t.classList.toggle('is-active', active);
        t.setAttribute('aria-selected', String(active));
      });
      tutorialViewEl.classList.toggle('hidden', currentMode !== 'tutorial');
      translatorViewEl.classList.toggle('hidden', currentMode !== 'translator');
      dictationViewEl.classList.toggle('hidden', currentMode !== 'dictation');
      conversationViewEl.classList.toggle('hidden', currentMode !== 'conversation');
    });
  });

  /* ============================================================
     IDIOMA COMPARTIDO

     Un unico selector en la barra alimenta los tres modos:
       · Tutorial     -> muestra el contenido de practiceLanguage
       · Traductor    -> traduce de referencia a practica
       · Conversacion -> la IA habla en practiceLanguage
     Cambiarlo desde cualquier pestana actualiza todo a la vez.
     ============================================================ */

  function loadLanguage() {
    try {
      const guardado = localStorage.getItem(LANG_STORAGE_KEY);
      return guardado === 'es' || guardado === 'en' ? guardado : 'en';
    } catch (err) {
      return 'en';
    }
  }

  function renderLanguage() {
    const practica = LANG_NAMES[practiceLanguage];
    const referencia = LANG_NAMES[referenceLanguage()];

    // El boton del idioma activo va relleno; el otro apagado. Aria refleja
    // el estado para lectores de pantalla.
    langButtons.forEach((btn) => {
      const activo = btn.dataset.lang === practiceLanguage;
      btn.classList.toggle('is-active', activo);
      btn.setAttribute('aria-checked', String(activo));
      btn.setAttribute(
        'aria-label',
        activo
          ? t('aria_practicing') + ' ' + LANG_NAMES[btn.dataset.lang]
          : t('aria_switch') + ' ' + LANG_NAMES[btn.dataset.lang]
      );
    });

    micDirectionEl.textContent = referencia + ' → ' + practica;

    // Toda la interfaz en el idioma que el usuario ya sabe.
    applyLocale();
    if (typeof renderTemas === 'function') renderTemas();
    const dicLang = document.getElementById('dictation-lang');
    if (dicLang) dicLang.textContent = practica;
  }

  function setLanguage(nuevo) {
    if (nuevo === practiceLanguage) return;

    // Si hay una conversacion en marcha, avisar ANTES de tocar nada: una
    // charla mezclando dos idiomas no serviria para evaluar, asi que
    // cambiar de idioma la reinicia. Si el usuario cancela, no se cambia
    // nada: ni el idioma ni la conversacion.
    if (conversationHistory.length > 0) {
      const seguir = confirm(t('confirm_lang'));
      if (!seguir) return;
    }

    practiceLanguage = nuevo;
    try {
      localStorage.setItem(LANG_STORAGE_KEY, nuevo);
    } catch (err) { /* modo privado: se pierde al cerrar, no es grave */ }

    renderLanguage();
    loadTutorial();
    renderStats();
    renderTranslationHistory();

    if (conversationHistory.length > 0) {
      resetConversation();
    }
  }

  // Pulsar el boton del idioma que YA esta activo no hace nada; pulsar el
  // otro cambia. Simple y sin ambiguedad.
  langButtons.forEach((btn) => {
    btn.addEventListener('click', () => {
      if (isProcessing) return;
      setLanguage(btn.dataset.lang);
    });
  });

  renderLanguage();

  /* ============================================================
     AVATAR: Web Audio API para sincronizar boca + aura con el audio
     ============================================================ */

  let audioCtx = null;
  let analyserNode = null;
  let audioDataArray = null;
  let mouthIsOpen = false;
  let lastMouthSwitchTime = 0;
  let animationFrameId = null;
  let lastObjectUrl = null;   // se revoca antes de crear el siguiente
  let lastSpoken = null;      // { text, language } para el boton de repetir

  const MOUTH_VOLUME_THRESHOLD = 22;    // 0-255, umbral para abrir la boca
  const MOUTH_MIN_SWITCH_INTERVAL = 85; // ms, evita parpadeo excesivo

  function ensureAudioGraph() {
    if (audioCtx) return;
    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    audioCtx = new AudioContextClass();
    const sourceNode = audioCtx.createMediaElementSource(avatarAudioEl);
    analyserNode = audioCtx.createAnalyser();
    analyserNode.fftSize = 256;
    audioDataArray = new Uint8Array(analyserNode.frequencyBinCount);
    sourceNode.connect(analyserNode);
    analyserNode.connect(audioCtx.destination);
  }

  function animateAvatar() {
    if (!analyserNode) return;
    analyserNode.getByteFrequencyData(audioDataArray);

    let sum = 0;
    for (let i = 0; i < audioDataArray.length; i += 1) sum += audioDataArray[i];
    const average = sum / audioDataArray.length;

    updateWaveformBars(audioDataArray);

    // Intensidad del aura (0..1): el panel del avatar "cobra vida" al hablar.
    const intensity = Math.min(1, average / 90);
    avatarStageEl.style.setProperty('--speak-intensity', intensity.toFixed(3));

    const now = performance.now();
    if (now - lastMouthSwitchTime > MOUTH_MIN_SWITCH_INTERVAL) {
      const shouldBeOpen = average > MOUTH_VOLUME_THRESHOLD;
      if (shouldBeOpen !== mouthIsOpen) {
        mouthIsOpen = shouldBeOpen;
        if (avatarImagesReady) {
          avatarImgEl.src = mouthIsOpen ? MOUTH_OPEN_SRC : MOUTH_CLOSED_SRC;
        }
        lastMouthSwitchTime = now;
      }
    }

    if (!avatarAudioEl.paused && !avatarAudioEl.ended) {
      animationFrameId = requestAnimationFrame(animateAvatar);
    } else {
      closeMouthAndStopWaveform();
    }
  }

  function updateWaveformBars(dataArray) {
    const step = Math.max(1, Math.floor(dataArray.length / waveformBars.length));
    waveformBars.forEach((bar, index) => {
      const value = dataArray[index * step] || 0;
      const scale = 0.3 + (value / 255) * 1.9;
      bar.style.transform = `scaleY(${scale})`;
    });
  }

  function closeMouthAndStopWaveform() {
    mouthIsOpen = false;
    if (avatarImagesReady) avatarImgEl.src = MOUTH_CLOSED_SRC;
    waveformBars.forEach((bar) => { bar.style.transform = 'scaleY(1)'; });
    avatarStageEl.style.setProperty('--speak-intensity', '0');
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
      animationFrameId = null;
    }
  }

  // El backend manda el audio en base64 dentro del JSON, no como archivo.
  // Aqui se convierte en algo que el elemento <audio> pueda reproducir.
  function base64ToObjectUrl(base64Data, mimeType) {
    const binary = atob(base64Data);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i += 1) bytes[i] = binary.charCodeAt(i);
    return URL.createObjectURL(new Blob([bytes], { type: mimeType }));
  }

  function playAudioBase64(base64Data, mimeType, spokenText, spokenLang) {
    if (!base64Data) return;

    // Deja de "pensar": a partir de aqui manda la animacion de la boca.
    // Se limpia aqui y no en setProcessing porque el audio arranca antes
    // de que termine el procesamiento.
    avatarThinking = false;

    // Abrir la boca YA, sin esperar.
    //
    // Antes la boca solo se abria cuando el Web Audio API empezaba a
    // analizar el volumen del audio, y entre convertir el blob y arrancar
    // la reproduccion pasaban un par de segundos: el texto aparecia y el
    // avatar seguia "pensando". Ahora se pone la boca abierta en el acto y
    // animateAvatar() toma el control en cuanto tiene datos reales de
    // volumen, asi que la transicion se ve inmediata.
    if (avatarImagesReady) {
      mouthIsOpen = true;
      avatarImgEl.src = MOUTH_OPEN_SRC;
    }

    ensureAudioGraph();
    if (audioCtx.state === 'suspended') audioCtx.resume();

    // Detener cualquier audio en curso antes de iniciar uno nuevo:
    // asi nunca se superponen dos audios.
    avatarAudioEl.pause();
    avatarAudioEl.currentTime = 0;

    // Liberar el audio anterior. Sin esto la memoria crece sin parar.
    if (lastObjectUrl) URL.revokeObjectURL(lastObjectUrl);

    try {
      lastObjectUrl = base64ToObjectUrl(base64Data, mimeType);
    } catch (err) {
      console.error(err);
      showToast('El audio recibido no es válido.', true);
      setStatus(t('ready'));
      return;
    }
    avatarAudioEl.src = lastObjectUrl;

    if (spokenText) lastSpoken = { text: spokenText, language: spokenLang };
    repeatBtn.disabled = false;

    avatarAudioEl.play().then(() => {
      setStatus(t('status_speaking'));
      animateAvatar();
    }).catch((err) => {
      console.error(err);
      showToast('No se pudo reproducir el audio.', true);
      setStatus(t('ready'));
    });
  }

  avatarAudioEl.addEventListener('ended', () => {
    closeMouthAndStopWaveform();
    setStatus(t('ready'));
  });

  // Pide al servidor la voz de un texto. Lo usa el boton de repetir y el
  // historial, para no tener que guardar el audio en el navegador.
  async function speakText(text, language) {
    if (!text) return;
    setStatus(t('status_speaking'));
    try {
      const response = await fetch('/api/speak', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text, language }),
      });
      const data = await response.json();
      if (!response.ok) {
        showToast(data.error || 'No se pudo generar el audio.', true);
        setStatus(t('ready'));
        return;
      }
      playAudioBase64(data.audio_base64, data.audio_mime, text, language);
    } catch (err) {
      console.error(err);
      showToast('No se pudo conectar con el servidor.', true);
      setStatus(t('ready'));
    }
  }

  repeatBtn.addEventListener('click', () => {
    if (lastSpoken) speakText(lastSpoken.text, lastSpoken.language);
  });

  /* ============================================================
     GRABACION DE MICROFONO (compartida por ambos modos)
     ============================================================ */

  let mediaRecorder = null;
  let recordedChunks = [];
  let activeStream = null;
  let isRecording = false;

  function getSupportedMimeType() {
    const candidates = ['audio/webm', 'audio/mp4', 'audio/ogg'];
    if (!window.MediaRecorder || !MediaRecorder.isTypeSupported) return '';
    return candidates.find((type) => MediaRecorder.isTypeSupported(type)) || '';
  }

  function extensionForMimeType(mimeType) {
    if (mimeType && mimeType.includes('mp4')) return 'mp4';
    if (mimeType && mimeType.includes('ogg')) return 'ogg';
    return 'webm';
  }

  function stopStreamTracks() {
    if (activeStream) {
      activeStream.getTracks().forEach((track) => track.stop());
      activeStream = null;
    }
  }

  async function beginRecording() {
    if (isRecording || isProcessing) return false;
    try {
      activeStream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (err) {
      showToast('No se otorgó permiso al micrófono. Habilítalo en tu navegador para grabar.', true);
      return false;
    }

    recordedChunks = [];
    const mimeType = getSupportedMimeType();
    try {
      mediaRecorder = mimeType ? new MediaRecorder(activeStream, { mimeType }) : new MediaRecorder(activeStream);
    } catch (err) {
      showToast('Este navegador no permite grabar audio.', true);
      stopStreamTracks();
      return false;
    }

    mediaRecorder.ondataavailable = (evt) => {
      if (evt.data && evt.data.size > 0) recordedChunks.push(evt.data);
    };
    mediaRecorder.start();
    isRecording = true;
    setStatus(t('status_listening'));
    return true;
  }

  function endRecording() {
    return new Promise((resolve) => {
      if (!mediaRecorder || !isRecording) { resolve(null); return; }
      mediaRecorder.onstop = () => {
        const type = mediaRecorder.mimeType || 'audio/webm';
        const blob = new Blob(recordedChunks, { type });
        stopStreamTracks();
        isRecording = false;
        resolve(blob);
      };
      mediaRecorder.stop();
    });
  }


  /* ============================================================
     ALMACENAMIENTO

     Todo se guarda en el navegador. Cada lectura va protegida: si el
     usuario navega en modo privado o borra los datos, la aplicacion
     sigue funcionando con valores vacios en vez de romperse.
     ============================================================ */

  function leerJSON(clave, porDefecto) {
    try {
      const crudo = localStorage.getItem(clave);
      if (!crudo) return porDefecto;
      const datos = JSON.parse(crudo);
      return datos === null || datos === undefined ? porDefecto : datos;
    } catch (err) {
      return porDefecto;
    }
  }

  function guardarJSON(clave, valor) {
    try {
      localStorage.setItem(clave, JSON.stringify(valor));
      return true;
    } catch (err) {
      console.warn('No se pudo guardar', clave, err);
      return false;
    }
  }

  function hoyISO() {
    return new Date().toISOString().slice(0, 10);
  }

  function diasEntre(isoA, isoB) {
    const a = new Date(isoA + 'T00:00:00');
    const b = new Date(isoB + 'T00:00:00');
    return Math.round((b - a) / 86400000);
  }

  /* ============================================================
     RACHA Y ESTADISTICAS
     ============================================================ */

  let stats = leerJSON(STATS_STORAGE_KEY, {
    streak: 0, lastDay: null, totalTurns: 0,
  });

  // Se llama cada vez que el usuario practica de verdad (un turno de
  // conversacion o una traduccion), no por abrir la aplicacion.
  function registrarActividad() {
    const hoy = hoyISO();
    stats.totalTurns = (stats.totalTurns || 0) + 1;

    if (stats.lastDay !== hoy) {
      const hueco = stats.lastDay ? diasEntre(stats.lastDay, hoy) : null;
      if (hueco === 1) {
        stats.streak = (stats.streak || 0) + 1;   // dia consecutivo
      } else {
        stats.streak = 1;                         // primer dia o racha rota
      }
      stats.lastDay = hoy;
    }

    guardarJSON(STATS_STORAGE_KEY, stats);
    renderStats();
  }

  // Una racha solo cuenta si se practico hoy o ayer. Si no, ya se rompio
  // aunque el numero siga guardado.
  function rachaVigente() {
    if (!stats.lastDay) return 0;
    const hueco = diasEntre(stats.lastDay, hoyISO());
    return hueco <= 1 ? (stats.streak || 0) : 0;
  }

  function renderStats() {
    const racha = rachaVigente();
    streakDaysEl.querySelector('span').textContent = racha;
    streakDaysEl.classList.toggle('is-hot', racha >= 2);
    streakDaysEl.title = racha === 1
      ? 'Llevas 1 día practicando'
      : 'Llevas ' + racha + ' días seguidos practicando';

    streakTurnsEl.querySelector('span').textContent = stats.totalTurns || 0;

    const evaluaciones = evaluacionesDeIdioma(practiceLanguage);
    if (evaluaciones.length === 0) {
      streakScoreEl.querySelector('span').textContent = '—';
      streakScoreEl.title = 'Aún no tienes evaluaciones en este idioma';
    } else {
      const suma = evaluaciones.reduce((total, e) => total + e.score, 0);
      const media = Math.round(suma / evaluaciones.length);
      streakScoreEl.querySelector('span').textContent = media;
      streakScoreEl.title = 'Promedio de tus ' + evaluaciones.length
        + ' evaluaciones en ' + LANG_NAMES[practiceLanguage];
    }
  }

  /* ============================================================
     HISTORIAL DE EVALUACIONES

     Antes la evaluacion se mostraba una vez y se perdia. Guardando la
     nota se puede dibujar la evolucion entre sesiones.
     ============================================================ */

  const MAX_EVALUACIONES = 40;

  function evaluacionesDeIdioma(idioma) {
    return leerJSON(EVAL_STORAGE_KEY, [])
      .filter((e) => e && e.language === idioma && typeof e.score === 'number');
  }

  function guardarEvaluacion(evaluacion, idioma) {
    const lista = leerJSON(EVAL_STORAGE_KEY, []);
    lista.push({
      date: new Date().toISOString(),
      language: idioma,
      score: evaluacion.score,
    });
    guardarJSON(EVAL_STORAGE_KEY, lista.slice(-MAX_EVALUACIONES));
  }

  // Grafico de linea dibujado a mano en SVG: sin librerias, sin descargas.
  function construirGraficoProgreso(idioma) {
    const evaluaciones = evaluacionesDeIdioma(idioma);
    if (evaluaciones.length < 2) return null;

    const recientes = evaluaciones.slice(-8);
    const notas = recientes.map((e) => e.score);
    const ANCHO = 300;
    const ALTO = 74;
    const MARGEN = 8;

    const minimo = Math.min(...notas);
    const maximo = Math.max(...notas);
    const rango = Math.max(maximo - minimo, 10);

    const puntos = notas.map((nota, i) => {
      const x = MARGEN + (i * (ANCHO - MARGEN * 2)) / Math.max(notas.length - 1, 1);
      const y = ALTO - MARGEN - ((nota - minimo) / rango) * (ALTO - MARGEN * 2);
      return { x: Math.round(x), y: Math.round(y) };
    });

    const linea = puntos.map((p) => p.x + ',' + p.y).join(' ');
    const circulos = puntos.map((p, i) => {
      const ultimo = i === puntos.length - 1;
      return '<circle cx="' + p.x + '" cy="' + p.y + '" r="' + (ultimo ? 4.5 : 3)
        + '" fill="' + (ultimo ? '#c01f63' : '#f57e22') + '"></circle>';
    }).join('');

    const primera = notas[0];
    const ultima = notas[notas.length - 1];
    const delta = ultima - primera;

    const panel = document.createElement('div');
    panel.className = 'progress-card';

    const cabecera = document.createElement('div');
    cabecera.className = 'progress-head';

    const titulo = document.createElement('h3');
    titulo.textContent = 'Tu progreso en ' + LANG_NAMES[idioma].toLowerCase();

    const deltaEl = document.createElement('span');
    deltaEl.className = 'progress-delta' + (delta < 0 ? ' is-down' : '');
    deltaEl.textContent = (delta >= 0 ? '+' : '') + delta + ' en '
      + notas.length + ' sesiones';

    cabecera.appendChild(titulo);
    cabecera.appendChild(deltaEl);

    const svg = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
    svg.setAttribute('class', 'progress-chart');
    svg.setAttribute('viewBox', '0 0 ' + ANCHO + ' ' + ALTO);
    svg.setAttribute('preserveAspectRatio', 'none');
    svg.setAttribute('role', 'img');
    svg.setAttribute('aria-label',
      'Evolución de tu puntuación: de ' + primera + ' a ' + ultima);
    svg.innerHTML = '<polyline points="' + linea + '" fill="none" '
      + 'stroke="#f57e22" stroke-width="2.5" stroke-linecap="round" '
      + 'stroke-linejoin="round"></polyline>' + circulos;

    const etiquetas = document.createElement('div');
    etiquetas.className = 'progress-labels';
    const izq = document.createElement('span');
    izq.textContent = 'Sesión ' + (evaluaciones.length - notas.length + 1)
      + ': ' + primera;
    const der = document.createElement('span');
    der.textContent = 'hoy: ' + ultima;
    etiquetas.appendChild(izq);
    etiquetas.appendChild(der);

    panel.appendChild(cabecera);
    panel.appendChild(svg);
    panel.appendChild(etiquetas);
    return panel;
  }

  /* ============================================================
     REPASO DE VOCABULARIO

     Las palabras que la evaluacion marca como problematicas se
     acumulan aqui con un contador, en vez de verse una vez y perderse.
     ============================================================ */

  const MAX_PALABRAS_REPASO = 60;

  function registrarPalabrasFalladas(evaluacion, idioma) {
    const candidatas = []
      .concat(evaluacion.problem_words || [])
      .concat(evaluacion.common_errors || []);

    if (candidatas.length === 0) return;

    const mazo = leerJSON(REVIEW_STORAGE_KEY, {});

    candidatas.forEach((cruda) => {
      const texto = String(cruda).trim();
      // Los "errores comunes" a veces vienen como frases largas
      // explicativas; no sirven como tarjeta de repaso.
      if (!texto || texto.length > 60) return;

      const clave = idioma + '::' + texto.toLowerCase();
      if (mazo[clave]) {
        mazo[clave].count += 1;
      } else {
        mazo[clave] = { text: texto, language: idioma, count: 1 };
      }
    });

    const entradas = Object.entries(mazo)
      .sort((a, b) => b[1].count - a[1].count)
      .slice(0, MAX_PALABRAS_REPASO);

    guardarJSON(REVIEW_STORAGE_KEY, Object.fromEntries(entradas));
  }

  function palabrasDeRepaso(idioma) {
    return Object.values(leerJSON(REVIEW_STORAGE_KEY, {}))
      .filter((p) => p && p.language === idioma)
      .sort((a, b) => b.count - a.count);
  }

  function construirRepaso(idioma) {
    const palabras = palabrasDeRepaso(idioma).slice(0, 8);
    if (palabras.length === 0) return null;

    const panel = document.createElement('div');
    panel.className = 'progress-card';

    const cabecera = document.createElement('div');
    cabecera.className = 'progress-head';
    const titulo = document.createElement('h3');
    titulo.textContent = 'Palabras para repasar';
    const nota = document.createElement('span');
    nota.className = 'progress-delta';
    nota.textContent = palabras.length + ' guardadas';
    cabecera.appendChild(titulo);
    cabecera.appendChild(nota);
    panel.appendChild(cabecera);

    const lista = document.createElement('div');
    lista.className = 'review-list';

    palabras.forEach((palabra) => {
      const fila = document.createElement('div');
      fila.className = 'review-item';

      const textos = document.createElement('div');
      textos.className = 'review-texts';
      const principal = document.createElement('span');
      principal.className = 'review-word';
      principal.textContent = palabra.text;
      textos.appendChild(principal);

      const contador = document.createElement('span');
      const nivel = palabra.count >= 3 ? 3 : palabra.count === 2 ? 2 : 1;
      contador.className = 'review-count level-' + nivel;
      contador.textContent = palabra.count === 1
        ? '1 vez' : palabra.count + ' veces';

      const escuchar = document.createElement('button');
      escuchar.type = 'button';
      escuchar.className = 'icon-btn';
      escuchar.textContent = t('listen');
      escuchar.addEventListener('click', () => {
        speakText(palabra.text, palabra.language);
      });

      fila.appendChild(textos);
      fila.appendChild(contador);
      fila.appendChild(escuchar);
      lista.appendChild(fila);
    });

    panel.appendChild(lista);
    return panel;
  }


  /* ============================================================
     PESTANA TUTORIAL

     El contenido viene de /api/tutorial (texto fijo del servidor, sin
     IA de por medio: carga al instante y no gasta cuota). El progreso
     de cada concepto se guarda por idioma en el navegador.
     ============================================================ */

  const ICONOS_CONCEPTO = {
    saludo: '¡Hi', numero: '12', cortesia: '♥',
    gramatica: 'Aa', pregunta: '?', frase: '“”',
  };

  // Nombres de los conceptos en el idioma de la interfaz. El servidor los
  // manda en su idioma; aqui se traducen por su id (que es estable) para
  // que salgan en la lengua que el usuario ya conoce. El concepto de
  // gramatica es distinto en cada idioma (to be / ser y estar), asi que ese
  // se deja tal como lo manda el servidor.
  const NOMBRES_CONCEPTO = {
    es: {
      saludos: 'Saludos', numeros: 'Números', cortesia: 'Cortesía',
      preguntas: 'Preguntas', 'frases-utiles': 'Frases útiles',
    },
    en: {
      saludos: 'Greetings', numeros: 'Numbers', cortesia: 'Courtesy',
      preguntas: 'Questions', 'frases-utiles': 'Useful phrases',
    },
  };

  function nombreConcepto(concepto) {
    const juego = NOMBRES_CONCEPTO[uiLang()] || {};
    return juego[concepto.id] || concepto.nombre;
  }

  let tutorialData = null;

  function progresoTutorial() {
    return leerJSON(TUTORIAL_STORAGE_KEY, {});
  }

  // Cada entrada aprendida se guarda como  idioma::concepto::indice
  function claveEntrada(conceptoId, indice) {
    return practiceLanguage + '::' + conceptoId + '::' + indice;
  }

  function entradaAprendida(conceptoId, indice) {
    return Boolean(progresoTutorial()[claveEntrada(conceptoId, indice)]);
  }

  function alternarEntrada(conceptoId, indice) {
    const progreso = progresoTutorial();
    const clave = claveEntrada(conceptoId, indice);
    if (progreso[clave]) {
      delete progreso[clave];
    } else {
      progreso[clave] = true;
    }
    guardarJSON(TUTORIAL_STORAGE_KEY, progreso);
  }

  function contarAprendidas(concepto) {
    let total = 0;
    for (let i = 0; i < concepto.total; i += 1) {
      if (entradaAprendida(concepto.id, i)) total += 1;
    }
    return total;
  }

  async function loadTutorial() {
    // El contenido se pide en el idioma que se PRACTICA: las frases de cada
    // leccion deben estar en ese idioma para que sirvan de practica. Los
    // nombres de los conceptos y las etiquetas se traducen aparte, en el
    // cliente, al idioma de la interfaz.
    const nombreIdioma = practiceLanguage === 'es' ? t('lang_es') : t('lang_en');
    originTitleEl.textContent = t('origin_of') + ' ' + nombreIdioma;
    originTextEl.textContent = t('tutorial_loading');
    conceptGridEl.innerHTML = '';
    cerrarLeccion();

    try {
      const respuesta = await fetch('/api/tutorial?language=' + practiceLanguage);
      const datos = await respuesta.json();
      if (!respuesta.ok) {
        originTextEl.textContent = t('tutorial_load_error');
        return;
      }
      tutorialData = datos;
      // El origen se muestra en el idioma de la INTERFAZ (el que el usuario
      // ya sabe): describe el idioma que se practica, pero en la lengua que
      // se entiende. El servidor manda las dos versiones etiquetadas.
      const origen = uiLang() === 'en' ? datos.origen_en : datos.origen_es;
      originTextEl.textContent = origen || datos.origen;
      renderConceptos();
    } catch (err) {
      console.error(err);
      originTextEl.textContent = t('tutorial_conn_error');
    }
  }

  function renderConceptos() {
    conceptGridEl.innerHTML = '';
    if (!tutorialData) return;

    tutorialData.conceptos.forEach((concepto) => {
      const aprendidas = contarAprendidas(concepto);
      const completo = aprendidas === concepto.total;

      const tarjeta = document.createElement('button');
      tarjeta.type = 'button';
      tarjeta.className = 'concept-card' + (completo ? ' is-done' : '');

      const icono = document.createElement('span');
      icono.className = 'concept-icon';
      icono.textContent = ICONOS_CONCEPTO[concepto.icono] || 'Aa';
      icono.setAttribute('aria-hidden', 'true');

      const nombre = document.createElement('span');
      nombre.className = 'concept-name';
      nombre.textContent = nombreConcepto(concepto);

      const progreso = document.createElement('span');
      progreso.className = 'concept-progress';
      if (completo) {
        progreso.textContent = t('concept_done');
      } else if (aprendidas === 0) {
        progreso.textContent = t('concept_start');
      } else {
        progreso.textContent = aprendidas + ' ' + t('concept_of') + ' ' + concepto.total;
      }

      const barra = document.createElement('span');
      barra.className = 'concept-bar';
      const relleno = document.createElement('span');
      relleno.style.width = Math.round((aprendidas / concepto.total) * 100) + '%';
      barra.appendChild(relleno);

      tarjeta.appendChild(icono);
      tarjeta.appendChild(nombre);
      tarjeta.appendChild(progreso);
      tarjeta.appendChild(barra);
      tarjeta.addEventListener('click', () => abrirLeccion(concepto));

      conceptGridEl.appendChild(tarjeta);
    });
  }

  function abrirLeccion(concepto) {
    lessonTitleEl.textContent = nombreConcepto(concepto);
    lessonEntriesEl.innerHTML = '';

    concepto.entradas.forEach((entrada, indice) => {
      const aprendida = entradaAprendida(concepto.id, indice);

      const fila = document.createElement('div');
      fila.className = 'lesson-entry' + (aprendida ? ' is-learned' : '');

      const textos = document.createElement('div');
      textos.className = 'entry-texts';
      const principal = document.createElement('p');
      principal.className = 'entry-main';
      principal.textContent = entrada.texto;
      const secundario = document.createElement('p');
      secundario.className = 'entry-sub';
      secundario.textContent = entrada.traduccion;
      textos.appendChild(principal);
      textos.appendChild(secundario);

      const escuchar = document.createElement('button');
      escuchar.type = 'button';
      escuchar.className = 'icon-btn';
      escuchar.textContent = t('listen');
      escuchar.addEventListener('click', () => {
        speakText(entrada.texto, practiceLanguage);
      });

      const marcar = document.createElement('button');
      marcar.type = 'button';
      marcar.className = 'entry-check';
      marcar.innerHTML = '<svg viewBox="0 0 24 24" width="14" height="14" '
        + 'fill="none" stroke="currentColor" stroke-width="3.5" '
        + 'stroke-linecap="round" stroke-linejoin="round">'
        + '<polyline points="20 6 9 17 4 12"></polyline></svg>';
      marcar.setAttribute('aria-label', t('mark_learned'));
      marcar.addEventListener('click', () => {
        alternarEntrada(concepto.id, indice);
        fila.classList.toggle('is-learned');
        actualizarContadorLeccion(concepto);
        renderConceptos();
      });

      fila.appendChild(textos);
      fila.appendChild(escuchar);
      fila.appendChild(marcar);
      lessonEntriesEl.appendChild(fila);
    });

    actualizarContadorLeccion(concepto);
    conceptGridEl.classList.add('hidden');
    lessonPanelEl.classList.remove('hidden');
  }

  function actualizarContadorLeccion(concepto) {
    lessonCountEl.textContent = contarAprendidas(concepto) + ' ' + t('concept_of')
      + ' ' + concepto.total + ' ' + t('lesson_learned');
  }

  function cerrarLeccion() {
    lessonPanelEl.classList.add('hidden');
    conceptGridEl.classList.remove('hidden');
  }

  lessonBackBtn.addEventListener('click', cerrarLeccion);

  resetTutorialBtn.addEventListener('click', () => {
    if (!confirm(t('confirm_reset') + ' '
        + LANG_NAMES[practiceLanguage] + '?')) return;

    // Solo se borra el idioma que se esta viendo; el otro se conserva.
    const progreso = progresoTutorial();
    Object.keys(progreso).forEach((clave) => {
      if (clave.startsWith(practiceLanguage + '::')) delete progreso[clave];
    });
    guardarJSON(TUTORIAL_STORAGE_KEY, progreso);
    cerrarLeccion();
    renderConceptos();
  });

  /* ============================================================
     TEMAS DE CONVERSACION
     ============================================================ */

  function etiquetaTema(tema) {
    return t('topic_' + tema) || tema;
  }

  function renderTemas() {
    topicSwitchEl.innerHTML = '';

    availableTopics.forEach((tema) => {
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'topic-chip' + (tema === currentTopic ? ' is-active' : '');
      chip.textContent = etiquetaTema(tema);
      chip.setAttribute('role', 'radio');
      chip.setAttribute('aria-checked', String(tema === currentTopic));

      chip.addEventListener('click', () => {
        if (isProcessing || tema === currentTopic) return;

        // El tema orienta el prompt desde el primer mensaje, asi que
        // cambiarlo a mitad de charla dejaria la conversacion incoherente.
        if (conversationHistory.length > 0) {
          if (!confirm('Cambiar de tema reinicia la conversación. ¿Seguir?')) return;
          resetConversation();
        }

        currentTopic = tema;
        renderTemas();
      });

      topicSwitchEl.appendChild(chip);
    });
  }

  /* ============================================================
     RECONOCIMIENTO DE VOZ EN EL NAVEGADOR (Web Speech API)

     Con STT_PROVIDER=browser el navegador transcribe y el servidor
     recibe texto. Es gratis, no gasta cuota y no sube audio a ningun
     sitio. Si el navegador no lo soporta (Firefox), se cae de vuelta
     a grabar y transcribir en el servidor.
     ============================================================ */

  const SpeechRecognitionClass =
    window.SpeechRecognition || window.webkitSpeechRecognition || null;

  const browserSttAvailable = Boolean(SpeechRecognitionClass);
  let recognition = null;
  let recognitionPromise = null;

  const LOCALES = { es: 'es-ES', en: 'en-US' };

  // Si el navegador no contesta al soltar, no dejamos la interfaz colgada.
  const RECOGNITION_TIMEOUT_MS = 5000;

  function beginBrowserRecognition(language) {
    if (!browserSttAvailable) return false;

    const rec = new SpeechRecognitionClass();
    rec.lang = LOCALES[language] || 'en-US';
    rec.interimResults = false;
    rec.maxAlternatives = 1;

    // continuous = true es imprescindible aquí.
    //
    // Con false, el navegador da por terminado el reconocimiento en cuanto
    // detecta una pausa al hablar, sin esperar a que se suelte el botón.
    // Como todo el mundo hace una pausa natural antes de soltar, el
    // reconocimiento terminaba antes de tiempo: se perdía lo dicho y la
    // interfaz se quedaba clavada en "Escuchando…" para siempre.
    //
    // Con true, quien manda es el botón: el reconocimiento dura exactamente
    // lo que dure la pulsación. Además permite frases con pausas.
    rec.continuous = true;

    let finalText = '';
    let settled = false;

    // La promesa se crea AL EMPEZAR, no al soltar. Así, si el navegador
    // termina el reconocimiento por su cuenta, onend siempre encuentra a
    // quien entregarle el resultado. Antes se perdía.
    recognitionPromise = new Promise((resolve) => {
      const finish = () => {
        if (settled) return;
        settled = true;
        resolve(finalText.trim());
      };

      rec.onresult = (event) => {
        for (let i = event.resultIndex; i < event.results.length; i += 1) {
          if (event.results[i].isFinal) {
            finalText += event.results[i][0].transcript;
          }
        }
      };

      rec.onerror = (event) => {
        if (event.error === 'not-allowed') {
          // Esto sí es culpa del permiso: el usuario puede arreglarlo.
          showToast('El navegador bloqueó el micrófono. Permite el acceso y recarga la página.', true);
          finish();
        } else if (event.error === 'network' || event.error === 'service-not-allowed') {
          // 'network' NO significa que no haya internet.
          //
          // El reconocimiento de Chrome manda el audio a un servicio de
          // Google usando una clave privada incrustada en el navegador. Los
          // navegadores derivados de Chromium (Brave, Chromium, Opera,
          // Electron) no la llevan, así que reciben 'network' siempre,
          // estén conectados o no. Un cortafuegos que bloquee ese servicio
          // da lo mismo. La API no dice cuál de los casos es.
          //
          // No hay nada que el usuario pueda tocar, así que no se le pide
          // que revise su conexión: se pasa al servidor y punto.
          marcarNavegadorInutil(event.error);
          finish();
        } else if (event.error === 'no-speech' || event.error === 'aborted') {
          // Normales. onend llega detrás y cierra.
        } else {
          console.error('Web Speech API:', event.error);
        }
      };

      rec.onend = finish;
    });

    try {
      rec.start();
      recognition = rec;
      return true;
    } catch (err) {
      // start() sobre un reconocimiento ya activo lanza InvalidStateError.
      console.error('No se pudo iniciar el reconocimiento', err);
      recognition = null;
      recognitionPromise = null;
      return false;
    }
  }

  function endBrowserRecognition() {
    if (!recognition || !recognitionPromise) return Promise.resolve('');

    const pendiente = recognitionPromise;

    try {
      recognition.stop();
    } catch (err) {
      // Ya había terminado por su cuenta. La promesa ya está resuelta,
      // así que no hay nada que hacer: basta con esperarla.
    }

    // Red de seguridad: si onend no llegara nunca, no se cuelga la interfaz.
    const conTope = new Promise((resolve) => {
      setTimeout(() => resolve(''), RECOGNITION_TIMEOUT_MS);
    });

    return Promise.race([pendiente, conTope]);
  }

  // Decide en cada pulsacion quien transcribe.
  //
  // browserSttBroken se activa la primera vez que el navegador demuestra que
  // no puede. A partir de ahi ya no se le vuelve a preguntar: se manda el
  // audio al servidor directamente.
  function useBrowserStt() {
    return preferBrowserStt && browserSttAvailable && !browserSttBroken;
  }

  // El navegador no puede reconocer voz. Se apunta y se avisa una sola vez.
  function marcarNavegadorInutil(motivo) {
    if (browserSttBroken) return;
    browserSttBroken = true;
    console.warn('Reconocimiento del navegador descartado:', motivo);
    showToast('Tu navegador no puede reconocer voz. A partir de ahora lo hará el servidor: vuelve a pulsar el micrófono.', true);
  }

  /* ============================================================
     MODO DICTADO

     El usuario dicta una frase, el servidor la corrige y el avatar lee
     la version correcta. No hay conversacion ni traduccion: es practica
     de como se dice bien algo.
     ============================================================ */

  const MAX_DICTADO = 30;

  async function handleDictationInput({ blob, text }) {
    if (isProcessing) return;
    setProcessing(true);

    try {
      const formData = new FormData();
      formData.append('practice_language', practiceLanguage);
      if (text) {
        formData.append('text', text);
      } else if (blob) {
        formData.append('audio', blob, 'dictado.webm');
      } else {
        return;
      }

      setStatus(t('status_correcting'));
      const resp = await fetch('/api/dictation', { method: 'POST', body: formData });
      const data = await resp.json();

      if (!resp.ok) {
        showToast(data.error || 'No se pudo corregir la frase.', true);
        return;
      }

      registrarActividad();
      guardarDictado(data);
      renderDictationHistory();

      // El avatar lee la version corregida.
      if (data.audio_base64) {
        playAudioBase64(data.audio_base64, data.audio_mime,
                        data.correction, practiceLanguage);
      } else {
        setStatus(t('ready'));
      }
    } catch (err) {
      console.error(err);
      showToast('Error de conexión al corregir.', true);
      setStatus(t('ready'));
    } finally {
      setProcessing(false);
    }
  }

  function guardarDictado(data) {
    const lista = leerJSON(DICTATION_STORAGE_KEY, []);
    lista.unshift({
      said: data.user_text,
      fixed: data.correction,
      explanation: data.explanation,
      perfect: data.no_errors,
      language: practiceLanguage,
    });
    guardarJSON(DICTATION_STORAGE_KEY, lista.slice(0, MAX_DICTADO));
  }

  function renderDictationHistory() {
    const lista = leerJSON(DICTATION_STORAGE_KEY, [])
      .filter((d) => d && d.language === practiceLanguage);

    dictationHistoryEl.innerHTML = '';

    if (lista.length === 0) {
      const vacio = document.createElement('p');
      vacio.className = 'empty-state';
      vacio.textContent = t('dictation_empty');
      dictationHistoryEl.appendChild(vacio);
      return;
    }

    lista.forEach((d) => {
      const card = document.createElement('div');
      card.className = 'dictation-card' + (d.perfect ? ' is-perfect' : '');

      // Lo que dijo el usuario
      const said = document.createElement('div');
      said.className = 'dictation-said';
      said.innerHTML = '<span class="dic-label">' + t('dic_said') + '</span>';
      const saidText = document.createElement('span');
      saidText.textContent = d.said;
      said.appendChild(saidText);
      card.appendChild(said);

      // La version corregida (solo si difiere)
      if (!d.perfect) {
        const fixed = document.createElement('div');
        fixed.className = 'dictation-fixed';
        fixed.innerHTML = '<span class="dic-label">' + t('dic_fixed') + '</span>';
        const fixedText = document.createElement('span');
        fixedText.textContent = d.fixed;
        fixed.appendChild(fixedText);
        card.appendChild(fixed);
      }

      // La explicacion, o la felicitacion si estaba perfecta
      const explain = document.createElement('p');
      explain.className = 'dictation-explain';
      explain.textContent = d.perfect
        ? (d.explanation || t('dic_perfect'))
        : d.explanation;
      if (explain.textContent) card.appendChild(explain);

      // Boton para volver a escuchar la version correcta
      const listen = document.createElement('button');
      listen.type = 'button';
      listen.className = 'icon-btn dic-listen';
      listen.textContent = t('listen');
      listen.addEventListener('click', () => speakText(d.fixed, d.language));
      card.appendChild(listen);

      dictationHistoryEl.appendChild(card);
    });
  }

  clearDictationBtn.addEventListener('click', () => {
    if (leerJSON(DICTATION_STORAGE_KEY, []).length === 0) return;
    guardarJSON(DICTATION_STORAGE_KEY, []);
    renderDictationHistory();
  });

  function attachHoldToRecord(button, onResult, getLanguage) {
    let usingBrowser = false;
    let active = false;    // hay una captura en curso
    let stopping = false;  // ya se está cerrando la captura

    const start = async (evt) => {
      if (evt && evt.cancelable) evt.preventDefault();
      if (isProcessing || active) return;   // ignora pulsaciones repetidas

      usingBrowser = useBrowserStt();

      let started = usingBrowser
        ? beginBrowserRecognition(getLanguage())
        : await beginRecording();

      // Si el reconocimiento del navegador ni siquiera arranca, se graba
      // audio y lo transcribe el servidor. Así no se pierde el turno.
      if (usingBrowser && !started) {
        marcarNavegadorInutil('no arrancó');
        usingBrowser = false;
        started = await beginRecording();
      }

      if (started) {
        active = true;
        button.classList.add('is-recording');
        setStatus(t('status_listening'));
      } else {
        setStatus(t('ready'));
      }
    };

    // mouseup y mouseleave pueden dispararse los dos al soltar. Sin el
    // guardia, la segunda llamada entraba mientras la primera esperaba y
    // el turno se enviaba por duplicado.
    const stop = async (evt) => {
      if (evt && evt.cancelable) evt.preventDefault();
      if (!active || stopping) return;

      stopping = true;
      button.classList.remove('is-recording');

      try {
        if (usingBrowser) {
          const text = await endBrowserRecognition();
          recognition = null;
          recognitionPromise = null;
          if (text) {
            onResult({ text });
          } else {
            showToast('No se entendió lo que dijiste. Inténtalo otra vez.', true);
            setStatus(t('ready'));
          }
          return;
        }

        const blob = await endRecording();
        if (blob && blob.size > 0) {
          onResult({ blob });
        } else {
          setStatus(t('ready'));
        }
      } finally {
        active = false;
        stopping = false;
      }
    };

    button.addEventListener('mousedown', start);
    button.addEventListener('touchstart', start, { passive: false });
    button.addEventListener('mouseup', stop);
    button.addEventListener('mouseleave', stop);
    button.addEventListener('touchend', stop);
    button.addEventListener('touchcancel', stop);
  }

  attachHoldToRecord(
    translatorMicBtn,
    handleTranslatorInput,
    () => referenceLanguage(),   // en el traductor se habla en el idioma conocido
  );

  attachHoldToRecord(
    conversationMicBtn,
    ({ text, blob }) => sendConversationTurn({ text, audioBlob: blob }),
    () => practiceLanguage,
  );

  attachHoldToRecord(
    dictationMicBtn,
    ({ text, blob }) => handleDictationInput({ text, blob }),
    () => practiceLanguage,   // se dicta en el idioma que se practica
  );

  // Barra espaciadora: solo en modo Traductor y nunca al escribir en un campo.
  document.addEventListener('keydown', (evt) => {
    if (evt.code !== 'Space' || currentMode !== 'translator') return;
    if (isEditableElement(document.activeElement) || evt.repeat || isProcessing) return;
    evt.preventDefault();
    translatorMicBtn.dispatchEvent(new Event('mousedown'));
  });
  document.addEventListener('keyup', (evt) => {
    if (evt.code !== 'Space' || currentMode !== 'translator') return;
    if (isEditableElement(document.activeElement)) return;
    evt.preventDefault();
    translatorMicBtn.dispatchEvent(new Event('mouseup'));
  });

  /* ============================================================
     MODO TRADUCTOR
     ============================================================ */

  // Recibe audio grabado (si transcribe el servidor) o texto ya
  // reconocido por el navegador (si STT_PROVIDER=browser).
  async function handleTranslatorInput({ blob, text }) {
    setProcessing(true);
    setStatus(text ? t('status_translating') : t('status_processing'));
    try {
      const formData = new FormData();
      // Se traduce del idioma conocido al que se practica, segun el pill.
      formData.append('direction', referenceLanguage() + '-' + practiceLanguage);
      if (text) {
        formData.append('text', text);
      } else {
        formData.append('audio', blob, `recording.${extensionForMimeType(blob.type)}`);
      }

      const response = await fetch('/api/translate', { method: 'POST', body: formData });
      const data = await response.json();

      if (!response.ok) {
        showToast(data.error || 'Ocurrió un error al traducir.', true);
        setStatus(t('ready'));
        return;
      }

      addTranslationToHistory(data);
      registrarActividad();
      setStatus(t('status_speaking'));
      playAudioBase64(data.audio_base64, data.audio_mime, data.translated_text, data.target_lang);
    } catch (err) {
      console.error(err);
      showToast('No se pudo conectar con el servidor. Verifica que esté en ejecución.', true);
      setStatus(t('ready'));
    } finally {
      setProcessing(false);
    }
  }

  function loadTranslationHistory() {
    try {
      const raw = localStorage.getItem(HISTORY_STORAGE_KEY);
      return raw ? JSON.parse(raw) : [];
    } catch (err) {
      return [];
    }
  }

  function saveTranslationHistory(list) {
    try {
      localStorage.setItem(HISTORY_STORAGE_KEY, JSON.stringify(list));
    } catch (err) {
      console.error('No se pudo guardar el historial de traducciones', err);
    }
  }

  const MAX_HISTORY_ENTRIES = 50;

  function addTranslationToHistory(entry) {
    translationHistory.unshift({
      original_text: entry.original_text,
      translated_text: entry.translated_text,
      source_lang: entry.source_lang,
      target_lang: entry.target_lang,
      // A proposito NO se guarda el audio: en base64 ocupa ~100 KB por
      // entrada y llenaba la cuota de localStorage (5 MB) en unas 40
      // traducciones, momento en el que el historial dejaba de guardarse.
      // Para repetir el audio se vuelve a pedir con /api/speak.
    });
    if (translationHistory.length > MAX_HISTORY_ENTRIES) {
      translationHistory = translationHistory.slice(0, MAX_HISTORY_ENTRIES);
    }
    saveTranslationHistory(translationHistory);
    renderTranslationHistory();
  }

  function renderTranslationHistory() {
    if (translationHistory.length === 0) {
      translationHistoryEl.innerHTML = '<p class="empty-state">Tus traducciones aparecerán aquí.</p>';
      return;
    }
    translationHistoryEl.innerHTML = '';
    translationHistory.forEach((entry) => {
      translationHistoryEl.appendChild(buildTranslationCard(entry));
    });
  }

  function buildTranslationCard(entry) {
    const card = document.createElement('div');
    card.className = 'translation-card';

    const tag = document.createElement('p');
    tag.className = 'lang-tag';
    tag.textContent = entry.source_lang === 'es' ? 'Español → Inglés' : 'Inglés → Español';
    card.appendChild(tag);

    const originalP = document.createElement('p');
    originalP.className = 'original-text';
    originalP.textContent = entry.original_text;
    card.appendChild(originalP);

    const translatedP = document.createElement('p');
    translatedP.className = 'translated-text';
    translatedP.textContent = entry.translated_text;
    card.appendChild(translatedP);

    const actions = document.createElement('div');
    actions.className = 'card-actions';

    const copyBtn = document.createElement('button');
    copyBtn.type = 'button';
    copyBtn.className = 'icon-btn';
    copyBtn.textContent = 'Copiar';
    copyBtn.addEventListener('click', () => {
      navigator.clipboard.writeText(entry.translated_text)
        .then(() => showToast('Traducción copiada.'))
        .catch(() => showToast('No se pudo copiar el texto.', true));
    });

    const playBtn = document.createElement('button');
    playBtn.type = 'button';
    playBtn.className = 'icon-btn';
    playBtn.textContent = 'Repetir audio';
    playBtn.addEventListener('click', () => speakText(entry.translated_text, entry.target_lang));

    actions.appendChild(copyBtn);
    actions.appendChild(playBtn);
    card.appendChild(actions);
    return card;
  }

  // Entrada de texto como alternativa al micrófono en Traductor.
  translatorTextForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const texto = translatorTextInput.value.trim();
    if (!texto || isProcessing) return;
    translatorTextInput.value = '';
    handleTranslatorInput({ text: texto, blob: null });
  });

  // Entrada de texto como alternativa al micrófono en Dictado.
  dictationTextForm.addEventListener('submit', (e) => {
    e.preventDefault();
    const texto = dictationTextInput.value.trim();
    if (!texto || isProcessing) return;
    dictationTextInput.value = '';
    handleDictationInput({ text: texto, blob: null });
  });

  clearHistoryBtn.addEventListener('click', () => {
    translationHistory = [];
    saveTranslationHistory(translationHistory);
    renderTranslationHistory();
  });

  /* ============================================================
     MODO CONVERSACION
     ============================================================ */

  function resetConversation() {
    conversationHistory = [];
    chatMessagesEl.innerHTML = '<p class="empty-state" id="conversation-empty-state">Escribe o habla para comenzar una conversación libre.</p>';
    evaluationPanelEl.classList.add('hidden');
    evaluationPanelEl.innerHTML = '';
    chatMessagesEl.classList.remove('hidden');
    chatInputRowEl.classList.remove('hidden');
    updateFinishButtonState();
  }

  function updateFinishButtonState() {
    finishConversationBtn.disabled = conversationHistory.length === 0 || isProcessing;
  }

  chatInputRowEl.addEventListener('submit', (evt) => {
    evt.preventDefault();
    const text = conversationTextInputEl.value.trim();
    if (!text || isProcessing) return;
    conversationTextInputEl.value = '';
    sendConversationTurn({ text });
  });

  async function sendConversationTurn({ text, audioBlob }) {
    setProcessing(true);
    setStatus(audioBlob ? t('status_processing') : t('status_thinking'));

    try {
      const formData = new FormData();
      formData.append('practice_language', practiceLanguage);
      formData.append('topic', currentTopic);
      formData.append('history', JSON.stringify(conversationHistory));
      if (audioBlob) {
        formData.append('audio', audioBlob, `recording.${extensionForMimeType(audioBlob.type)}`);
      } else {
        formData.append('text', text);
      }

      const response = await fetch('/api/conversation', { method: 'POST', body: formData });
      const data = await response.json();

      if (!response.ok) {
        showToast(data.error || 'Ocurrió un error en la conversación.', true);
        setStatus(t('ready'));
        return;
      }

      ensureChatListReady();
      appendChatBubble('user', data.user_text, null, null);
      appendChatBubble('assistant', data.ai_text, data.translated_text, practiceLanguage);

      conversationHistory = data.history;
      registrarActividad();
      updateFinishButtonState();

      setStatus(t('status_speaking'));
      playAudioBase64(data.audio_base64, data.audio_mime, data.ai_text, practiceLanguage);
    } catch (err) {
      console.error(err);
      showToast('No se pudo conectar con el servidor. Verifica que esté en ejecución.', true);
      setStatus(t('ready'));
    } finally {
      setProcessing(false);
    }
  }

  function ensureChatListReady() {
    const emptyState = document.getElementById('conversation-empty-state');
    if (emptyState) emptyState.remove();
  }

  function appendChatBubble(role, text, translation, spokenLang) {
    const bubble = document.createElement('div');
    bubble.className = `chat-bubble ${role}`;

    const textP = document.createElement('p');
    textP.style.margin = '0';
    textP.textContent = text;
    bubble.appendChild(textP);

    if (role === 'assistant') {
      if (translation) {
        const translationP = document.createElement('p');
        translationP.className = 'translation-line';
        translationP.textContent = translation;
        bubble.appendChild(translationP);
      }
      if (spokenLang) {
        const replayBtn = document.createElement('button');
        replayBtn.type = 'button';
        replayBtn.className = 'icon-btn';
        replayBtn.style.alignSelf = 'flex-start';
        replayBtn.textContent = 'Repetir audio';
        replayBtn.addEventListener('click', () => speakText(text, spokenLang));
        bubble.appendChild(replayBtn);
      }
    }

    chatMessagesEl.appendChild(bubble);
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
  }

  finishConversationBtn.addEventListener('click', async () => {
    if (isProcessing || conversationHistory.length === 0) return;
    setProcessing(true);
    setStatus('Generando evaluación…');
    try {
      const response = await fetch('/api/conversation/evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ history: conversationHistory, practice_language: practiceLanguage }),
      });
      const data = await response.json();

      if (!response.ok) {
        showToast(data.error || 'No se pudo generar la evaluación.', true);
        setStatus(t('ready'));
        return;
      }

      // Antes esto se mostraba y se perdia. Ahora la nota alimenta el
      // grafico de progreso y las palabras falladas van al mazo de repaso.
      guardarEvaluacion(data, practiceLanguage);
      registrarPalabrasFalladas(data, practiceLanguage);
      renderStats();

      lastEvaluation = data;
      renderEvaluation(data);
      setStatus(t('ready'));
    } catch (err) {
      console.error(err);
      showToast('No se pudo conectar con el servidor. Verifica que esté en ejecución.', true);
      setStatus(t('ready'));
    } finally {
      setProcessing(false);
    }
  });

  /*
    Muestra el avatar contento unos segundos tras una buena nota.

    No depende de imagenesDisponibles.feliz: ese objeto se llena cuando
    /api/status responde, y si la evaluacion llega antes, estaria vacio y
    la imagen no se mostraria nunca (justo el fallo que se veia). En vez de
    eso se intenta cargar la imagen con un Image() temporal y solo se
    aplica si carga sin error. Asi funciona aunque el servidor no la haya
    detectado al arrancar, o aunque se anada despues.
  */
  function mostrarAvatarFeliz() {
    if (!avatarImagesReady) return;

    const prueba = new Image();
    prueba.onload = () => {
      // Si mientras cargaba empezo a sonar audio, manda la animacion de la
      // boca: no se pisa una locucion en curso con la cara de feliz.
      if (!avatarAudioEl.paused) return;
      avatarImgEl.src = HAPPY_SRC;
      setTimeout(() => {
        if (!avatarAudioEl.paused) return;
        avatarImgEl.src = MOUTH_CLOSED_SRC;
      }, 4000);
    };
    prueba.onerror = () => { /* no hay flengfeliz.png: no pasa nada */ };
    prueba.src = HAPPY_SRC;
  }

  function renderEvaluation(evaluation) {
    const score = Math.max(0, Math.min(100, Math.round(Number(evaluation.score) || 0)));

    // Con buena nota, el avatar celebra unos segundos.
    if (score >= 70) mostrarAvatarFeliz();

    // La evaluacion reemplaza al chat para poder mostrarse completa,
    // en vez de competir con el por el espacio del panel.
    chatMessagesEl.classList.add('hidden');
    chatInputRowEl.classList.add('hidden');

    evaluationPanelEl.innerHTML = '';
    evaluationPanelEl.classList.remove('hidden');

    const scoreRow = document.createElement('div');
    scoreRow.className = 'evaluation-score';

    const scoreCircle = document.createElement('div');
    scoreCircle.className = 'score-circle';
    scoreCircle.style.setProperty('--score', score);
    const scoreSpan = document.createElement('span');
    scoreSpan.textContent = String(score);
    scoreCircle.appendChild(scoreSpan);

    const scoreCaption = document.createElement('div');
    const captionTitle = document.createElement('h3');
    captionTitle.style.cssText = 'margin:0 0 4px;font-family:var(--font-display);font-size:16px;color:var(--white)';
    captionTitle.textContent = 'Resultado general';
    const captionText = document.createElement('p');
    captionText.style.cssText = 'margin:0;font-size:13.5px;color:var(--ink-300)';
    captionText.textContent = 'Puntuación aproximada de 0 a 100 sobre esta conversación.';
    scoreCaption.appendChild(captionTitle);
    scoreCaption.appendChild(captionText);

    scoreRow.appendChild(scoreCircle);
    scoreRow.appendChild(scoreCaption);
    evaluationPanelEl.appendChild(scoreRow);

    // Progreso entre sesiones. Solo aparece a partir de la segunda:
    // con un unico punto no hay evolucion que ensenar.
    const grafico = construirGraficoProgreso(practiceLanguage);
    if (grafico) evaluationPanelEl.appendChild(grafico);

    // Mazo de repaso acumulado de todas las evaluaciones.
    const repaso = construirRepaso(practiceLanguage);
    if (repaso) evaluationPanelEl.appendChild(repaso);

    const disclaimer = document.createElement('p');
    disclaimer.className = 'evaluation-disclaimer';
    disclaimer.textContent = t('eval_disclaimer');
    evaluationPanelEl.appendChild(disclaimer);

    const grid = document.createElement('div');
    grid.className = 'evaluation-grid';
    grid.appendChild(buildEvaluationTextBlock(t('eval_pronunciation'), evaluation.pronunciation));
    grid.appendChild(buildEvaluationTextBlock(t('eval_fluency'), evaluation.fluency));
    grid.appendChild(buildEvaluationListBlock(t('eval_problem_words'), evaluation.problem_words, true));
    grid.appendChild(buildEvaluationListBlock(t('eval_common_errors'), evaluation.common_errors));
    grid.appendChild(buildEvaluationListBlock(t('eval_corrections'), evaluation.corrected_phrases));
    grid.appendChild(buildEvaluationListBlock(t('eval_recommendations'), evaluation.recommendations));
    evaluationPanelEl.appendChild(grid);

    const actions = document.createElement('div');
    actions.className = 'evaluation-actions';

    const backBtn = document.createElement('button');
    backBtn.type = 'button';
    backBtn.className = 'finish-btn';
    backBtn.textContent = t('back_conversation');
    backBtn.addEventListener('click', showConversationView);

    
    const pdfBtn = document.createElement('button');
    pdfBtn.type = 'button';
    pdfBtn.className = 'finish-btn';
    pdfBtn.textContent = t('detailed_pdf');
    pdfBtn.addEventListener('click', async () => {
      pdfBtn.disabled = true;
      pdfBtn.textContent = t('generating_pdf');
      try {
        const resp = await fetch('/api/evaluation/pdf', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            evaluation: lastEvaluation,
            language: practiceLanguage,
            turns: conversationHistory.filter(m => m.role === 'user').length,
          }),
        });
        if (!resp.ok) {
          showToast('No se pudo generar el PDF.', true);
          return;
        }
        const blob = await resp.blob();
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = 'fleng_evaluacion_' + practiceLanguage + '.pdf';
        a.click();
        URL.revokeObjectURL(url);
      } catch (err) {
        console.error(err);
        showToast('Error de conexión al generar el PDF.', true);
      } finally {
        pdfBtn.disabled = false;
        pdfBtn.textContent = t('detailed_pdf');
      }
    });

const newBtn = document.createElement('button');
    newBtn.type = 'button';
    newBtn.className = 'send-btn';
    newBtn.textContent = t('new_conversation');
    newBtn.addEventListener('click', () => {
      resetConversation();
      showConversationView();
    });

    actions.appendChild(pdfBtn);
    actions.appendChild(backBtn);
    actions.appendChild(newBtn);
    evaluationPanelEl.appendChild(actions);
  }

  function showConversationView() {
    evaluationPanelEl.classList.add('hidden');
    evaluationPanelEl.innerHTML = '';
    chatMessagesEl.classList.remove('hidden');
    chatInputRowEl.classList.remove('hidden');
    chatMessagesEl.scrollTop = chatMessagesEl.scrollHeight;
  }

  function buildEvaluationTextBlock(title, text) {
    const block = document.createElement('div');
    block.className = 'evaluation-block';
    const h3 = document.createElement('h3');
    h3.textContent = title;
    const p = document.createElement('p');
    p.textContent = text || 'Sin datos suficientes.';
    block.appendChild(h3);
    block.appendChild(p);
    return block;
  }

  function buildEvaluationListBlock(title, items, asChips) {
    const block = document.createElement('div');
    block.className = 'evaluation-block';
    const h3 = document.createElement('h3');
    h3.textContent = title;
    block.appendChild(h3);

    const list = Array.isArray(items) ? items.filter(Boolean) : [];
    if (list.length === 0) {
      const p = document.createElement('p');
      p.textContent = 'Sin datos suficientes.';
      block.appendChild(p);
      return block;
    }

    if (asChips) {
      const wrap = document.createElement('div');
      wrap.className = 'chip-list';
      list.forEach((item) => {
        const chip = document.createElement('span');
        chip.className = 'chip';
        chip.textContent = item;
        wrap.appendChild(chip);
      });
      block.appendChild(wrap);
    } else {
      const ul = document.createElement('ul');
      list.forEach((item) => {
        const li = document.createElement('li');
        li.textContent = item;
        ul.appendChild(li);
      });
      block.appendChild(ul);
    }
    return block;
  }

  /* --------------------------------- Inicio --------------------------------- */

  /* ============================================================
     MODAL: COMO FUNCIONAN LOS BOTONES DE IDIOMA

     Aparece la primera vez que se abre la app. El boton "?" de la barra
     lo reabre siempre que se quiera.
     ============================================================ */

  const HELP_SEEN_KEY = 'fleng_tutorial_idioma_visto';
  const langHelpModal = document.getElementById('lang-help-modal');
  const helpBtn = document.getElementById('help-btn');
  const helpOkBtn = document.getElementById('lang-help-ok');

  function abrirModalIdioma() {
    applyLocale();   // el modal se muestra en el idioma de la interfaz
    langHelpModal.classList.remove('hidden');
  }

  function cerrarModalIdioma() {
    langHelpModal.classList.add('hidden');
    try { localStorage.setItem(HELP_SEEN_KEY, '1'); } catch (err) { /* nada */ }
  }

  function setupLanguageHelp() {
    helpBtn.addEventListener('click', abrirModalIdioma);
    helpOkBtn.addEventListener('click', cerrarModalIdioma);
    // Cerrar tocando fuera de la tarjeta.
    langHelpModal.addEventListener('click', (e) => {
      if (e.target === langHelpModal) cerrarModalIdioma();
    });

    // La primera vez que se abre la app, mostrarlo solo.
    let visto = false;
    try { visto = localStorage.getItem(HELP_SEEN_KEY) === '1'; } catch (err) { /* nada */ }
    if (!visto) abrirModalIdioma();
  }

  renderTranslationHistory();
  renderDictationHistory();
  updateFinishButtonState();
  renderStats();
  renderTemas();
  loadTutorial();
  setupLanguageHelp();
  checkStatus();
});
