"""Servidor web y API REST para EcoHarmony Park - Inscripción a actividades.

Expone endpoints para consultar cupos, reglas de negocio y procesar inscripciones
utilizando el núcleo de dominio probado de ecoharmony_park."""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import sys
from typing import Any

from flask import Flask, jsonify, render_template, request

# Asegurar acceso al paquete src
BASE_DIR = Path(__file__).resolve().parent
SRC_DIR = BASE_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from ecoharmony_park.inscripciones import (
    Actividad,
    Confirmacion,
    DatosVisitanteInvalidos,
    EdadNoPermitida,
    ErrorInscripcion,
    HorarioInvalido,
    InscripcionDuplicada,
    ServicioInscripcion,
    SinCupo,
    SolicitudInscripcion,
    TerminosActividad,
    TerminosNoAceptados,
    Visitante,
)

app = Flask(
    __name__,
    static_folder=str(BASE_DIR / "static"),
    template_folder=str(BASE_DIR / "templates"),
)


def crear_servicio_inicial() -> ServicioInscripcion:
    """Instancia un ServicioInscripcion con cupos predeterminados para pruebas."""
    ahora_referencia = datetime.now().replace(minute=0, second=0, microsecond=0)
    # Generar turnos para hoy y los próximos 5 días hábiles
    cupos: dict[tuple[Actividad, datetime], int] = {}
    inscripciones_previas: dict[tuple[str, datetime], Actividad] = {}

    for dia_offset in range(0, 6):
        dia = (ahora_referencia + timedelta(days=dia_offset)).date()
        for hora in range(ServicioInscripcion.HORA_APERTURA, ServicioInscripcion.HORA_CIERRE + 1):
            turno = datetime(dia.year, dia.month, dia.day, hora, 0)
            for actividad in Actividad:
                cupo_max = ServicioInscripcion.CUPO_MAXIMO.get(actividad, 10)
                # Configurar disponibilidad estándar
                cupos[(actividad, turno)] = cupo_max

    # Sembrar intencionalmente un caso de cupo agotado para pruebas (Palestra a las 15:00 del próximo día abierto)
    maniana = ahora_referencia + timedelta(days=1)
    while maniana.weekday() == 0:  # evitar lunes si el siguiente día cae lunes
        maniana += timedelta(days=1)
    turno_agotado = datetime(maniana.year, maniana.month, maniana.day, 15, 0)
    cupos[(Actividad.PALESTRA, turno_agotado)] = 0

    # Sembrar una reserva existente para probar DNI duplicado
    turno_duplicado = datetime(maniana.year, maniana.month, maniana.day, 11, 0)
    inscripciones_previas[("30123456", turno_duplicado)] = Actividad.SAFARI

    return ServicioInscripcion(cupos=cupos, inscripciones_existentes=inscripciones_previas)


# Servicio global en memoria para la sesión local
servicio = crear_servicio_inicial()


def parsear_ahora(ahora_param: str | None) -> datetime:
    """Devuelve el instante de referencia actual o el especificado por simulación."""
    if ahora_param:
        try:
            # Soporta formato ISO: "2026-10-20T10:00:00" o "2026-10-20 10:00"
            return datetime.fromisoformat(ahora_param.replace(" ", "T"))
        except ValueError:
            pass
    return datetime.now().replace(microsecond=0)


@app.route("/")
def index():
    """Ruta principal que sirve la interfaz de usuario."""
    template_file = BASE_DIR / "templates" / "index.html"
    if template_file.exists():
        return render_template("index.html")
    return jsonify({
        "mensaje": "EcoHarmony Park API en ejecución. La interfaz HTML se cargará en templates/index.html.",
        "endpoints": [
            "/api/config",
            "/api/cupos",
            "/api/inscribir",
            "/api/correos",
            "/api/reset",
        ],
    })


@app.route("/api/config", methods=["GET"])
def obtener_configuracion():
    """Devuelve los metadatos de configuración, actividades y horarios permitidos."""
    ahora = parsear_ahora(request.args.get("ahora"))

    actividades_info = []
    for act in Actividad:
        terminos = servicio.terminos_para(act)
        actividades_info.append({
            "id": act.name,
            "nombre": act.value,
            "edad_minima": servicio.EDAD_MINIMA.get(act, 0),
            "requiere_vestimenta": act in servicio.ACTIVIDADES_CON_VESTIMENTA,
            "cupo_maximo": servicio.CUPO_MAXIMO.get(act, 10),
            "terminos": {
                "identificador": terminos.identificador,
                "texto": terminos.texto,
            },
        })

    turnos_horas = list(range(ServicioInscripcion.HORA_APERTURA, ServicioInscripcion.HORA_CIERRE + 1))

    return jsonify({
        "ahora_simulado": ahora.isoformat(),
        "hora_apertura": ServicioInscripcion.HORA_APERTURA,
        "hora_cierre": ServicioInscripcion.HORA_CIERRE,
        "turnos_horas": turnos_horas,
        "anticipacion_minima_minutos": int(ServicioInscripcion.ANTICIPACION_MINIMA.total_seconds() // 60),
        "anticipacion_maxima_horas": int(ServicioInscripcion.ANTICIPACION_MAXIMA.total_seconds() // 3600),
        "talles_disponibles": sorted(list(ServicioInscripcion.TALLES)),
        "feriados": [f"{dia:02d}/{mes:02d}" for mes, dia in ServicioInscripcion.FERIADOS],
        "actividades": actividades_info,
    })


@app.route("/api/cupos", methods=["GET"])
def consultar_cupos():
    """Consulta la disponibilidad y estado de los turnos para una fecha y hora dadas."""
    fecha_str = request.args.get("fecha")
    hora_str = request.args.get("hora")
    ahora = parsear_ahora(request.args.get("ahora"))

    if not fecha_str:
        return jsonify({"error": "Debe especificar el parámetro 'fecha' en formato YYYY-MM-DD"}), 400

    try:
        dia = date.fromisoformat(fecha_str)
    except ValueError:
        return jsonify({"error": "Formato de fecha inválido. Utilice YYYY-MM-DD"}), 400

    abierto = servicio.fecha_habilitada(dia)
    motivo_cierre = None
    if not abierto:
        if dia.weekday() == 0:
            motivo_cierre = "El parque permanece cerrado los días lunes"
        elif (dia.month, dia.day) in ServicioInscripcion.FERIADOS:
            motivo_cierre = "El parque permanece cerrado en días feriados"
        else:
            motivo_cierre = "Fecha no disponible"

    disponibilidad_turnos: dict[str, Any] = {}

    horas_a_evaluar = []
    if hora_str:
        try:
            h = int(hora_str.split(":")[0])
            horas_a_evaluar.append(h)
        except ValueError:
            return jsonify({"error": "Formato de hora inválido. Utilice HH:MM"}), 400
    else:
        horas_a_evaluar = list(range(ServicioInscripcion.HORA_APERTURA, ServicioInscripcion.HORA_CIERRE + 1))

    for h in horas_a_evaluar:
        turno = datetime(dia.year, dia.month, dia.day, h, 0)
        h_key = f"{h:02d}:00"

        # Evaluar anticipación
        es_valido_horario = True
        motivo_horario = None
        anticipacion = turno - ahora
        if not abierto:
            es_valido_horario = False
            motivo_horario = motivo_cierre
        elif anticipacion < ServicioInscripcion.ANTICIPACION_MINIMA:
            es_valido_horario = False
            motivo_horario = "Turno pasado o no cumple la anticipación mínima de 15 minutos"
        elif anticipacion > ServicioInscripcion.ANTICIPACION_MAXIMA:
            es_valido_horario = False
            motivo_horario = "Supera la anticipación máxima de 24 horas"

        actividades_cupos = {}
        for act in Actividad:
            ofrecida = (act, turno) in servicio.cupos
            disponibles = servicio.cupos_disponibles(act, turno)
            actividades_cupos[act.value] = {
                "disponibles": disponibles,
                "agotado": ofrecida and disponibles <= 0,
                "ofrecida": ofrecida,
            }

        disponibilidad_turnos[h_key] = {
            "habilitado": es_valido_horario and abierto,
            "motivo": motivo_horario,
            "actividades": actividades_cupos,
        }

    return jsonify({
        "fecha": fecha_str,
        "parque_abierto": abierto,
        "motivo_cierre": motivo_cierre,
        "turnos": disponibilidad_turnos,
    })


@app.route("/api/inscribir", methods=["POST"])
def procesar_inscripcion():
    """Endpoint principal de creación de inscripción."""
    datos = request.get_json(silent=True)
    if not datos:
        return jsonify({"exito": False, "tipo_error": "JsonInvalido", "mensaje": "Cuerpo de solicitud JSON esperado"}), 400

    ahora = parsear_ahora(datos.get("ahora"))

    # 1. Parsear actividad
    actividad_str = datos.get("actividad")
    actividad_encontrada = None
    for act in Actividad:
        if act.value.lower() == str(actividad_str).strip().lower():
            actividad_encontrada = act
            break
    if not actividad_encontrada:
        return jsonify({
            "exito": False,
            "tipo_error": "ActividadInvalida",
            "mensaje": f"Actividad '{actividad_str}' no válida. Opciones: {[a.value for a in Actividad]}",
        }), 400

    # 2. Parsear fecha y hora
    try:
        fecha_str = datos.get("fecha", "")
        hora_str = datos.get("hora", "")
        partes_hora = [int(p) for p in hora_str.split(":")]
        hora_h = partes_hora[0]
        hora_m = partes_hora[1] if len(partes_hora) > 1 else 0
        dia = date.fromisoformat(fecha_str)
        horario = datetime(dia.year, dia.month, dia.day, hora_h, hora_m)
    except Exception:
        return jsonify({
            "exito": False,
            "tipo_error": "HorarioInvalido",
            "mensaje": "Fecha u hora inválida. Use fecha YYYY-MM-DD y hora HH:MM.",
        }), 400

    # 3. Parsear participantes
    visitantes_raw = datos.get("visitantes")
    if not isinstance(visitantes_raw, list):
        return jsonify({
            "exito": False,
            "tipo_error": "DatosVisitanteInvalidos",
            "mensaje": "Debe informar una lista de visitantes",
        }), 422

    visitantes_objetos = []
    for v in visitantes_raw:
        if not isinstance(v, dict):
            return jsonify({
                "exito": False,
                "tipo_error": "DatosVisitanteInvalidos",
                "mensaje": "Cada participante debe tener una ficha válida",
            }), 422
        visitantes_objetos.append(
            Visitante(
                nombre=v.get("nombre"),
                dni=v.get("dni"),
                edad=v.get("edad"),
                talla=v.get("talla") if v.get("talla") else None,
            )
        )

    cantidad_personas = datos.get("cantidad_personas")
    if cantidad_personas is None:
        cantidad_personas = len(visitantes_objetos)

    val_terminos = datos.get("acepta_terminos")
    if isinstance(val_terminos, bool):
        acepta_terminos = val_terminos
    elif isinstance(val_terminos, str):
        acepta_terminos = val_terminos.strip().lower() in ("true", "1", "t", "yes", "si", "sí")
    elif isinstance(val_terminos, (int, float)):
        acepta_terminos = (val_terminos == 1)
    else:
        acepta_terminos = False

    id_terminos = datos.get("id_terminos_aceptados")
    email = datos.get("email")

    solicitud = SolicitudInscripcion(
        actividad=actividad_encontrada,
        horario=horario,
        cantidad_personas=cantidad_personas,
        visitantes=visitantes_objetos,
        acepta_terminos=acepta_terminos,
        email=email,
        id_terminos_aceptados=id_terminos,
    )

    try:
        confirmacion = servicio.inscribir(solicitud, ahora)
        return jsonify({
            "exito": True,
            "confirmacion": {
                "numero_orden": confirmacion.numero_orden,
                "destinatario": confirmacion.destinatario,
                "resumen": confirmacion.resumen,
                "subtotales": list(confirmacion.subtotales),
                "total": confirmacion.total,
                "codigos_qr": list(confirmacion.codigos_qr),
                "html": ServicioInscripcion.mostrar_confirmacion(confirmacion),
            },
        }), 201

    except HorarioInvalido as e:
        return jsonify({"exito": False, "tipo_error": "HorarioInvalido", "mensaje": str(e)}), 400
    except SinCupo as e:
        return jsonify({"exito": False, "tipo_error": "SinCupo", "mensaje": str(e)}), 409
    except EdadNoPermitida as e:
        return jsonify({"exito": False, "tipo_error": "EdadNoPermitida", "mensaje": str(e)}), 422
    except DatosVisitanteInvalidos as e:
        return jsonify({"exito": False, "tipo_error": "DatosVisitanteInvalidos", "mensaje": str(e)}), 422
    except TerminosNoAceptados as e:
        return jsonify({"exito": False, "tipo_error": "TerminosNoAceptados", "mensaje": str(e)}), 403
    except InscripcionDuplicada as e:
        return jsonify({"exito": False, "tipo_error": "InscripcionDuplicada", "mensaje": str(e)}), 409
    except ErrorInscripcion as e:
        return jsonify({"exito": False, "tipo_error": "ErrorInscripcion", "mensaje": str(e)}), 400
    except Exception as e:
        return jsonify({"exito": False, "tipo_error": "ErrorInesperado", "mensaje": str(e)}), 500


@app.route("/api/correos", methods=["GET"])
def obtener_correos_enviados():
    """Devuelve la bandeja de correos simulados para inspección visual en frontend."""
    lista = []
    for c in reversed(servicio.correos_enviados):
        lista.append({
            "numero_orden": c.numero_orden,
            "destinatario": c.destinatario,
            "resumen": c.resumen,
            "total": c.total,
            "cantidad_qr": len(c.codigos_qr),
            "codigos_qr": list(c.codigos_qr),
        })
    return jsonify({"correos": lista, "total_enviados": len(lista)})


@app.route("/api/reset", methods=["POST"])
def resetear_servicio():
    """Restablece el estado de cupos e inscripciones en memoria."""
    global servicio
    servicio = crear_servicio_inicial()
    return jsonify({"exito": True, "mensaje": "Servicio reiniciado con datos de prueba iniciales"})


if __name__ == "__main__":
    print("Iniciando EcoHarmony Park Web App en http://127.0.0.1:5000")
    app.run(host="127.0.0.1", port=5000, debug=True)
