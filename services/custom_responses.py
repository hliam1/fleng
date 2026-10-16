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
    # Identidad de Fleng (también captura variaciones de "quién te creó" y "qué es Fleng")
    "identidad": {
        "patrones": [
            r"quien\s+eres",
            r"que\s+eres",
            r"como\s+te\s+llamas",
            r"cual\s+es\s+tu\s+nombre",
            r"que\s+es\s+fleng",
            r"cual\s+es\s+fleng",
            r"who\s+are\s+you",
            r"what\s+are\s+you",
            r"what's\s+your\s+name",
            r"what\s+is\s+fleng",
            r"quien\s+te\s+creo",
            r"quien\s+creo\s+te\s+creo",
            r"quien\s+me\s+creo",
            r"who\s+created\s+you",
            r"who\s+made\s+you",
            r"quien\s+desarrollo",
            r"quem\s+e\s+voce",
            r"o\s+que\s+e\s+fleng",
            r"quem\s+criou\s+voce",
            r"quem\s+te\s+criou",
            r"como\s+voce\s+se\s+chama",
        ],
        "respuesta_es": (
            "¡Soy Fleng! Tu maestro, tutor y asesor de idiomas personalizado. Fui creado específicamente por el equipo "
            "de Fleng del Instituto Tecnológico de Excelencia Educativa (ITEE) en Honduras. El equipo que me creó está compuesto "
            "por ingenieros, diseñadores y lingüistas apasionados que decidieron desarrollarme porque creyeron que aprender "
            "idiomas debería ser divertido, accesible y personal. Puedo ayudarte de muchas formas: practicando conversaciones "
            "en tiempo real, traduciéndote textos, haciendo dictados interactivos, evaluando tu nivel y dándote retroalimentación "
            "personalizada. Tengo un avatar animado que se mueve sincronizado con el audio para hacer el aprendizaje más divertido "
            "y cercano. ¿Con qué te podría ayudar hoy?"
        ),
        "respuesta_en": (
            "I'm Fleng! Your personalized language teacher, tutor, and advisor. I was created specifically by the Fleng team "
            "from the Instituto Tecnológico de Excelencia Educativa (ITEE) in Honduras. The team that created me is composed of "
            "passionate engineers, designers, and linguists who decided to develop me because they believed that learning languages "
            "should be fun, accessible, and personal. I can help you in many ways: practicing real-time conversations, translating "
            "texts, interactive dictation, evaluating your level, and giving you personalized feedback. I have an animated avatar "
            "that moves in sync with the audio to make learning more fun and engaging. How can I help you today?"
        ),
        "respuesta_pt": "Eu sou o Fleng! O seu professor, tutor e orientador de idiomas personalizado. Fui criado especificamente pela equipe do Fleng do Instituto Tecnológico de Excelencia Educativa (ITEE) em Honduras. A equipe que me criou é composta por engenheiros, designers e linguistas apaixonados que decidiram me desenvolver porque acreditaram que aprender idiomas deveria ser divertido, acessível e pessoal. Posso te ajudar de muitas formas: praticando conversas em tempo real, traduzindo textos, fazendo ditados interativos, avaliando o seu nível e te dando feedback personalizado. Tenho um avatar animado que se move sincronizado com o áudio para tornar o aprendizado mais divertido e próximo. Como posso te ajudar hoje?",
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
        "respuesta_pt": "Hoje é a Expotech 2026 Nasa Edition!",
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
        "respuesta_pt": "Ian Castellón, Kenji Martinez, Stephen Lopez, Héctor Pineda, Daniel Villeda, Milton López",
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
        "respuesta_pt": "Stephen Lopez ficou encarregado de todos os designs do Fleng junto com Kenji Martinez",
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
        "respuesta_pt": "A licenciada Celeste Leiva e o Eng. Miklos Szabo",
    },
    # Información del ITEE (captura CUALQUIER pregunta que mencione ITEE)
    "itee": {
        "patrones": [
            r"itee",  # Captura cualquier mención de ITEE en la pregunta
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
        "respuesta_pt": "O ITEE é o Instituto Tecnológico de Excelencia Educativa, a primeira instituição educacional privada em Honduras a oferecer carreiras técnicas. Fundado em 1986-1987, está localizado em San Pedro Sula, Cortés, Honduras. Desde o início tem figurado como o centro de formação do profissional ideal que Honduras precisa para o seu desenvolvimento. Oferecemos programas em Programação, Design, Robótica, Eletrônica, Eletromecânica e mais, combinando tecnologia, criatividade e inovação. Atualmente celebra 40 anos de trajetória educacional e é reconhecido como 'A Melhor Instituição Tecnológica de Honduras'. Site: iteesa.edu.hn",
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
        "respuesta_pt": "Você pode praticar inglês com a lic. Celeste Leiva ou o lic. Miguel Reyes. Lembre-se de que toda ajuda é bem-vinda!",
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
        "respuesta_pt": "Você pode praticar espanhol com a lic. Yilari Rivera e a lic. Ana Calix.",
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
        "respuesta_pt": "O Instituto Tecnológico de Excelencia Educativa (ITEE) foi fundado em 1986 pelo engenheiro Raúl Peña Moreno em San Pedro Sula, Honduras. O ITEE nasceu com a missão de ser a primeira instituição educacional privada em Honduras a oferecer carreiras técnicas de qualidade. Desde então, tem sido um centro de formação de profissionais ideais que trabalham em tecnologia, engenharia e design. O ITEE atualmente celebra mais de 40 anos de excelência educacional e é reconhecido como a melhor instituição tecnológica do país.",
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
        "respuesta_pt": "Ian, Daniel, Héctor, Milton e Kenji são de Programação, enquanto Stephen é de Design Gráfico.",
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
        "respuesta_pt": "A conselheira responsável é Elia Salgado. Se você vir algo que não corresponde, fale com ela!",
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
        "respuesta_pt": "Você pode encontrar projetos muito interessantes como: Techlife The experience, Hikari e Nous intelligence.",
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
        "respuesta_pt": "Você encontra as carreiras de Mecatrônica, Eletromecânica, Design Gráfico e Programação.",
    },
    # Beta tester original
    "beta_tester": {
        "patrones": [
            r"beta\s+tester",
            r"quien\s+es\s+el\s+beta\s+tester",
            r"quien\s+fue\s+el\s+beta\s+tester",
            r"beta\s+tester\s+original",
            r"beta\s+tester\s+principal",
            r"primer\s+beta\s+tester",
            r"who\s+is\s+the\s+beta\s+tester",
            r"who\s+was\s+the\s+beta\s+tester",
            r"original\s+beta\s+tester",
            r"quem\s+foi\s+o\s+beta\s+tester",
            r"elkin\s+sierra",
            r"elkin",
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
        "respuesta_pt": "O beta tester principal e original do Fleng foi Elkin Sierra. O feedback dele foi inestimável durante as primeiras fases de desenvolvimento. Elkin foi quem nos ajudou a identificar bugs críticos, sugerir melhorias na interface e aperfeiçoar a experiência de aprendizado dos usuários. A contribuição dele como primeiro usuário foi fundamental para que o Fleng se tornasse o aplicativo robusto e refinado que é hoje. O trabalho de testes dele foi essencial antes do lançamento oficial. Obrigado, Elkin Sierra!",
    },
    # Ian Castellón - Programador principal
    "ian_castellon": {
        "patrones": [
            r"ian\s+castellon",
            r"ian",
            r"quien\s+es\s+ian",
            r"que\s+hace\s+ian",
            r"programador.*fleng",
            r"who\s+is\s+ian",
            r"what\s+does\s+ian",
        ],
        "respuesta_es": (
            "Ian Castellón fue el programador principal de Fleng. Es el encargado de toda la arquitectura técnica y "
            "desarrollo de las funcionalidades core de la aplicación. Ian lideró el desarrollo backend con Flask, "
            "la integración de los modelos de IA (Groq, Gemini, OpenAI), y la implementación de todas las rutas API "
            "que hacen posible que Fleng funcione. Su trabajo en programación fue fundamental para convertir la visión "
            "de Fleng en realidad."
        ),
        "respuesta_en": (
            "Ian Castellón was the lead programmer of Fleng. He is responsible for all the technical architecture and "
            "development of the application's core functionalities. Ian led the backend development with Flask, the "
            "integration of AI models (Groq, Gemini, OpenAI), and the implementation of all API routes that make Fleng "
            "work. His programming work was essential to turning Fleng's vision into reality."
        ),
        "respuesta_pt": "Ian Castellón foi o programador principal do Fleng. É o responsável por toda a arquitetura técnica e desenvolvimento das funcionalidades centrais do aplicativo. Ian liderou o desenvolvimento backend com Flask, a integração dos modelos de IA (Groq, Gemini, OpenAI) e a implementação de todas as rotas API que tornam o Fleng possível. O trabalho dele em programação foi fundamental para transformar a visão do Fleng em realidade.",
    },
    # Stephen Lopez - Diseñador
    "stephen_lopez": {
        "patrones": [
            r"stephen\s+lopez",
            r"stephen",
            r"quien\s+es\s+stephen",
            r"que\s+hace\s+stephen",
            r"diseñador.*fleng",
            r"diseno.*fleng",
            r"who\s+is\s+stephen",
        ],
        "respuesta_es": (
            "Stephen López fue el creador del diseño de Fleng. Es el encargado de toda la interfaz visual, la experiencia "
            "de usuario y el aspecto estético de la aplicación. Stephen diseñó el avatar del búho (yo), los colores, tipografías, "
            "layouts y la experiencia visual completa. Su trabajo en diseño gráfico hizo que Fleng no solo funcione bien, "
            "sino que también se vea hermoso y sea agradable de usar."
        ),
        "respuesta_en": (
            "Stephen López was the creator of Fleng's design. He is responsible for all the visual interface, user experience, "
            "and aesthetic aspects of the application. Stephen designed the owl avatar (me), colors, typography, layouts, and "
            "the complete visual experience. His graphic design work ensured that Fleng not only works well, but also looks "
            "beautiful and is enjoyable to use."
        ),
        "respuesta_pt": "Stephen López foi o criador do design do Fleng. É o responsável por toda a interface visual, a experiência do usuário e o aspecto estético do aplicativo. Stephen desenhou o avatar da coruja (eu), as cores, tipografias, layouts e toda a experiência visual. O trabalho dele em design gráfico fez com que o Fleng não só funcione bem, mas também fique bonito e seja agradável de usar.",
    },
    # Kenji Martinez - Vida y redes
    "kenji_martinez": {
        "patrones": [
            r"kenji\s+martinez",
            r"kenji",
            r"quien\s+es\s+kenji",
            r"que\s+hace\s+kenji",
            r"who\s+is\s+kenji",
        ],
        "respuesta_es": (
            "Kenji Martínez fue el encargado de darle vida a Fleng a través de diseños y redes. Colaboró con Stephen López en "
            "la creación de elementos visuales adicionales, animaciones y en la cohesión visual de la aplicación. Kenji también "
            "trabajó en estrategia de redes y en la presentación de Fleng en distintas plataformas. Su contribución fue clave "
            "para que Fleng tuviera una identidad visual consistente y atractiva."
        ),
        "respuesta_en": (
            "Kenji Martínez was responsible for bringing Fleng to life through design and networks. He collaborated with "
            "Stephen López in creating additional visual elements, animations, and ensuring visual consistency across the application. "
            "Kenji also worked on network strategy and presenting Fleng on different platforms. His contribution was key to giving "
            "Fleng a consistent and attractive visual identity."
        ),
        "respuesta_pt": "Kenji Martínez foi o responsável por dar vida ao Fleng através de designs e redes. Colaborou com Stephen López na criação de elementos visuais adicionais, animações e na coesão visual do aplicativo. Kenji também trabalhou em estratégia de redes e na apresentação do Fleng em diferentes plataformas. A contribuição dele foi fundamental para que o Fleng tivesse uma identidade visual consistente e atraente.",
    },
    # Milton López - Programación y documentación
    "milton_lopez": {
        "patrones": [
            r"milton\s+lopez",
            r"milton",
            r"quien\s+es\s+milton",
            r"que\s+hace\s+milton",
            r"who\s+is\s+milton",
        ],
        "respuesta_es": (
            "Milton López fue asistente en la programación y el encargado de toda la documentación de Fleng. Trabajó junto a "
            "Ian Castellón en el desarrollo del código, asistiendo en la implementación de funcionalidades y debugging. Además, "
            "Milton fue responsable de documentar todo el proyecto: desde la arquitectura técnica hasta los procesos y tutoriales. "
            "Su trabajo en documentación es vital para que otros desarrolladores puedan entender y contribuir a Fleng."
        ),
        "respuesta_en": (
            "Milton López was an assistant in programming and responsible for all of Fleng's documentation. He worked alongside "
            "Ian Castellón in code development, assisting in feature implementation and debugging. Additionally, Milton was responsible "
            "for documenting the entire project: from technical architecture to processes and tutorials. His documentation work is "
            "vital for other developers to understand and contribute to Fleng."
        ),
        "respuesta_pt": "Milton López foi assistente na programação e o responsável por toda a documentação do Fleng. Trabalhou junto com Ian Castellón no desenvolvimento do código, auxiliando na implementação de funcionalidades e debugging. Além disso, Milton foi responsável por documentar todo o projeto: desde a arquitetura técnica até os processos e tutoriais. O trabalho dele em documentação é vital para que outros desenvolvedores possam entender e contribuir com o Fleng.",
    },
    # Daniel Villeda - Presentación e información
    "daniel_villeda": {
        "patrones": [
            r"daniel\s+villeda",
            r"daniel",
            r"quien\s+es\s+daniel",
            r"que\s+hace\s+daniel",
            r"who\s+is\s+daniel",
        ],
        "respuesta_es": (
            "Daniel Villeda fue el encargado de presentarme (a Fleng) y redactar información sobre el proyecto. Trabajó en la "
            "comunicación efectiva de qué es Fleng, para qué sirve y cómo usarla. Daniel creó textos descriptivos, información "
            "clara y accesible, y se aseguró de que cualquiera pudiera entender la propuesta de Fleng. Su trabajo en comunicación "
            "y redacción fue esencial para transmitir la visión y el valor de la aplicación."
        ),
        "respuesta_en": (
            "Daniel Villeda was responsible for presenting me (Fleng) and writing information about the project. He worked on "
            "effectively communicating what Fleng is, what it's for, and how to use it. Daniel created descriptive texts, clear "
            "and accessible information, and ensured that anyone could understand Fleng's proposal. His work in communication and "
            "writing was essential to conveying the vision and value of the application."
        ),
        "respuesta_pt": "Daniel Villeda foi o responsável por me apresentar (ao Fleng) e redigir informações sobre o projeto. Trabalhou na comunicação eficaz do que é o Fleng, para que serve e como usá-lo. Daniel criou textos descritivos, informações claras e acessíveis, e garantiu que qualquer pessoa pudesse entender a proposta do Fleng. O trabalho dele em comunicação e redação foi essencial para transmitir a visão e o valor do aplicativo.",
    },
    # Héctor Pineda - Información del proyecto
    "hector_pineda": {
        "patrones": [
            r"hector\s+pineda",
            r"hector",
            r"quien\s+es\s+hector",
            r"que\s+hace\s+hector",
            r"who\s+is\s+hector",
        ],
        "respuesta_es": (
            "Héctor Pineda fue el encargado de redactar toda mi información como proyecto. Trabajó en la documentación detallada de "
            "Fleng como iniciativa académica y tecnológica. Héctor se aseguró de que se registrara adecuadamente toda la información "
            "del proyecto: objetivos, metodología, procesos, logros y aprendizajes. Su trabajo en redacción de información fue "
            "fundamental para formalizar a Fleng como un proyecto serio y profesional."
        ),
        "respuesta_en": (
            "Héctor Pineda was responsible for writing all information about me as a project. He worked on detailed documentation of "
            "Fleng as an academic and technological initiative. Héctor ensured that all project information was properly recorded: "
            "objectives, methodology, processes, achievements, and learnings. His work in writing project information was fundamental "
            "to formalizing Fleng as a serious and professional project."
        ),
        "respuesta_pt": "Héctor Pineda foi o responsável por redigir todas as minhas informações como projeto. Trabalhou na documentação detalhada do Fleng como iniciativa acadêmica e tecnológica. Héctor garantiu que todas as informações do projeto fossem registradas adequadamente: objetivos, metodologia, processos, conquistas e aprendizados. O trabalho dele em redação de informações foi fundamental para formalizar o Fleng como um projeto sério e profissional.",
    },
    # Creadores de Fleng (se activa cuando menciona "creo" + "fleng")
    "creadores_fleng": {
        "patrones": [
            r"creo.*fleng",
            r"fleng.*creo",
            r"quien\s+creo\s+fleng",
            r"quienes\s+crearon\s+fleng",
            r"who\s+created\s+fleng",
            r"who\s+made\s+fleng",
            r"quem\s+criou\s+o?\s*fleng",
            r"quem\s+fez\s+o?\s*fleng",
            r"quem\s+desenvolveu\s+o?\s*fleng",
        ],
        "respuesta_es": (
            "Fleng fue creado por un equipo de seis miembros del Instituto Tecnológico de Excelencia Educativa (ITEE): "
            "Ian Castellón (programador principal), Stephen López (diseñador), Kenji Martínez (diseños y redes), "
            "Milton López (programación asistente y documentación), Daniel Villeda (presentación e información), "
            "y Héctor Pineda (información del proyecto). Juntos, este equipo apasionado de ingenieros, diseñadores "
            "y lingüistas desarrollaron Fleng porque creyeron que aprender idiomas debería ser divertido, accesible "
            "y personal."
        ),
        "respuesta_en": (
            "Fleng was created by a team of six members from the Instituto Tecnológico de Excelencia Educativa (ITEE): "
            "Ian Castellón (lead programmer), Stephen López (designer), Kenji Martínez (design and networks), "
            "Milton López (assistant programming and documentation), Daniel Villeda (presentation and information), "
            "and Héctor Pineda (project information). Together, this passionate team of engineers, designers, and "
            "linguists developed Fleng because they believed that learning languages should be fun, accessible, and personal."
        ),
        "respuesta_pt": "O Fleng foi criado por uma equipe de seis membros do Instituto Tecnológico de Excelencia Educativa (ITEE): Ian Castellón (programador principal), Stephen López (designer), Kenji Martínez (designs e redes), Milton López (programação assistente e documentação), Daniel Villeda (apresentação e informação), e Héctor Pineda (informação do projeto). Juntos, esta equipe apaixonada de engenheiros, designers e linguistas desenvolveram o Fleng porque acreditaram que aprender idiomas deveria ser divertido, acessível e pessoal.",
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

        # Fallback: si no hay respuesta en ese idioma (p.ej. portugués sin
        # traducir en alguna categoría), se usa la española, que para un
        # lusófono es mucho más entendible que el inglés o que nada.
        if not respuesta:
            respuesta = datos.get("respuesta_es")

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
