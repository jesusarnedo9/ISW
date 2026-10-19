import base64
from dataclasses import replace
from datetime import timedelta

import pytest

from ecoharmony_park import (
    Actividad,
    DatosVisitanteInvalidos,
    InscripcionDuplicada,
    ServicioInscripcion,
    SinCupo,
    SolicitudInscripcion,
    TerminosNoAceptados,
    Visitante,
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


def crear_solicitud_multiple(horario, visitantes, acepta_terminos=True):
    return SolicitudInscripcion(
        actividad=Actividad.TIROLESA,
        horario=horario,
        cantidad_personas=len(visitantes),
        visitantes=visitantes,
        acepta_terminos=acepta_terminos,
        email="ana@example.com",
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


def test_inscripcion_completa_exitosa(servicio, ahora, horario_seleccionado, visitante_valido):
    solicitud = crear_solicitud_multiple(horario_seleccionado, [visitante_valido])

    confirmacion = servicio.inscribir(solicitud, ahora)

    assert confirmacion.numero_orden
    assert confirmacion.destinatario == solicitud.email
    assert len(confirmacion.codigos_qr) == 1
    assert servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)] == 1


def test_descontar_cupos_al_inscribirse(servicio, ahora, horario_seleccionado, visitante_valido):
    cupos_iniciales = servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)]
    solicitud = crear_solicitud_multiple(horario_seleccionado, [visitante_valido])

    servicio.inscribir(solicitud, ahora)

    assert servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)] == cupos_iniciales - 1


def test_inscripcion_rechazada_no_modifica_cupos(
    servicio, ahora, horario_seleccionado, visitante_valido
):
    cupos_iniciales = servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)]
    solicitud = crear_solicitud_multiple(
        horario_seleccionado, [visitante_valido], acepta_terminos=False
    )

    with pytest.raises(TerminosNoAceptados):
        servicio.inscribir(solicitud, ahora)

    assert servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)] == cupos_iniciales


def test_inscripcion_con_varios_visitantes(servicio, ahora, horario_seleccionado, visitante_valido):
    segundo_visitante = Visitante(nombre="Luis Pérez", dni=32123456, edad=27, talla="L")
    solicitud = crear_solicitud_multiple(horario_seleccionado, [visitante_valido, segundo_visitante])

    confirmacion = servicio.inscribir(solicitud, ahora)

    assert len(confirmacion.codigos_qr) == 2
    assert servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)] == 0


def test_confirmacion_contiene_datos_de_reserva(
    servicio, ahora, horario_seleccionado, visitante_valido
):
    solicitud = crear_solicitud_multiple(horario_seleccionado, [visitante_valido])

    confirmacion = servicio.inscribir(solicitud, ahora)

    assert solicitud.actividad.value in confirmacion.resumen
    assert horario_seleccionado.strftime("%d/%m/%Y") in confirmacion.resumen
    assert horario_seleccionado.strftime("%H:%M") in confirmacion.resumen
    assert visitante_valido.nombre in confirmacion.resumen


def test_enviar_correo_de_confirmacion(
    servicio, ahora, horario_seleccionado, visitante_valido, monkeypatch
):
    correos_enviados = []
    monkeypatch.setattr(
        servicio,
        "enviar_email",
        lambda confirmacion: correos_enviados.append(confirmacion),
    )
    solicitud = crear_solicitud_multiple(horario_seleccionado, [visitante_valido])

    confirmacion = servicio.inscribir(solicitud, ahora)

    assert correos_enviados == [confirmacion]
    assert all(correos_enviados[0].codigos_qr)


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


def test_permite_inscribir_hasta_el_ultimo_cupo(ahora, horario_seleccionado):
    visitantes = [
        Visitante("Ana", 30123456, 25, "M"),
        Visitante("Luis", 32123456, 27, "L"),
    ]
    servicio = ServicioInscripcion(cupos={(Actividad.TIROLESA, horario_seleccionado): 2})

    servicio.inscribir(solicitud(Actividad.TIROLESA, horario_seleccionado, visitantes), ahora)

    assert servicio.cupos[(Actividad.TIROLESA, horario_seleccionado)] == 0


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


def test_rechaza_terminos_sin_respuesta(servicio, ahora, horario_seleccionado, visitante_valido):
    pedido = solicitud(
        Actividad.TIROLESA,
        horario_seleccionado,
        [visitante_valido],
        acepta_terminos=None,
    )

    with pytest.raises(TerminosNoAceptados):
        servicio.inscribir(pedido, ahora)


def test_permite_otra_actividad_en_un_horario_diferente(
    ahora, horario_seleccionado, visitante_valido
):
    turno_anterior = horario_seleccionado - timedelta(hours=1)
    servicio = ServicioInscripcion(
        cupos={(Actividad.TIROLESA, horario_seleccionado): 1},
        inscripciones_existentes={(str(visitante_valido.dni), turno_anterior): Actividad.SAFARI},
    )

    assert servicio.inscribir(solicitud(Actividad.TIROLESA, horario_seleccionado, [visitante_valido]), ahora).numero_orden


def test_dni_con_ceros_iniciales_no_evita_la_restriccion_de_horario(
    ahora, horario_seleccionado, visitante_valido
):
    servicio = ServicioInscripcion(
        cupos={(Actividad.TIROLESA, horario_seleccionado): 1},
        inscripciones_existentes={("030123456", horario_seleccionado): Actividad.SAFARI},
    )

    with pytest.raises(InscripcionDuplicada):
        servicio.inscribir(solicitud(Actividad.TIROLESA, horario_seleccionado, [visitante_valido]), ahora)


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
    assert ("30123456", horario_seleccionado) in servicio.inscripciones_existentes
    assert ("32123456", horario_seleccionado) in servicio.inscripciones_existentes
    html = servicio.mostrar_confirmacion(confirmacion)
    assert all(uri in html for uri in confirmacion.codigos_qr)
    assert html.count("<img ") == 2


def test_rechazo_por_cupo_no_genera_qr_ni_correo(
    servicio, ahora, horario_seleccionado, visitante_valido, monkeypatch
):
    segundo = Visitante("Luis", 32123456, 27, "L")
    tercero = Visitante("Eva", 33123456, 29, "S")
    qr_generados = []
    correos = []
    monkeypatch.setattr(servicio, "_crear_qr_uri", lambda dato: qr_generados.append(dato))
    monkeypatch.setattr(servicio, "enviar_email", correos.append)
    cupos_antes = servicio.cupos.copy()

    with pytest.raises(SinCupo):
        servicio.inscribir(
            solicitud(Actividad.TIROLESA, horario_seleccionado, [visitante_valido, segundo, tercero]),
            ahora,
        )

    assert servicio.cupos == cupos_antes
    assert servicio.inscripciones_existentes == {}
    assert qr_generados == []
    assert correos == []
