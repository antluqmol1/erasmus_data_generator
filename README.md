# Generador de Datos Sintéticos Erasmus para Process Mining

Este proyecto genera un conjunto de datos sintéticos que simulan el proceso de solicitud y gestión de plazas Erasmus en la Universidad de Sevilla, basándose en el flujo y plazos reales observados. Los datos están diseñados para ser utilizados con herramientas de Process Mining como Celonis, permitiendo analizar y visualizar los flujos del proceso.

El sistema utiliza opcionalmente un Modelo de Lenguaje Grande (LLM) a través de la API de OpenAI (GPT-4) para generar datos más realistas y variados (nombres de universidades, motivos de alegación, patrones de proceso).

## Componentes Principales

-   `generate_data.py`: Script principal que orquesta la generación de todos los archivos de datos CSV. Contiene la lógica de simulación detallada.
-   `llm_helpers.py`: Contiene funciones auxiliares para interactuar con la API de OpenAI y generar datos específicos (universidades, motivos de alegación, secuencias de actividades). Incluye funciones de *fallback* que generan datos genéricos si la API no está disponible o si se desactiva su uso.
-   `requirements.txt`: Lista las dependencias de Python necesarias.
-   `.env` (No incluido, debe crearse manualmente): Archivo para almacenar la clave de API de OpenAI (`OPENAI_API_KEY`).
-   `data/` (Directorio): Carpeta donde se guardarán los archivos CSV generados.

## Funcionamiento Detallado

1.  **Configuración (`generate_data.py`)**: Se definen constantes como el número de estudiantes (`NUM_ESTUDIANTES`), número de destinos (`NUM_DESTINOS`), el porcentaje de estudiantes con alegaciones (`PCT_ESTUDIANTES_CON_ALEGACIONES` ~17.5%), si se deben usar las funciones del LLM (`USE_LLM = True/False`), y los plazos clave (`PLAZOS`) para ciertas actividades basados en convocatorias reales.
2.  **Generación de Datos Maestros**:
    *   `generar_destinos()`: Crea `Destinos.csv`. Utiliza `llm_helpers.get_universities()` o datos genéricos. Añade número de plazas, un estado de cancelación aleatorio (~5% de destinos) y una columna `RequiereIdioma` (booleana, ~65% `True`). **Importante**: Si un destino se marca como cancelado, su `FechaCancelación` se establece antes de la publicación del listado provisional, simulando cancelaciones tempranas.
    *   `generar_estudiantes()`: Crea `Estudiantes.csv`. Genera datos para cada estudiante (ID, grado ponderado, sexo, nota expediente, fecha de solicitud realista dentro del plazo, destinos solicitados/asignados, estado final ponderado). La asignación final (`DestinoAsignado`) tiene en cuenta la probabilidad de obtener el destino solicitado versus otras preferencias.
    *   `generar_actividades()`: Crea `Actividades.csv`. Define la lista detallada y actualizada (IDs 1-33, renumerados) de las posibles actividades del proceso Erasmus.
3.  **Generación de Datos Transaccionales y Event Log**:
    *   `generar_alegaciones()`: Crea `Alegaciones.csv`. Selecciona un porcentaje de estudiantes (~17.5%) para generarles una alegación. Usa `llm_helpers.get_alegation_motives()` o motivos predefinidos. Las fechas de alegación y resolución se generan respetando los plazos definidos en `PLAZOS`. Devuelve un conjunto con los IDs de estudiantes con alegaciones.
    *   `generar_historico_adjudicaciones()`: Crea `HistoricoAdjudicaciones.csv`. Simula las rondas de adjudicación (1ª, 2ª, 3ª, Final). Para cada estudiante y cada ronda en la que podría aparecer, registra su estado potencial (`Titular`, `Suplente`, `No Asignado`) y el destino asociado en la fecha de publicación de esa lista.
    *   `generar_eventlog()`: Crea `EventLog.csv`, el archivo clave.
        *   **Cancelaciones Tempranas**: Primero comprueba si el destino solicitado por el estudiante fue cancelado tempranamente. Si es así, asigna una ruta corta específica que incluye el evento de cancelación (ID 33) con el timestamp correspondiente a la fecha de cancelación, considerando si requería idioma o no.
        *   **Selección de Ruta**: Si no hay cancelación temprana, selecciona una secuencia de IDs de actividad (`ruta`) para el estudiante.
            *   Define `rutas_base` para cada `EstadoFinal` posible, incluyendo variantes con y sin pasos de idioma, y reintentos de idioma (ej: 1->2->1->3).
            *   Genera **variaciones** de estas rutas base para simular la **opcionalidad** de las alegaciones (IDs 7, 8, 9, insertadas después de la publicación provisional, ID 6).
            *   **Filtra** las variaciones generadas:
                *   Primero por **requerimiento de idioma**: si el destino lo requiere, solo se consideran rutas que incluyan los pasos 1 y 3 (o 1 y 2 para exclusión/reintento); si no, solo rutas que omitan los pasos 1, 2 y 3. La inscripción (ID 4) siempre va después de la aceptación de idioma (ID 3) si esta ocurre.
                *   Segundo por **alegaciones**: si el estudiante *tiene* una alegación (según `estudiantes_con_alegaciones_ids`), solo elige rutas (ya filtradas por idioma) que incluyan los pasos 7, 8, 9; si *no* tiene alegación, solo elige rutas que *no* los incluyan.
            *   Añade rutas con posible cancelación administrativa (ID 33) como variación.
            *   Si `USE_LLM` es `True`, llama a `llm_helpers.get_process_patterns()` (con un prompt actualizado que instruye sobre la opcionalidad y las nuevas reglas de idioma) para obtener más patrones y los mezcla con los generados programáticamente.
        *   **Generación de Eventos y Timestamps**: Itera por la `ruta` seleccionada.
            *   Para actividades de **publicación** (IDs 6, 10, 14, 18, 22), asigna un **timestamp fijo** a las 00:01:00 del día correspondiente, asegurando que sea posterior al evento previoa.
            *   Para actividades con plazo definido en `PLAZOS` (inscripción, alegación, respuestas a adjudicación), genera un timestamp **dentro** del plazo usando una distribución bimodal (más probabilidad al inicio y final del plazo) y horas realistas.
            *   Para actividades sin plazo (ej. pasos intermedios de LA), añade un delta de tiempo aleatorio corto.
            *   Asigna el actor y un detalle descriptivo (enriquecido para respuestas y cancelaciones).
4.  **Guardado**: Todos los DataFrames generados se guardan como archivos CSV en la carpeta `data/`.

## Uso

1.  **Prerrequisitos**: Python 3.x, `pip`.
2.  **Instalación**: Clona, crea entorno virtual (recomendado), `pip install -r requirements.txt`.
3.  **Configuración API OpenAI (Opcional)**: Si `USE_LLM = True`, crea `.env` con `OPENAI_API_KEY='tu_clave'`. Si no, pon `USE_LLM = False`.
4.  **Revisar Plazos (Opcional)**: Verifica/ajusta las fechas en el diccionario `PLAZOS` en `generate_data.py` si necesitas simular una convocatoria diferente.
5.  **Ejecución**: `python generate_data.py`.
6.  **Salida**: Los siguientes archivos CSV se generarán en la carpeta `data/`:
    *   `Actividades.csv`: Diccionario de actividades (IDs 1-33).
    *   `Alegaciones.csv`: Detalles de las alegaciones generadas.
    *   `Destinos.csv`: Información de los destinos, incluyendo `RequiereIdioma` y cancelaciones.
    *   `Estudiantes.csv`: Datos de los estudiantes (solicitud, asignación final, etc.).
    *   `EventLog.csv`: El log de eventos detallado con timestamps realistas, listo para Process Mining.
    *   `HistoricoAdjudicaciones.csv`: Simulación del estado (Titular/Suplente) y destino del estudiante en cada ronda de adjudicación.

Estos archivos CSV contienen los datos sintéticos listos para ser cargados y analizados en herramientas de Process Mining. 