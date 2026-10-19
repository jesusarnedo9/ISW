from datetime import timedelta

import pytest

from ecoharmony_park import Actividad, EdadNoPermitida, HorarioInvalido, SinCupo, Visitante, ServicioInscripcion



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
    [
        (Actividad.TIROLESA, 7),
        (Actividad.TIROLESA, 0),
        (Actividad.PALESTRA, 11),
        (Actividad.PALESTRA, 0),
    ],
)
def test_rechazar_visitante_por_debajo_de_la_edad_minima(servicio, actividad, edad):
    visitante = Visitante("Ana", 30123456, edad, "M")

    with pytest.raises(EdadNoPermitida):
        servicio.validar_visitante(visitante, actividad)




#### Rami ####

def test_rechazar_horario_no_disponible(horario_seleccionado):
    # Precondiciones: horario válido en principio, pero sin turno ofertado para la actividad
    servicio = ServicioInscripcion(cupos={})

    # Pasos y resultado
    with pytest.raises((SinCupo, HorarioInvalido)):
        servicio.seleccionar_actividad(
            Actividad.TIROLESA,
            horario_actividad=horario_seleccionado,
            horario_seleccionado=horario_seleccionado,
        )