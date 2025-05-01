import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta, time

from llm_helpers import get_universities, get_alegation_motives, get_process_patterns

# ---- Configuración general ----
NUM_ESTUDIANTES = 2107
NUM_DESTINOS = 372
PCT_ESTUDIANTES_CON_ALEGACIONES = 0.175
RUTA_DATA = "data"
USE_LLM = True  # <<--- Activa o desactiva llamadas a LLM

# Crear carpeta data si no existe
os.makedirs(RUTA_DATA, exist_ok=True)

# ---- Plazos Clave (Curso 23-24 de ejemplo) ----
PLAZOS = {
    # ID Actividad: (Fecha Inicio Plazo, Fecha Fin Plazo)
    # -- IDs Nuevos (Original - 1, IDs >=2) --
    # Actividad "Inscripción Programa Erasmus Registrada" (Original ID 5) -> Nuevo ID 4
    4: (datetime(2022, 11, 2), datetime(2022, 11, 30)),
    # Actividad "Alegación Presentada" (Original ID 8) -> Nuevo ID 7
    7: (datetime(2022, 12, 12), datetime(2022, 12, 27)),
    # Actividad "Respuesta Recibida (Aceptación/Reserva 1ª Adj.)" (Original ID 12) -> Nuevo ID 11
    11: (datetime(2023, 1, 11), datetime(2023, 1, 17)),
    # Actividad "Respuesta Recibida (Renuncia 1ª Adj.)" (Original ID 13) -> Nuevo ID 12
    12: (datetime(2023, 1, 11), datetime(2023, 1, 17)),
    # Actividad "Respuesta Recibida (Aceptación/Reserva 2ª Adj.)" (Original ID 16) -> Nuevo ID 15
    15: (datetime(2023, 1, 19), datetime(2023, 1, 23)),
    # Actividad "Respuesta Recibida (Renuncia 2ª Adj.)" (Original ID 17) -> Nuevo ID 16
    16: (datetime(2023, 1, 19), datetime(2023, 1, 23)),
    # Actividad "Respuesta Recibida (Aceptación/Reserva 3ª Adj.)" (Original ID 20) -> Nuevo ID 19
    19: (datetime(2023, 1, 25), datetime(2023, 1, 30)),
    # Actividad "Respuesta Recibida (Renuncia 3ª Adj.)" (Original ID 21) -> Nuevo ID 20
    20: (datetime(2023, 1, 25), datetime(2023, 1, 30)),
}

# ---- Funciones Auxiliares ----
def generar_hora_realista():
    """Genera una hora del día, priorizando 08:00-23:59 con excepciones raras."""
    prob_horas_normales = 0.95 # 95% de probabilidad de horas "normales"

    if random.random() < prob_horas_normales:
        # Horas normales (08:00 - 23:59)
        hora = random.randint(8, 23)
    else:
        # Horas raras (00:00 - 07:59)
        hora = random.randint(0, 7)
    
    minuto = random.randint(0, 59)
    segundo = random.randint(0, 59)
    return time(hora, minuto, segundo)

def generar_timestamp_en_plazo(inicio_plazo, fin_plazo, fecha_evento_anterior):
    """Genera un timestamp dentro de un plazo con picos al inicio/final."""
    # Asegurar que las fechas son solo date para el cálculo de días
    inicio_plazo_dt = inicio_plazo.date()
    fin_plazo_dt = fin_plazo.date()
    fecha_evento_anterior_dt = fecha_evento_anterior.date()

    # El inicio efectivo no puede ser anterior al evento previo
    inicio_efectivo_dt = max(inicio_plazo_dt, fecha_evento_anterior_dt)

    # Si el inicio efectivo ya supera el fin del plazo, devolver fin_plazo como fallback
    if inicio_efectivo_dt > fin_plazo_dt:
        # Añadir un tiempo aleatorio realista al día final
        hora_aleatoria = generar_hora_realista()
        return datetime.combine(fin_plazo_dt, hora_aleatoria)

    # Calcular días disponibles
    dias_disponibles = (fin_plazo_dt - inicio_efectivo_dt).days + 1
    fechas_posibles = [inicio_efectivo_dt + timedelta(days=i) for i in range(dias_disponibles)]

    pesos = []
    peso_pico = 5 # Mayor peso para los días pico
    peso_normal = 1 # Peso normal para el resto

    if dias_disponibles <= 4: # Si el plazo es muy corto, peso uniforme
        pesos = [peso_normal] * dias_disponibles
    else:
        for i in range(dias_disponibles):
            if i < 2 or i >= dias_disponibles - 2: # Primeros 2 días o últimos 2 días
                pesos.append(peso_pico)
            else:
                pesos.append(peso_normal)

    # Seleccionar fecha basada en pesos
    fecha_seleccionada = random.choices(fechas_posibles, weights=pesos, k=1)[0]

    # Generar hora realista
    hora_aleatoria = generar_hora_realista()
    timestamp_final = datetime.combine(fecha_seleccionada, hora_aleatoria)

    # Asegurar que el timestamp final no es anterior al evento anterior + 1 segundo
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

    # Eliminamos la ponderación de países aquí, ya que viene del LLM (o fallback)
    # paises_ponderados = { ... }
    # lista_paises = list(paises_ponderados.keys())
    # pesos_paises = list(paises_ponderados.values())

    destinos = []
    # Iterar sobre las universidades *realmente generadas*
    for i, (nombre, pais) in enumerate(universidades_con_pais, start=1):
        # Usamos nombre y país directamente de la enumeración
        # 'i' ya es el ID basado en 1

        plazas = random.randint(1, 5)
        cancelado_bool = random.random() < 0.05 # ~5% de destinos cancelados
        cancelado = "Sí" if cancelado_bool else "No"
        
        # Fecha de cancelación ANTES del listado provisional (si está cancelado)
        fecha_cancelacion = ""
        if cancelado_bool:
            inicio_solicitudes = datetime(2022, 11, 2)
            pub_provisional = datetime(2022, 12, 12)
            delta_cancelacion = pub_provisional - inicio_solicitudes
            # Asegurarse de que el rango para randint es válido
            if delta_cancelacion.days > 16:
                dias_random_cancelacion = random.randint(15, delta_cancelacion.days - 1)
                fecha_cancelacion_dt = inicio_solicitudes + timedelta(days=dias_random_cancelacion)
                fecha_cancelacion = fecha_cancelacion_dt.strftime('%Y-%m-%d')
            else: # Si el periodo es muy corto, cancelar en un día intermedio
                fecha_cancelacion_dt = inicio_solicitudes + timedelta(days=delta_cancelacion.days // 2)
                fecha_cancelacion = fecha_cancelacion_dt.strftime('%Y-%m-%d')
            
        # --- Añadir columna RequiereIdioma ---
        requiere_idioma = random.random() < 0.65 # Aproximadamente 65% requieren idioma
        
        destinos.append([i, nombre, pais, plazas, cancelado, fecha_cancelacion, requiere_idioma])
    
    # Advertencia si el número generado es menor que el solicitado
    if len(universidades_con_pais) < num_destinos:
        print(f"⚠️ Advertencia: Se solicitaron {num_destinos} destinos, pero solo se generaron {len(universidades_con_pais)}. Se usarán solo los generados.")
        
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
    pesos_estados = [70, 15, 10, 5] # Ponderamos también los estados finales

    for i in range(1, num_estudiantes + 1):
        # Elegimos grado según la ponderación
        grado = random.choices(lista_grados, weights=pesos_grados, k=1)[0]
        sexo = random.choice(["M", "F"])
        expediente = round(random.uniform(5.0, 10.0), 1)
        # Fecha de solicitud dentro del plazo de INSCRIPCIÓN (Actividad 5)
        fecha_solicitud_dt = generar_timestamp_en_plazo(
            PLAZOS[4][0], PLAZOS[4][1], PLAZOS[4][0] - timedelta(days=1)
        )
        fecha_solicitud = fecha_solicitud_dt.strftime('%Y-%m-%d')
        destino_solicitado = random.choice(destinos_df["DestinoID"].tolist())

        # --- Lógica Destino Asignado y Estado Final (Revisada) ---
        estado_final = random.choices(estados_finales, weights=pesos_estados, k=1)[0]
        destino_asignado = np.nan # Por defecto

        if estado_final == "Aceptado":
            # Más probable obtener el solicitado, pero posible obtener otro
            if random.random() < 0.8: # 80% de prob. de obtener el solicitado si es aceptado
                destino_asignado = destino_solicitado
            else:
                posibles_alternativos = destinos_df[destinos_df["DestinoID"] != destino_solicitado]["DestinoID"].tolist()
                if posibles_alternativos:
                    destino_asignado = random.choice(posibles_alternativos)
                else: # Si solo había un destino, se asigna ese
                    destino_asignado = destino_solicitado
            # Si por alguna razón quedó NaN, forzar el solicitado
            if pd.isna(destino_asignado):
                destino_asignado = destino_solicitado

        elif estado_final == "Renuncia":
            # Si renuncia, usualmente tuvo una asignación (podría ser la solicitada u otra)
             if random.random() < 0.7: # 70% prob. que fuera el solicitado al que renuncia
                 destino_asignado = destino_solicitado
             else:
                posibles_alternativos = destinos_df[destinos_df["DestinoID"] != destino_solicitado]["DestinoID"].tolist()
                if posibles_alternativos:
                    destino_asignado = random.choice(posibles_alternativos)
                else:
                    destino_asignado = destino_solicitado
             # Mantenemos el DestinoAsignado aunque renuncie, para el histórico

        # Para 'No asignado' o 'Excluido', destino_asignado permanece np.nan (definido al inicio)

        estudiantes.append([i, grado, sexo, expediente, fecha_solicitud, destino_solicitado, destino_asignado, estado_final])
    return pd.DataFrame(estudiantes, columns=["EstudianteID", "Grado", "Sexo", "Expediente", "FechaSolicitud", "DestinoSolicitado", "DestinoAsignado", "EstadoFinal"])

def generar_actividades():
    # Los IDs se reajustan para empezar en 1. El OrdenSecuencial también se ajusta.
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

def generar_eventlog(estudiantes_df, actividades_df, destinos_df, estudiantes_con_alegaciones_ids):
    eventos = []
    actividad_actor_map = dict(zip(actividades_df["ActividadID"], actividades_df["ActorDefecto"]))

    # Obtener IDs y fechas de destinos cancelados tempranamente
    destinos_cancelados_df = destinos_df[destinos_df['Cancelado'] == 'Sí'].copy()
    # Convertir fecha cancelación a datetime si no está vacía y es válida
    destinos_cancelados_df['FechaCancelacion_dt'] = pd.to_datetime(destinos_cancelados_df['FechaCancelación'], errors='coerce')
    # Filtrar cancelaciones tempranas (antes de 1ª adj, ej. antes de 01/01/2023)
    destinos_cancelados_temprano = destinos_cancelados_df.dropna(subset=['FechaCancelacion_dt']).set_index('DestinoID')
    mapa_fechas_cancelacion = destinos_cancelados_temprano['FechaCancelacion_dt'].to_dict()
    ids_destinos_cancelados_temprano = set(mapa_fechas_cancelacion.keys())

    # --- Rutas de actividades (ACTUALIZADAS con IDs renumerados desde 1) ---
    rutas_base = {
        # ESTADO FINAL: ACEPTADO
        "Aceptado": [
            # --- CON IDIOMA (Rutas con 1 y 3, 3 antes de 4) ---
            # Idioma OK (1->3), Sin Alegación, Acepta 1ª, LA OK
            [1, 3, 4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32],
            # Idioma OK (1->3), Sin Alegación, Renuncia 1ª, Acepta 2ª, LA OK
            [1, 3, 4, 5, 6, 10, 12, 13, 14, 15, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32],
            # Idioma OK (1->3), Sin Alegación, Renuncia 1ª/2ª, Acepta 3ª, LA OK
            [1, 3, 4, 5, 6, 10, 12, 13, 14, 16, 17, 18, 19, 22, 23, 24, 25, 27, 28, 29, 31, 32],
            # Idioma REINTENTO (1->2->1->3), Sin Alegación, Acepta 1ª, LA OK
            [1, 2, 1, 3, 4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32],
            
            # --- SIN IDIOMA (Rutas sin 1, 2, 3) ---
            # Sin Idioma, Sin Alegación, Acepta 1ª, LA OK
            [4, 5, 6, 10, 11, 14, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32],
            # Sin Idioma, Sin Alegación, Renuncia 1ª, Acepta 2ª, LA OK
            [4, 5, 6, 10, 12, 13, 14, 15, 18, 22, 23, 24, 25, 27, 28, 29, 31, 32],
            # Sin Idioma, Sin Alegación, Renuncia 1ª/2ª, Acepta 3ª, LA OK
            [4, 5, 6, 10, 12, 13, 14, 16, 17, 18, 19, 22, 23, 24, 25, 27, 28, 29, 31, 32],
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

    # --- Definir fechas fijas para publicaciones --- 
    FECHAS_PUBLICACION = {
        6: datetime(2022, 12, 12, 0, 1, 0), # Pub Provisional (Inicio plazo Alegaciones ID 7)
        10: datetime(2023, 1, 11, 0, 1, 0), # Pub 1ª Adj (Inicio plazo Respuesta 1ª ID 11)
        14: datetime(2023, 1, 19, 0, 1, 0), # Pub 2ª Adj (Inicio plazo Respuesta 2ª ID 15)
        18: datetime(2023, 1, 25, 0, 1, 0), # Pub 3ª Adj (Inicio plazo Respuesta 3ª ID 19)
        22: datetime(2023, 2, 1, 0, 1, 0),  # Pub Definitiva
    }

    for idx, row in estudiantes_df.iterrows():
        estudiante_id = row["EstudianteID"]
        fecha_evento_anterior_base = datetime.strptime(row["FechaSolicitud"], '%Y-%m-%d')
        fecha_evento_anterior = datetime.combine(fecha_evento_anterior_base.date(), generar_hora_realista())
        estado_final = row["EstadoFinal"]
        destino_solicitado = row["DestinoSolicitado"]
        destino_asignado_final = row["DestinoAsignado"]
        id_destino_log = destino_asignado_final if not pd.isna(destino_asignado_final) else destino_solicitado
        if pd.isna(id_destino_log): id_destino_log = random.choice(destinos_df["DestinoID"].tolist())

        ruta_seleccionada = None
        fecha_cancelacion_destino = None
        requiere_idioma = False # Valor por defecto

        # --- Obtener si el destino SOLICITADO requiere idioma ---
        try:
            destino_info = destinos_df.loc[destinos_df['DestinoID'] == destino_solicitado].iloc[0]
            requiere_idioma = destino_info['RequiereIdioma']
        except IndexError:
            print(f"⚠️ Advertencia: No se encontró información del destino {destino_solicitado} para Estudiante {estudiante_id}. Asumiendo que NO requiere idioma.")

        # --- Comprobar si el DESTINO SOLICITADO fue cancelado tempranamente (ACTUALIZADO) ---
        if destino_solicitado in ids_destinos_cancelados_temprano:
            print(f"ℹ️ Estudiante {estudiante_id}: Destino solicitado {destino_solicitado} cancelado tempranamente.")
            fecha_cancelacion_destino = mapa_fechas_cancelacion[destino_solicitado]
            # Seleccionar ruta de cancelación basada en si requería idioma
            if requiere_idioma:
                # ¿Tuvo tiempo de ser rechazado antes de cancelar?
                # Simplificación: Si cancela pronto, asumimos rechazo. Si tarda, asumimos OK.
                pub_provisional = datetime(2022, 12, 12) # Fecha ref. para "tarde"
                if fecha_cancelacion_destino < pub_provisional:
                    ruta_seleccionada = rutas_cancelacion["idioma_rechazo"] # [1, 2, 33]
                else:
                    # Podría ser ok o reintento ok, elegimos aleatoriamente
                    ruta_seleccionada = random.choice([
                        rutas_cancelacion["con_idioma"], # [1, 3, 4, 5, 6, 10, 33]
                        rutas_cancelacion["idioma_reintento_ok"] #[1, 2, 1, 3, 4, 33]
                    ])
            else:
                 ruta_seleccionada = rutas_cancelacion["sin_idioma"] # [4, 5, 6, 10, 33]
            
            # estado_final = "No asignado" # Opcional: forzar estado

        # --- Si no hay cancelación temprana, proceder con la lógica normal (ACTUALIZADA) --- 
        if ruta_seleccionada is None:
            # 1. Obtener todas las rutas posibles para el estado final del estudiante
            lista_rutas_estado = rutas_completas_por_estado.get(estado_final, rutas_default)
            if not lista_rutas_estado: lista_rutas_estado = rutas_default # Fallback

            # 2. Filtrar por requerimiento de idioma
            rutas_filtradas_idioma = []
            if requiere_idioma:
                # Seleccionar rutas que SÍ contienen pasos de idioma (empiezan con 1 o tienen [..., 1, 2, ...])
                rutas_filtradas_idioma = [r for r in lista_rutas_estado if r and (r[0] == 1 or (1 in r and 2 in r))]
            else:
                # Seleccionar rutas que NO contienen pasos de idioma (1, 2, 3)
                rutas_filtradas_idioma = [r for r in lista_rutas_estado if r and not any(act_id in r for act_id in [1, 2, 3])]

            # 3. Filtrar por alegaciones
            tiene_alegacion = estudiante_id in estudiantes_con_alegaciones_ids
            rutas_filtradas_final = []
            if tiene_alegacion:
                # Solo rutas (ya filtradas por idioma) que contengan la secuencia de alegación (7, 8, 9)
                rutas_filtradas_final = [r for r in rutas_filtradas_idioma if 7 in r and 8 in r and 9 in r]
            else:
                # Solo rutas (ya filtradas por idioma) que NO contengan la secuencia de alegación
                rutas_filtradas_final = [r for r in rutas_filtradas_idioma if not (7 in r and 8 in r and 9 in r)]

            # --- Selección de Ruta Final (con fallbacks mejorados) ---
            if rutas_filtradas_final:
                ruta_seleccionada = random.choice(rutas_filtradas_final)
            elif rutas_filtradas_idioma: # Fallback 1: No había rutas con/sin alegación, pero sí para el idioma
                 print(f"⚠️ Advertencia: No se encontraron rutas filtradas por alegación ({tiene_alegacion}) para Estudiante {estudiante_id} (Estado: {estado_final}, Idioma: {requiere_idioma}). Seleccionando ruta compatible con idioma.")
                 ruta_seleccionada = random.choice(rutas_filtradas_idioma)
            elif lista_rutas_estado: # Fallback 2: No había rutas para el idioma, usar las del estado
                 print(f"⚠️ Advertencia: No se encontraron rutas filtradas por idioma ({requiere_idioma}) para Estudiante {estudiante_id} (Estado: {estado_final}). Seleccionando de la lista completa del estado.")
                 ruta_seleccionada = random.choice(lista_rutas_estado)
            else: # Fallback 3: Usar default global
                 print(f"🆘 Error Crítico: No hay rutas disponibles para Estudiante {estudiante_id}. Usando ruta default global.")
                 ruta_seleccionada = random.choice(rutas_default)

        # ---- Fin Selección Ruta ----
        ruta = ruta_seleccionada

        # --- Bucle principal de eventos --- 
        for actividad_id in ruta:
            # --- Lógica Timestamp (ACTUALIZADA para publicaciones fijas) ---
            fecha_actual = None # Inicializar

            # 1. Evento de Cancelación Admin (ID 33) con fecha conocida
            if actividad_id == 33 and fecha_cancelacion_destino is not None:
                fecha_minima = fecha_evento_anterior + timedelta(seconds=1)
                fecha_actual = max(fecha_cancelacion_destino, fecha_minima)
                fecha_actual = datetime.combine(fecha_actual.date(), generar_hora_realista())
                fecha_actual = max(fecha_actual, fecha_minima)
            
            # 2. Eventos de Publicación Fija (IDs 6, 10, 14, 18, 22)
            elif actividad_id in FECHAS_PUBLICACION:
                fecha_fija = FECHAS_PUBLICACION[actividad_id]
                fecha_minima = fecha_evento_anterior + timedelta(seconds=1)
                # Asegurar que la fecha fija es posterior al evento anterior
                fecha_actual = max(fecha_fija, fecha_minima)
                # Si la fecha fija tuvo que adelantarse, al menos mantener la hora 00:01
                if fecha_actual > fecha_fija:
                    # Comprobar si al menos es el mismo día
                    if fecha_actual.date() == fecha_fija.date():
                         # Mantener la hora 00:01 si es posible, sino la hora mínima
                         hora_minima = fecha_minima.time()
                         hora_fija = time(0, 1, 0)
                         fecha_actual = datetime.combine(fecha_actual.date(), max(hora_fija, hora_minima))
                    # Si tuvo que cambiar el día, ya no podemos forzar la hora 00:01
                    # y se queda con el timestamp mínimo (fecha_actual ya tiene ese valor)
                
            # 3. Eventos con Plazo definido en PLAZOS
            elif actividad_id in PLAZOS:
                 inicio_plazo, fin_plazo = PLAZOS[actividad_id]
                 fecha_actual = generar_timestamp_en_plazo(inicio_plazo, fin_plazo, fecha_evento_anterior)
            
            # 4. Resto de eventos (sin plazo fijo ni publicación fija)
            else:
                # Lógica de delta aleatorio (sin cambios)
                delta_dias = random.randint(0, 2)
                delta_horas = random.randint(1, 12)
                delta_total = timedelta(days=delta_dias, hours=delta_horas, minutes=random.randint(0,59))
                fecha_propuesta = fecha_evento_anterior + delta_total
                
                # Heurística para evitar adelantar plazos (sin cambios)
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

            # Actualizar fecha evento anterior para el siguiente ciclo
            fecha_evento_anterior = fecha_actual
            # --- Fin Lógica Timestamp ---            
            
            actor = actividad_actor_map.get(actividad_id, "Desconocido")
            detalle = actividades_df.loc[actividades_df['ActividadID'] == actividad_id, 'NombreActividad'].iloc[0] # Detalle base
            
            # --- Actualizar IDs en la generación de detalles específicos --- 
            # IDs originales eran 12, 16, 20. Nuevos IDs son 11, 15, 19.
            if actividad_id in [11, 15, 19]: 
                ronda_adj = (actividad_id - 11) // 4 + 1
                detalle = f"Respuesta {ronda_adj}ª Adj: Aceptación/Reserva"
            # IDs originales eran 13, 17, 21. Nuevos IDs son 12, 16, 20.
            elif actividad_id in [12, 16, 20]: 
                ronda_adj = (actividad_id - 12) // 4 + 1
                detalle = f"Respuesta {ronda_adj}ª Adj: Renuncia"
            # ID original era 34. Nuevo ID es 33.
            elif actividad_id == 33: 
                detalle = "Destino Solicitado Cancelado (Admin)"

            eventos.append([
                estudiante_id,
                actividad_id,
                fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
                int(id_destino_log),
                detalle,
                actor
            ])
            # --- Fin resto del bucle ---

    eventos_df = pd.DataFrame(eventos, columns=["EstudianteID", "ActividadID", "Timestamp", "DestinoID", "Detalle", "Actor"])
    eventos_df.insert(0, "EventID", range(1, len(eventos_df) + 1))
    return eventos_df

def generar_alegaciones(estudiantes_df):
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

def generar_historico_adjudicaciones(estudiantes_df, destinos_df, estudiantes_con_alegaciones_ids):
    """Genera un histórico de adjudicaciones simulando rondas y estados (Titular/Suplente)."""
    historico = []
    asignacion_id_counter = 1

    # Fechas clave de publicación para referencia temporal
    fecha_pub_1ra = datetime(2023, 1, 11)
    fecha_pub_2da = datetime(2023, 1, 19)
    fecha_pub_3ra = datetime(2023, 1, 25)
    fecha_pub_final = datetime(2023, 2, 1) # Estimada tras 3ª adj.

    for idx, row in estudiantes_df.iterrows():
        estudiante_id = row["EstudianteID"]
        destino_solicitado = row["DestinoSolicitado"]
        destino_final_asignado = row["DestinoAsignado"]
        estado_final = row["EstadoFinal"]
        # No necesitamos la fecha base solicitud aquí realmente

        # --- Simulación de adjudicación en rondas ---
        destino_en_ronda = np.nan
        estado_en_ronda = "No Asignado"
        asignado_definitivo = False

        # Iterar por las rondas de publicación
        for ronda, fecha_pub, siguiente_fecha_pub in [
            (1, fecha_pub_1ra, fecha_pub_2da),
            (2, fecha_pub_2da, fecha_pub_3ra),
            (3, fecha_pub_3ra, fecha_pub_final)
        ]:
            if asignado_definitivo: # Si ya aceptó en ronda anterior, no aparece más
                 break

            # ¿Estaba ya asignado (titular/suplente) en la ronda anterior?
            era_titular_anterior = estado_en_ronda == "Titular"
            era_suplente_anterior = estado_en_ronda == "Suplente"

            # Resetear estado para esta ronda
            estado_en_ronda = "No Asignado"
            destino_ronda_actual = np.nan

            # Lógica de asignación SIMPLIFICADA
            if estado_final not in ["Excluido"]:
                prob_aparecer_en_lista = 0.8 if ronda == 1 else 0.5 # Más prob en 1ª
                if era_suplente_anterior: prob_aparecer_en_lista = 0.9 # Más prob si era suplente
                
                if random.random() < prob_aparecer_en_lista:
                    # ¿Obtiene el destino final en esta ronda?
                    if (estado_final == "Aceptado" and not pd.isna(destino_final_asignado) and 
                        (random.random() < 0.6 or destino_final_asignado != destino_solicitado)): # Prob de obtenerlo ahora
                        estado_en_ronda = "Titular"
                        destino_ronda_actual = destino_final_asignado
                    # ¿O sigue siendo suplente o titular de algo que renunciará?
                    elif (estado_final == "Renuncia" and not pd.isna(destino_final_asignado) and
                          random.random() < 0.7): # Prob de obtenerlo antes de renunciar
                        estado_en_ronda = "Titular"
                        destino_ronda_actual = destino_final_asignado
                    elif random.random() < 0.6: # Prob de ser suplente
                        estado_en_ronda = "Suplente"
                        # Suplente para el solicitado o el final si es distinto? Vamos con solicitado
                        destino_ronda_actual = destino_solicitado
                    else: # Caso raro: Titular de algo intermedio (no modelado aquí, queda No Asignado)
                         estado_en_ronda = "No Asignado"
            
            # Si se le asignó algo en esta ronda, registrar
            if not pd.isna(destino_ronda_actual):
                 historico.append([
                    asignacion_id_counter, estudiante_id, int(destino_ronda_actual),
                    fecha_pub.strftime('%Y-%m-%d'), f"{ronda}ª Adjudicación", estado_en_ronda
                 ])
                 asignacion_id_counter += 1
            
            # Simular aceptación si es Titular y su estado final es Aceptado
            if estado_en_ronda == "Titular" and estado_final == "Aceptado":
                # Si el destino de esta ronda coincide con el final, se considera aceptado
                if destino_ronda_actual == destino_final_asignado:
                    asignado_definitivo = True # No aparecerá en más listas

            # Si estado final es Renuncia y fue Titular, asumimos que renuncia tras esta ronda
            elif estado_en_ronda == "Titular" and estado_final == "Renuncia":
                 asignado_definitivo = True # No aparecerá más (simulamos renuncia implícita)


        # --- Registro Final (si estado final Aceptado y no se registró antes) ---
        if estado_final == "Aceptado" and not pd.isna(destino_final_asignado):
            ya_registrado_final = any(
                h[1] == estudiante_id and
                h[2] == int(destino_final_asignado) and
                h[5] == "Titular"
                for h in historico
            )
            if not ya_registrado_final:
                historico.append([
                    asignacion_id_counter, estudiante_id, int(destino_final_asignado),
                    fecha_pub_final.strftime('%Y-%m-%d'), "Adjudicación Final", "Titular"
                ])
                asignacion_id_counter += 1

    return pd.DataFrame(
        historico,
        columns=[
            "AsignacionID", "EstudianteID", "DestinoID", "FechaAsignacion",
            "Ronda", "EstadoEnRonda"
        ]
    )

# ---- Ejecución principal ----

if __name__ == "__main__":
    # Set global para IDs de estudiantes con alegaciones
    # Necesita ser global para que generar_historico_adjudicaciones pueda acceder
    global estudiantes_con_alegaciones_ids
    estudiantes_con_alegaciones_ids = set()

    destinos = generar_destinos(NUM_DESTINOS)
    estudiantes = generar_estudiantes(NUM_ESTUDIANTES, destinos)
    actividades = generar_actividades()

    # Generamos alegaciones PRIMERO y actualizamos el set global
    alegaciones, estudiantes_con_alegaciones_ids_local = generar_alegaciones(estudiantes)
    estudiantes_con_alegaciones_ids.update(estudiantes_con_alegaciones_ids_local)

    # Generamos histórico y eventlog DESPUÉS de saber quién tiene alegaciones
    historico = generar_historico_adjudicaciones(
        estudiantes, destinos, estudiantes_con_alegaciones_ids # Pasar el set
    )
    eventlog = generar_eventlog(
        estudiantes, actividades, destinos, estudiantes_con_alegaciones_ids
    )

    # --- Corrección de Tipos de Datos antes de Guardar ---
    # Convertir DestinoAsignado a tipo Int64 nullable de pandas para permitir NaN pero ser entero
    estudiantes['DestinoAsignado'] = estudiantes['DestinoAsignado'].astype(pd.Int64Dtype())
    historico['DestinoID'] = historico['DestinoID'].astype(pd.Int64Dtype()) # También en histórico por consistencia

    # Guardar todos los CSVs
    destinos.to_csv(f"{RUTA_DATA}/Destinos.csv", index=False)
    estudiantes.to_csv(f"{RUTA_DATA}/Estudiantes.csv", index=False)
    actividades.to_csv(f"{RUTA_DATA}/Actividades.csv", index=False)
    eventlog.to_csv(f"{RUTA_DATA}/EventLog.csv", index=False)
    alegaciones.to_csv(f"{RUTA_DATA}/Alegaciones.csv", index=False)
    historico.to_csv(f"{RUTA_DATA}/HistoricoAdjudicaciones.csv", index=False)

    print("\n✅ Generación de CSVs Erasmus COMPLETADA.")
