import pytest

from ecoharmony_park import (
    Actividad,
    InscripcionDuplicada,
    SolicitudInscripcion,
    TerminosNoAceptados,
    Visitante
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


#### Rami ####

def crear_solicitud_multiple(horario, visitantes, acepta_terminos=True):
    return SolicitudInscripcion(
        actividad=Actividad.TIROLESA,
        horario=horario,
        cantidad_personas=len(visitantes),
        visitantes=visitantes,
        acepta_terminos=acepta_terminos,
        email="ana@example.com",
    )


def test_inscripcion_completa_exitosa(servicio, ahora, horario_seleccionado, visitante_valido):
    # Precondiciones
    solicitud = crear_solicitud_multiple(horario_seleccionado, [visitante_valido])

    # Pasos
    confirmacion = servicio.inscribir(solicitud, ahora)

    # Resultado
    assert confirmacion.numero_orden
    assert confirmacion.destinatario == solicitud.email
    assert len(confirmacion.codigos_qr) == 1
    assert servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)] == 1


def test_descontar_cupos_al_inscribirse(servicio, ahora, horario_seleccionado, visitante_valido):
    # Precondiciones
    cupos_iniciales = servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)]
    solicitud = crear_solicitud_multiple(horario_seleccionado, [visitante_valido])

    # Pasos
    servicio.inscribir(solicitud, ahora)

    # Resultado
    assert servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)] == cupos_iniciales - 1


def test_inscripcion_rechazada_no_modifica_cupos(
    servicio, ahora, horario_seleccionado, visitante_valido
):
    # Precondiciones
    cupos_iniciales = servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)]
    solicitud = crear_solicitud_multiple(
        horario_seleccionado, [visitante_valido], acepta_terminos=False
    )

    # Pasos
    with pytest.raises(TerminosNoAceptados):
        servicio.inscribir(solicitud, ahora)

    # Resultado
    assert servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)] == cupos_iniciales


def test_inscripcion_con_varios_visitantes(servicio, ahora, horario_seleccionado, visitante_valido):
    # Precondiciones
    segundo_visitante = Visitante(nombre="Luis Pérez", dni=32123456, edad=27, talla="L")
    solicitud = crear_solicitud_multiple(horario_seleccionado, [visitante_valido, segundo_visitante])

    # Pasos
    confirmacion = servicio.inscribir(solicitud, ahora)

    # Resultado
    assert len(confirmacion.codigos_qr) == 2
    assert servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)] == 0


def test_confirmacion_contiene_datos_de_reserva(
    servicio, ahora, horario_seleccionado, visitante_valido
):
    # Precondiciones
    solicitud = crear_solicitud_multiple(horario_seleccionado, [visitante_valido])

    # Pasos
    confirmacion = servicio.inscribir(solicitud, ahora)

    # Resultado
    assert solicitud.actividad.value in confirmacion.resumen
    assert horario_seleccionado.strftime("%d/%m/%Y") in confirmacion.resumen
    assert horario_seleccionado.strftime("%H:%M") in confirmacion.resumen
    assert visitante_valido.nombre in confirmacion.resumen


def test_enviar_correo_de_confirmacion(
    servicio, ahora, horario_seleccionado, visitante_valido, monkeypatch
):
    # Precondiciones: se define un punto de integración reemplazable para el correo.
    # Se reemplaza el emisor por un espía para comprobar la invocación.
    correos_enviados = []
    monkeypatch.setattr(
        servicio,
        "enviar_email",
        lambda confirmacion: correos_enviados.append(confirmacion),
    )
    solicitud = crear_solicitud_multiple(horario_seleccionado, [visitante_valido])

    # Pasos
    confirmacion = servicio.inscribir(solicitud, ahora)

    # Resultado: se envía una sola vez la confirmación con su código QR.
    assert correos_enviados == [confirmacion]
    assert all(correos_enviados[0].codigos_qr)
