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
    1: (datetime(2022, 11, 2), datetime(2022, 11, 28)), # Presentación Solicitudes (y Convalidación Idioma)
    5: (datetime(2022, 11, 2), datetime(2022, 11, 30)), # Inscripción Programa Erasmus Registrada
    8: (datetime(2022, 12, 12), datetime(2022, 12, 27)), # Alegaciones (desde pub prov hasta deadline)
    12: (datetime(2023, 1, 11), datetime(2023, 1, 17)), # Respuesta 1ª Adj (desde pub 1ª adj hasta deadline)
    13: (datetime(2023, 1, 11), datetime(2023, 1, 17)), # Respuesta 1ª Adj (Renuncia)
    16: (datetime(2023, 1, 19), datetime(2023, 1, 23)), # Respuesta 2ª Adj (desde pub 2ª adj hasta deadline)
    17: (datetime(2023, 1, 19), datetime(2023, 1, 23)), # Respuesta 2ª Adj (Renuncia)
    20: (datetime(2023, 1, 25), datetime(2023, 1, 30)), # Respuesta 3ª Adj (desde pub 3ª adj hasta deadline)
    21: (datetime(2023, 1, 25), datetime(2023, 1, 30)), # Respuesta 3ª Adj (Renuncia)
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
            
        destinos.append([i, nombre, pais, plazas, cancelado, fecha_cancelacion])
    
    # Advertencia si el número generado es menor que el solicitado
    if len(universidades_con_pais) < num_destinos:
        print(f"⚠️ Advertencia: Se solicitaron {num_destinos} destinos, pero solo se generaron {len(universidades_con_pais)}. Se usarán solo los generados.")
        
    return pd.DataFrame(
        destinos,
        columns=[
            "DestinoID", "NombreDestino", "País", "NúmeroPlazas",
            "Cancelado", "FechaCancelación"
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
            PLAZOS[5][0], PLAZOS[5][1], PLAZOS[5][0] - timedelta(days=1)
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
    actividades = [
        # Fase Inicial / Convalidación Idioma (IDs 1-4, Orden 1-3)
        (1, "Solicitud Convalidación Idioma Presentada", "Fase Inicial", "Manual", "Estudiante", 1),
        (2, "Solicitud Convalidación Idioma Recibida", "Fase Inicial", "Automática", "Instituto de Idiomas", 2),
        (3, "Resolución Convalidación Idioma (Rechazada)", "Fase Inicial", "Automática", "Instituto de Idiomas", 3),
        (4, "Resolución Convalidación Idioma (Aceptada)", "Fase Inicial", "Automática", "Instituto de Idiomas", 3),

        # Inscripción y Listado Provisional (IDs 5-7, Orden 4-6)
        (5, "Inscripción Programa Erasmus Registrada", "Inscripción", "Manual", "Estudiante", 4),
        (6, "Cálculo Notas Participantes Realizado", "Adjudicación Provisional", "Automática", "SEVIUS", 5),
        (7, "Publicación Listado Provisional", "Adjudicación Provisional", "Automática", "SEVIUS", 6),

        # Alegaciones (IDs 8-10, Orden 7-9)
        (8, "Alegación Presentada", "Alegaciones", "Manual", "Estudiante", 7),
        (9, "Alegación Recibida", "Alegaciones", "Automática", "SEVIUS", 8),
        (10, "Resolución Alegación Emitida", "Alegaciones", "Automática", "SEVIUS", 9),

        # --- 1ª Adjudicación y Respuesta (IDs 11-14, Orden 10-12) ---
        (11, "Publicación 1ª Adjudicación", "Adjudicaciones", "Automática", "SEVIUS", 10),
        (12, "Respuesta Recibida (Aceptación/Reserva 1ª Adj.)", "Adjudicaciones", "Manual", "Estudiante", 11),
        (13, "Respuesta Recibida (Renuncia 1ª Adj.)", "Adjudicaciones", "Manual", "Estudiante", 11),
        (14, "Actualización Orden Preferencias (Post-1ª Adj.)", "Adjudicaciones", "Automática", "SEVIUS", 12), # Ocurre si hubo renuncias (ID 13)

        # --- 2ª Adjudicación y Respuesta (IDs 15-18, Orden 13-15) ---
        (15, "Publicación 2ª Adjudicación", "Adjudicaciones", "Automática", "SEVIUS", 13),
        (16, "Respuesta Recibida (Aceptación/Reserva 2ª Adj.)", "Adjudicaciones", "Manual", "Estudiante", 14),
        (17, "Respuesta Recibida (Renuncia 2ª Adj.)", "Adjudicaciones", "Manual", "Estudiante", 14),
        (18, "Actualización Orden Preferencias (Post-2ª Adj.)", "Adjudicaciones", "Automática", "SEVIUS", 15), # Ocurre si hubo renuncias (ID 17)

        # --- 3ª Adjudicación y Respuesta (IDs 19-22, Orden 16-18) ---
        (19, "Publicación 3ª Adjudicación", "Adjudicaciones", "Automática", "SEVIUS", 16),
        (20, "Respuesta Recibida (Aceptación/Reserva 3ª Adj.)", "Adjudicaciones", "Manual", "Estudiante", 17),
        (21, "Respuesta Recibida (Renuncia 3ª Adj.)", "Adjudicaciones", "Manual", "Estudiante", 17),
        (22, "Actualización Orden Preferencias (Post-3ª Adj.)", "Adjudicaciones", "Automática", "SEVIUS", 18), # Ocurre si hubo renuncias (ID 21)

        # Listado Definitivo (ID 23, Orden 19)
        (23, "Publicación Listado Definitivo", "Adjudicación Final", "Automática", "SEVIUS", 19),

        # Learning Agreement (IDs 24-31, Orden 20-23)
        (24, "Envío LA a Responsable Destino", "Learning Agreement", "Manual", "Estudiante", 20),
        (25, "LA Recibido por Responsable", "Learning Agreement", "Automática", "Responsable Destino", 21),
        (26, "LA Validado por Responsable", "Learning Agreement", "Manual", "Responsable Destino", 22),
        (27, "LA Rechazado por Responsable", "Learning Agreement", "Manual", "Responsable Destino", 22),
        (28, "Envío LA a Subdirectora RRII", "Learning Agreement", "Manual", "Estudiante", 23),
        (29, "LA Recibido por Subdirectora", "Learning Agreement", "Automática", "Subdirectora RRII", 24),
        (30, "LA Validado por Subdirectora", "Learning Agreement", "Manual", "Subdirectora RRII", 25),
        (31, "LA Rechazado por Subdirectora", "Learning Agreement", "Manual", "Subdirectora RRII", 25),

        # Formalización y Fin (IDs 32-33, Orden 26-27)
        (32, "Formalización Acuerdo SEVIUS", "Formalización", "Manual", "Estudiante", 26),
        (33, "Proceso Erasmus Finalizado", "Finalizado", "Automática", "Sistema", 27),

        # Evento de Cancelación Administrativa (ID 34, Orden ~10)
        # El orden 10 indica que puede ocurrir alrededor del tiempo de las adjudicaciones.
        (34, "Cancelación Plaza (Admin)", "Cancelación", "Automática", "SEVIUS", 10)
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

    # --- Rutas de actividades (ACTUALIZADAS con opcionalidad y rondas) ---
    # Se añadirán más variaciones programáticamente abajo
    rutas_base = {
        "Aceptado": [
            # Base: Idioma OK, Sin Alegación, Acepta 1ª, LA OK
            [1, 2, 4, 5, 6, 7, 11, 12, 15, 19, 23, 24, 25, 26, 28, 29, 30, 32, 33],
            # Base: Idioma OK, Sin Alegación, Renuncia 1ª, Acepta 2ª, LA OK
            [1, 2, 4, 5, 6, 7, 11, 13, 14, 15, 16, 19, 23, 24, 25, 26, 28, 29, 30, 32, 33],
            # Base: Idioma OK, Sin Alegación, Renuncia 1ª/2ª, Acepta 3ª, LA OK
            [1, 2, 4, 5, 6, 7, 11, 13, 14, 15, 17, 18, 19, 20, 23, 24, 25, 26, 28, 29, 30, 32, 33],
        ],
        "Renuncia": [
            # Base: Idioma OK, Sin Alegación, Renuncia en 1ª
            [1, 2, 4, 5, 6, 7, 11, 13, 14],
            # Base: Idioma OK, Sin Alegación, Acepta 1ª, Renuncia en 2ª
            [1, 2, 4, 5, 6, 7, 11, 12, 15, 17, 18],
             # Base: Idioma OK, Sin Alegación, Acepta 1ª/2ª, Renuncia en 3ª
            [1, 2, 4, 5, 6, 7, 11, 12, 15, 16, 19, 21, 22],
        ],
        "No asignado": [
            # Base: Idioma OK, Sin Alegación, Pasa todas las rondas sin plaza
            [1, 2, 4, 5, 6, 7, 11, 14, 15, 18, 19, 22, 23],
            # Base: Idioma OK, Sin Alegación, No pasa de provisional
            [1, 2, 4, 5, 6, 7],
        ],
        "Excluido": [
            # Base: Rechazado en Idioma
            [1, 2, 3],
        ]
    }

    # --- Lógica para generar variaciones de rutas (opcionalidad) ---
    rutas_completas_por_estado = {}
    for estado, lista_rutas_base in rutas_base.items():
        variaciones = []
        for ruta_base in lista_rutas_base:
            # 1. Ruta Original (con idioma si aplica, sin alegación)
            variaciones.append(ruta_base)
            # 2. Sin Idioma (si la original lo tenía)
            if ruta_base[0] == 1:
                variaciones.append(ruta_base[3:])
            # 3. Con Alegación (añadir 8, 9, 10 después del paso 7)
            if 7 in ruta_base:
                idx_7 = ruta_base.index(7)
                ruta_con_alegacion = ruta_base[:idx_7+1] + [8, 9, 10] + ruta_base[idx_7+1:]
                variaciones.append(ruta_con_alegacion)
                # 4. Sin Idioma y Con Alegación (si aplica)
                if ruta_base[0] == 1:
                     ruta_sin_idioma_con_alegacion = ruta_con_alegacion[3:]
                     variaciones.append(ruta_sin_idioma_con_alegacion)

        # Eliminar duplicados y rutas vacías si las hubiera
        rutas_completas_por_estado[estado] = [list(t) for t in set(tuple(v) for v in variaciones if v)]

    # Añadir rutas de Cancelación Administrativa (ID 34)
    # Se añade como posibilidad a estados donde tendría sentido (ej. antes de finalizar)
    for estado in ["Aceptado", "Renuncia", "No asignado"]:
        if estado in rutas_completas_por_estado:
            # Ejemplo: Cancelación después de 1ª Adjudicación
            ruta_cancelacion = [1, 2, 4, 5, 6, 7, 11, 34]
            rutas_completas_por_estado[estado].append(ruta_cancelacion)
            # Ejemplo: Cancelación sin pasos de idioma
            ruta_cancelacion_sin_idioma = [5, 6, 7, 11, 34]
            rutas_completas_por_estado[estado].append(ruta_cancelacion_sin_idioma)


    # Ruta default (simplificada)
    rutas_default = [[5, 6, 7]] # Asume que al menos se inscribe

    # Mezclar patrones LLM si se usan
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
        id_destino_log = destino_asignado_final if not pd.isna(destino_asignado_final) else destino_solicitado
        if pd.isna(id_destino_log): id_destino_log = random.choice(destinos_df["DestinoID"].tolist())

        ruta_seleccionada = None
        fecha_cancelacion_destino = None

        # --- Comprobar si el DESTINO SOLICITADO fue cancelado tempranamente ---
        if destino_solicitado in ids_destinos_cancelados_temprano:
            print(f"ℹ️ Estudiante {estudiante_id}: Destino solicitado {destino_solicitado} cancelado tempranamente.")
            fecha_cancelacion_destino = mapa_fechas_cancelacion[destino_solicitado]
            # Forzar una ruta corta de cancelación
            # ¿Necesitó idioma? Lo simulamos para ver si incluir 1-4
            necesita_idioma = random.random() < 0.7
            if necesita_idioma:
                # Verificar si la cancelación ocurre después de la posible fecha de resolución idioma
                fecha_resol_idioma_aprox = fecha_evento_anterior + timedelta(days=random.randint(3,10))
                if fecha_cancelacion_destino > fecha_resol_idioma_aprox:
                    ruta_seleccionada = [1, 2, 4, 5, 34] # Idioma OK -> Inscripción -> Cancelación
                else:
                    ruta_seleccionada = [1, 2, 3, 34] # Idioma Rechazado -> Cancelación (o justo después de recibir)
            else:
                 ruta_seleccionada = [5, 34] # Inscripción -> Cancelación
            
            # Opcional: Podríamos ajustar el estado final aquí si quisiéramos forzar "No asignado",
            # pero lo dejamos para mantener la distribución original de estados finales por ahora.
            # estado_final = "No asignado" # Descomentar para forzar

        # --- Si no hay cancelación temprana, proceder con la lógica normal --- 
        if ruta_seleccionada is None:
            lista_rutas_estado = rutas_completas_por_estado.get(estado_final, rutas_default)
            if not lista_rutas_estado: lista_rutas_estado = rutas_default
            tiene_alegacion = estudiante_id in estudiantes_con_alegaciones_ids
            rutas_filtradas_final = []
            if tiene_alegacion:
                # Solo rutas que contengan la secuencia de alegación (8, 9, 10)
                rutas_filtradas_final = [r for r in lista_rutas_estado if 8 in r and 9 in r and 10 in r]
            else:
                # Solo rutas que NO contengan la secuencia de alegación
                rutas_filtradas_final = [r for r in lista_rutas_estado if not (8 in r and 9 in r and 10 in r)]

            # --- Selección de Ruta Final ---
            if rutas_filtradas_final:
                ruta_seleccionada = random.choice(rutas_filtradas_final)
            else:
                # Fallback MUY robusto: si el filtrado eliminó todas las rutas
                # Intentar seleccionar de la lista original del estado sin filtrar por alegación
                print(f"⚠️ Advertencia: No se encontraron rutas filtradas por alegación ({tiene_alegacion}) para Estudiante {estudiante_id} (Estado: {estado_final}). Seleccionando de la lista completa del estado.")
                if lista_rutas_estado:
                    ruta_seleccionada = random.choice(lista_rutas_estado)
                else:
                    # Fallback ÚLTIMO: usar la default global
                    print(f"🆘 Error Crítico: No hay rutas disponibles para Estudiante {estudiante_id}. Usando ruta default global.")
                    ruta_seleccionada = random.choice(rutas_default)

        # ---- Fin Selección Ruta ----
        ruta = ruta_seleccionada 

        # --- Bucle principal de eventos --- 
        for actividad_id in ruta:
            # --- Lógica Timestamp (modificada para manejar fecha de cancelación) ---
            if actividad_id == 34 and fecha_cancelacion_destino is not None:
                # Usar la fecha específica de cancelación para el evento 34
                # Asegurarse que es posterior al evento anterior
                fecha_minima = fecha_evento_anterior + timedelta(seconds=1)
                fecha_actual = max(fecha_cancelacion_destino, fecha_minima)
                # Añadir hora realista
                fecha_actual = datetime.combine(fecha_actual.date(), generar_hora_realista())
                 # Asegurar de nuevo que es posterior
                fecha_actual = max(fecha_actual, fecha_minima) 
            elif actividad_id in PLAZOS:
                 inicio_plazo, fin_plazo = PLAZOS[actividad_id]
                 fecha_actual = generar_timestamp_en_plazo(inicio_plazo, fin_plazo, fecha_evento_anterior)
            else:
                # Lógica de delta para eventos sin plazo (igual que antes)
                delta_dias = random.randint(0, 2) # 0 a 2 días para eventos intermedios
                delta_horas = random.randint(1, 12) # Algunas horas de diferencia
                delta_total = timedelta(days=delta_dias, hours=delta_horas, minutes=random.randint(0,59))
                
                fecha_propuesta = fecha_evento_anterior + delta_total
                
                # Asegurar que no nos adelantamos a un plazo futuro conocido cercano (heurística)
                # Buscar el próximo plazo en la ruta del estudiante
                proximo_plazo_inicio = None
                try:
                    indice_actual = ruta.index(actividad_id)
                    for act_futura_id in ruta[indice_actual+1:]:
                        if act_futura_id in PLAZOS:
                            proximo_plazo_inicio = PLAZOS[act_futura_id][0]
                            break
                except ValueError: # actividad_id no está en ruta (raro)
                    pass 
                    
                # Si hay un próximo plazo y la fecha propuesta lo supera, acortar el delta
                if proximo_plazo_inicio and fecha_propuesta >= proximo_plazo_inicio:
                    fecha_actual = fecha_evento_anterior + timedelta(hours=random.randint(1,3)) # Acortar mucho
                    # Asegurarse de no quedar *justo antes* del plazo
                    if fecha_actual >= proximo_plazo_inicio:
                       fecha_actual = proximo_plazo_inicio - timedelta(minutes=random.randint(1,30))
                else:
                    fecha_actual = fecha_propuesta

            # Actualizar fecha evento anterior
            fecha_evento_anterior = fecha_actual
            # --- Fin Lógica Timestamp ---
            
            # --- Resto del bucle (actor, detalle, append) sin cambios --- 
            actor = actividad_actor_map.get(actividad_id, "Desconocido")
            detalle = actividades_df.loc[actividades_df['ActividadID'] == actividad_id, 'NombreActividad'].iloc[0] # Detalle base
            if actividad_id in [12, 16, 20]: detalle = f"Respuesta {int((actividad_id-12)/4)+1}ª Adj: Aceptación/Reserva"
            if actividad_id in [13, 17, 21]: detalle = f"Respuesta {int((actividad_id-13)/4)+1}ª Adj: Renuncia"
            if actividad_id == 34: detalle = "Destino Solicitado Cancelado (Admin)" # Detalle específico

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
