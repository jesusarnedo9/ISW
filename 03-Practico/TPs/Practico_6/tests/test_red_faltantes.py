"""Reglas de inscripción que aún no estaban cubiertas por la fase Green."""

from dataclasses import replace

import pytest

from ecoharmony_park import (
    Actividad,
    DatosVisitanteInvalidos,
    HorarioInvalido,
    InscripcionDuplicada,
    ServicioInscripcion,
    SolicitudInscripcion,
    Visitante,
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


@pytest.mark.parametrize("actividad", [Actividad.TIROLESA, Actividad.PALESTRA])
def test_rechaza_talle_fuera_del_catalogo(servicio, visitante_valido, actividad):
    visitante = replace(visitante_valido, talla="XXXL")

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(visitante, actividad)


def test_rechaza_dni_negativo(servicio, visitante_valido):
    visitante = replace(visitante_valido, dni=-1)

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(visitante, Actividad.TIROLESA)


def test_rechaza_dni_repetido_en_la_misma_solicitud(
    servicio, ahora, horario_seleccionado, visitante_valido, monkeypatch
):
    correos_enviados = []
    monkeypatch.setattr(servicio, "enviar_email", correos_enviados.append)
    segundo = replace(visitante_valido, nombre="Otra Ana")
    solicitud = SolicitudInscripcion(
        actividad=Actividad.TIROLESA,
        horario=horario_seleccionado,
        cantidad_personas=2,
        visitantes=[visitante_valido, segundo],
        acepta_terminos=True,
        email="ana@example.com",
    )
    cupos_antes = servicio.cupos.copy()

    with pytest.raises(InscripcionDuplicada):
        servicio.inscribir(solicitud, ahora)

    assert servicio.cupos == cupos_antes
    assert servicio.inscripciones_existentes == {}
    assert correos_enviados == []


def test_rechaza_horario_sin_seleccionar(servicio, ahora):
    with pytest.raises(HorarioInvalido):
        servicio.seleccionar_horario(None, ahora)
