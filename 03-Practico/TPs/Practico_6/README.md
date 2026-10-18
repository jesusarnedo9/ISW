# Práctico 6 - TDD: Inscribirme a actividad

Este proyecto contiene únicamente la fase **Red** del ciclo TDD para la historia de usuario:

> Como visitante quiero inscribirme a una actividad para reservar mi lugar en la misma.

La API de `src/ecoharmony_park/inscripciones.py` define el contrato mínimo para que las pruebas puedan importarse y ejecutarse. Sus operaciones todavía lanzan `NotImplementedError` de forma intencional. No hay lógica de negocio implementada.

## Ejecutar la fase Red

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest
```

El resultado esperado en esta etapa es que la colección sea exitosa y que las pruebas fallen. Una prueba verde antes de implementar el comportamiento indicaría que no está comprobando la regla esperada.

## Organización

- `tests/test_horarios.py`: fechas, días de apertura, turnos y anticipación.
- `tests/test_actividades.py`: disponibilidad, cupos y edades mínimas.
- `tests/test_visitantes.py`: datos requeridos, tipos, cantidad de participantes y talles.
- `tests/test_inscripcion.py`: términos, solapamientos y confirmación por correo con QR.

Las pruebas están escritas como tests aislados, con datos fáciles de leer y un escenario por comportamiento, siguiendo los patrones de la cátedra.

