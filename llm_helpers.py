import os
from dotenv import load_dotenv
import random

# Importar la clase OpenAI
from openai import OpenAI

# Cargar variables de entorno
load_dotenv()

# Configurar la API Key es ahora implícito al instanciar el cliente
# openai.api_key = os.getenv("OPENAI_API_KEY") # <-- Ya no se necesita

# Instanciar el cliente OpenAI (lee la key de la variable de entorno)
try:
    client = OpenAI()
except Exception as e:
    print(f"Error al instanciar el cliente OpenAI. Asegúrate de que OPENAI_API_KEY está en tu .env: {e}")
    client = None # Marcar como None si falla la inicialización

# ---- Funciones ----

def get_universities(n=300):
    """
    Llama a GPT para generar nombres de universidades europeas plausibles y su país,
    priorizando países como Italia, Francia, Polonia y Alemania.
    Devuelve una lista de tuplas: [(nombre, pais), ...]
    """
    if not client:
        print("Cliente OpenAI no inicializado. Usando fallback para universidades.")
        return fallback_universities(n)

    prompt = (
        f"Genera una lista de {n} nombres plausibles de universidades europeas y su país. "
        f"Prioriza instituciones de Italia, Francia, Polonia y Alemania, pero incluye otras europeas también. "
        f"Formatea cada entrada como: Nombre Universidad - País. Ejemplo: Sorbonne Université - France\n"
        f"Devuelve SOLO la lista, una entrada por línea."
    )
    try:
        # Usar la nueva sintaxis client.chat.completions.create
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un generador de datos académicos. Devuelves listas en formato 'Nombre - País'."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        # Acceder al contenido de la respuesta con la nueva estructura
        text = response.choices[0].message.content

        universidades_paises = []
        for line in text.strip().split('\n'):
            parts = line.split(' - ')
            if len(parts) == 2:
                nombre = parts[0].strip()
                pais = parts[1].strip()
                universidades_paises.append((nombre, pais))
            else:
                print(f"Advertencia: Línea de universidad mal formateada: {line}")

        if not universidades_paises:
            raise ValueError("El LLM no devolvió universidades válidas.")

        return universidades_paises[:n] # Devuelve lista de tuplas

    except Exception as e:
        print(f"Error al llamar a la API de OpenAI para universidades: {e}")
        print("Generando nombres de universidades y países genéricos.")
        return fallback_universities(n)

def fallback_universities(n):
    """Función helper para el fallback de universidades."""
    paises_fallback = ["Italia", "Alemania", "Francia", "Polonia", "Portugal", "Países Bajos", "Suecia"]
    return [(f"Universidad Genérica {i}", random.choice(paises_fallback)) for i in range(1, n + 1)]

def get_alegation_motives(n=20):
    """
    Llama a GPT para generar motivos realistas y específicos de alegaciones Erasmus.
    """
    if not client:
        print("Cliente OpenAI no inicializado. Usando fallback para motivos de alegación.")
        return fallback_alegation_motives()
        
    prompt = (
        f"Genera una lista de {n} motivos específicos y realistas por los cuales un estudiante de la Universidad de Sevilla podría presentar una alegación relacionada con su solicitud Erasmus. "
        f"Incluye diferentes categorías como: errores administrativos (ej. 'Error en cálculo de nota media', 'Documentación traspapelada'), problemas con destinos (ej. 'Destino cancelado sin alternativa viable', 'Información errónea sobre asignaturas en destino X'), motivos personales justificados (ej. 'Enfermedad sobrevenida documentada', 'Situación familiar grave inesperada'), problemas académicos (ej. 'No reconocimiento de créditos específicos', 'Error en baremación por idioma')."
        f"Evita motivos demasiado genéricos como 'Problemas personales'. "
        f"Formatea la respuesta como una lista simple, un motivo por línea, sin numeración ni guiones iniciales."
    )
    try:
        # Usar la nueva sintaxis
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Eres un experto en gestión de programas de movilidad estudiantil."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7
        )
        # Acceder al contenido
        text = response.choices[0].message.content

        motivos = []
        for m in text.split("\n"):
            if m.strip():
                motivos.append(m.strip("- ").strip())

        if not motivos:
             raise ValueError("El LLM no devolvió motivos válidos.")

        return motivos[:n]

    except Exception as e:
        print(f"Error al llamar a la API de OpenAI para motivos: {e}")
        print("Usando motivos de alegación por defecto.")
        return fallback_alegation_motives()

def fallback_alegation_motives():
    """Función helper para el fallback de motivos de alegación (MEJORADA)."""
    return [
        "Error en cálculo de nota media expediente",
        "No consideración de certificado de idioma B2 presentado",
        "Asignación incorrecta de destino según preferencias",
        "Destino cancelado sin ofrecimiento de alternativa adecuada",
        "Problemas médicos graves sobrevenidos (documentados)",
        "Situación familiar crítica inesperada (justificada)",
        "Discrepancia en información sobre plan de estudios de universidad destino",
        "Error en la baremación de méritos adicionales",
        "Incidencia técnica durante aceptación/reserva de plaza",
        "Falta de actualización de nota media tras revisión",
        "Problema con reconocimiento de créditos de asignatura específica",
        "Retraso injustificado en notificación administrativa",
        "Error en publicación de listado provisional",
        "Conflicto de fechas con prácticas curriculares obligatorias",
        "Denegación de visado por causas ajenas al estudiante",
        "Incompatibilidad académica sobrevenida con destino asignado",
        "Fallo en la plataforma al adjuntar documentación requerida",
        "No inclusión en listado provisional por error administrativo",
        "Reclamación sobre el número de plazas ofertadas para un destino",
        "Solicitud de cambio de destino por causa mayor documentada"
    ]

def get_process_patterns(n=10):
    """
    Llama a GPT para generar patrones (secuencias de IDs de actividad) realistas del proceso Erasmus.
    """
    if not client:
        print("Cliente OpenAI no inicializado. Usando fallback para patrones de proceso.")
        return fallback_process_patterns()
        
    # Obtener descripción de actividades para el prompt (ACTUALIZADA con IDs renumerados)
    actividades_desc = """
    1: Solicitud Convalidación Idioma Recibida
    2: Resolución Convalidación Idioma (Rechazada)
    3: Resolución Convalidación Idioma (Aceptada)
    4: Inscripción Programa Erasmus Registrada
    5: Cálculo Notas Participantes Realizado
    6: Publicación Listado Provisional
    7: Alegación Presentada
    8: Alegación Recibida
    9: Resolución Alegación Emitida
    10: Publicación 1ª Adjudicación
    11: Respuesta Recibida (Aceptación/Reserva 1ª Adj.)
    12: Respuesta Recibida (Renuncia 1ª Adj.)
    13: Actualización Orden Preferencias (Post-1ª Adj.)
    14: Publicación 2ª Adjudicación
    15: Respuesta Recibida (Aceptación/Reserva 2ª Adj.)
    16: Respuesta Recibida (Renuncia 2ª Adj.)
    17: Actualización Orden Preferencias (Post-2ª Adj.)
    18: Publicación 3ª Adjudicación
    19: Respuesta Recibida (Aceptación/Reserva 3ª Adj.)
    20: Respuesta Recibida (Renuncia 3ª Adj.)
    21: Actualización Orden Preferencias (Post-3ª Adj.)
    22: Publicación Listado Definitivo
    23: Envío LA a Responsable Destino
    24: LA Recibido por Responsable
    25: LA Validado por Responsable
    26: LA Rechazado por Responsable
    27: Envío LA a Subdirectora RRII
    28: LA Recibido por Subdirectora
    29: LA Validado por Subdirectora
    30: LA Rechazado por Subdirectora
    31: Formalización Acuerdo SEVIUS
    32: Proceso Erasmus Finalizado
    33: Cancelación Plaza (Admin)
    """

    # Reescribir prompt usando una única f-string multilínea con triple comillas
    prompt = f"""Eres un experto en procesos de movilidad estudiantil Erasmus. 
Basándote en la siguiente lista de posibles actividades y sus IDs (renumerados desde 1):
{actividades_desc}

Genera {n} patrones (secuencias de IDs) realistas que podría seguir un estudiante. 
TEN EN CUENTA LO SIGUIENTE:

- Los pasos de convalidación de idioma (1, 2, 3) son OPCIONALES (si el destino requiere idioma, ~65%).
- SI OCURREN los pasos de idioma, la actividad 4 (Inscripción) DEBE ser POSTERIOR a la 3 (Aceptación Idioma).
- SI OCURRE la actividad 2 (Rechazo Idioma), puede haber un REINTENTO (añadir otra secuencia 1 -> 2 ó 1 -> 3) o el proceso puede terminar ahí (exclusión).
- Los pasos de alegaciones (7, 8, 9) son OPCIONALES (~15-20%). Van DESPUÉS de la publicación provisional (ID 6).
- Incluye variaciones comunes como aceptación/reserva/renuncia en adjudicaciones (1ª: 10-13, 2ª: 14-17, 3ª: 18-21), finalización con LA (23-30) y formalización (31-32), o finales abruptos (exclusión [ej. 1,2 o 1,2,1,2], renuncia [ej. 1,3,4,...,10,12], no asignación [ej. 1,3,4,...,21,22], cancelación admin [ej. ..., 33]).

Asegúrate de que el orden de las actividades en cada patrón sea lógicamente correcto. 
Formatea CADA patrón como una lista de Python de enteros. Ejemplo: [4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32]
Devuelve SOLO las listas, una por línea.
"""

    try:
        # Usar la nueva sintaxis
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Generas listas de Python representando secuencias de IDs de actividad."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6 # Temperatura un poco más baja para seguir el formato
        )
        # Acceder al contenido
        text = response.choices[0].message.content

        # Parsear la respuesta para extraer las listas
        patrones = []
        # --- Usar ast.literal_eval para mayor seguridad --- 
        import ast 
        for line in text.strip().split('\n'):
            try:
                # Intentar evaluar la línea como un literal de Python seguro
                pattern = ast.literal_eval(line.strip())
                if isinstance(pattern, list) and all(isinstance(item, int) for item in pattern):
                    patrones.append(pattern)
            except (ValueError, SyntaxError):
                # Ignorar líneas que no se puedan parsear
                print(f"Advertencia: No se pudo parsear la línea del LLM con ast.literal_eval: {line}")
                continue

        if not patrones:
             raise ValueError("El LLM no devolvió patrones válidos.")

        return patrones

    except Exception as e:
        print(f"Error al llamar a la API de OpenAI o parsear la respuesta: {e}")
        print("Usando patrones de proceso por defecto.")
        return fallback_process_patterns()

def fallback_process_patterns():
    """Función helper para el fallback de patrones de proceso."""
    return [
        # --- Aceptados --- 
        # Con Idioma OK (1->3), Sin Alegación, Acepta 1ª, LA OK
        [1, 3, 4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32],
        # Sin Idioma, Sin Alegación, Acepta 2ª, LA OK
        [4, 5, 6, 10, 12, 13, 14, 15, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32],
        # Con Idioma REINTENTO OK (1->2->1->3), Con Alegación, Acepta 3ª, LA OK
        [1, 2, 1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 16, 17, 18, 19, 22, 23, 24, 25, 27, 28, 29, 31, 32],
        # Sin Idioma, Con Alegación, Acepta 1ª, LA con problemas resueltos
        [4, 5, 6, 7, 8, 9, 10, 11, 14, 18, 22, 23, 24, 26, 27, 28, 30, 27, 28, 29, 31, 32], # LA Rechazado->Reintentado

        # --- Renuncias --- 
        # Con Idioma OK (1->3), Sin Alegación, Renuncia en 1ª
        [1, 3, 4, 5, 6, 10, 12, 13],
        # Sin Idioma, Sin Alegación, Acepta 1ª, Renuncia en 2ª
        [4, 5, 6, 10, 11, 14, 16, 17],
        # Con Idioma OK (1->3), Con Alegación, Renuncia en 3ª
        [1, 3, 4, 5, 6, 7, 8, 9, 10, 11, 14, 15, 18, 20, 21],
        # Con Idioma REINTENTO OK (1->2->1->3), Sin Alegación, Renuncia en 2ª
        [1, 2, 1, 3, 4, 5, 6, 10, 11, 14, 16, 17],

        # --- No Asignados / Excluidos --- 
        # Con Idioma OK (1->3), Sin Alegación, No asignado final
        [1, 3, 4, 5, 6, 10, 13, 14, 17, 18, 21, 22],
        # Sin Idioma, Sin Alegación, No asignado final
        [4, 5, 6, 10, 13, 14, 17, 18, 21, 22],
        # Excluido en Idioma (primer intento)
        [1, 2],
        # Excluido en Idioma (segundo intento)
        [1, 2, 1, 2],

        # --- Cancelación Admin --- 
        # Con Idioma OK (1->3), Sin Alegación, Cancelado tras 1ª Adj
        [1, 3, 4, 5, 6, 10, 33],
        # Sin Idioma, Sin Alegación, Cancelado tras provisional
        [4, 5, 6, 33],
        # Con Idioma Rechazo (1->2), Cancelado
        [1, 2, 33]
    ]
