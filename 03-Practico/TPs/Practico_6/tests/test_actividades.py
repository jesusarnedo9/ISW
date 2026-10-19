from dataclasses import replace
from datetime import timedelta

import pytest

from ecoharmony_park import (
    Actividad,
    EdadNoPermitida,
    HorarioInvalido,
    ServicioInscripcion,
    SinCupo,
    SolicitudInscripcion,
    Visitante,
)


def test_elegir_actividad_con_cupo_en_el_horario_seleccionado(servicio, horario_seleccionado):
    elegida = servicio.seleccionar_actividad(
        Actividad.TIROLESA,
        horario_actividad=horario_seleccionado,
        horario_seleccionado=horario_seleccionado,
    )

    assert elegida == Actividad.TIROLESA


def test_elegir_actividad_sin_cupo_en_el_horario_seleccionado(servicio, horario_seleccionado):
    with pytest.raises(SinCupo):
        servicio.seleccionar_actividad(
            Actividad.SAFARI,
            horario_actividad=horario_seleccionado,
            horario_seleccionado=horario_seleccionado,
        )


def test_elegir_actividad_con_cupo_fuera_del_horario_seleccionado(servicio, horario_seleccionado):
    otro_horario = horario_seleccionado + timedelta(hours=1)
    servicio.cupos[(Actividad.TIROLESA, otro_horario)] = 2

    with pytest.raises(HorarioInvalido):
        servicio.seleccionar_actividad(
            Actividad.TIROLESA,
            horario_actividad=otro_horario,
            horario_seleccionado=horario_seleccionado,
        )


def test_elegir_actividad_sin_cupo_fuera_del_horario_seleccionado(servicio, horario_seleccionado):
    otro_horario = horario_seleccionado + timedelta(hours=1)
    servicio.cupos[(Actividad.SAFARI, otro_horario)] = 0

    with pytest.raises(HorarioInvalido):
        servicio.seleccionar_actividad(
            Actividad.SAFARI,
            horario_actividad=otro_horario,
            horario_seleccionado=horario_seleccionado,
        )


@pytest.mark.parametrize("actividad", list(Actividad))
def test_permitir_solo_las_cuatro_actividades_del_parque(actividad, horario_seleccionado):
    from ecoharmony_park import ServicioInscripcion

    servicio = ServicioInscripcion(cupos={(actividad, horario_seleccionado): 1})

    assert servicio.seleccionar_actividad(
        actividad, horario_seleccionado, horario_seleccionado
    ) == actividad


def test_rechazar_cantidad_de_personas_mayor_al_cupo(servicio, horario_seleccionado):
    with pytest.raises(SinCupo):
        servicio.seleccionar_actividad(
            Actividad.TIROLESA,
            horario_seleccionado,
            horario_seleccionado,
            cantidad_personas=3,
        )


@pytest.mark.parametrize(
    ("actividad", "edad_minima"),
    [(Actividad.TIROLESA, 8), (Actividad.PALESTRA, 12)],
)
def test_aceptar_edad_minima_de_actividad(servicio, actividad, edad_minima):
    visitante = Visitante("Ana", 30123456, edad_minima, "M")

    assert servicio.validar_visitante(visitante, actividad) is None


@pytest.mark.parametrize(
    ("actividad", "edad"),
    [(Actividad.TIROLESA, 7), (Actividad.PALESTRA, 11)],
)
def test_rechazar_visitante_por_debajo_de_la_edad_minima(servicio, actividad, edad):
    visitante = Visitante("Ana", 30123456, edad, "M")

    with pytest.raises(EdadNoPermitida):
        servicio.validar_visitante(visitante, actividad)


@pytest.mark.parametrize("actividad", [Actividad.TIROLESA, Actividad.PALESTRA])
def test_edad_cero_es_rechazada_por_el_minimo_de_la_actividad(servicio, actividad):
    visitante = Visitante("Ana", 30123456, 0, "M")

    with pytest.raises(EdadNoPermitida):
        servicio.validar_visitante(visitante, actividad)


def test_rechazar_horario_no_disponible(horario_seleccionado):
    servicio = ServicioInscripcion(cupos={})

    with pytest.raises((SinCupo, HorarioInvalido)):
        servicio.seleccionar_actividad(
            Actividad.TIROLESA,
            horario_actividad=horario_seleccionado,
            horario_seleccionado=horario_seleccionado,
        )


@pytest.mark.parametrize(
    "actividad", ["Montaña rusa", None], ids=["fuera-del-catalogo", "sin-seleccion"]
)
def test_rechaza_actividad_invalida_aunque_tenga_cupo(
    actividad, ahora, horario_seleccionado, visitante_valido
):
    servicio = ServicioInscripcion(cupos={(actividad, horario_seleccionado): 1})
    solicitud = SolicitudInscripcion(
        actividad=actividad,
        horario=horario_seleccionado,
        cantidad_personas=1,
        visitantes=[visitante_valido],
        acepta_terminos=True,
        email="ana@example.com",
    )

    with pytest.raises(ValueError):
        servicio.inscribir(solicitud, ahora)

    assert servicio.cupos[(actividad, horario_seleccionado)] == 1
    assert servicio.inscripciones_existentes == {}


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


@pytest.mark.parametrize("actividad", [Actividad.SAFARI, Actividad.JARDINERIA])
def test_edad_cero_es_valida_si_la_actividad_admite_todas_las_edades(
    servicio, visitante_valido, actividad
):
    assert servicio.validar_visitante(replace(visitante_valido, edad=0, talla=None), actividad) is None


def test_muestra_cupos_disponibles(servicio, horario_seleccionado):
    assert servicio.cupos_disponibles(Actividad.TIROLESA, horario_seleccionado) == 2
    assert servicio.cupos_disponibles(Actividad.SAFARI, horario_seleccionado) == 0
