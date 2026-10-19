from dataclasses import replace

import pytest

from ecoharmony_park import Actividad, DatosVisitanteInvalidos, Visitante


def test_seleccionar_actividad_y_proceder_ingresando_datos_del_visitante(
    servicio, visitante_valido
):
    assert servicio.validar_visitante(visitante_valido, Actividad.TIROLESA) is None


def test_seleccionar_actividad_y_proceder_sin_ingresar_datos_del_visitante(servicio):
    visitante_sin_datos = Visitante(nombre="", dni="", edad="", talla=None)

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(visitante_sin_datos, Actividad.TIROLESA)


def test_ingresar_digitos_en_el_campo_dni(servicio):
    visitante = Visitante("Ana", dni=30123456, edad=25, talla="M")

    assert servicio.validar_visitante(visitante, Actividad.TIROLESA) is None


def test_ingresar_digitos_en_el_campo_edad(servicio):
    visitante = Visitante("Ana", dni=30123456, edad=25, talla="M")

    assert servicio.validar_visitante(visitante, Actividad.TIROLESA) is None


def test_ingresar_digitos_en_el_campo_nombre(servicio):
    visitante = Visitante(nombre=1234, dni=30123456, edad=25, talla="M")

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(visitante, Actividad.TIROLESA)


def test_ingresar_digitos_en_el_campo_talla(servicio):
    visitante = Visitante("Ana", dni=30123456, edad=25, talla=42)

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(visitante, Actividad.TIROLESA)


def test_ingresar_cadena_de_caracteres_en_el_campo_dni(servicio):
    visitante = Visitante("Ana", dni="ABC123", edad=25, talla="M")

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(visitante, Actividad.TIROLESA)


def test_ingresar_cadena_de_caracteres_en_el_campo_edad(servicio):
    visitante = Visitante("Ana", dni=30123456, edad="veinticinco", talla="M")

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(visitante, Actividad.TIROLESA)


def test_ingresar_cadena_de_caracteres_en_el_campo_nombre(servicio):
    visitante = Visitante(nombre="Ana Pérez", dni=30123456, edad=25, talla="M")

    assert servicio.validar_visitante(visitante, Actividad.TIROLESA) is None


@pytest.mark.parametrize("talla", ["XS", "S", "M", "L", "XL", "XXL"])
def test_ingresar_cadena_de_caracteres_valida_en_el_campo_talla(servicio, talla):
    visitante = Visitante("Ana", dni=30123456, edad=25, talla=talla)

    assert servicio.validar_visitante(visitante, Actividad.TIROLESA) is None


@pytest.mark.parametrize("actividad", [Actividad.TIROLESA, Actividad.PALESTRA])
def test_requerir_talla_en_actividades_con_vestimenta(servicio, actividad):
    visitante = Visitante("Ana", dni=30123456, edad=25, talla=None)

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(visitante, actividad)


@pytest.mark.parametrize("actividad", [Actividad.SAFARI, Actividad.JARDINERIA])
def test_permitir_omitir_talla_en_actividades_sin_vestimenta(servicio, actividad):
    visitante = Visitante("Ana", dni=30123456, edad=25, talla=None)

    assert servicio.validar_visitante(visitante, actividad) is None


def test_requerir_un_visitante_por_cada_persona_indicada(servicio, visitante_valido):
    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_participantes(2, [visitante_valido])


def test_rechazar_cantidad_de_personas_cero(servicio):
    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_participantes(0, [])


@pytest.mark.parametrize("dni", [
    "",
    "   ",
    "ABC123",
    "30123A56"
])
def test_rechazar_dni_invalido(servicio, dni):
    visitante = Visitante(
        nombre="Ana",
        dni=dni,
        edad=25,
        talla="M"
    )

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(
            visitante,
            Actividad.TIROLESA
        )


@pytest.mark.parametrize("edad", [-10, -1])
def test_rechazar_edad_negativa(servicio, edad):
    visitante = Visitante(
        nombre="Ana",
        dni=30123456,
        edad=edad,
        talla="M"
    )

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(
            visitante,
            Actividad.SAFARI
        )


@pytest.mark.parametrize("nombre", [
    " ",
    "   ",
    "\t"
])
def test_rechazar_nombre_solo_espacios(servicio, nombre):
    visitante = Visitante(
        nombre=nombre,
        dni=30123456,
        edad=25,
        talla="M"
    )

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(
            visitante,
            Actividad.TIROLESA
        )


@pytest.mark.parametrize("cantidad", [-1, -5, -10])
def test_rechazar_cantidad_participantes_negativa(
    servicio, cantidad
):
    visitantes = []

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_participantes(
            cantidad,
            visitantes
        )


def test_rechazar_visitantes_superiores_a_cantidad(
    servicio, visitante_valido
):
    cantidad_personas = 1

    segundo_visitante = Visitante(
        nombre="Juan Pérez",
        dni=35234567,
        edad=30,
        talla="L"
    )

    visitantes = [
        visitante_valido,
        segundo_visitante
    ]

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_participantes(
            cantidad_personas,
            visitantes
        )


@pytest.mark.parametrize("actividad", [Actividad.TIROLESA, Actividad.PALESTRA])
def test_rechaza_talle_fuera_del_catalogo(servicio, visitante_valido, actividad):
    visitante = replace(visitante_valido, talla="XXXL")

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(visitante, actividad)


def test_rechaza_dni_negativo(servicio, visitante_valido):
    visitante = replace(visitante_valido, dni=-1)

    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(visitante, Actividad.TIROLESA)


@pytest.mark.parametrize("cantidad", [None, 1.5, "dos", True])
def test_rechaza_cantidad_no_entera(servicio, cantidad):
    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_participantes(cantidad, [])


@pytest.mark.parametrize("visitantes", [None, "Ana", [], [None]])
def test_rechaza_conjunto_de_visitantes_malformado(servicio, visitantes):
    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_participantes(1, visitantes)


@pytest.mark.parametrize("dni", [0, "0", " 30123456 ", True])
def test_rechaza_dni_no_positivo_o_con_formato_invalido(servicio, visitante_valido, dni):
    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(replace(visitante_valido, dni=dni), Actividad.TIROLESA)


def test_acepta_dni_numerico_ingresado_como_texto(servicio, visitante_valido):
    assert servicio.validar_visitante(
        replace(visitante_valido, dni="30123456"), Actividad.TIROLESA
    ) is None


def test_rechaza_edad_no_informada(servicio, visitante_valido):
    with pytest.raises(DatosVisitanteInvalidos):
        servicio.validar_visitante(replace(visitante_valido, edad=None), Actividad.TIROLESA)


def test_talle_no_se_valida_si_la_actividad_no_lo_requiere(servicio, visitante_valido):
    assert servicio.validar_visitante(replace(visitante_valido, talla=42), Actividad.SAFARI) is None
