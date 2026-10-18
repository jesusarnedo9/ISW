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

