"""Casos de caja negra que faltaban al contrastar la US con la matriz."""

from dataclasses import replace
from datetime import datetime, timedelta
import base64

import pytest

from ecoharmony_park import (
    Actividad,
    DatosVisitanteInvalidos,
    EdadNoPermitida,
    HorarioInvalido,
    InscripcionDuplicada,
    ServicioInscripcion,
    SinCupo,
    SolicitudInscripcion,
    TerminosNoAceptados,
    Visitante,
)


def solicitud(actividad, horario, visitantes, **cambios):
    datos = dict(
        actividad=actividad,
        horario=horario,
        cantidad_personas=len(visitantes),
        visitantes=visitantes,
        acepta_terminos=True,
        email="ana@example.com",
    )
    datos.update(cambios)
    return SolicitudInscripcion(**datos)


# CP01: una reserva completa por cada actividad, no solo seleccionar la opción.
@pytest.mark.parametrize(
    ("actividad", "edad", "talla", "capacidad"),
    [
        (Actividad.TIROLESA, 8, "M", 10),
        (Actividad.SAFARI, 0, None, 8),
        (Actividad.PALESTRA, 12, "S", 12),
        (Actividad.JARDINERIA, 0, None, 12),
    ],
)
def test_inscripcion_valida_de_cada_actividad(
    ahora, horario_seleccionado, actividad, edad, talla, capacidad
):
    servicio = ServicioInscripcion(cupos={(actividad, horario_seleccionado): capacidad})
    visitante = Visitante("Ana Pérez", 30123456, edad, talla)

    confirmacion = servicio.inscribir(solicitud(actividad, horario_seleccionado, [visitante]), ahora)

    assert actividad.value in confirmacion.resumen
    assert servicio.cupos[(actividad, horario_seleccionado)] == capacidad - 1


# CP05: los dos extremos de la ventana están incluidos; un segundo fuera no.
@pytest.mark.parametrize("anticipacion", [timedelta(hours=24), timedelta(minutes=15)])
def test_permite_limites_exactos_de_reserva(servicio, horario_seleccionado, anticipacion):
    assert servicio.seleccionar_horario(horario_seleccionado, horario_seleccionado - anticipacion) == horario_seleccionado


@pytest.mark.parametrize(
    "anticipacion", [timedelta(hours=24, seconds=1), timedelta(minutes=14, seconds=59)]
)
def test_rechaza_un_segundo_fuera_de_la_ventana(servicio, horario_seleccionado, anticipacion):
    with pytest.raises(HorarioInvalido):
        servicio.seleccionar_horario(horario_seleccionado, horario_seleccionado - anticipacion)


# CP06/07: turno inexistente y turno agotado producen resultados distintos.
def test_distingue_actividad_no_ofrecida_de_cupo_agotado(horario_seleccionado):
    sin_oferta = ServicioInscripcion(cupos={})
    agotada = ServicioInscripcion(cupos={(Actividad.SAFARI, horario_seleccionado): 0})

    with pytest.raises(HorarioInvalido):
        sin_oferta.seleccionar_actividad(Actividad.SAFARI, horario_seleccionado, horario_seleccionado)
    with pytest.raises(SinCupo):
        agotada.seleccionar_actividad(Actividad.SAFARI, horario_seleccionado, horario_seleccionado)


@pytest.mark.parametrize(
    ("actividad", "exceso"),
    [(Actividad.SAFARI, 9), (Actividad.TIROLESA, 11), (Actividad.PALESTRA, 13), (Actividad.JARDINERIA, 13)],
)
def test_no_configura_mas_cupos_que_el_maximo_de_cada_actividad(
    actividad, exceso, horario_seleccionado
):
    with pytest.raises(ValueError):
        ServicioInscripcion(cupos={(actividad, horario_seleccionado): exceso})


def test_permite_inscribir_hasta_el_ultimo_cupo(ahora, horario_seleccionado):
    visitantes = [
        Visitante("Ana", 30123456, 25, "M"),
        Visitante("Luis", 32123456, 27, "L"),
    ]
    servicio = ServicioInscripcion(cupos={(Actividad.TIROLESA, horario_seleccionado): 2})

    servicio.inscribir(solicitud(Actividad.TIROLESA, horario_seleccionado, visitantes), ahora)

    assert servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)] == 0


# CP08/09: valores que la interfaz normalmente impide, pero llegan al servicio.
@pytest.mark.parametrize("cantidad", [None, 1.5, "dos", True])
def test_rechaza_cantidad_no_entera(servicio, cantidad):
    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_participantes(cantidad, [])


@pytest.mark.parametrize("visitantes", [None, "Ana", [None]])
def test_rechaza_conjunto_de_visitantes_malformado(servicio, visitantes):
    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_participantes(1, visitantes)


# CP11: DNI debe ser positivo y solo de dígitos, sin espacios.
@pytest.mark.parametrize("dni", [0, "0", " 30123456 ", True])
def test_rechaza_dni_no_positivo_o_con_formato_invalido(servicio, visitante_valido, dni):
    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(replace(visitante_valido, dni=dni), Actividad.TIROLESA)


# CP12/13: "todas las edades" incluye menores de un año; talle no aplica a Safari.
@pytest.mark.parametrize("actividad", [Actividad.SAFARI, Actividad.JARDINERIA])
def test_edad_cero_es_valida_si_la_actividad_admite_todas_las_edades(
    servicio, visitante_valido, actividad
):
    assert servicio.validar_visitante(replace(visitante_valido, edad=0, talla=None), actividad) is None


def test_talle_no_se_valida_si_la_actividad_no_lo_requiere(servicio, visitante_valido):
    assert servicio.validar_visitante(replace(visitante_valido, talla=42), Actividad.SAFARI) is None


# CP14: los términos son distintos por actividad y solo vale aceptar los propios.
def test_cada_actividad_presenta_sus_propios_terminos(servicio):
    terminos = [servicio.terminos_para(actividad) for actividad in Actividad]

    assert len({termino.identificador for termino in terminos}) == 4
    assert all(termino.texto.strip() for termino in terminos)


def test_rechaza_terminos_de_otra_actividad(
    servicio, ahora, horario_seleccionado, visitante_valido
):
    id_ajeno = servicio.terminos_para(Actividad.SAFARI).identificador
    pedido = solicitud(
        Actividad.TIROLESA,
        horario_seleccionado,
        [visitante_valido],
        id_terminos_aceptados=id_ajeno,
    )
    cupos_antes = servicio.cupos.copy()

    with pytest.raises(TerminosNoAceptados):
        servicio.inscribir(pedido, ahora)

    assert servicio.cupos == cupos_antes
    assert servicio.inscripciones_existentes == {}


def test_acepta_terminos_de_la_actividad_elegida(
    servicio, ahora, horario_seleccionado, visitante_valido
):
    id_propio = servicio.terminos_para(Actividad.TIROLESA).identificador
    pedido = solicitud(
        Actividad.TIROLESA,
        horario_seleccionado,
        [visitante_valido],
        id_terminos_aceptados=id_propio,
    )

    assert servicio.inscribir(pedido, ahora).numero_orden


# CP15: otra hora es válida; el mismo DNI y hora no.
def test_permite_otra_actividad_en_un_horario_diferente(
    ahora, horario_seleccionado, visitante_valido
):
    turno_anterior = horario_seleccionado - timedelta(hours=1)
    servicio = ServicioInscripcion(
        cupos={(Actividad.TIROLESA, horario_seleccionado): 1},
        inscripciones_existentes={(str(visitante_valido.dni), turno_anterior): Actividad.SAFARI},
    )

    assert servicio.inscribir(solicitud(Actividad.TIROLESA, horario_seleccionado, [visitante_valido]), ahora).numero_orden


# CP16: el destinatario debe permitir la confirmación.
@pytest.mark.parametrize("email", [None, "", "   ", "ana-sin-arroba"])
def test_rechaza_correo_faltante_o_invalido_sin_reservar(
    servicio, ahora, horario_seleccionado, visitante_valido, monkeypatch, email
):
    correos = []
    monkeypatch.setattr(servicio, "enviar_email", correos.append)
    cupos_antes = servicio.cupos.copy()

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.inscribir(
            solicitud(Actividad.TIROLESA, horario_seleccionado, [visitante_valido], email=email),
            ahora,
        )

    assert servicio.cupos == cupos_antes
    assert servicio.inscripciones_existentes == {}
    assert correos == []


# CP17/20: un QR real por persona, incluido en el correo y visible en el HTML.
def test_confirmacion_contiene_detalle_importes_y_qr_mostrables(
    servicio, ahora, horario_seleccionado, visitante_valido, monkeypatch
):
    correos = []
    monkeypatch.setattr(servicio, "enviar_email", correos.append)
    otro = Visitante("Luis Pérez", 32123456, 27, "L")

    confirmacion = servicio.inscribir(
        solicitud(Actividad.TIROLESA, horario_seleccionado, [visitante_valido, otro]), ahora
    )

    assert confirmacion.subtotales == (0, 0)
    assert confirmacion.total == 0
    for visitante in [visitante_valido, otro]:
        assert visitante.nombre in confirmacion.resumen
        assert str(visitante.dni) in confirmacion.resumen
        assert str(visitante.edad) in confirmacion.resumen
        assert visitante.talla in confirmacion.resumen
    assert confirmacion.numero_orden in confirmacion.resumen
    assert len(confirmacion.codigos_qr) == 2
    assert len(set(confirmacion.codigos_qr)) == 2
    for uri in confirmacion.codigos_qr:
        assert uri.startswith("data:image/svg+xml;base64,")
        assert b"<svg" in base64.b64decode(uri.split(",", 1)[1])
    assert correos == [confirmacion]
    html = servicio.mostrar_confirmacion(confirmacion)
    assert all(uri in html for uri in confirmacion.codigos_qr)
    assert html.count("<img ") == 2


# CP19: consultar cupos y días abiertos para alimentar la interfaz.
def test_muestra_cupos_disponibles(servicio, horario_seleccionado):
    assert servicio.cupos_disponibles(Actividad.TIROLESA, horario_seleccionado) == 2
    assert servicio.cupos_disponibles(Actividad.SAFARI, horario_seleccionado) == 0


@pytest.mark.parametrize(
    ("dia", "habilitado"),
    [
        (datetime(2026, 10, 20), True),
        (datetime(2026, 10, 26), False),
        (datetime(2026, 12, 25), False),
        (datetime(2027, 1, 1), False),
    ],
)
def test_calendario_deshabilita_dias_cerrados(servicio, dia, habilitado):
    assert servicio.fecha_habilitada(dia) is habilitado
