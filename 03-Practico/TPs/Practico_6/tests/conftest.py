from datetime import datetime

import pytest

from ecoharmony_park import Actividad, ServicioInscripcion, Visitante


@pytest.fixture
def ahora() -> datetime:
    return datetime(2026, 10, 20, 10, 0)


@pytest.fixture
def horario_seleccionado() -> datetime:
    return datetime(2026, 10, 20, 15, 0)


@pytest.fixture
def visitante_valido() -> Visitante:
    return Visitante(nombre="Ana Pérez", dni=30123456, edad=25, talla="M")


@pytest.fixture
def servicio(horario_seleccionado: datetime) -> ServicioInscripcion:
    return ServicioInscripcion(
        cupos={
            (Actividad.TIROLESA, horario_seleccionado): 2,
            (Actividad.SAFARI, horario_seleccionado): 0,
        }
    )
