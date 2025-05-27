import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time

from llm_helpers import get_universities, get_alegation_motives, get_process_patterns

# ---- Configuración general ----
NUM_ESTUDIANTES = 3231
NUM_DESTINOS = 400  # Aumentamos destinos para tener ~2000 plazas (400 destinos * ~5 plazas promedio)
PCT_ESTUDIANTES_CON_ALEGACIONES = 0.175
RUTA_DATA = "data"
USE_LLM = True  # <<--- Activamos o desactivamos llamadas a LLM

# Creamos carpeta data si no existe
os.makedirs(RUTA_DATA, exist_ok=True)

# ---- Plazos Clave (Curso 23-24) ----
PLAZOS = {
    4: (datetime(2022, 11, 2), datetime(2022, 11, 30)),    # Inscripción
    7: (datetime(2022, 12, 12), datetime(2022, 12, 27)),   # Alegación
    11: (datetime(2023, 1, 11), datetime(2023, 1, 17)),    # Respuesta 1ª Adj
    12: (datetime(2023, 1, 11), datetime(2023, 1, 17)),    # Renuncia 1ª Adj
    15: (datetime(2023, 1, 19), datetime(2023, 1, 23)),    # Respuesta 2ª Adj
    16: (datetime(2023, 1, 19), datetime(2023, 1, 23)),    # Renuncia 2ª Adj
    19: (datetime(2023, 1, 25), datetime(2023, 1, 30)),    # Respuesta 3ª Adj
    20: (datetime(2023, 1, 25), datetime(2023, 1, 30)),    # Renuncia 3ª Adj
}

# ---- Funciones Auxiliares ----
def generar_hora_realista():
    """Generamos una hora del día, priorizando 08:00-23:59 con excepciones raras."""
    prob_horas_normales = 0.95 # Establecemos 95% de probabilidad para horas "normales"

    if random.random() < prob_horas_normales:
        # Seleccionamos horas normales (08:00 - 23:59)
        hora = random.randint(8, 23)
    else:
        # Ocasionalmente usamos horas raras (00:00 - 07:59)
        hora = random.randint(0, 7)
    
    minuto = random.randint(0, 59)
    segundo = random.randint(0, 59)
    return time(hora, minuto, segundo)

def generar_timestamp_en_plazo(inicio_plazo, fin_plazo, fecha_evento_anterior):
    """Generamos un timestamp dentro de un plazo con picos al inicio/final."""
    # Nos aseguramos de que las fechas son solo date para el cálculo de días
    inicio_plazo_dt = inicio_plazo.date()
    fin_plazo_dt = fin_plazo.date()
    fecha_evento_anterior_dt = fecha_evento_anterior.date()

    # Establecemos que el inicio efectivo no puede ser anterior al evento previo
    inicio_efectivo_dt = max(inicio_plazo_dt, fecha_evento_anterior_dt)

    # Si el inicio efectivo ya supera el fin del plazo, devolvemos fin_plazo como fallback
    if inicio_efectivo_dt > fin_plazo_dt:
        # Añadimos un tiempo aleatorio realista al día final
        hora_aleatoria = generar_hora_realista()
        return datetime.combine(fin_plazo_dt, hora_aleatoria)

    # Calculamos días disponibles
    dias_disponibles = (fin_plazo_dt - inicio_efectivo_dt).days + 1
    fechas_posibles = [inicio_efectivo_dt + timedelta(days=i) for i in range(dias_disponibles)]

    pesos = []
    peso_pico = 5 # Asignamos mayor peso para los días pico
    peso_normal = 1 # Peso normal para el resto

    if dias_disponibles <= 4: # Si el plazo es muy corto, usamos peso uniforme
        pesos = [peso_normal] * dias_disponibles
    else:
        for i in range(dias_disponibles):
            if i < 2 or i >= dias_disponibles - 2: # Primeros 2 días o últimos 2 días
                pesos.append(peso_pico)
            else:
                pesos.append(peso_normal)

    # Seleccionamos fecha basada en pesos
    fecha_seleccionada = random.choices(fechas_posibles, weights=pesos, k=1)[0]

    # Generamos hora realista
    hora_aleatoria = generar_hora_realista()
    timestamp_final = datetime.combine(fecha_seleccionada, hora_aleatoria)

    # Nos aseguramos de que el timestamp final no es anterior al evento anterior + 1 segundo
    timestamp_minimo = fecha_evento_anterior + timedelta(seconds=1)
    timestamp_final = max(timestamp_final, timestamp_minimo)

    return timestamp_final

# ---- Funciones para generar datos ----

def generar_destinos(num_destinos):
    if USE_LLM:
        print("🔄 Obteniendo universidades y países desde el LLM...")
        universidades_con_pais = get_universities(num_destinos) # [(nombre, pais), ...]
        print(f"✅ LLM generó {len(universidades_con_pais)} universidades.")
    else:
        # Mantenemos la generación genérica si no se usa LLM
        paises_fallback = ["Italia", "Alemania", "Francia", "Polonia", "Portugal", "Países Bajos", "Suecia", "Noruega", "Austria", "Suiza", "Dinamarca"]
        universidades_con_pais = [(f"Universidad de Ciudad {i}", random.choice(paises_fallback)) for i in range(1, num_destinos + 1)]

    # Ya no necesitamos ponderación de países aquí, ya que viene del LLM (o fallback)
    # paises_ponderados = { ... }
    # lista_paises = list(paises_ponderados.keys())
    # pesos_paises = list(paises_ponderados.values())

    destinos = []
    # Iteramos sobre las universidades *realmente generadas*
    for i, (nombre, pais) in enumerate(universidades_con_pais, start=1):
        # Usamos nombre y país directamente de la enumeración
        # 'i' ya es el ID basado en 1

        cancelado_bool = random.random() < 0.05 # ~5% de destinos cancelados
        cancelado = "Sí" if cancelado_bool else "No"
        
        # CORRECCIÓN: Destinos cancelados tienen 0 plazas desde el inicio
        if cancelado_bool:
            plazas = 0  # Destinos cancelados no tienen plazas disponibles
        else:
            # Distribución más controlada de plazas para aproximar 2000 plazas totales
            # Con 400 destinos activos (~95%), necesitamos ~5.3 plazas promedio
            rand_plazas = random.random()
            if rand_plazas < 0.15:      # 15% con 1-2 plazas (destinos pequeños)
                plazas = random.randint(1, 2)
            elif rand_plazas < 0.35:    # 20% con 3 plazas (destinos medianos)
                plazas = 3
            elif rand_plazas < 0.60:    # 25% con 4-5 plazas (destinos grandes)
                plazas = random.randint(4, 5)
            elif rand_plazas < 0.85:    # 25% con 6-7 plazas (destinos muy grandes)
                plazas = random.randint(6, 7)
            else:                       # 15% con 8-10 plazas (destinos excepcionales)
                plazas = random.randint(8, 10)
        
        # Establecemos fecha de cancelación ANTES del listado provisional (si está cancelado)
        fecha_cancelacion = ""
        if cancelado_bool:
            inicio_solicitudes = datetime(2022, 11, 2)
            pub_provisional = datetime(2022, 12, 12)
            delta_cancelacion = pub_provisional - inicio_solicitudes
            # Nos aseguramos de que el rango para randint es válido
            if delta_cancelacion.days > 16:
                dias_random_cancelacion = random.randint(15, delta_cancelacion.days - 1)
                fecha_cancelacion_dt = inicio_solicitudes + timedelta(days=dias_random_cancelacion)
                fecha_cancelacion = fecha_cancelacion_dt.strftime('%Y-%m-%d')
            else: # Si el periodo es muy corto, cancelamos en un día intermedio
                fecha_cancelacion_dt = inicio_solicitudes + timedelta(days=delta_cancelacion.days // 2)
                fecha_cancelacion = fecha_cancelacion_dt.strftime('%Y-%m-%d')
            
        # --- Añadimos columna RequiereIdioma ---
        requiere_idioma = random.random() < 0.65 # Establecemos que aproximadamente 65% requieren idioma
        
        destinos.append([i, nombre, pais, plazas, cancelado, fecha_cancelacion, requiere_idioma])
    
    # Mostramos advertencia si el número generado es menor que el solicitado
    if len(universidades_con_pais) < num_destinos:
        print(f"⚠️ Advertencia: Se solicitaron {num_destinos} destinos, pero solo se generaron {len(universidades_con_pais)}. Usaremos solo los generados.")
        
    return pd.DataFrame(
        destinos,
        columns=[
            "DestinoID", "NombreDestino", "País", "NúmeroPlazas",
            "Cancelado", "FechaCancelación", "RequiereIdioma"
        ]
    )

def generar_estudiantes(num_estudiantes, destinos_df):
    estudiantes = []

    # Ponderamos los grados para que algunos sean más frecuentes
    grados_ponderados = {
        "GII - Ingeniería del Software": 40,
        "GII - Ingeniería de Computadores": 25,
        "GII - Tecnologías Informáticas": 20,
        "GII - Ingeniería de la Salud": 15
    }
    lista_grados = list(grados_ponderados.keys())
    pesos_grados = list(grados_ponderados.values())
    estados_finales = ["Aceptado", "Renuncia", "No asignado", "Excluido"]
    # Ajustamos pesos para que ~62% sean aceptados (2000/3231), considerando que algunos renunciarán
    pesos_estados = [62, 8, 25, 5]  # 62% aceptados, 8% renuncias, 25% no asignados, 5% excluidos

    # CORRECCIÓN: Preparar lista de destinos disponibles por fecha
    destinos_disponibles_por_fecha = {}
    for _, destino in destinos_df.iterrows():
        destino_id = destino['DestinoID']
        cancelado = destino['Cancelado'] == 'Sí'
        fecha_cancelacion = destino['FechaCancelación']
        
        if cancelado and fecha_cancelacion:
            try:
                fecha_cancel_dt = datetime.strptime(fecha_cancelacion, '%Y-%m-%d')
                destinos_disponibles_por_fecha[destino_id] = fecha_cancel_dt
            except ValueError:
                # Si hay error en la fecha, asumir que está disponible
                destinos_disponibles_por_fecha[destino_id] = None
        else:
            # Destino no cancelado, siempre disponible
            destinos_disponibles_por_fecha[destino_id] = None

    for i in range(1, num_estudiantes + 1):
        # Elegimos grado según la ponderación
        grado = random.choices(lista_grados, weights=pesos_grados, k=1)[0]
        sexo = random.choice(["M", "F"])
        expediente = round(random.uniform(5.0, 10.0), 1)
        # Establecemos fecha de solicitud dentro del plazo de INSCRIPCIÓN (Actividad 4)
        fecha_solicitud_dt = generar_timestamp_en_plazo(
            PLAZOS[4][0], PLAZOS[4][1], PLAZOS[4][0] - timedelta(days=1)
        )
        fecha_solicitud = fecha_solicitud_dt.strftime('%Y-%m-%d')
        
        # CORRECCIÓN: Seleccionar destino que esté disponible en la fecha de solicitud
        destinos_disponibles = []
        for destino_id, fecha_cancelacion in destinos_disponibles_por_fecha.items():
            if fecha_cancelacion is None or fecha_solicitud_dt < fecha_cancelacion:
                destinos_disponibles.append(destino_id)
        
        if not destinos_disponibles:
            # Fallback: usar todos los destinos si no hay disponibles
            destinos_disponibles = destinos_df["DestinoID"].tolist()
        
        destino_solicitado = random.choice(destinos_disponibles)

        # Estados iniciales (se recalcularán desde gestión de plazas)
        estado_final = random.choices(estados_finales, weights=pesos_estados, k=1)[0]
        
        # Destino asignado inicial (se recalculará después)
        destino_asignado = np.nan
        if estado_final in ["Aceptado", "Renuncia"]:
            # Pre-asignación temporal para EventLog coherente
            destino_asignado = destino_solicitado if random.random() < 0.85 else random.choice(destinos_disponibles)

        estudiantes.append([i, grado, sexo, expediente, fecha_solicitud, destino_solicitado, destino_asignado, estado_final])
    return pd.DataFrame(estudiantes, columns=["EstudianteID", "Grado", "Sexo", "Expediente", "FechaSolicitud", "DestinoSolicitado", "DestinoAsignado", "EstadoFinal"])

def generar_actividades():
    actividades = [
        # Fase Inicial / Convalidación Idioma (IDs 1-3, Orden 1-2)
        (1, "Solicitud Convalidación Idioma Recibida", "Fase Inicial", "Automática", "Instituto de Idiomas", 1),
        (2, "Resolución Convalidación Idioma (Rechazada)", "Fase Inicial", "Automática", "Instituto de Idiomas", 2),
        (3, "Resolución Convalidación Idioma (Aceptada)", "Fase Inicial", "Automática", "Instituto de Idiomas", 2),

        # Inscripción y Listado Provisional (IDs 4-6, Orden 3-5)
        (4, "Inscripción Programa Erasmus Registrada", "Inscripción", "Manual", "Estudiante", 3),
        (5, "Cálculo Notas Participantes Realizado", "Adjudicación Provisional", "Automática", "SEVIUS", 4),
        (6, "Publicación Listado Provisional", "Adjudicación Provisional", "Automática", "SEVIUS", 5),

        # Alegaciones (IDs 7-9, Orden 6-8)
        (7, "Alegación Presentada", "Alegaciones", "Manual", "Estudiante", 6),
        (8, "Alegación Recibida", "Alegaciones", "Automática", "SEVIUS", 7),
        (9, "Resolución Alegación Emitida", "Alegaciones", "Automática", "SEVIUS", 8),

        # --- 1ª Adjudicación y Respuesta (IDs 10-13, Orden 9-11) ---
        (10, "Publicación 1ª Adjudicación", "Adjudicaciones", "Automática", "SEVIUS", 9),
        (11, "Respuesta Recibida (Aceptación/Reserva 1ª Adj.)", "Adjudicaciones", "Manual", "Estudiante", 10),
        (12, "Respuesta Recibida (Renuncia 1ª Adj.)", "Adjudicaciones", "Manual", "Estudiante", 10),
        (13, "Actualización Orden Preferencias (Post-1ª Adj.)", "Adjudicaciones", "Automática", "SEVIUS", 11),

        # --- 2ª Adjudicación y Respuesta (IDs 14-17, Orden 12-14) ---
        (14, "Publicación 2ª Adjudicación", "Adjudicaciones", "Automática", "SEVIUS", 12),
        (15, "Respuesta Recibida (Aceptación/Reserva 2ª Adj.)", "Adjudicaciones", "Manual", "Estudiante", 13),
        (16, "Respuesta Recibida (Renuncia 2ª Adj.)", "Adjudicaciones", "Manual", "Estudiante", 13),
        (17, "Actualización Orden Preferencias (Post-2ª Adj.)", "Adjudicaciones", "Automática", "SEVIUS", 14),

        # --- 3ª Adjudicación y Respuesta (IDs 18-21, Orden 15-17) ---
        (18, "Publicación 3ª Adjudicación", "Adjudicaciones", "Automática", "SEVIUS", 15),
        (19, "Respuesta Recibida (Aceptación/Reserva 3ª Adj.)", "Adjudicaciones", "Manual", "Estudiante", 16),
        (20, "Respuesta Recibida (Renuncia 3ª Adj.)", "Adjudicaciones", "Manual", "Estudiante", 16),
        (21, "Actualización Orden Preferencias (Post-3ª Adj.)", "Adjudicaciones", "Automática", "SEVIUS", 17),

        # Listado Definitivo (ID 22, Orden 18)
        (22, "Publicación Listado Definitivo", "Adjudicación Final", "Automática", "SEVIUS", 18),

        # Learning Agreement (IDs 23-30, Orden 19-24)
        (23, "Envío LA a Responsable Destino", "Learning Agreement", "Manual", "Estudiante", 19),
        (24, "LA Recibido por Responsable", "Learning Agreement", "Automática", "Responsable Destino", 20),
        (25, "LA Validado por Responsable", "Learning Agreement", "Manual", "Responsable Destino", 21),
        (26, "LA Rechazado por Responsable", "Learning Agreement", "Manual", "Responsable Destino", 21),
        (27, "Envío LA a Subdirectora RRII", "Learning Agreement", "Manual", "Estudiante", 22),
        (28, "LA Recibido por Subdirectora", "Learning Agreement", "Automática", "Subdirectora RRII", 23),
        (29, "LA Validado por Subdirectora", "Learning Agreement", "Manual", "Subdirectora RRII", 24),
        (30, "LA Rechazado por Subdirectora", "Learning Agreement", "Manual", "Subdirectora RRII", 24),

        # Formalización y Fin (IDs 31-32, Orden 25-26)
        (31, "Formalización Acuerdo SEVIUS", "Formalización", "Manual", "Estudiante", 25),
        (32, "Proceso Erasmus Finalizado", "Finalizado", "Automática", "Sistema", 26),

        # Evento de Cancelación Administrativa (ID 33, Orden ~9)
        # (Original 34 -> Nuevo 33). El orden 9 indica que puede ocurrir alrededor de las adjudicaciones.
        (33, "Cancelación Plaza (Admin)", "Cancelación", "Automática", "SEVIUS", 9)
    ]
    return pd.DataFrame(actividades, columns=["ActividadID", "NombreActividad", "Fase", "TipoActividad", "ActorDefecto", "OrdenSecuencial"])

def generar_bucles_la_dinamicos():
    """
    Genera bucles dinámicos de Learning Agreement con reintentos realistas.
    Retorna secuencias de IDs que representan los diferentes escenarios de LA.
    """
    bucles_la = []
    
    # Escenarios base para LA
    escenarios_base = [
        # LA directo exitoso (sin problemas)
        [23, 24, 25, 27, 28, 29],  # Responsable OK -> Subdirectora OK
        
        # LA con 1 reintento en Responsable (90% se resuelve)
        [23, 24, 26, 23, 24, 25, 27, 28, 29],
        
        # LA con 2 reintentos en Responsable (90% se resuelve)
        [23, 24, 26, 23, 24, 26, 23, 24, 25, 27, 28, 29],
        
        # LA con 3 reintentos en Responsable (90% se resuelve)
        [23, 24, 26, 23, 24, 26, 23, 24, 26, 23, 24, 25, 27, 28, 29],
        
        # LA con 1 reintento en Subdirectora (90% se resuelve)
        [23, 24, 25, 27, 28, 30, 27, 28, 29],
        
        # LA con 2 reintentos en Subdirectora (90% se resuelve)
        [23, 24, 25, 27, 28, 30, 27, 28, 30, 27, 28, 29],
        
        # LA con reintentos en ambos niveles (90% se resuelve)
        [23, 24, 26, 23, 24, 25, 27, 28, 30, 27, 28, 29],
        [23, 24, 26, 23, 24, 26, 23, 24, 25, 27, 28, 30, 27, 28, 30, 27, 28, 29],
        
        # --- CASOS NO RESUELTOS (10%) ---
        # LA rechazado definitivamente por Responsable tras 3 intentos
        [23, 24, 26, 23, 24, 26, 23, 24, 26],
        
        # LA rechazado definitivamente por Subdirectora tras 2 intentos
        [23, 24, 25, 27, 28, 30, 27, 28, 30],
        
        # LA rechazado definitivamente tras múltiples intentos en ambos niveles
        [23, 24, 26, 23, 24, 25, 27, 28, 30, 27, 28, 30],
        [23, 24, 26, 23, 24, 26, 23, 24, 25, 27, 28, 30, 27, 28, 30],
    ]
    
    return escenarios_base

def aplicar_bucles_la_a_ruta(ruta_base):
    """
    Aplica bucles de LA dinámicos a una ruta base que llegue hasta el LA.
    Respeta la probabilidad 90% resuelto / 10% no resuelto.
    """
    if 23 not in ruta_base:  # Si no tiene LA, devolver ruta original
        return ruta_base
    
    # Encontrar donde empieza el LA en la ruta
    try:
        idx_la_inicio = ruta_base.index(23)
        ruta_pre_la = ruta_base[:idx_la_inicio]
        
        # Obtener bucles de LA disponibles
        bucles_la = generar_bucles_la_dinamicos()
        
        # Separar bucles resueltos vs no resueltos
        bucles_resueltos = [b for b in bucles_la if b[-1] == 29]  # Terminan en "LA Validado por Subdirectora"
        bucles_no_resueltos = [b for b in bucles_la if b[-1] != 29]  # No terminan en validación
        
        # Aplicar probabilidad: 90% resuelto, 10% no resuelto
        if random.random() < 0.90:
            # 90% de casos: LA se resuelve finalmente
            bucle_seleccionado = random.choice(bucles_resueltos)
            nueva_ruta = ruta_pre_la + bucle_seleccionado + [31, 32]  # Añadir formalización
        else:
            # 10% de casos: LA no se resuelve
            bucle_seleccionado = random.choice(bucles_no_resueltos)
            nueva_ruta = ruta_pre_la + bucle_seleccionado + [32]  # Finalizar sin formalización
        
        return nueva_ruta
        
    except ValueError:
        # Si hay error, devolver ruta original
        return ruta_base

def generar_eventlog(estudiantes_df, actividades_df, destinos_df, estudiantes_con_alegaciones_ids):
    eventos = []
    actividad_actor_map = dict(zip(actividades_df["ActividadID"], actividades_df["ActorDefecto"]))

    # Procesar destinos cancelados tempranamente
    destinos_cancelados = destinos_df[destinos_df['Cancelado'] == 'Sí'].copy()
    destinos_cancelados['FechaCancelacion_dt'] = pd.to_datetime(destinos_cancelados['FechaCancelación'], errors='coerce')
    destinos_cancelados_temprano = destinos_cancelados.dropna(subset=['FechaCancelacion_dt']).set_index('DestinoID')
    mapa_fechas_cancelacion = destinos_cancelados_temprano['FechaCancelacion_dt'].to_dict()
    ids_destinos_cancelados_temprano = set(mapa_fechas_cancelacion.keys())

    # --- Rutas de actividades (ACTUALIZADAS con IDs renumerados desde 1) ---
    rutas_base = {
        # ESTADO FINAL: ACEPTADO
        "Aceptado": [
            # --- CON IDIOMA (Rutas con 1 y 3, 3 antes de 4) ---
            # Idioma OK (1->3), Sin Alegación, Acepta 1ª, LA OK directo
            [1, 3, 4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32],
            # Idioma OK (1->3), Sin Alegación, Acepta 1ª, LA con 1 reintento Responsable
            [1, 3, 4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 26, 23, 24, 25, 27, 28, 29, 31, 32],
            # Idioma OK (1->3), Sin Alegación, Acepta 1ª, LA con 2 reintentos Responsable
            [1, 3, 4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 26, 23, 24, 26, 23, 24, 25, 27, 28, 29, 31, 32],
            # Idioma OK (1->3), Sin Alegación, Acepta 1ª, LA con reintento Subdirectora
            [1, 3, 4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 25, 27, 28, 30, 27, 28, 29, 31, 32],
            # Idioma OK (1->3), Sin Alegación, Acepta 1ª, LA con múltiples reintentos (Resp+Subdir)
            [1, 3, 4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 26, 23, 24, 25, 27, 28, 30, 27, 28, 29, 31, 32],
            
            # Idioma OK (1->3), Sin Alegación, Renuncia 1ª, Acepta 2ª, LA OK
            [1, 3, 4, 5, 6, 10, 12, 13, 14, 15, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32],
            # Idioma OK (1->3), Sin Alegación, Renuncia 1ª/2ª, Acepta 3ª, LA con reintentos
            [1, 3, 4, 5, 6, 10, 12, 13, 14, 16, 17, 18, 19, 22, 23, 24, 26, 23, 24, 25, 27, 28, 29, 31, 32],
            # Idioma REINTENTO (1->2->1->3), Sin Alegación, Acepta 1ª, LA OK
            [1, 2, 1, 3, 4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32],
            
            # --- SIN IDIOMA (Rutas sin 1, 2, 3) ---
            # Sin Idioma, Sin Alegación, Acepta 1ª, LA OK directo
            [4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32],
            # Sin Idioma, Sin Alegación, Acepta 1ª, LA con reintentos Responsable
            [4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 26, 23, 24, 25, 27, 28, 29, 31, 32],
            # Sin Idioma, Sin Alegación, Acepta 1ª, LA con reintentos Subdirectora
            [4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 25, 27, 28, 30, 27, 28, 29, 31, 32],
            # Sin Idioma, Sin Alegación, Renuncia 1ª, Acepta 2ª, LA OK
            [4, 5, 6, 10, 12, 13, 14, 15, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32],
            # Sin Idioma, Sin Alegación, Renuncia 1ª/2ª, Acepta 3ª, LA con múltiples reintentos
            [4, 5, 6, 10, 12, 13, 14, 16, 17, 18, 19, 22, 23, 24, 26, 23, 24, 26, 23, 24, 25, 27, 28, 30, 27, 28, 29, 31, 32],
            
            # --- RUTAS CON LA RECHAZADO DEFINITIVAMENTE (10% casos) ---
            # Con Idioma, LA rechazado por Responsable tras 3 intentos -> Proceso finalizado
            [1, 3, 4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 26, 23, 24, 26, 23, 24, 26, 32],
            # Sin Idioma, LA rechazado por Subdirectora tras 2 intentos -> Proceso finalizado  
            [4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 25, 27, 28, 30, 27, 28, 30, 32],
            # Con Idioma, LA rechazado por ambos (Resp+Subdir) tras múltiples intentos -> Proceso finalizado
            [1, 3, 4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 26, 23, 24, 25, 27, 28, 30, 27, 28, 30, 32],
        ],
        # ESTADO FINAL: RENUNCIA
        "Renuncia": [
            # --- CON IDIOMA ---
            # Idioma OK (1->3), Sin Alegación, Renuncia en 1ª
            [1, 3, 4, 5, 6, 10, 12, 13],
            # Idioma OK (1->3), Sin Alegación, Acepta 1ª, Renuncia en 2ª
            [1, 3, 4, 5, 6, 10, 11, 14, 16, 17],
            # Idioma OK (1->3), Sin Alegación, Acepta 1ª/2ª, Renuncia en 3ª
            [1, 3, 4, 5, 6, 10, 11, 14, 15, 18, 20, 21],
            # Idioma REINTENTO OK (1->2->1->3), Sin Alegación, Renuncia en 1ª
            [1, 2, 1, 3, 4, 5, 6, 10, 12, 13],
            
            # --- SIN IDIOMA ---
            # Sin Idioma, Sin Alegación, Renuncia en 1ª
            [4, 5, 6, 10, 12, 13],
            # Sin Idioma, Sin Alegación, Acepta 1ª, Renuncia en 2ª
            [4, 5, 6, 10, 11, 14, 16, 17],
            # Sin Idioma, Sin Alegación, Acepta 1ª/2ª, Renuncia en 3ª
            [4, 5, 6, 10, 11, 14, 15, 18, 20, 21],
        ],
        # ESTADO FINAL: NO ASIGNADO
        "No asignado": [
            # --- CON IDIOMA ---
            # Idioma OK (1->3), Sin Alegación, Pasa todas las rondas sin plaza
            [1, 3, 4, 5, 6, 10, 13, 14, 17, 18, 21, 22],
            # Idioma REINTENTO OK (1->2->1->3), Sin Alegación, No pasa de provisional
            [1, 2, 1, 3, 4, 5, 6],
            # Idioma REINTENTO FALLIDO (1->2->1->2) -> Equivalente a Excluido
            [1, 2, 1, 2],

            # --- SIN IDIOMA ---
            # Sin Idioma, Sin Alegación, Pasa todas las rondas sin plaza
            [4, 5, 6, 10, 13, 14, 17, 18, 21, 22],
            # Sin Idioma, Sin Alegación, No pasa de provisional
            [4, 5, 6],
        ],
        # ESTADO FINAL: EXCLUIDO
        "Excluido": [
            # Base: Rechazado en Idioma (primer intento)
            [1, 2],
            # Base: Rechazado en Idioma (segundo intento)
            [1, 2, 1, 2],
            # Base: Sin idioma, excluido por otros motivos (ej. documentación)
            [4, 5],
            # Base: Sin idioma, excluido tras provisional
            [4, 5, 6],
        ]
    }

    # --- Lógica para generar variaciones de rutas (ACTUALIZADA con IDs renumerados) ---
    rutas_completas_por_estado = {}
    for estado, lista_rutas_base in rutas_base.items():
        variaciones = []
        for ruta_base in lista_rutas_base:
            variaciones.append(ruta_base)
            # Añadir versión con Alegación si la ruta base llega hasta la fase (contiene ID 6, pub prov)
            # Y si NO ES una ruta corta de exclusión por idioma ([1,2] o [1,2,1,2])
            if 6 in ruta_base and ruta_base != [1, 2] and ruta_base != [1, 2, 1, 2]:
                try:
                    idx_6 = ruta_base.index(6)
                    # Alegaciones van después de ID 6 (Pub Prov): IDs 7, 8, 9
                    ruta_con_alegacion = ruta_base[:idx_6+1] + [7, 8, 9] + ruta_base[idx_6+1:]
                    variaciones.append(ruta_con_alegacion)
                except ValueError: 
                    pass
                    
        rutas_unicas = set(tuple(v) for v in variaciones if v)
        rutas_completas_por_estado[estado] = [list(t) for t in rutas_unicas]

    # --- Rutas de Cancelación Administrativa (ACTUALIZADAS con IDs renumerados) ---
    # Cancelación ID es ahora 33
    rutas_cancelacion = {
        "con_idioma": [1, 3, 4, 5, 6, 10, 33],       # Idioma OK (1->3) -> Cancelación post-1ªAdj (10)
        "sin_idioma": [4, 5, 6, 10, 33],           # Sin Idioma -> Cancelación post-1ªAdj (10)
        "idioma_rechazo": [1, 2, 33],              # Idioma Rechazado (1->2) -> Cancelación
        "idioma_reintento_ok": [1, 2, 1, 3, 4, 33] # Reintento OK (1->2->1->3) -> Cancelación post-Inscripción (4)
    }
    # Añadir rutas de cancelación como posibilidad
    for estado in ["Aceptado", "Renuncia", "No asignado"]:
        if estado in rutas_completas_por_estado:
            rutas_completas_por_estado[estado].extend(rutas_cancelacion.values())

    # --- Ruta default (ACTUALIZADA) ---
    # Inscripción (4), Cálculo Notas (5), Pub Prov (6)
    rutas_default = [[4, 5, 6]]

    # --- Mezclar patrones LLM (La lógica de mezcla se mantiene) ---
    if USE_LLM:
        print("🔄 Obteniendo patrones de proceso desde el LLM...")
        try:
            patrones_llm = get_process_patterns(n=20)
            print(f"✅ LLM generó {len(patrones_llm)} patrones.")
            # Simplificado: Añadir a todos los estados principales
            for estado in ["Aceptado", "Renuncia", "No asignado"]:
                if estado in rutas_completas_por_estado:
                    rutas_completas_por_estado[estado].extend(patrones_llm)
            rutas_default.extend(patrones_llm)
        except Exception as e:
            print(f"❌ Error obteniendo o procesando patrones LLM: {e}")



    for idx, row in estudiantes_df.iterrows():
        estudiante_id = row["EstudianteID"]
        fecha_evento_anterior_base = datetime.strptime(row["FechaSolicitud"], '%Y-%m-%d')
        fecha_evento_anterior = datetime.combine(fecha_evento_anterior_base.date(), generar_hora_realista())
        estado_final = row["EstadoFinal"]
        destino_solicitado = row["DestinoSolicitado"]
        destino_asignado_final = row["DestinoAsignado"]
        
        # Mejorar la lógica de destino para el log
        if not pd.isna(destino_asignado_final):
            id_destino_log = destino_asignado_final
        else:
            # Si no tiene destino asignado, usar el solicitado para el tracking
            id_destino_log = destino_solicitado
        
        # Validación adicional
        if pd.isna(id_destino_log): 
            id_destino_log = random.choice(destinos_df["DestinoID"].tolist())

        ruta_seleccionada = None
        fecha_cancelacion_destino = None
        requiere_idioma = False # Valor por defecto

        # Obtener si el destino requiere idioma
        try:
            destino_info = destinos_df.loc[destinos_df['DestinoID'] == destino_solicitado].iloc[0]
            requiere_idioma = destino_info['RequiereIdioma']
        except IndexError:
            print(f"⚠️ Destino {destino_solicitado} no encontrado para Estudiante {estudiante_id}. Asumiendo sin idioma.")
            requiere_idioma = False

        # Comprobar cancelación temprana del destino
        if destino_solicitado in ids_destinos_cancelados_temprano:
            fecha_cancelacion_destino = mapa_fechas_cancelacion[destino_solicitado]
            # Seleccionar ruta de cancelación
            if requiere_idioma:
                pub_provisional = datetime(2022, 12, 12)
                if fecha_cancelacion_destino < pub_provisional:
                    ruta_seleccionada = rutas_cancelacion["idioma_rechazo"]
                else:
                    ruta_seleccionada = random.choice([
                        rutas_cancelacion["con_idioma"],
                        rutas_cancelacion["idioma_reintento_ok"]
                    ])
            else:
                ruta_seleccionada = rutas_cancelacion["sin_idioma"]

        # Selección de ruta normal si no hay cancelación
        if ruta_seleccionada is None:
            lista_rutas_estado = rutas_completas_por_estado.get(estado_final, rutas_default)
            if not lista_rutas_estado: 
                lista_rutas_estado = rutas_default

            # Filtrar por idioma
            if requiere_idioma:
                rutas_filtradas_idioma = [r for r in lista_rutas_estado if r and (r[0] == 1 or (1 in r and 2 in r))]
            else:
                rutas_filtradas_idioma = [r for r in lista_rutas_estado if r and not any(act_id in r for act_id in [1, 2, 3])]

            # Filtrar por alegaciones
            tiene_alegacion = estudiante_id in estudiantes_con_alegaciones_ids
            if tiene_alegacion:
                rutas_filtradas_final = [r for r in rutas_filtradas_idioma if 7 in r and 8 in r and 9 in r]
            else:
                rutas_filtradas_final = [r for r in rutas_filtradas_idioma if not (7 in r and 8 in r and 9 in r)]

                    # Selección con fallbacks
        if rutas_filtradas_final:
            ruta_seleccionada = random.choice(rutas_filtradas_final)
        elif rutas_filtradas_idioma:
            ruta_seleccionada = random.choice(rutas_filtradas_idioma)
        elif lista_rutas_estado:
            ruta_seleccionada = random.choice(lista_rutas_estado)
        else:
            ruta_seleccionada = random.choice(rutas_default)
        
        # NUEVA FUNCIONALIDAD: Aplicar bucles de LA dinámicos si la ruta llega al LA
        if estado_final == "Aceptado" and 23 in ruta_seleccionada:
            ruta = aplicar_bucles_la_a_ruta(ruta_seleccionada)
        else:
            ruta = ruta_seleccionada

        # Generar eventos de la ruta
        for actividad_id in ruta:
            # Calcular timestamp del evento
            if actividad_id == 33 and fecha_cancelacion_destino is not None:
                # Cancelación administrativa
                fecha_minima = fecha_evento_anterior + timedelta(seconds=1)
                fecha_actual = max(fecha_cancelacion_destino, fecha_minima)
                fecha_actual = datetime.combine(fecha_actual.date(), generar_hora_realista())
                fecha_actual = max(fecha_actual, fecha_minima)
            elif actividad_id in FECHAS_PUBLICACION:
                # Publicaciones con fecha fija
                fecha_fija = FECHAS_PUBLICACION[actividad_id]
                fecha_minima = fecha_evento_anterior + timedelta(seconds=1)
                fecha_actual = max(fecha_fija, fecha_minima)
                if fecha_actual > fecha_fija and fecha_actual.date() == fecha_fija.date():
                    hora_minima = fecha_minima.time()
                    hora_fija = time(0, 1, 0)
                    fecha_actual = datetime.combine(fecha_actual.date(), max(hora_fija, hora_minima))
            elif actividad_id in PLAZOS:
                # Eventos con plazo definido
                inicio_plazo, fin_plazo = PLAZOS[actividad_id]
                fecha_actual = generar_timestamp_en_plazo(inicio_plazo, fin_plazo, fecha_evento_anterior)
            else:
                # Eventos con delta aleatorio
                delta_total = timedelta(days=random.randint(0, 2), hours=random.randint(1, 12), minutes=random.randint(0,59))
                fecha_propuesta = fecha_evento_anterior + delta_total
                
                # Evitar adelantar plazos futuros
                proximo_plazo_inicio = None
                try:
                    indice_actual = ruta.index(actividad_id)
                    for act_futura_id in ruta[indice_actual+1:]:
                        if act_futura_id in PLAZOS:
                            proximo_plazo_inicio = PLAZOS[act_futura_id][0]
                            break
                except ValueError:
                    pass
                    
                if proximo_plazo_inicio and fecha_propuesta >= proximo_plazo_inicio:
                    fecha_actual = fecha_evento_anterior + timedelta(hours=random.randint(1,3))
                    if fecha_actual >= proximo_plazo_inicio:
                       fecha_actual = proximo_plazo_inicio - timedelta(minutes=random.randint(1,30))
                else:
                    fecha_actual = fecha_propuesta

            fecha_evento_anterior = fecha_actual            
            
            # Generar detalle del evento
            actor = actividad_actor_map.get(actividad_id, "Desconocido")
            detalle = actividades_df.loc[actividades_df['ActividadID'] == actividad_id, 'NombreActividad'].iloc[0]
            
            # Detalles específicos para respuestas y cancelaciones
            if actividad_id in [11, 15, 19]: 
                ronda_adj = (actividad_id - 11) // 4 + 1
                detalle = f"Respuesta {ronda_adj}ª Adj: Aceptación/Reserva"
            elif actividad_id in [12, 16, 20]: 
                ronda_adj = (actividad_id - 12) // 4 + 1
                detalle = f"Respuesta {ronda_adj}ª Adj: Renuncia"
            elif actividad_id == 33: 
                detalle = "Destino Solicitado Cancelado (Admin)"

            eventos.append([
                estudiante_id, actividad_id, fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
                int(id_destino_log), detalle, actor
            ])

    eventos_df = pd.DataFrame(eventos, columns=["EstudianteID", "ActividadID", "Timestamp", "DestinoID", "Detalle", "Actor"])
    eventos_df.insert(0, "EventID", range(1, len(eventos_df) + 1))
    return eventos_df

def generar_alegaciones(estudiantes_df):
    """
    Genera alegaciones con fechas que serán coordinadas posteriormente con el EventLog.
    NOTA: Las fechas se generan inicialmente de forma aproximada y se sincronizarán 
    después con las fechas reales del EventLog.
    """
    motivos = get_alegation_motives(20) if USE_LLM else [
        "Error en nota media", "Cambio de destino no solicitado", "Fallo administrativo", 
        "Revisión de expediente", "Problemas médicos", "No contabilización de créditos",
        "Error en fecha límite de entrega", "Destino cancelado sin aviso", "Falta de actualización de notas",
        "Confusión en adjudicación de plaza", "Problemas técnicos en la plataforma", 
        "Revisión de expediente Erasmus anterior", "Actualización posterior de expediente académico",
        "Error en selección de prioridades", "Equivalencia incorrecta de estudios",
        "Problemas familiares graves", "Motivos laborales inesperados", 
        "Crisis sanitaria no prevista", "Nueva acreditación académica", "Error humano de revisión"
    ]

    estudiantes_con_alegacion = estudiantes_df.sample(frac=PCT_ESTUDIANTES_CON_ALEGACIONES)
    alegaciones = []

    for idx, row in estudiantes_con_alegacion.iterrows():
        estudiante_id = row["EstudianteID"]
        fecha_solicitud = datetime.strptime(row["FechaSolicitud"], '%Y-%m-%d')
        
        # FECHAS TEMPORALES - Se sincronizarán con EventLog después
        fecha_alegacion = fecha_solicitud + timedelta(days=random.randint(20, 50))

        motivo = random.choice(motivos)
        resultado = random.choice(["Aceptada", "Rechazada"])
        fecha_resolucion = fecha_alegacion + timedelta(days=random.randint(7, 20))

        if resultado == "Aceptada":
            accion = random.choice(["Reasignación", "Confirmación destino inicial"])
        else:
            accion = "No cambio"

        alegaciones.append([
            idx + 1,  # AlegacionID único
            estudiante_id,
            fecha_alegacion.strftime('%Y-%m-%d'),
            motivo,
            resultado,
            fecha_resolucion.strftime('%Y-%m-%d'),
            accion
        ])

    alegaciones_df = pd.DataFrame(alegaciones, columns=[
        "AlegacionID", "EstudianteID", "FechaAlegacion", "MotivoAlegacion", 
        "ResultadoAlegacion", "FechaResolucion", "AccionTrasResolucion"
    ])
    
    # Obtenemos el conjunto de IDs de estudiantes con alegaciones
    estudiantes_con_alegaciones_ids = set(alegaciones_df["EstudianteID"].unique())
    
    # Devolvemos tanto el DataFrame como el conjunto de IDs
    return alegaciones_df, estudiantes_con_alegaciones_ids

def sincronizar_fechas_historico_eventlog(historico_df, eventlog_df):
    """Sincroniza las fechas del histórico con las fechas reales del EventLog."""
    print("🕐 Sincronizando fechas entre Histórico y EventLog...")
    
    historico_sincronizado = historico_df.copy()
    
    for idx, row in historico_sincronizado.iterrows():
        estudiante_id = row['EstudianteID']
        ronda = row['Ronda']
        
        if ronda in RONDA_A_ACTIVIDAD:
            actividad_id = RONDA_A_ACTIVIDAD[ronda]
            evento_publicacion = eventlog_df[
                (eventlog_df['EstudianteID'] == estudiante_id) & 
                (eventlog_df['ActividadID'] == actividad_id)
            ]
            
            if len(evento_publicacion) > 0:
                fecha_real = pd.to_datetime(evento_publicacion.iloc[0]['Timestamp']).strftime('%Y-%m-%d')
                historico_sincronizado.at[idx, 'FechaAsignacion'] = fecha_real
    
    return historico_sincronizado

def sincronizar_alegaciones_eventlog(alegaciones_df, eventlog_df):
    """Sincroniza las fechas de alegaciones con las fechas reales del EventLog."""
    print("🕐 Sincronizando fechas de alegaciones con EventLog...")
    
    alegaciones_sincronizadas = alegaciones_df.copy()
    
    for idx, row in alegaciones_sincronizadas.iterrows():
        estudiante_id = row['EstudianteID']
        
        eventos_alegacion = eventlog_df[
            (eventlog_df['EstudianteID'] == estudiante_id) & 
            (eventlog_df['ActividadID'].isin([7, 8, 9]))
        ].sort_values('Timestamp')
        
        if len(eventos_alegacion) > 0:
            # Fecha de presentación (ActividadID 7)
            evento_presentacion = eventos_alegacion[eventos_alegacion['ActividadID'] == 7]
            if len(evento_presentacion) > 0:
                fecha_real_alegacion = pd.to_datetime(evento_presentacion.iloc[0]['Timestamp']).strftime('%Y-%m-%d')
                alegaciones_sincronizadas.at[idx, 'FechaAlegacion'] = fecha_real_alegacion
            
            # Fecha de resolución (ActividadID 9)
            evento_resolucion = eventos_alegacion[eventos_alegacion['ActividadID'] == 9]
            if len(evento_resolucion) > 0:
                fecha_real_resolucion = pd.to_datetime(evento_resolucion.iloc[0]['Timestamp']).strftime('%Y-%m-%d')
                alegaciones_sincronizadas.at[idx, 'FechaResolucion'] = fecha_real_resolucion
    
    return alegaciones_sincronizadas

def extraer_historico_desde_gestion_plazas(gestion_plazas, eventlog_df):
    """Extrae el histórico de adjudicaciones desde la gestión de plazas."""
    historico = []
    asignacion_id_counter = 1
    
    fechas_fallback = {
        "1ª Adjudicación": "2023-01-11",
        "2ª Adjudicación": "2023-01-19", 
        "3ª Adjudicación": "2023-01-25",
        "Adjudicación Final": "2023-02-01"
    }
    
    for destino_id in gestion_plazas['asignaciones_titulares']:
        for ronda in RONDAS:
            actividad_id = RONDA_A_ACTIVIDAD[ronda]
            eventos_publicacion = eventlog_df[
                (eventlog_df['ActividadID'] == actividad_id) & 
                (eventlog_df['DestinoID'] == destino_id)
            ]
            
            if len(eventos_publicacion) > 0:
                fecha_publicacion = pd.to_datetime(eventos_publicacion.iloc[0]['Timestamp']).strftime('%Y-%m-%d')
            else:
                fecha_publicacion = fechas_fallback[ronda]
            
            # Registrar titulares y suplentes
            for tipo, lista in [("Titular", gestion_plazas['asignaciones_titulares'][destino_id][ronda]),
                               ("Suplente", gestion_plazas['asignaciones_suplentes'][destino_id][ronda])]:
                for estudiante_id in lista:
                    historico.append([
                        asignacion_id_counter, estudiante_id, destino_id,
                        fecha_publicacion, ronda, tipo
                    ])
                    asignacion_id_counter += 1

    return pd.DataFrame(historico, columns=[
        "AsignacionID", "EstudianteID", "DestinoID", "FechaAsignacion", "Ronda", "EstadoEnRonda"
    ])

def validar_coherencia_datos(estudiantes_df, eventlog_df, historico_df):
    """
    Valida la coherencia entre las tres fuentes de datos principales.
    ACTUALIZADA: Se enfoca en coherencia estructural, no en estados vs EventLog
    (ya que los estados se actualizan desde gestión de plazas).
    """
    inconsistencias = []
    
    print("🔍 Validando coherencia de datos...")
    
    for _, estudiante in estudiantes_df.iterrows():
        estudiante_id = estudiante['EstudianteID']
        estado_final = estudiante['EstadoFinal']
        destino_asignado = estudiante['DestinoAsignado']
        destino_solicitado = estudiante['DestinoSolicitado']
        
        # Obtener eventos del estudiante
        eventos = eventlog_df[eventlog_df['EstudianteID'] == estudiante_id].sort_values('Timestamp')
        historico_est = historico_df[historico_df['EstudianteID'] == estudiante_id]
        
        if len(eventos) == 0:
            inconsistencias.append(f"Estudiante {estudiante_id}: Sin eventos en EventLog")
            continue
        
        # Validación 1: Coherencia básica de destinos (RELAJADA - diferencias son normales en Erasmus)
        # Solo reportar si es una diferencia muy extraña (ej. destino inexistente)
        # if not pd.isna(destino_asignado) and destino_asignado != destino_solicitado:
        #     inconsistencias.append(f"Estudiante {estudiante_id}: Destino asignado ({destino_asignado}) diferente al solicitado ({destino_solicitado})")
        
        # Validación 2: Estados vs destinos asignados
        if estado_final == "Aceptado" and pd.isna(destino_asignado):
            inconsistencias.append(f"Estudiante {estudiante_id}: Estado 'Aceptado' pero sin destino asignado")
        
        if estado_final in ["Renuncia", "No asignado", "Excluido"] and not pd.isna(destino_asignado):
            inconsistencias.append(f"Estudiante {estudiante_id}: Estado '{estado_final}' pero tiene destino asignado ({destino_asignado})")
        
        # Validación 3: Destino asignado vs histórico
        if not pd.isna(destino_asignado) and len(historico_est) > 0:
            destinos_historico = set(historico_est['DestinoID'].tolist())
            if destino_asignado not in destinos_historico:
                inconsistencias.append(f"Estudiante {estudiante_id}: Destino asignado {destino_asignado} no aparece en histórico")
        
        # Validación 4: Fechas de adjudicación vs eventos (sincronización)
        for _, adj in historico_est.iterrows():
            fecha_adj = pd.to_datetime(adj['FechaAsignacion'])
            ronda = adj['Ronda']
            
            # Buscar evento de publicación correspondiente
            if "1ª" in ronda:
                eventos_pub = eventos[eventos['ActividadID'] == 10]
            elif "2ª" in ronda:
                eventos_pub = eventos[eventos['ActividadID'] == 14]
            elif "3ª" in ronda:
                eventos_pub = eventos[eventos['ActividadID'] == 18]
            elif "Final" in ronda:
                eventos_pub = eventos[eventos['ActividadID'] == 22]
            else:
                continue
                
            if len(eventos_pub) > 0:
                fecha_evento = pd.to_datetime(eventos_pub.iloc[0]['Timestamp']).date()
                if fecha_adj.date() != fecha_evento:
                    inconsistencias.append(f"Estudiante {estudiante_id}: Fecha adjudicación {ronda} no coincide (Histórico: {fecha_adj.date()}, EventLog: {fecha_evento})")
        
        # Validación 5: Estudiantes excluidos no deberían tener histórico de adjudicaciones
        if estado_final == "Excluido" and len(historico_est) > 0:
            inconsistencias.append(f"Estudiante {estudiante_id}: Estado 'Excluido' pero tiene histórico de adjudicaciones")
    
    # Mostrar resumen de validación
    if inconsistencias:
        print(f"⚠️ Se encontraron {len(inconsistencias)} inconsistencias:")
        for inc in inconsistencias[:10]:  # Mostrar solo las primeras 10
            print(f"   - {inc}")
        if len(inconsistencias) > 10:
            print(f"   ... y {len(inconsistencias) - 10} más.")
    else:
        print("✅ No se encontraron inconsistencias.")
    
    return inconsistencias

def gestionar_plazas_por_destino_y_ronda():
    """
    Gestiona las plazas disponibles por destino en cada ronda de adjudicación.
    Retorna un diccionario con el estado de plazas por destino y ronda.
    """
    return {
        'plazas_disponibles': {},  # {destino_id: {ronda: plazas_restantes}}
        'asignaciones_titulares': {},  # {destino_id: {ronda: [estudiante_ids]}}
        'asignaciones_suplentes': {},  # {destino_id: {ronda: [estudiante_ids]}}
        'renuncias': {}  # {destino_id: {ronda: [estudiante_ids_que_renunciaron]}}
    }

def simular_adjudicacion_con_plazas(estudiantes_df, destinos_df):
    """
    Simula el proceso de adjudicación considerando el número real de plazas disponibles.
    Retorna información detallada de asignaciones por ronda.
    """
    print("🎯 Simulando adjudicación con control de plazas...")
    
    # Inicializar gestión de plazas
    gestion_plazas = gestionar_plazas_por_destino_y_ronda()
    
    # Inicializar plazas disponibles para cada destino
    for _, destino in destinos_df.iterrows():
        destino_id = destino['DestinoID']
        num_plazas = destino['NúmeroPlazas']
        
        # SIMPLIFICADO: Los destinos cancelados ya tienen NúmeroPlazas = 0 desde el CSV
        plazas_iniciales = num_plazas
        
        gestion_plazas['plazas_disponibles'][destino_id] = {
            '1ª Adjudicación': plazas_iniciales,
            '2ª Adjudicación': plazas_iniciales,
            '3ª Adjudicación': plazas_iniciales,
            'Adjudicación Final': plazas_iniciales
        }
        
        gestion_plazas['asignaciones_titulares'][destino_id] = {
            '1ª Adjudicación': [],
            '2ª Adjudicación': [],
            '3ª Adjudicación': [],
            'Adjudicación Final': []
        }
        
        gestion_plazas['asignaciones_suplentes'][destino_id] = {
            '1ª Adjudicación': [],
            '2ª Adjudicación': [],
            '3ª Adjudicación': [],
            'Adjudicación Final': []
        }
        
        gestion_plazas['renuncias'][destino_id] = {
            '1ª Adjudicación': [],
            '2ª Adjudicación': [],
            '3ª Adjudicación': [],
            'Adjudicación Final': []
        }
    
    # Simular cada ronda de adjudicación
    rondas = ['1ª Adjudicación', '2ª Adjudicación', '3ª Adjudicación', 'Adjudicación Final']
    
    for ronda in rondas:
        print(f"   📋 Procesando {ronda}...")
        
        # Obtener estudiantes elegibles para esta ronda
        estudiantes_elegibles = []
        for _, estudiante in estudiantes_df.iterrows():
            estudiante_id = estudiante['EstudianteID']
            destino_solicitado = estudiante['DestinoSolicitado']
            estado_final = estudiante['EstadoFinal']
            
            # Lógica para determinar si el estudiante participa en esta ronda
            participa = False
            if ronda == '1ª Adjudicación':
                # Todos los no excluidos participan en 1ª
                participa = estado_final != 'Excluido'
            elif ronda == '2ª Adjudicación':
                # Solo los que no fueron asignados como titulares en 1ª EN CUALQUIER DESTINO o renunciaron
                fue_titular_1ra = False
                renuncio_1ra = False
                
                for destino_check in gestion_plazas['asignaciones_titulares']:
                    if estudiante_id in gestion_plazas['asignaciones_titulares'][destino_check]['1ª Adjudicación']:
                        fue_titular_1ra = True
                        if estudiante_id in gestion_plazas['renuncias'][destino_check]['1ª Adjudicación']:
                            renuncio_1ra = True
                        break
                
                participa = (not fue_titular_1ra or renuncio_1ra) and estado_final != 'Excluido'
            elif ronda == '3ª Adjudicación':
                # Solo los que no fueron asignados como titulares en 1ª/2ª EN CUALQUIER DESTINO o renunciaron
                fue_titular_1ra_2da = False
                renuncio_1ra_2da = False
                
                for destino_check in gestion_plazas['asignaciones_titulares']:
                    # Verificar 1ª adjudicación
                    if estudiante_id in gestion_plazas['asignaciones_titulares'][destino_check]['1ª Adjudicación']:
                        fue_titular_1ra_2da = True
                        if estudiante_id in gestion_plazas['renuncias'][destino_check]['1ª Adjudicación']:
                            renuncio_1ra_2da = True
                    
                    # Verificar 2ª adjudicación
                    if estudiante_id in gestion_plazas['asignaciones_titulares'][destino_check]['2ª Adjudicación']:
                        fue_titular_1ra_2da = True
                        if estudiante_id in gestion_plazas['renuncias'][destino_check]['2ª Adjudicación']:
                            renuncio_1ra_2da = True
                
                participa = (not fue_titular_1ra_2da or renuncio_1ra_2da) and estado_final != 'Excluido'
            else:  # Adjudicación Final
                # Todos los que llegaron hasta aquí
                participa = estado_final in ['Aceptado', 'No asignado']
            
            if participa:
                estudiantes_elegibles.append({
                    'estudiante_id': estudiante_id,
                    'destino_solicitado': destino_solicitado,
                    'expediente': estudiante['Expediente'],
                    'estado_final': estado_final
                })
        
        # CORRECCIÓN: Aplicar filtros de elegibilidad (incluyendo requisitos de idioma)
        estudiantes_elegibles = aplicar_filtros_elegibilidad(estudiantes_elegibles, destinos_df)
        
        # Agrupar por destino y ordenar por expediente (mayor a menor)
        destinos_solicitados = {}
        for est in estudiantes_elegibles:
            destino = est['destino_solicitado']
            if destino not in destinos_solicitados:
                destinos_solicitados[destino] = []
            destinos_solicitados[destino].append(est)
        
        # Procesar cada destino
        for destino_id, candidatos in destinos_solicitados.items():
            # Ordenar candidatos por expediente (mayor nota = mayor prioridad)
            candidatos_ordenados = sorted(candidatos, key=lambda x: x['expediente'], reverse=True)
            
            # CORRECCIÓN: Calcular plazas realmente disponibles considerando asignaciones previas Y renuncias
            plazas_totales = gestion_plazas['plazas_disponibles'][destino_id][ronda]
            asignaciones_previas = len(gestion_plazas['asignaciones_titulares'][destino_id][ronda])
            renuncias_previas = len(gestion_plazas['renuncias'][destino_id][ronda])
            plazas_realmente_disponibles = max(0, plazas_totales - asignaciones_previas + renuncias_previas)
            
            # Asignar titulares (hasta el límite de plazas realmente disponibles)
            titulares_asignados = 0
            for candidato in candidatos_ordenados:
                if titulares_asignados < plazas_realmente_disponibles:
                    # Verificar que el estudiante no esté ya asignado en este destino en esta ronda
                    if candidato['estudiante_id'] not in gestion_plazas['asignaciones_titulares'][destino_id][ronda]:
                        gestion_plazas['asignaciones_titulares'][destino_id][ronda].append(candidato['estudiante_id'])
                        titulares_asignados += 1
                else:
                    # Asignar como suplente
                    if candidato['estudiante_id'] not in gestion_plazas['asignaciones_suplentes'][destino_id][ronda]:
                        gestion_plazas['asignaciones_suplentes'][destino_id][ronda].append(candidato['estudiante_id'])
        
        # NUEVA FUNCIONALIDAD: Reasignación a destinos alternativos
        # Buscar estudiantes que no obtuvieron plaza en su destino preferido
        # y reasignarlos a destinos con plazas disponibles
        estudiantes_sin_plaza = []
        for est in estudiantes_elegibles:
            estudiante_id = est['estudiante_id']
            destino_solicitado = est['destino_solicitado']
            
            # Verificar si no fue asignado como titular en su destino preferido
            if estudiante_id not in gestion_plazas['asignaciones_titulares'][destino_solicitado][ronda]:
                estudiantes_sin_plaza.append(est)
        
        # CORRECCIÓN: Buscar destinos con plazas realmente disponibles
        destinos_con_plazas = []
        for destino_id in gestion_plazas['plazas_disponibles']:
            plazas_totales = gestion_plazas['plazas_disponibles'][destino_id][ronda]
            asignaciones_actuales = len(gestion_plazas['asignaciones_titulares'][destino_id][ronda])
            renuncias_actuales = len(gestion_plazas['renuncias'][destino_id][ronda])
            plazas_restantes = max(0, plazas_totales - asignaciones_actuales + renuncias_actuales)
            
            # Añadir cada plaza disponible como una entrada separada
            for _ in range(plazas_restantes):
                destinos_con_plazas.append(destino_id)
        
        # CORRECCIÓN: Reasignación más realista con menor probabilidad
        if estudiantes_sin_plaza and destinos_con_plazas:
            # Ordenar estudiantes sin plaza por expediente
            estudiantes_sin_plaza_ordenados = sorted(estudiantes_sin_plaza, 
                                                    key=lambda x: x['expediente'], reverse=True)
            
            for estudiante in estudiantes_sin_plaza_ordenados:
                if not destinos_con_plazas:
                    break
                    
                # CORRECCIÓN: Reducir probabilidad a 15% (más realista)
                # Solo los estudiantes más flexibles aceptan destinos alternativos
                if random.random() < 0.15:
                    # Filtrar destinos alternativos por compatibilidad (mismo país o región)
                    destino_original_info = destinos_df[destinos_df['DestinoID'] == estudiante['destino_solicitado']].iloc[0]
                    pais_original = destino_original_info['País']
                    
                    # Buscar destinos compatibles (mismo país o países vecinos)
                    destinos_compatibles = []
                    for destino_alt in destinos_con_plazas:
                        destino_alt_info = destinos_df[destinos_df['DestinoID'] == destino_alt].iloc[0]
                        pais_alt = destino_alt_info['País']
                        
                        # Compatibilidad: mismo país o países "similares" (simplificado)
                        if (pais_alt == pais_original or 
                            (pais_original in ['Francia', 'Bélgica'] and pais_alt in ['Francia', 'Bélgica']) or
                            (pais_original in ['Alemania', 'Austria'] and pais_alt in ['Alemania', 'Austria']) or
                            (pais_original in ['Italia', 'Malta'] and pais_alt in ['Italia', 'Malta'])):
                            destinos_compatibles.append(destino_alt)
                    
                    # Si hay destinos compatibles, usar esos; sino, cualquier disponible
                    destinos_a_considerar = destinos_compatibles if destinos_compatibles else destinos_con_plazas
                    
                    if destinos_a_considerar:
                        destino_alternativo = random.choice(destinos_a_considerar)
                        
                        # CORRECCIÓN: Verificar que no esté ya asignado antes de añadir
                        if estudiante['estudiante_id'] not in gestion_plazas['asignaciones_titulares'][destino_alternativo][ronda]:
                            gestion_plazas['asignaciones_titulares'][destino_alternativo][ronda].append(estudiante['estudiante_id'])
                            destinos_con_plazas.remove(destino_alternativo)  # Reducir plazas disponibles
        
        # Simular renuncias en esta ronda (libera plazas para la siguiente)
        for destino_id in gestion_plazas['asignaciones_titulares']:
            titulares_ronda = gestion_plazas['asignaciones_titulares'][destino_id][ronda]
            
            # Simular renuncias (probabilidad basada en el estado final del estudiante)
            for titular_id in titulares_ronda:
                estudiante_info = estudiantes_df[estudiantes_df['EstudianteID'] == titular_id].iloc[0]
                estado_final = estudiante_info['EstadoFinal']
                
                # Probabilidad de renuncia basada en estado final y ronda
                prob_renuncia = 0.0
                if estado_final == 'Renuncia':
                    if ronda == '1ª Adjudicación':
                        prob_renuncia = 0.4  # 40% renuncia en 1ª
                    elif ronda == '2ª Adjudicación':
                        prob_renuncia = 0.3  # 30% renuncia en 2ª
                    elif ronda == '3ª Adjudicación':
                        prob_renuncia = 0.3  # 30% renuncia en 3ª
                
                if random.random() < prob_renuncia:
                    gestion_plazas['renuncias'][destino_id][ronda].append(titular_id)
                    
                    # CORRECCIÓN: Liberar plaza para todas las rondas siguientes
                    ronda_actual_idx = rondas.index(ronda)
                    for siguiente_ronda_idx in range(ronda_actual_idx + 1, len(rondas)):
                        siguiente_ronda = rondas[siguiente_ronda_idx]
                        # Solo incrementar si no se ha decrementado ya por otra renuncia
                        gestion_plazas['plazas_disponibles'][destino_id][siguiente_ronda] += 1
                    
                    # Promover suplente a titular en la siguiente ronda si hay suplentes disponibles
                    if ronda != 'Adjudicación Final':
                        siguiente_ronda_idx = rondas.index(ronda) + 1
                        if siguiente_ronda_idx < len(rondas):
                            siguiente_ronda = rondas[siguiente_ronda_idx]
                            suplentes_disponibles = gestion_plazas['asignaciones_suplentes'][destino_id][ronda]
                            if suplentes_disponibles:
                                # Promover al primer suplente (mejor expediente)
                                promovido = suplentes_disponibles.pop(0)
                                gestion_plazas['asignaciones_titulares'][destino_id][siguiente_ronda].append(promovido)
                                # Decrementar la plaza que acabamos de incrementar
                                gestion_plazas['plazas_disponibles'][destino_id][siguiente_ronda] -= 1
    
    return gestion_plazas

def ajustar_asignaciones_por_plazas(gestion_plazas, destinos_df):
    """
    Ajusta las asignaciones para que respeten estrictamente el número de plazas disponibles.
    MEJORADO: Ahora elimina completamente todas las sobreasignaciones.
    """
    print("🔧 Ajustando asignaciones para respetar límites de plazas...")
    
    ajustes_realizados = 0
    destinos_con_problemas = 0
    
    for _, destino in destinos_df.iterrows():
        destino_id = destino['DestinoID']
        plazas_totales = destino['NúmeroPlazas']
        
        if plazas_totales == 0:  # Destinos cancelados, no procesar
            continue
        
        # MEJORADO: Recopilar todas las asignaciones por ronda y eliminar duplicados
        estudiantes_por_ronda = {}
        
        for ronda in ['1ª Adjudicación', '2ª Adjudicación', '3ª Adjudicación', 'Adjudicación Final']:
            titulares = set(gestion_plazas['asignaciones_titulares'][destino_id][ronda])
            renuncias = set(gestion_plazas['renuncias'][destino_id][ronda])
            efectivos_ronda = titulares - renuncias
            estudiantes_por_ronda[ronda] = list(efectivos_ronda)
        
        # Calcular estudiantes únicos finales (última aparición)
        estudiantes_finales = {}  # {estudiante_id: ultima_ronda}
        for ronda in ['1ª Adjudicación', '2ª Adjudicación', '3ª Adjudicación', 'Adjudicación Final']:
            for estudiante_id in estudiantes_por_ronda[ronda]:
                estudiantes_finales[estudiante_id] = ronda
        
        total_asignados_finales = len(estudiantes_finales)
        
        if total_asignados_finales > plazas_totales:
            exceso = total_asignados_finales - plazas_totales
            destinos_con_problemas += 1
            print(f"   ⚠️ Destino {destino_id}: {total_asignados_finales} asignados para {plazas_totales} plazas (exceso: {exceso})")
            
            # MEJORADO: Ordenar estudiantes por expediente (mantener los mejores)
            estudiantes_con_expediente = []
            for estudiante_id in estudiantes_finales.keys():
                # Buscar expediente del estudiante (simplificado: usar ID como proxy)
                estudiantes_con_expediente.append((estudiante_id, estudiante_id))  # (id, expediente_proxy)
            
            # Ordenar por "expediente" (ID como proxy) y mantener los primeros
            estudiantes_ordenados = sorted(estudiantes_con_expediente, key=lambda x: x[1])
            estudiantes_a_mantener = set([est[0] for est in estudiantes_ordenados[:plazas_totales]])
            estudiantes_a_remover = set([est[0] for est in estudiantes_ordenados[plazas_totales:]])
            
            # MEJORADO: Remover completamente a los estudiantes excesivos de TODAS las rondas
            for estudiante_id in estudiantes_a_remover:
                for ronda in ['1ª Adjudicación', '2ª Adjudicación', '3ª Adjudicación', 'Adjudicación Final']:
                    # Remover de titulares
                    if estudiante_id in gestion_plazas['asignaciones_titulares'][destino_id][ronda]:
                        gestion_plazas['asignaciones_titulares'][destino_id][ronda].remove(estudiante_id)
                        ajustes_realizados += 1
                    
                    # Remover de suplentes
                    if estudiante_id in gestion_plazas['asignaciones_suplentes'][destino_id][ronda]:
                        gestion_plazas['asignaciones_suplentes'][destino_id][ronda].remove(estudiante_id)
                    
                    # Remover de renuncias (si estaba ahí)
                    if estudiante_id in gestion_plazas['renuncias'][destino_id][ronda]:
                        gestion_plazas['renuncias'][destino_id][ronda].remove(estudiante_id)
    
    if ajustes_realizados > 0:
        print(f"   🔧 Se realizaron {ajustes_realizados} ajustes en {destinos_con_problemas} destinos")
    else:
        print(f"   ✅ No se requirieron ajustes")
    
    # NUEVO: Verificación post-ajuste
    print("🔍 Verificando ajustes realizados...")
    destinos_aun_problematicos = 0
    
    for _, destino in destinos_df.iterrows():
        destino_id = destino['DestinoID']
        plazas_totales = destino['NúmeroPlazas']
        
        if plazas_totales == 0:
            continue
        
        # Recalcular asignaciones finales
        estudiantes_finales_post = set()
        for ronda in ['1ª Adjudicación', '2ª Adjudicación', '3ª Adjudicación', 'Adjudicación Final']:
            titulares = set(gestion_plazas['asignaciones_titulares'][destino_id][ronda])
            renuncias = set(gestion_plazas['renuncias'][destino_id][ronda])
            efectivos = titulares - renuncias
            estudiantes_finales_post.update(efectivos)
        
        if len(estudiantes_finales_post) > plazas_totales:
            destinos_aun_problematicos += 1
            print(f"   ❌ Destino {destino_id} AÚN tiene problemas: {len(estudiantes_finales_post)} > {plazas_totales}")
    
    if destinos_aun_problematicos == 0:
        print(f"   ✅ Todos los destinos respetan ahora los límites de plazas")
    else:
        print(f"   ⚠️ {destinos_aun_problematicos} destinos aún tienen problemas")
    
    return gestion_plazas

# FUNCIÓN ELIMINADA: generar_eventlog_con_plazas
# Esta función tenía errores en el mapeo de actividades y duplicaba funcionalidad.
# Se mantiene la función generar_eventlog() original que ya está correctamente implementada.

def actualizar_estados_desde_gestion_plazas(estudiantes_df, gestion_plazas):
    """
    Actualiza los estados finales y destinos asignados basándose en la gestión real de plazas.
    """
    print("🔄 Actualizando estados finales desde gestión de plazas...")
    
    estudiantes_actualizado = estudiantes_df.copy()
    
    for idx, row in estudiantes_actualizado.iterrows():
        estudiante_id = row['EstudianteID']
        destino_solicitado = row['DestinoSolicitado']
        estado_original = row['EstadoFinal']
        
        # Verificar si el estudiante fue asignado como titular en alguna ronda EN CUALQUIER DESTINO
        fue_titular = False
        ronda_asignacion = None
        destino_final = None
        renuncio = False
        
        # CORRECCIÓN: Buscar en TODOS los destinos, no solo el solicitado
        for ronda in ['1ª Adjudicación', '2ª Adjudicación', '3ª Adjudicación', 'Adjudicación Final']:
            # Buscar en todos los destinos
            for destino_id in gestion_plazas['asignaciones_titulares']:
                titulares_ronda = gestion_plazas['asignaciones_titulares'][destino_id][ronda]
                renuncias_ronda = gestion_plazas['renuncias'][destino_id][ronda]
                
                if estudiante_id in titulares_ronda:
                    fue_titular = True
                    ronda_asignacion = ronda
                    destino_final = destino_id
                    
                    # Verificar si renunció
                    if estudiante_id in renuncias_ronda:
                        renuncio = True
                        # Si renunció, continuar buscando en rondas posteriores
                        # por si fue asignado de nuevo
                        destino_final = None
                    else:
                        # Si no renunció, este es su destino final
                        # Salir de ambos bucles
                        break
            
            # Si encontró asignación sin renuncia, salir del bucle de rondas
            if fue_titular and not renuncio:
                break
        
        # Determinar estado final basándose en la gestión de plazas
        if estado_original == 'Excluido':
            # Los excluidos siguen siendo excluidos
            nuevo_estado = 'Excluido'
            nuevo_destino = np.nan
        elif fue_titular and not renuncio:
            # Fue titular y no renunció = Aceptado
            nuevo_estado = 'Aceptado'
            nuevo_destino = destino_final
        elif fue_titular and renuncio:
            # CORRECCIÓN: Fue titular pero renunció = Renuncia SIN destino asignado
            nuevo_estado = 'Renuncia'
            nuevo_destino = np.nan  # Los que renuncian NO mantienen destino asignado
        else:
            # Nunca fue titular = No asignado
            nuevo_estado = 'No asignado'
            nuevo_destino = np.nan
        
        # Actualizar el DataFrame
        estudiantes_actualizado.at[idx, 'EstadoFinal'] = nuevo_estado
        estudiantes_actualizado.at[idx, 'DestinoAsignado'] = nuevo_destino
    
    return estudiantes_actualizado

def verificar_actualizacion_destinos(estudiantes_original, estudiantes_actualizado):
    """
    Función de depuración para verificar que la actualización de destinos funciona correctamente.
    """
    print("🔍 Verificando actualización de destinos asignados...")
    
    # Contar cambios
    cambios_estado = 0
    cambios_destino = 0
    destinos_asignados_nuevos = 0
    
    for idx, (orig, act) in enumerate(zip(estudiantes_original.iterrows(), estudiantes_actualizado.iterrows())):
        orig_row = orig[1]
        act_row = act[1]
        
        # Verificar cambios de estado
        if orig_row['EstadoFinal'] != act_row['EstadoFinal']:
            cambios_estado += 1
        
        # Verificar cambios de destino
        orig_destino = orig_row['DestinoAsignado']
        act_destino = act_row['DestinoAsignado']
        
        if pd.isna(orig_destino) != pd.isna(act_destino):
            if pd.isna(orig_destino) and not pd.isna(act_destino):
                destinos_asignados_nuevos += 1
            cambios_destino += 1
        elif not pd.isna(orig_destino) and not pd.isna(act_destino) and orig_destino != act_destino:
            cambios_destino += 1
    
    # Estadísticas finales
    total_aceptados = len(estudiantes_actualizado[estudiantes_actualizado['EstadoFinal'] == 'Aceptado'])
    total_con_destino = len(estudiantes_actualizado[estudiantes_actualizado['DestinoAsignado'].notna()])
    
    print(f"   📊 Cambios de estado: {cambios_estado}")
    print(f"   📊 Cambios de destino: {cambios_destino}")
    print(f"   📊 Nuevos destinos asignados: {destinos_asignados_nuevos}")
    print(f"   📊 Total estudiantes aceptados: {total_aceptados}")
    print(f"   📊 Total estudiantes con destino asignado: {total_con_destino}")
    
    # Verificar coherencia
    if total_aceptados != total_con_destino:
        print(f"   ⚠️ INCONSISTENCIA: {total_aceptados} aceptados pero {total_con_destino} con destino")
    else:
        print(f"   ✅ COHERENCIA: Todos los aceptados tienen destino asignado")
    
    return {
        'cambios_estado': cambios_estado,
        'cambios_destino': cambios_destino,
        'destinos_asignados_nuevos': destinos_asignados_nuevos,
        'total_aceptados': total_aceptados,
        'total_con_destino': total_con_destino
    }

def verificar_coherencia_plazas(destinos_df, gestion_plazas, estudiantes_df):
    """
    Verifica la coherencia entre el número de plazas disponibles y las asignaciones reales.
    """
    print("🔍 Verificando coherencia entre plazas disponibles y asignaciones...")
    
    total_plazas_disponibles = destinos_df['NúmeroPlazas'].sum()
    total_estudiantes_aceptados = len(estudiantes_df[estudiantes_df['EstadoFinal'] == 'Aceptado'])
    
    print(f"   📊 Total plazas disponibles en destinos: {total_plazas_disponibles}")
    print(f"   📊 Total estudiantes aceptados: {total_estudiantes_aceptados}")
    
    # Contar asignaciones reales por ronda
    asignaciones_por_ronda = {}
    for ronda in ['1ª Adjudicación', '2ª Adjudicación', '3ª Adjudicación', 'Adjudicación Final']:
        total_asignados = 0
        total_renuncias = 0
        
        for destino_id in gestion_plazas['asignaciones_titulares']:
            titulares = len(gestion_plazas['asignaciones_titulares'][destino_id][ronda])
            renuncias = len(gestion_plazas['renuncias'][destino_id][ronda])
            total_asignados += titulares
            total_renuncias += renuncias
        
        asignaciones_por_ronda[ronda] = {
            'asignados': total_asignados,
            'renuncias': total_renuncias,
            'efectivos': total_asignados - total_renuncias
        }
        
        print(f"   📋 {ronda}: {total_asignados} asignados, {total_renuncias} renuncias, {total_asignados - total_renuncias} efectivos")
    
    # CORRECCIÓN: Verificar destinos con sobreasignación (método corregido)
    destinos_problematicos = []
    for _, destino in destinos_df.iterrows():
        destino_id = destino['DestinoID']
        plazas_totales = destino['NúmeroPlazas']
        
        # CORRECCIÓN: Contar estudiantes únicos asignados finalmente (sin renuncias)
        estudiantes_asignados_finales = set()
        
        for ronda in ['1ª Adjudicación', '2ª Adjudicación', '3ª Adjudicación', 'Adjudicación Final']:
            titulares = set(gestion_plazas['asignaciones_titulares'][destino_id][ronda])
            renuncias = set(gestion_plazas['renuncias'][destino_id][ronda])
            efectivos_ronda = titulares - renuncias
            estudiantes_asignados_finales.update(efectivos_ronda)
        
        total_asignados_unicos = len(estudiantes_asignados_finales)
        if total_asignados_unicos > plazas_totales:
            destinos_problematicos.append({
                'destino_id': destino_id,
                'plazas_totales': plazas_totales,
                'asignaciones_finales': total_asignados_unicos,
                'exceso': total_asignados_unicos - plazas_totales
            })
    
    if destinos_problematicos:
        print(f"   ⚠️ PROBLEMA: {len(destinos_problematicos)} destinos con sobreasignación:")
        for problema in destinos_problematicos[:5]:  # Mostrar solo los primeros 5
            print(f"      - Destino {problema['destino_id']}: {problema['plazas_totales']} plazas, {problema['asignaciones_finales']} asignados (exceso: {problema['exceso']})")
    else:
        print(f"   ✅ No hay destinos con sobreasignación")
    
    return {
        'total_plazas_disponibles': total_plazas_disponibles,
        'total_estudiantes_aceptados': total_estudiantes_aceptados,
        'asignaciones_por_ronda': asignaciones_por_ronda,
        'destinos_problematicos': destinos_problematicos
    }

def generar_reporte_gestion_plazas(gestion_plazas, destinos_df, estudiantes_df):
    """
    Genera un reporte detallado de la gestión de plazas por destino y ronda.
    """
    print("📊 Generando reporte de gestión de plazas...")
    
    reporte = []
    
    for destino_id in gestion_plazas['plazas_disponibles']:
        destino_info = destinos_df[destinos_df['DestinoID'] == destino_id].iloc[0]
        nombre_destino = destino_info['NombreDestino']
        plazas_totales = destino_info['NúmeroPlazas']
        
        for ronda in ['1ª Adjudicación', '2ª Adjudicación', '3ª Adjudicación', 'Adjudicación Final']:
            titulares = gestion_plazas['asignaciones_titulares'][destino_id][ronda]
            suplentes = gestion_plazas['asignaciones_suplentes'][destino_id][ronda]
            renuncias = gestion_plazas['renuncias'][destino_id][ronda]
            plazas_disponibles = gestion_plazas['plazas_disponibles'][destino_id][ronda]
            
            # Calcular estadísticas
            num_titulares = len(titulares)
            num_suplentes = len(suplentes)
            num_renuncias = len(renuncias)
            total_candidatos = num_titulares + num_suplentes
            tasa_ocupacion = (num_titulares / plazas_totales * 100) if plazas_totales > 0 else 0
            tasa_renuncia = (num_renuncias / num_titulares * 100) if num_titulares > 0 else 0
            
            reporte.append({
                'DestinoID': destino_id,
                'NombreDestino': nombre_destino,
                'Ronda': ronda,
                'PlazasTotales': plazas_totales,
                'PlazasDisponibles': plazas_disponibles,
                'NumTitulares': num_titulares,
                'NumSuplentes': num_suplentes,
                'NumRenuncias': num_renuncias,
                'TotalCandidatos': total_candidatos,
                'TasaOcupacion': round(tasa_ocupacion, 2),
                'TasaRenuncia': round(tasa_renuncia, 2),
                'Competitividad': 'Alta' if total_candidatos > plazas_totales * 2 else 'Media' if total_candidatos > plazas_totales else 'Baja'
            })
    
    reporte_df = pd.DataFrame(reporte)
    return reporte_df

def validar_coherencia_temporal_destinos(estudiantes_df, destinos_df):
    """
    Valida que no haya estudiantes solicitando destinos que ya estaban cancelados
    en su fecha de solicitud.
    """
    print("🕐 Validando coherencia temporal entre solicitudes y cancelaciones...")
    
    inconsistencias_temporales = []
    
    for _, estudiante in estudiantes_df.iterrows():
        estudiante_id = estudiante['EstudianteID']
        destino_solicitado = estudiante['DestinoSolicitado']
        fecha_solicitud = datetime.strptime(estudiante['FechaSolicitud'], '%Y-%m-%d')
        
        # Buscar información del destino solicitado
        destino_info = destinos_df[destinos_df['DestinoID'] == destino_solicitado]
        
        if len(destino_info) > 0:
            destino_info = destino_info.iloc[0]
            cancelado = destino_info['Cancelado'] == 'Sí'
            fecha_cancelacion_str = destino_info['FechaCancelación']
            
            if cancelado and fecha_cancelacion_str:
                try:
                    fecha_cancelacion = datetime.strptime(fecha_cancelacion_str, '%Y-%m-%d')
                    
                    # Verificar si el estudiante solicitó después de la cancelación
                    if fecha_solicitud >= fecha_cancelacion:
                        inconsistencias_temporales.append(
                            f"Estudiante {estudiante_id}: Solicitó destino {destino_solicitado} "
                            f"el {fecha_solicitud.strftime('%Y-%m-%d')} pero fue cancelado "
                            f"el {fecha_cancelacion.strftime('%Y-%m-%d')}"
                        )
                except ValueError:
                    # Error en formato de fecha
                    inconsistencias_temporales.append(
                        f"Estudiante {estudiante_id}: Destino {destino_solicitado} "
                        f"tiene fecha de cancelación inválida: {fecha_cancelacion_str}"
                    )
    
    if inconsistencias_temporales:
        print(f"   ⚠️ Se encontraron {len(inconsistencias_temporales)} inconsistencias temporales:")
        for inc in inconsistencias_temporales[:5]:  # Mostrar solo las primeras 5
            print(f"      - {inc}")
        if len(inconsistencias_temporales) > 5:
            print(f"      ... y {len(inconsistencias_temporales) - 5} más.")
    else:
        print(f"   ✅ No se encontraron inconsistencias temporales")
    
    return inconsistencias_temporales

def validar_requisitos_idioma(estudiante_info, destino_info):
    """
    Valida si un estudiante cumple los requisitos de idioma para un destino específico.
    """
    if destino_info['RequiereIdioma'] == 'No':
        return True  # No hay requisitos de idioma
    
    # Simular que el 85% de los estudiantes cumplen los requisitos de idioma
    # En un sistema real, esto se basaría en certificaciones reales
    return random.random() < 0.85

def aplicar_filtros_elegibilidad(estudiantes_elegibles, destinos_df):
    """
    Aplica filtros de elegibilidad incluyendo requisitos de idioma.
    """
    estudiantes_filtrados = []
    
    for estudiante in estudiantes_elegibles:
        destino_id = estudiante['destino_solicitado']
        destino_info = destinos_df[destinos_df['DestinoID'] == destino_id].iloc[0]
        
        # Validar requisitos de idioma
        if validar_requisitos_idioma(estudiante, destino_info):
            estudiantes_filtrados.append(estudiante)
        # Si no cumple requisitos de idioma, el estudiante queda excluido automáticamente
    
    return estudiantes_filtrados

# ---- Constantes globales ----
RONDAS = ["1ª Adjudicación", "2ª Adjudicación", "3ª Adjudicación", "Adjudicación Final"]
RONDA_A_ACTIVIDAD = {
    "1ª Adjudicación": 10, "2ª Adjudicación": 14,
    "3ª Adjudicación": 18, "Adjudicación Final": 22
}
FECHAS_PUBLICACION = {
    6: datetime(2022, 12, 12, 0, 1, 0),   # Pub Provisional
    10: datetime(2023, 1, 11, 0, 1, 0),   # Pub 1ª Adj
    14: datetime(2023, 1, 19, 0, 1, 0),   # Pub 2ª Adj
    18: datetime(2023, 1, 25, 0, 1, 0),   # Pub 3ª Adj
    22: datetime(2023, 2, 1, 0, 1, 0),    # Pub Definitiva
}

def verificar_coherencia_final_plazas_estudiantes(destinos_df, estudiantes_df, gestion_plazas):
    """
    Verifica la coherencia final entre el número total de plazas disponibles 
    y el número de estudiantes que finalmente van de Erasmus.
    """
    print("🔍 Verificando coherencia final entre plazas y estudiantes...")
    
    # Calcular plazas totales disponibles
    total_plazas_disponibles = destinos_df['NúmeroPlazas'].sum()
    destinos_activos = len(destinos_df[destinos_df['NúmeroPlazas'] > 0])
    destinos_cancelados = len(destinos_df[destinos_df['NúmeroPlazas'] == 0])
    
    # Calcular estudiantes finales por estado
    estudiantes_aceptados = len(estudiantes_df[estudiantes_df['EstadoFinal'] == 'Aceptado'])
    estudiantes_con_destino = len(estudiantes_df[estudiantes_df['DestinoAsignado'].notna()])
    estudiantes_renuncias = len(estudiantes_df[estudiantes_df['EstadoFinal'] == 'Renuncia'])
    estudiantes_no_asignados = len(estudiantes_df[estudiantes_df['EstadoFinal'] == 'No asignado'])
    estudiantes_excluidos = len(estudiantes_df[estudiantes_df['EstadoFinal'] == 'Excluido'])
    
    # Calcular asignaciones reales desde gestión de plazas
    asignaciones_reales_finales = 0
    for destino_id in gestion_plazas['asignaciones_titulares']:
        estudiantes_finales_destino = set()
        for ronda in ['1ª Adjudicación', '2ª Adjudicación', '3ª Adjudicación', 'Adjudicación Final']:
            titulares = set(gestion_plazas['asignaciones_titulares'][destino_id][ronda])
            renuncias = set(gestion_plazas['renuncias'][destino_id][ronda])
            efectivos = titulares - renuncias
            estudiantes_finales_destino.update(efectivos)
        asignaciones_reales_finales += len(estudiantes_finales_destino)
    
    # Calcular tasas
    tasa_ocupacion = (estudiantes_aceptados / total_plazas_disponibles * 100) if total_plazas_disponibles > 0 else 0
    tasa_participacion = (estudiantes_aceptados / NUM_ESTUDIANTES * 100)
    
    # Mostrar estadísticas
    print(f"   📊 PLAZAS DISPONIBLES:")
    print(f"      • Total plazas: {total_plazas_disponibles}")
    print(f"      • Destinos activos: {destinos_activos}")
    print(f"      • Destinos cancelados: {destinos_cancelados}")
    
    print(f"   📊 ESTUDIANTES FINALES:")
    print(f"      • Total estudiantes: {NUM_ESTUDIANTES}")
    print(f"      • Aceptados: {estudiantes_aceptados}")
    print(f"      • Con destino asignado: {estudiantes_con_destino}")
    print(f"      • Renuncias: {estudiantes_renuncias}")
    print(f"      • No asignados: {estudiantes_no_asignados}")
    print(f"      • Excluidos: {estudiantes_excluidos}")
    
    print(f"   📊 COHERENCIA:")
    print(f"      • Tasa de ocupación: {tasa_ocupacion:.1f}% ({estudiantes_aceptados}/{total_plazas_disponibles})")
    print(f"      • Tasa de participación: {tasa_participacion:.1f}% ({estudiantes_aceptados}/{NUM_ESTUDIANTES})")
    print(f"      • Asignaciones reales (gestión): {asignaciones_reales_finales}")
    
    # Verificar coherencias
    coherencias = []
    if estudiantes_aceptados != estudiantes_con_destino:
        coherencias.append(f"❌ Estudiantes aceptados ({estudiantes_aceptados}) ≠ Con destino ({estudiantes_con_destino})")
    else:
        coherencias.append(f"✅ Estudiantes aceptados = Con destino asignado")
    
    if estudiantes_aceptados != asignaciones_reales_finales:
        coherencias.append(f"❌ Estudiantes aceptados ({estudiantes_aceptados}) ≠ Asignaciones reales ({asignaciones_reales_finales})")
    else:
        coherencias.append(f"✅ Estudiantes aceptados = Asignaciones reales")
    
    if estudiantes_aceptados > total_plazas_disponibles:
        coherencias.append(f"❌ Más estudiantes aceptados ({estudiantes_aceptados}) que plazas disponibles ({total_plazas_disponibles})")
    else:
        coherencias.append(f"✅ Estudiantes aceptados ≤ Plazas disponibles")
    
    # Verificar distribución realista
    if tasa_ocupacion > 95:
        coherencias.append(f"⚠️ Tasa de ocupación muy alta ({tasa_ocupacion:.1f}%) - Poco realista")
    elif tasa_ocupacion < 70:
        coherencias.append(f"⚠️ Tasa de ocupación baja ({tasa_ocupacion:.1f}%) - Revisar demanda")
    else:
        coherencias.append(f"✅ Tasa de ocupación realista ({tasa_ocupacion:.1f}%)")
    
    print(f"   📋 VERIFICACIONES:")
    for coherencia in coherencias:
        print(f"      {coherencia}")
    
    return {
        'total_plazas': total_plazas_disponibles,
        'estudiantes_aceptados': estudiantes_aceptados,
        'tasa_ocupacion': tasa_ocupacion,
        'tasa_participacion': tasa_participacion,
        'coherencias': coherencias
    }

# ---- Ejecución principal ----
if __name__ == "__main__":
    print("🚀 Iniciando generación de datos Erasmus con coordinación mejorada...")

    destinos = generar_destinos(NUM_DESTINOS)
    estudiantes = generar_estudiantes(NUM_ESTUDIANTES, destinos)
    actividades = generar_actividades()

    # Generamos alegaciones PRIMERO para obtener los IDs correspondientes
    alegaciones, estudiantes_con_alegaciones_ids = generar_alegaciones(estudiantes)

    # PASO 1: Simular adjudicación con control de plazas
    print("🎯 Simulando proceso de adjudicación con control de plazas...")
    gestion_plazas = simular_adjudicacion_con_plazas(estudiantes, destinos)
    
    # PASO 1.5: Ajustar asignaciones para respetar límites de plazas
    gestion_plazas = ajustar_asignaciones_por_plazas(gestion_plazas, destinos)

    # PASO 2: Generar EventLog como fuente de verdad (CORREGIDO: usar función original)
    print("📊 Generando EventLog como fuente de verdad...")
    eventlog = generar_eventlog(estudiantes, actividades, destinos, estudiantes_con_alegaciones_ids)

    # PASO 2.5: Actualizar estados finales basándose en gestión de plazas
    print("🔄 Actualizando estados finales desde gestión de plazas...")
    estudiantes_original = estudiantes.copy()  # Guardar copia para verificación
    estudiantes = actualizar_estados_desde_gestion_plazas(estudiantes, gestion_plazas)
    
    # Verificar que la actualización funcionó correctamente
    verificar_actualizacion_destinos(estudiantes_original, estudiantes)
    
    # Verificar coherencia entre plazas y asignaciones
    verificar_coherencia_plazas(destinos, gestion_plazas, estudiantes)

    # PASO 3: Extraer histórico coherente desde gestión de plazas
    print("📋 Extrayendo histórico de adjudicaciones desde gestión de plazas...")
    historico = extraer_historico_desde_gestion_plazas(gestion_plazas, eventlog)

    # PASO 3.5: Sincronizar fechas entre histórico y EventLog
    historico = sincronizar_fechas_historico_eventlog(historico, eventlog)

    # PASO 3.6: Sincronizar fechas de alegaciones con EventLog
    print("🔄 Sincronizando fechas de alegaciones con EventLog...")
    alegaciones = sincronizar_alegaciones_eventlog(alegaciones, eventlog)

    # PASO 4: Generar reporte de gestión de plazas
    print("📊 Generando reporte de gestión de plazas...")
    reporte_plazas = generar_reporte_gestion_plazas(gestion_plazas, destinos, estudiantes)

    # PASO 5: Validar coherencia entre todas las fuentes
    print("✅ Validando coherencia entre fuentes de datos...")
    inconsistencias = validar_coherencia_datos(estudiantes, eventlog, historico)
    
    # PASO 5.5: Validar coherencia temporal de destinos
    inconsistencias_temporales = validar_coherencia_temporal_destinos(estudiantes, destinos)
    inconsistencias.extend(inconsistencias_temporales)

    # PASO 6: Verificar coherencia final entre plazas y estudiantes
    print("🔍 Verificando coherencia final del sistema...")
    coherencia_final = verificar_coherencia_final_plazas_estudiantes(destinos, estudiantes, gestion_plazas)

    # --- Corrección de Tipos de Datos antes de Guardar ---
    # Convertir DestinoAsignado a tipo Int64 nullable de pandas para permitir NaN pero ser entero
    estudiantes['DestinoAsignado'] = estudiantes['DestinoAsignado'].astype(pd.Int64Dtype())
    historico['DestinoID'] = historico['DestinoID'].astype(pd.Int64Dtype()) # También en histórico por consistencia

    # Guardar todos los CSVs
    print("💾 Guardando archivos CSV...")
    destinos.to_csv(f"{RUTA_DATA}/Destinos.csv", index=False)
    estudiantes.to_csv(f"{RUTA_DATA}/Estudiantes.csv", index=False)
    actividades.to_csv(f"{RUTA_DATA}/Actividades.csv", index=False)
    eventlog.to_csv(f"{RUTA_DATA}/EventLog.csv", index=False)
    alegaciones.to_csv(f"{RUTA_DATA}/Alegaciones.csv", index=False)
    historico.to_csv(f"{RUTA_DATA}/HistoricoAdjudicaciones.csv", index=False)
    reporte_plazas.to_csv(f"{RUTA_DATA}/ReporteGestionPlazas.csv", index=False)

    # Guardar reporte de validación
    if inconsistencias:
        with open(f"{RUTA_DATA}/reporte_inconsistencias.txt", "w", encoding="utf-8") as f:
            f.write("REPORTE DE INCONSISTENCIAS\n")
            f.write("=" * 50 + "\n\n")
            for inc in inconsistencias:
                f.write(f"- {inc}\n")
        print(f"⚠️ Se guardó reporte de inconsistencias en {RUTA_DATA}/reporte_inconsistencias.txt")

    print(f"\n✅ Generación de CSVs Erasmus COMPLETADA con coordinación mejorada.")
    print(f"📈 Resumen: {len(inconsistencias)} inconsistencias detectadas y reportadas.")
