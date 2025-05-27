# Generador de Datos Sintéticos Erasmus para Process Mining

Este proyecto genera un conjunto de datos sintéticos que simulan el proceso completo de solicitud y gestión de plazas Erasmus en la Universidad de Sevilla. Los datos están diseñados específicamente para análisis de Process Mining con herramientas como Celonis, garantizando coherencia total entre todas las fuentes de datos.

## 🎯 Características Principales

- **✅ Coherencia Total**: EventLog como fuente de verdad única con sincronización automática
- **🎯 Gestión Realista de Plazas**: Control estricto del número de plazas por destino y ronda
- **🌍 Diversidad Geográfica**: Universidades de todos los países de la UE (excepto España)
- **🔄 Learning Agreement Avanzado**: Bucles de reintento realistas (90% resueltos, 10% rechazados definitivamente)
- **📊 Escalabilidad**: 3,231 estudiantes, 400 destinos, ~2,000 plazas disponibles
- **🤖 Integración LLM**: Generación inteligente de universidades, motivos de alegación y patrones de proceso
- **🔍 Validación Automática**: Sistema completo de verificación de coherencia

## 📈 Resultados del Sistema (Última Ejecución)

### 📊 **Estadísticas Generales**

- **Estudiantes Totales**: 3,231
- **Destinos Disponibles**: 400 (380 activos, 20 cancelados)
- **Plazas Totales**: 2,007
- **Estudiantes Aceptados**: 1,999 (99.6% ocupación)
- **Tasa de Participación**: 61.9% (1,999/3,231)

### 🎯 **Distribución de Estados Finales**

- **Aceptados**: 1,999 estudiantes (61.9%)
- **No Asignados**: 808 estudiantes (25.0%)
- **Renuncias**: 259 estudiantes (8.0%)
- **Excluidos**: 165 estudiantes (5.1%)

### 🌍 **Diversidad Geográfica Lograda**

- **26 países de la UE** representados (todos excepto España)
- **Distribución equilibrada** con énfasis en destinos principales
- **Universidades realistas** generadas por LLM (GPT-4)

### ✅ **Coherencia del Sistema**

- **100% coherencia** entre estudiantes aceptados y destinos asignados
- **0 inconsistencias** en gestión de plazas
- **Sincronización perfecta** entre EventLog, Histórico y Alegaciones
- **Validación temporal exitosa** (solicitudes vs cancelaciones)

## 🔄 Proceso de Generación

### **Fase 1: Generación Base**

1. **Destinos**: 400 universidades europeas con distribución realista de plazas (1-10 por destino)
2. **Estudiantes**: 3,231 perfiles con expedientes académicos variados
3. **Actividades**: 33 actividades del proceso Erasmus con orden secuencial

### **Fase 2: Simulación de Adjudicación**

1. **Control de Plazas**: Gestión estricta por destino y ronda
2. **Filtros de Elegibilidad**: Requisitos de idioma y académicos
3. **Reasignación Inteligente**: 15% de estudiantes aceptan destinos alternativos
4. **Gestión de Renuncias**: Liberación automática de plazas

### **Fase 3: Learning Agreement Avanzado**

1. **Bucles de Reintento**: 2-4 intentos por estudiante
2. **Doble Validación**: Responsable Destino + Subdirectora RRII
3. **Probabilidades Realistas**: 90% resueltos, 10% rechazados definitivamente
4. **Patrones Complejos**: Hasta 15 actividades por bucle de LA

### **Fase 4: Coordinación y Validación**

1. **EventLog como Fuente de Verdad**: Todas las fechas se sincronizan desde aquí
2. **Actualización de Estados**: Basada en gestión real de plazas
3. **Validación Automática**: 7 tipos de verificaciones de coherencia
4. **Reportes Detallados**: Gestión de plazas y inconsistencias

## 📁 Archivos Generados

| Archivo                       | Registros | Descripción                                       |
| ----------------------------- | --------- | ------------------------------------------------- |
| `Destinos.csv`                | 400       | Universidades europeas con plazas y requisitos    |
| `Estudiantes.csv`             | 3,231     | Perfiles académicos y estados finales             |
| `Actividades.csv`             | 33        | Catálogo de actividades del proceso               |
| `EventLog.csv`                | ~45,000   | Eventos temporales del proceso (fuente de verdad) |
| `Alegaciones.csv`             | ~565      | Alegaciones con motivos generados por LLM         |
| `HistoricoAdjudicaciones.csv` | ~8,000    | Asignaciones por ronda sincronizadas              |
| `ReporteGestionPlazas.csv`    | 1,600     | Estadísticas detalladas por destino/ronda         |

## 🔍 Validaciones Implementadas

### ✅ **Coherencia Estructural**

- Estados finales vs destinos asignados
- Estudiantes aceptados = Estudiantes con destino
- Asignaciones reales = Estados en CSV

### ✅ **Gestión de Plazas**

- Respeto estricto de límites por destino
- Control de sobreasignaciones automático
- Liberación de plazas por renuncias

### ✅ **Coherencia Temporal**

- Solicitudes posteriores a cancelaciones
- Sincronización EventLog ↔ Histórico ↔ Alegaciones
- Secuencias lógicas de actividades

### ✅ **Requisitos Académicos**

- Filtros de idioma en adjudicaciones
- Validación de expedientes académicos
- Compatibilidad destino-estudiante

## 🚀 Mejoras Implementadas

### **Incoherencias Corregidas**

- ✅ Destinos cancelados vs solicitudes temporales
- ✅ Renuncias manteniendo destino asignado
- ✅ Sobreasignación de plazas por destino
- ✅ Reasignación irealista (85% → 15%)
- ✅ Requisitos de idioma no validados
- ✅ Fechas desincronizadas entre fuentes

### **Código Optimizado**

- ✅ ~150 líneas de código redundante eliminadas
- ✅ Constantes globales organizadas
- ✅ Funciones duplicadas consolidadas
- ✅ Lógica de timestamps simplificada
- ✅ Validaciones mejoradas con reportes específicos

### **Funcionalidades Avanzadas**

- ✅ Learning Agreement con bucles de reintento realistas
- ✅ Gestión inteligente de plazas por ronda
- ✅ Reasignación geográficamente compatible
- ✅ Diversidad completa de países UE
- ✅ Integración LLM para datos realistas

## 📊 Casos de Uso para Process Mining

### **Análisis de Rendimiento**

- Tiempo promedio de procesamiento por estudiante
- Cuellos de botella en Learning Agreement
- Eficiencia de rondas de adjudicación

### **Análisis de Conformidad**

- Cumplimiento de plazos por actividad
- Secuencias de proceso estándar vs variantes
- Detección de patrones anómalos

### **Análisis de Recursos**

- Carga de trabajo por actor (Responsables, Subdirectora)
- Distribución temporal de actividades
- Optimización de capacidades

### **Análisis Predictivo**

- Predicción de renuncias por perfil
- Estimación de demanda por destino
- Optimización de oferta de plazas

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   LLM (GPT-4)   │    │  Gestión Plazas  │    │   Validación    │
│                 │    │                  │    │   Automática    │
│ • Universidades │    │ • Control límites│    │ • 7 tipos checks│
│ • Motivos       │ ──▶│ • Reasignaciones │ ──▶│ • Reportes      │
│ • Patrones      │    │ • Renuncias      │    │ • Coherencia    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────────────────────────────────────────────────────┐
│                    EventLog (Fuente de Verdad)                  │
│                                                                 │
│ • 45,000+ eventos temporales                                    │
│ • Sincronización automática de fechas                          │
│ • Bucles complejos de Learning Agreement                       │
└─────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────┐
│                     Archivos CSV Finales                       │
│                                                                 │
│ Destinos │ Estudiantes │ Actividades │ Alegaciones │ Histórico  │
└─────────────────────────────────────────────────────────────────┘
```

## ⚙️ Instalación y Uso

### **Requisitos**

```bash
pip install pandas numpy python-dotenv openai
```

### **Configuración**

1. Crear archivo `.env` con tu API key de OpenAI:

```
OPENAI_API_KEY=tu_api_key_aqui
```

2. Ejecutar el generador:

```bash
python generate_data.py
```

### **Personalización**

- `NUM_ESTUDIANTES`: Número de estudiantes (actual: 3,231)
- `NUM_DESTINOS`: Número de destinos (actual: 400)
- `PCT_ESTUDIANTES_CON_ALEGACIONES`: Porcentaje con alegaciones (actual: 17.5%)
- `USE_LLM`: Activar/desactivar integración con LLM

## 📈 Resultados de Validación

```
✅ Generación de CSVs Erasmus COMPLETADA con coordinación mejorada.
📈 Resumen: 0 inconsistencias detectadas y reportadas.

🔍 Verificando coherencia final entre plazas y estudiantes...
   📊 PLAZAS DISPONIBLES:
      • Total plazas: 2,007
      • Destinos activos: 380
      • Destinos cancelados: 20

   📊 ESTUDIANTES FINALES:
      • Total estudiantes: 3,231
      • Aceptados: 1,999
      • Con destino asignado: 1,999
      • Renuncias: 259
      • No asignados: 808
      • Excluidos: 165

   📊 COHERENCIA:
      • Tasa de ocupación: 99.6% (1,999/2,007)
      • Tasa de participación: 61.9% (1,999/3,231)
      • Asignaciones reales (gestión): 1,999

   📋 VERIFICACIONES:
      ✅ Estudiantes aceptados = Con destino asignado
      ✅ Estudiantes aceptados = Asignaciones reales
      ✅ Estudiantes aceptados ≤ Plazas disponibles
      ✅ Tasa de ocupación realista (99.6%)
```

## 🎯 Estado del Proyecto

**✅ COMPLETADO** - El sistema genera datos sintéticos completamente coherentes y realistas para análisis de Process Mining del proceso Erasmus, con:

- **Coherencia total** entre todas las fuentes de datos
- **Gestión realista** de plazas con control estricto
- **Learning Agreement avanzado** con bucles de reintento
- **Diversidad geográfica** completa (26 países UE)
- **Validación automática** sin inconsistencias detectadas
- **Escalabilidad** demostrada (3,231 estudiantes, 400 destinos)

El generador está listo para uso en producción y análisis de Process Mining con herramientas como Celonis.
