import pytest

from ecoharmony_park import (
    Actividad,
    InscripcionDuplicada,
    SolicitudInscripcion,
    TerminosNoAceptados,
)


def crear_solicitud(horario, visitante, acepta_terminos=True):
    return SolicitudInscripcion(
        actividad=Actividad.TIROLESA,
        horario=horario,
        cantidad_personas=1,
        visitantes=[visitante],
        acepta_terminos=acepta_terminos,
        email="ana@example.com",
    )


def test_proceder_aceptando_terminos_y_condiciones(
    servicio, ahora, horario_seleccionado, visitante_valido
):
    solicitud = crear_solicitud(horario_seleccionado, visitante_valido, acepta_terminos=True)

    confirmacion = servicio.inscribir(solicitud, ahora)

    assert confirmacion.numero_orden


def test_proceder_sin_aceptar_terminos_y_condiciones(
    servicio, ahora, horario_seleccionado, visitante_valido
):
    solicitud = crear_solicitud(horario_seleccionado, visitante_valido, acepta_terminos=False)

    with pytest.raises(TerminosNoAceptados):
        servicio.inscribir(solicitud, ahora)


def test_impedir_que_un_dni_reserve_otra_actividad_en_el_mismo_horario(
    servicio, ahora, horario_seleccionado, visitante_valido
):
    servicio.inscripciones_existentes[(str(visitante_valido.dni), horario_seleccionado)] = (
        Actividad.SAFARI
    )
    solicitud = crear_solicitud(horario_seleccionado, visitante_valido)

    with pytest.raises(InscripcionDuplicada):
        servicio.inscribir(solicitud, ahora)


def test_enviar_confirmacion_al_email_del_visitante(
    servicio, ahora, horario_seleccionado, visitante_valido
):
    solicitud = crear_solicitud(horario_seleccionado, visitante_valido)

    confirmacion = servicio.inscribir(solicitud, ahora)

    assert confirmacion.destinatario == "ana@example.com"
    assert "Tirolesa" in confirmacion.resumen


def test_incluir_un_codigo_qr_por_visitante_en_la_confirmacion(
    servicio, ahora, horario_seleccionado, visitante_valido
):
    solicitud = crear_solicitud(horario_seleccionado, visitante_valido)

    confirmacion = servicio.inscribir(solicitud, ahora)

    assert len(confirmacion.codigos_qr) == solicitud.cantidad_personas
    assert all(confirmacion.codigos_qr)

