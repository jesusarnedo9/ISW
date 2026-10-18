# Práctico 6 - TDD: Inscribirme a actividad

> Como visitante quiero inscribirme a una actividad para reservar mi lugar en la misma.

La rama `test/inscripciones-adicionales` implementó la primera fase Green. Esta
rama agrega pruebas Red para reglas de la historia que aún no se validaban:
actividad obligatoria y perteneciente al catálogo, talle permitido, DNI positivo,
un solo registro por DNI y turno, y horario obligatorio. También completa la
prueba que verifica la invocación del envío de correo con la confirmación y sus QR.

## Ejecutar las pruebas

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

Al crear esta rama, el resultado esperado es **79 pruebas aprobadas y 7 fallidas**.
Las siete fallas corresponden a las reglas nuevas: la actividad inválida se
prueba con dos entradas y el talle inválido con dos actividades. No se modificó
la implementación de `src/ecoharmony_park/inscripciones.py`.

## Organización

- `tests/test_horarios.py`: fechas, días de apertura, turnos y anticipación.
- `tests/test_actividades.py`: disponibilidad, cupos y edades mínimas.
- `tests/test_visitantes.py`: datos requeridos, tipos, cantidad de participantes y talles.
- `tests/test_inscripcion.py`: términos, solapamientos y confirmación por correo con QR.
- `tests/test_red_faltantes.py`: reglas pendientes detectadas después de la primera fase Green.

