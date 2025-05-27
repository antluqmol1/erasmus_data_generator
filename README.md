# Generador de Datos Sintéticos Erasmus para Process Mining

Este proyecto genera un conjunto de datos sintéticos que simulan el proceso de solicitud y gestión de plazas Erasmus en la Universidad de Sevilla, basándose en el flujo y plazos reales observados. Los datos están diseñados para ser utilizados con herramientas de Process Mining como Celonis, permitiendo analizar y visualizar los flujos del proceso.

El sistema utiliza opcionalmente un Modelo de Lenguaje Grande (LLM) a través de la API de OpenAI (GPT-4) para generar datos más realistas y variados (nombres de universidades, motivos de alegación, patrones de proceso).

## 🎯 Características Principales

- **Coordinación Total**: EventLog como fuente de verdad única
- **Gestión Realista de Plazas**: Control de plazas disponibles por destino y ronda
- **Sincronización Automática**: Fechas coherentes entre todas las fuentes
- **Validación Integral**: Detección automática de inconsistencias
- **Datos Realistas**: Uso opcional de LLM para mayor variabilidad

## 📁 Componentes del Sistema

- `generate_data.py`: Script principal con lógica de coordinación y simulación
- `llm_helpers.py`: Funciones para interactuar con OpenAI GPT-4 (con fallbacks)
- `requirements.txt`: Dependencias de Python necesarias
- `.env` (crear manualmente): Clave de API de OpenAI (`OPENAI_API_KEY`)
- `data/`: Directorio donde se guardan los CSV generados

## 🔄 Flujo de Generación Coordinado

### 1. **Datos Maestros**

- **Destinos**: Universidades europeas (priorizando Italia, Francia, Polonia, Alemania) con plazas limitadas, cancelaciones (~5%) y requisitos de idioma (~65%)
- **Estudiantes**: 2107 estudiantes con grados ponderados, expedientes realistas y destinos solicitados
- **Actividades**: 33 actividades del proceso Erasmus (IDs renumerados 1-33)

### 2. **Simulación de Adjudicación con Plazas**

- **Control de Plazas**: Gestión realista del número limitado de plazas por destino
- **Rondas de Adjudicación**: 1ª, 2ª, 3ª y Final con promoción de suplentes
- **Estados por Ronda**: Titular, Suplente, con seguimiento de renuncias
- **Liberación de Plazas**: Las renuncias liberan plazas para siguientes rondas

### 3. **EventLog como Fuente de Verdad**

- **Rutas Inteligentes**: Selección basada en estado final, requisitos de idioma y alegaciones
- **Timestamps Realistas**: Fechas fijas para publicaciones, plazos para respuestas
- **Cancelaciones Tempranas**: Gestión de destinos cancelados antes de adjudicaciones
- **Patrones LLM**: Integración opcional de patrones generados por GPT-4

### 4. **Extracción y Sincronización**

- **Histórico Coherente**: Extraído directamente desde eventos de publicación del EventLog
- **Estados Actualizados**: Calculados desde la gestión real de plazas
- **Fechas Sincronizadas**: Alineación automática entre EventLog, Histórico y Alegaciones
- **Validación Automática**: Detección y reporte de inconsistencias

## 📊 Archivos CSV Generados

| Archivo                       | Descripción                                          | Registros Aprox. |
| ----------------------------- | ---------------------------------------------------- | ---------------- |
| `Destinos.csv`                | Universidades con plazas, cancelaciones y requisitos | 372              |
| `Estudiantes.csv`             | Datos académicos y estados finales coordinados       | 2,107            |
| `Actividades.csv`             | Diccionario de actividades del proceso               | 33               |
| `EventLog.csv`                | Log de eventos con timestamps realistas              | ~35,000          |
| `Alegaciones.csv`             | Alegaciones con fechas sincronizadas                 | ~370             |
| `HistoricoAdjudicaciones.csv` | Estados por ronda extraídos del EventLog             | ~8,000           |
| `ReporteGestionPlazas.csv`    | Análisis detallado de ocupación por destino          | ~1,500           |

## 🚀 Uso

### Instalación

```bash
git clone [repositorio]
cd erasmus_data_generator
pip install -r requirements.txt
```

### Configuración (Opcional)

```bash
# Para usar LLM (recomendado para mayor realismo)
echo "OPENAI_API_KEY='tu_clave_aqui'" > .env
```

### Ejecución

```bash
python generate_data.py
```

### Configuración Avanzada

En `generate_data.py` puedes ajustar:

- `NUM_ESTUDIANTES`: Número de estudiantes (default: 2107)
- `NUM_DESTINOS`: Número de destinos (default: 372)
- `PCT_ESTUDIANTES_CON_ALEGACIONES`: Porcentaje con alegaciones (default: 17.5%)
- `USE_LLM`: Usar OpenAI GPT-4 (default: True)
- `PLAZOS`: Fechas específicas de la convocatoria

## 🔍 Validación y Calidad

El sistema incluye validación automática que verifica:

- ✅ Coherencia entre estados finales y destinos asignados
- ✅ Sincronización de fechas entre fuentes
- ✅ Consistencia de adjudicaciones con plazas disponibles
- ✅ Correspondencia entre EventLog e Histórico
- ✅ Lógica de cancelaciones y renuncias

Si se detectan inconsistencias, se genera automáticamente `reporte_inconsistencias.txt`.

## 📈 Casos de Uso para Process Mining

Los datos generados permiten analizar:

- **Flujos de Proceso**: Rutas más comunes, cuellos de botella, variaciones
- **Tiempos de Respuesta**: Análisis de plazos y cumplimiento
- **Gestión de Plazas**: Eficiencia en adjudicaciones, tasas de ocupación
- **Alegaciones**: Patrones, motivos frecuentes, resoluciones
- **Cancelaciones**: Impacto en el proceso, gestión de incidencias

## 🛠️ Arquitectura Técnica

- **Coordinación**: EventLog como única fuente de verdad
- **Gestión de Estado**: Estados calculados desde adjudicaciones reales
- **Sincronización**: Fechas extraídas y alineadas automáticamente
- **Validación**: Verificación cruzada entre todas las fuentes
- **Escalabilidad**: Diseño modular para fácil extensión

Los datos generados están listos para importar directamente en Celonis u otras herramientas de Process Mining.
