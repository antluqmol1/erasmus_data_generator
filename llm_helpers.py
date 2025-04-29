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
    Llama a GPT para generar motivos realistas de alegaciones Erasmus.
    """
    if not client:
        print("Cliente OpenAI no inicializado. Usando fallback para motivos de alegación.")
        return fallback_alegation_motives()
        
    prompt = (
        f"Genera {n} motivos realistas por los cuales un estudiante de la Universidad de Sevilla podría presentar una alegación en un programa Erasmus. "
        "Proporciona solo la lista de motivos."
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
    """Función helper para el fallback de motivos de alegación."""
    return [
        "Error en nota media", "Cambio de destino no solicitado", "Fallo administrativo", 
        "Revisión de expediente", "Problemas médicos", "No contabilización de créditos",
        # ... (resto de motivos por defecto) ...
    ]

def get_process_patterns(n=10):
    """
    Llama a GPT para generar patrones (secuencias de IDs de actividad) realistas del proceso Erasmus.
    """
    if not client:
        print("Cliente OpenAI no inicializado. Usando fallback para patrones de proceso.")
        return fallback_process_patterns()
        
    # Obtener descripción de actividades para el prompt (simplificado)
    actividades_desc = """
    1: Solicitud presentada
    2: Envío documentación
    3: Revisión documentación
    4: Solicitud validada
    5: Adjudicación provisional
    6: Notificación plaza asignada
    7: Aceptación de plaza
    8: Confirmación aceptación
    9: Renuncia a plaza
    10: Cancelación por baja voluntaria
    11: Cancelación de destino (Admin)
    12: Reasignación de destino (Admin)
    13: Alegación presentada
    14: Resolución alegación
    15: Solicitud modificación destino
    16: Resolución modificación destino
    17: Firma compromiso Erasmus
    18: Emisión certificado movilidad
    """

    prompt = (
        f"Eres un experto en procesos de movilidad estudiantil Erasmus. "
        f"Basándote en la siguiente lista de posibles actividades y sus IDs:\n{actividades_desc}\n"
        f"Genera {n} patrones (secuencias de IDs) realistas que podría seguir un estudiante. "
        f"Incluye variaciones comunes como aceptación normal, renuncia, alegaciones, cancelaciones/reasignaciones, etc. "
        f"Asegúrate de que el orden de las actividades en cada patrón sea lógicamente correcto. "
        f"Formatea CADA patrón como una lista de Python de enteros. Ejemplo: [1, 2, 3, 4, 5, 6, 7, 8, 17, 18]"
        f"Devuelve SOLO las listas, una por línea."
    )

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
        [1, 2, 3, 4, 5, 6, 7, 8, 17, 18],
        [1, 2, 3, 4, 5, 9, 10],
        [1, 2, 3, 4, 5, 11, 12, 6, 7, 8, 17, 18],
        [1, 2, 3, 4, 5, 6, 13, 14, 7, 8, 17, 18],
        [1, 2, 3, 4, 10],
    ]
