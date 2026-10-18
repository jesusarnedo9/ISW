from datetime import datetime, timedelta

import pytest

from ecoharmony_park import HorarioInvalido


def test_seleccionar_un_horario_en_el_futuro(servicio, ahora, horario_seleccionado):
    assert servicio.seleccionar_horario(horario_seleccionado, ahora) == horario_seleccionado


def test_seleccionar_un_horario_en_el_pasado(servicio, ahora):
    horario_pasado = ahora - timedelta(hours=1)

    with pytest.raises(HorarioInvalido):
        servicio.seleccionar_horario(horario_pasado, ahora)


@pytest.mark.parametrize("hora", range(9, 18))
def test_aceptar_cada_turno_horario_disponible(servicio, hora):
    # Se parte de las 8:00 para que todos los turnos 9-17 sean futuros y con
    # la anticipación mínima exigida.
    ahora = datetime(2026, 10, 20, 8, 0)
    turno = datetime(2026, 10, 20, hora, 0)

    assert servicio.seleccionar_horario(turno, ahora) == turno


@pytest.mark.parametrize(
    "turno",
    [datetime(2026, 10, 20, 8, 0), datetime(2026, 10, 20, 18, 0)],
    ids=["antes-de-las-9", "a-las-18-cota-superior"],
)
def test_rechazar_horarios_fuera_de_los_turnos(servicio, ahora, turno):
    with pytest.raises(HorarioInvalido):
        servicio.seleccionar_horario(turno, ahora)


def test_rechazar_un_turno_que_no_comienza_en_hora_exacta(servicio, ahora):
    with pytest.raises(HorarioInvalido):
        servicio.seleccionar_horario(datetime(2026, 10, 20, 15, 30), ahora)


def test_rechazar_un_lunes_por_cierre_del_parque(servicio):
    lunes = datetime(2026, 10, 26, 15, 0)
    ahora = datetime(2026, 10, 26, 8, 0)

    with pytest.raises(HorarioInvalido):
        servicio.seleccionar_horario(lunes, ahora)


@pytest.mark.parametrize(
    "feriado",
    [datetime(2026, 12, 25, 15, 0), datetime(2027, 1, 1, 15, 0)],
    ids=["navidad", "anio-nuevo"],
)
def test_rechazar_feriados_con_parque_cerrado(servicio, feriado):
    ahora = feriado - timedelta(hours=5)

    with pytest.raises(HorarioInvalido):
        servicio.seleccionar_horario(feriado, ahora)


def test_rechazar_inscripcion_con_mas_de_24_horas_de_anticipacion(servicio):
    ahora = datetime(2026, 10, 20, 10, 0)
    turno = datetime(2026, 10, 21, 11, 0)

    with pytest.raises(HorarioInvalido):
        servicio.seleccionar_horario(turno, ahora)


def test_rechazar_inscripcion_a_menos_de_15_minutos_del_turno(servicio):
    turno = datetime(2026, 10, 20, 15, 0)
    ahora = datetime(2026, 10, 20, 14, 46)

    with pytest.raises(HorarioInvalido):
        servicio.seleccionar_horario(turno, ahora)

