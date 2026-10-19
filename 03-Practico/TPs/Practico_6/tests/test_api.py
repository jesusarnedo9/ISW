"""Pruebas de integración de la API REST de la interfaz web."""

import pytest
from datetime import datetime, timedelta
import app as flask_app_module


@pytest.fixture
def client():
    flask_app_module.app.config["TESTING"] = True
    # Resetear servicio antes de cada test
    flask_app_module.servicio = flask_app_module.crear_servicio_inicial()
    with flask_app_module.app.test_client() as client:
        yield client


def fecha_y_horario_valido():
    """Calcula una fecha habilitada y un momento simulado válido dentro del rango de cupos generados."""
    hoy = datetime.now().date()
    for offset in range(1, 6):
        candidato = hoy + timedelta(days=offset)
        if flask_app_module.servicio.fecha_habilitada(candidato):
            fecha_str = candidato.strftime("%Y-%m-%d")
            ahora_str = f"{fecha_str}T08:00:00"
            return fecha_str, ahora_str
    fecha_str = hoy.strftime("%Y-%m-%d")
    return fecha_str, f"{fecha_str}T08:00:00"


def test_api_config(client):
    res = client.get("/api/config")
    assert res.status_code == 200
    data = res.get_json()
    assert "actividades" in data
    assert len(data["actividades"]) == 4
    assert "feriados" in data
    assert "turnos_horas" in data


def test_api_cupos_fecha_valida(client):
    fecha_str, _ = fecha_y_horario_valido()
    res = client.get(f"/api/cupos?fecha={fecha_str}")
    assert res.status_code == 200
    data = res.get_json()
    assert "turnos" in data
    assert "parque_abierto" in data


def test_api_inscribir_exitoso(client):
    fecha_str, ahora_str = fecha_y_horario_valido()
    payload = {
        "actividad": "Tirolesa",
        "fecha": fecha_str,
        "hora": "10:00",
        "cantidad_personas": 1,
        "visitantes": [
            {"nombre": "Ana Pérez", "dni": 30123456, "edad": 25, "talla": "M"}
        ],
        "acepta_terminos": True,
        "id_terminos_aceptados": "TYC-TIRO-v1",
        "email": "ana@example.com",
        "ahora": ahora_str,
    }
    res = client.post("/api/inscribir", json=payload)
    assert res.status_code == 201
    data = res.get_json()
    assert data["exito"] is True
    assert "numero_orden" in data["confirmacion"]
    assert len(data["confirmacion"]["codigos_qr"]) == 1
    assert data["confirmacion"]["codigos_qr"][0].startswith("data:image/svg+xml;base64,")


def test_api_inscribir_sin_aceptar_terminos(client):
    fecha_str, ahora_str = fecha_y_horario_valido()
    payload = {
        "actividad": "Tirolesa",
        "fecha": fecha_str,
        "hora": "10:00",
        "cantidad_personas": 1,
        "visitantes": [
            {"nombre": "Ana Pérez", "dni": 30123456, "edad": 25, "talla": "M"}
        ],
        "acepta_terminos": False,
        "email": "ana@example.com",
        "ahora": ahora_str,
    }
    res = client.post("/api/inscribir", json=payload)
    assert res.status_code == 403
    data = res.get_json()
    assert data["exito"] is False
    assert data["tipo_error"] == "TerminosNoAceptados"


def test_api_inscribir_con_acepta_terminos_texto_false(client):
    fecha_str, ahora_str = fecha_y_horario_valido()
    payload = {
        "actividad": "Tirolesa",
        "fecha": fecha_str,
        "hora": "10:00",
        "cantidad_personas": 1,
        "visitantes": [
            {"nombre": "Ana Pérez", "dni": 30123456, "edad": 25, "talla": "M"}
        ],
        "acepta_terminos": "false",
        "email": "ana@example.com",
        "ahora": ahora_str,
    }
    res = client.post("/api/inscribir", json=payload)
    assert res.status_code == 403
    data = res.get_json()
    assert data["exito"] is False
    assert data["tipo_error"] == "TerminosNoAceptados"


@pytest.mark.parametrize(
    "visitantes_invalidos",
    [
        None,
        "cadena_invalida",
        123,
        [None],
        ["invalido"],
        [{"nombre": "Ana"}, None],
    ],
)
def test_api_inscribir_visitantes_mal_formados_no_provoca_error_500(client, visitantes_invalidos):
    fecha_str, ahora_str = fecha_y_horario_valido()
    payload = {
        "actividad": "Tirolesa",
        "fecha": fecha_str,
        "hora": "10:00",
        "cantidad_personas": 1,
        "visitantes": visitantes_invalidos,
        "acepta_terminos": True,
        "id_terminos_aceptados": "TYC-TIRO-v1",
        "email": "ana@example.com",
        "ahora": ahora_str,
    }
    res = client.post("/api/inscribir", json=payload)
    assert res.status_code == 422
    data = res.get_json()
    assert data["exito"] is False
    assert data["tipo_error"] == "DatosVisitanteInvalidos"


def test_api_correos_enviados(client):
    fecha_str, ahora_str = fecha_y_horario_valido()
    payload = {
        "actividad": "Safari",
        "fecha": fecha_str,
        "hora": "11:00",
        "cantidad_personas": 1,
        "visitantes": [
            {"nombre": "Carlos Gómez", "dni": 28999888, "edad": 30}
        ],
        "acepta_terminos": True,
        "id_terminos_aceptados": "TYC-SAF-v1",
        "email": "carlos@example.com",
        "ahora": ahora_str,
    }
    client.post("/api/inscribir", json=payload)

    res = client.get("/api/correos")
    assert res.status_code == 200
    data = res.get_json()
    assert data["total_enviados"] >= 1
    assert data["correos"][0]["destinatario"] == "carlos@example.com"
