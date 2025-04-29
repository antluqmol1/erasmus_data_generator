import os
import random
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

from llm_helpers import get_universities, get_alegation_motives, get_process_patterns

# ---- Configuración general ----
NUM_ESTUDIANTES = 426
NUM_DESTINOS = 302
PCT_ESTUDIANTES_CON_ALEGACIONES = 0.09
RUTA_DATA = "data"
USE_LLM = True  # <<--- Activa o desactiva llamadas a LLM

# Crear carpeta data si no existe
os.makedirs(RUTA_DATA, exist_ok=True)

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
    for i in range(1, num_destinos + 1):
        # Usamos nombre y país de la lista generada
        nombre, pais = universidades_con_pais[i-1]

        # pais = random.choices(lista_paises, weights=pesos_paises, k=1)[0] # <-- Ya no se necesita
        plazas = random.randint(1, 5)
        cancelado = random.choice(["No"] * 9 + ["Sí"])
        fecha_cancelacion = (datetime(2023, 6, random.randint(1, 30)).strftime('%Y-%m-%d') if cancelado == "Sí" else "")
        destinos.append([i, nombre, pais, plazas, cancelado, fecha_cancelacion])
    return pd.DataFrame(destinos, columns=["DestinoID", "NombreDestino", "País", "NúmeroPlazas", "Cancelado", "FechaCancelación"])

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
        fecha_solicitud = datetime(2023, 1, random.randint(10, 31)).strftime('%Y-%m-%d')
        destino_solicitado = random.choice(destinos_df["DestinoID"].tolist())
        destino_asignado = destino_solicitado if random.random() > 0.3 else np.nan

        # Elegimos estado final según la ponderación
        estado_final = random.choices(estados_finales, weights=pesos_estados, k=1)[0]

        # Ajuste para coherencia: Si el estado es Aceptado, debe tener un destino asignado
        if estado_final == "Aceptado" and pd.isna(destino_asignado):
            destino_asignado = destino_solicitado # Forzamos la asignación
        # Ajuste: Si es Excluido o No asignado, no debería tener destino asignado
        elif estado_final in ["Excluido", "No asignado"] and not pd.isna(destino_asignado):
             destino_asignado = np.nan # Forzamos NaN
        # Ajuste: Si Renuncia, usualmente tuvo asignación previa
        elif estado_final == "Renuncia" and pd.isna(destino_asignado):
             destino_asignado = destino_solicitado # Asumimos que se le asignó el solicitado antes de renunciar

        estudiantes.append([i, grado, sexo, expediente, fecha_solicitud, destino_solicitado, destino_asignado, estado_final])
    return pd.DataFrame(estudiantes, columns=["EstudianteID", "Grado", "Sexo", "Expediente", "FechaSolicitud", "DestinoSolicitado", "DestinoAsignado", "EstadoFinal"])

def generar_actividades():
    actividades = [
        (1, "Solicitud presentada", "Fase inicial", "Manual", "Estudiante", 1),
        (2, "Envío de documentación", "Fase inicial", "Manual", "Estudiante", 2),
        (3, "Revisión de documentación", "Fase inicial", "Automática", "Administración", 3),
        (4, "Solicitud validada", "Fase inicial", "Automática", "Administración", 4),
        (5, "Adjudicación provisional", "Fase de adjudicación", "Automática", "Administración", 5),
        (6, "Notificación de plaza asignada", "Fase de adjudicación", "Automática", "Administración", 6),
        (7, "Aceptación de plaza", "Fase de aceptación", "Manual", "Estudiante", 7),
        (8, "Confirmación de aceptación", "Fase de aceptación", "Manual", "Estudiante", 8),
        (9, "Renuncia a plaza", "Fase de renuncia", "Manual", "Estudiante", 9),
        (10, "Cancelación por baja voluntaria", "Fase de renuncia", "Manual", "Estudiante", 10),
        (11, "Cancelación de destino", "Fase de reubicación", "Automática", "Administración", 11),
        (12, "Reasignación de destino", "Fase de reubicación", "Automática", "Administración", 12),
        (13, "Alegación presentada", "Fase de alegaciones", "Manual", "Estudiante", 13),
        (14, "Resolución de alegación", "Fase de alegaciones", "Automática", "Administración", 14),
        (15, "Solicitud de modificación de destino", "Fase de alegaciones", "Manual", "Estudiante", 15),
        (16, "Resolución modificación de destino", "Fase de alegaciones", "Automática", "Administración", 16),
        (17, "Firma de compromiso Erasmus", "Fase final", "Manual", "Estudiante", 17),
        (18, "Emisión de certificado de movilidad", "Fase final", "Automática", "Administración", 18)
    ]
    return pd.DataFrame(actividades, columns=["ActividadID", "NombreActividad", "Fase", "TipoActividad", "ActorDefecto", "OrdenSecuencial"])

def generar_eventlog(estudiantes_df, actividades_df, destinos_df, estudiantes_con_alegaciones_ids):
    eventos = []
    actividad_actor_map = dict(zip(actividades_df["ActividadID"], actividades_df["ActorDefecto"]))

    # Definimos rutas de actividades realistas AGRUPADAS POR ESTADO FINAL TÍPICO
    rutas_por_estado = {
        "Aceptado": [
            [1, 2, 3, 4, 5, 6, 7, 8, 17, 18],          # Flujo normal
            [1, 2, 3, 4, 5, 6, 13, 14, 7, 8, 17, 18], # Con alegación (resuelta positivamente o sin efecto)
            [1, 2, 3, 4, 5, 11, 12, 6, 7, 8, 17, 18], # Con cancelación y reasignación exitosa
            [1, 2, 3, 4, 5, 6, 13, 14, 15, 16, 7, 8, 17, 18], # Con alegación -> modificación -> aceptación
        ],
        "Renuncia": [
            [1, 2, 3, 4, 5, 6, 9],                     # Renuncia tras asignación
            [1, 2, 3, 4, 5, 6, 10],                    # Baja voluntaria tras asignación
            [1, 2, 3, 4, 10],                         # Baja voluntaria antes de asignación
            [1, 2, 3, 4, 5, 6, 13, 14, 9],             # Alegación (resuelta) -> Renuncia
        ],
        "No asignado": [
            [1, 2, 3, 4, 5],                           # Llega a adjudicación provisional pero no se le asigna plaza
            [1, 2, 3, 4],                              # No pasa de validación
        ],
        "Excluido": [
            [1, 2, 3],                                 # Excluido en revisión inicial de documentación
            [1, 2],                                    # Ni siquiera completa envío documentación
        ]
    }
    # Ruta por defecto si el estado no coincide
    rutas_default = [[1, 2, 3, 4]]

    # Si usamos LLM, obtenemos patrones adicionales y los mezclamos
    if USE_LLM:
        print("🔄 Obteniendo patrones de proceso desde el LLM...")
        patrones_llm = get_process_patterns(n=15) # Pedimos más patrones al LLM
        print(f"✅ LLM generó {len(patrones_llm)} patrones.")

        # Añadimos/Mezclamos los patrones del LLM a las rutas existentes
        # Podríamos hacer una lógica más sofisticada para asignarlos por estado,
        # pero por simplicidad, los añadimos como opciones generales a cada estado
        # (excepto quizás a los más cortos como Excluido)
        for estado, lista_rutas in rutas_por_estado.items():
            if estado not in ["Excluido"]: # No añadir rutas largas a excluidos
                rutas_por_estado[estado].extend(patrones_llm)
        # También añadimos a la default por si acaso
        rutas_default.extend(patrones_llm)

    for idx, row in estudiantes_df.iterrows():
        estudiante_id = row["EstudianteID"]
        fecha_actual = datetime.strptime(row["FechaSolicitud"], '%Y-%m-%d')

        estado_final = row["EstadoFinal"]
        lista_de_rutas_posibles = rutas_por_estado.get(estado_final, rutas_default)

        # ---- Lógica de selección de ruta modificada ----
        ruta_seleccionada = None
        if estudiante_id in estudiantes_con_alegaciones_ids:
            # Filtrar rutas que contienen alegaciones (13 y 14)
            rutas_con_alegacion = [r for r in lista_de_rutas_posibles if 13 in r and 14 in r]
            if rutas_con_alegacion:
                ruta_seleccionada = random.choice(rutas_con_alegacion)
            else:
                # Fallback: No se encontraron rutas con alegaciones para este estado.
                # Usamos una ruta genérica con alegación o una de las originales.
                # Opción 1: Usar una ruta original del estado (menos consistente aquí)
                # ruta_seleccionada = random.choice(lista_de_rutas_posibles)
                # Opción 2: Usar una ruta fija con alegación (ej. la normal de aceptado con alegación)
                ruta_predeterminada_alegacion = [1, 2, 3, 4, 5, 6, 13, 14, 7, 8, 17, 18]
                # Comprobar si esta ruta es mínimamente compatible con el estado final (ej. no para excluidos)
                if estado_final not in ["Excluido", "No asignado"]:
                     ruta_seleccionada = ruta_predeterminada_alegacion
                else: # Si es excluido/no asignado, no forzar ruta de alegación larga
                     ruta_seleccionada = random.choice(lista_de_rutas_posibles) 
                print(f"⚠️ Advertencia: Estudiante {estudiante_id} con alegación pero sin ruta compatible encontrada para estado '{estado_final}'. Usando fallback.")
        
        # Si no tiene alegación o el fallback anterior no asignó ruta
        if ruta_seleccionada is None:
             ruta_seleccionada = random.choice(lista_de_rutas_posibles)
        # ---- Fin lógica modificada ----

        # Renombramos la variable para el resto del código
        ruta = ruta_seleccionada 

        destino_id = row["DestinoSolicitado"]
        if pd.isna(destino_id):
            destino_id = random.choice(destinos_df["DestinoID"].tolist())

        for actividad_id in ruta:
            # Añadimos desfases realistas entre eventos
            if actividad_id in [1,2,3]:  # Iniciales
                delta_dias = random.randint(3, 7)
            elif actividad_id in [4,5]:  # Validación / adjudicación
                delta_dias = random.randint(7, 15)
            elif actividad_id in [6,7,8,9,10,11,12,13,14]:  # Cambios, alegaciones, renuncias
                delta_dias = random.randint(10, 20)
            else:  # Firma final, certificado
                delta_dias = random.randint(20, 30)

            fecha_actual += timedelta(days=delta_dias)

            # Actor de la actividad
            actor = actividad_actor_map.get(actividad_id, "Desconocido")

            # Detalle del evento (puedes enriquecerlo más si quieres)
            if actividad_id in [5,6,12]:
                detalle = "Adjudicación a destino Erasmus"
            elif actividad_id in [9,10]:
                detalle = "Renuncia voluntaria"
            elif actividad_id in [13,14]:
                detalle = "Alegación sobre adjudicación"
            else:
                detalle = ""

            eventos.append([
                estudiante_id,
                actividad_id,
                fecha_actual.strftime('%Y-%m-%d %H:%M:%S'),
                int(destino_id),
                detalle,
                actor
            ])

    eventos_df = pd.DataFrame(eventos, columns=["EstudianteID", "ActividadID", "Timestamp", "DestinoID", "Detalle", "Actor"])
    eventos_df.insert(0, "EventID", range(1, len(eventos_df)+1))  # Creamos un ID único de evento
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

def generar_historico_adjudicaciones(estudiantes_df):
    historico = []
    for idx, row in estudiantes_df.iterrows():
        if not pd.isna(row["DestinoAsignado"]):
            fecha_asignacion = datetime.strptime(row["FechaSolicitud"], '%Y-%m-%d') + timedelta(days=30)
            historico.append([
                idx + 1,
                row["EstudianteID"],
                row["DestinoAsignado"],
                fecha_asignacion.strftime('%Y-%m-%d'),
                "Inicial",
                "Aceptado" if row["EstadoFinal"] == "Aceptado" else "Renunciado"
            ])
    return pd.DataFrame(historico, columns=["AsignacionID", "EstudianteID", "DestinoID", "FechaAsignacion", "TipoAsignacion", "EstadoAsignacion"])

# ---- Ejecución principal ----

if __name__ == "__main__":
    destinos = generar_destinos(NUM_DESTINOS)
    estudiantes = generar_estudiantes(NUM_ESTUDIANTES, destinos)
    actividades = generar_actividades()
    # Generamos alegaciones PRIMERO para saber qué estudiantes las tienen
    alegaciones, estudiantes_con_alegaciones_ids = generar_alegaciones(estudiantes)
    # Pasamos los IDs con alegaciones a generar_eventlog
    eventlog = generar_eventlog(estudiantes, actividades, destinos, estudiantes_con_alegaciones_ids)
    historico = generar_historico_adjudicaciones(estudiantes)

    # Guardar todos los CSVs
    destinos.to_csv(f"{RUTA_DATA}/Destinos.csv", index=False)
    estudiantes.to_csv(f"{RUTA_DATA}/Estudiantes.csv", index=False)
    actividades.to_csv(f"{RUTA_DATA}/Actividades.csv", index=False)
    eventlog.to_csv(f"{RUTA_DATA}/EventLog.csv", index=False)
    alegaciones.to_csv(f"{RUTA_DATA}/Alegaciones.csv", index=False)
    historico.to_csv(f"{RUTA_DATA}/HistoricoAdjudicaciones.csv", index=False)

    print("\n✅ Generación de CSVs Erasmus COMPLETADA.")
