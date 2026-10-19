# Práctico 6 - TDD: Inscribirme a actividad

> Como visitante quiero inscribirme a una actividad para reservar mi lugar en la misma.

El práctico incluye el servicio de inscripción en Python, pruebas automatizadas y una interfaz web para recorrer la historia de usuario.

## Ciclo Red → Green → Refactor

1. La rama comenzó con **79 pruebas aprobadas y 7 Red**. Esas siete documentaban validaciones faltantes de actividad, talle, DNI, duplicados y horario.
2. Se agregaron casos de equivalencia: el checkpoint **Red** tuvo **93 aprobadas y 35 fallidas**. El commit Red conserva las pruebas sin modificar `src/`.
3. En **Green** se implementaron las reglas y el comprobante. La suite pasó a **128 aprobadas**.
4. En **Refactor** se separó la validación de la solicitud de la construcción de la confirmación y se normalizaron los DNI de reservas existentes. Un caso adicional capturó los ceros iniciales y se completaron clases que no estaban aisladas: **134 aprobadas**.
5. Se precisó la regla de edad: **0** es un dato válido para Safari y Jardinería; en Tirolesa y Palestra incumple la edad mínima. Las pruebas quedaron reunidas por tema.
6. Se integró la interfaz web y sus pruebas de API. La suite completa verifica tanto el dominio como la API.

## Ejecutar las pruebas

Desde este directorio, con Python 3.11 o posterior:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

## Ejecutar la interfaz

Desde este directorio:

```powershell
python app.py
```

Abrir `http://127.0.0.1:5000` en el navegador. La interfaz permite consultar cupos, inscribir participantes y visualizar el comprobante con un QR por persona. `reportlab` genera los QR como imágenes SVG. El envío de correo es simulado: las confirmaciones se guardan en memoria y pueden consultarse desde la interfaz.

## Decisiones del grupo y alcance

- La inscripción a actividades se considera incluida con la entrada: subtotal y total adicionales de **$0**. La FAQ pide esos campos en el correo, pero no fija precios de actividades.
- Hay términos distintos por actividad. Los cuatro textos e identificadores están definidos en el servicio y quedan pendientes de validación por la cátedra/PO, como exige la FAQ.
- Edad **0** representa a un menor de un año y se admite en Safari y Jardinería, que son para todas las edades.
- La validación de correo exige un formato básico `nombre@dominio`. No se inventaron límites de longitud para DNI ni nombre.
- La interfaz es una aplicación web para demostrar la historia de usuario; el envío de correo se simula en memoria.

## Archivos de pruebas

- `tests/test_horarios.py`: días, turnos y anticipación.
- `tests/test_actividades.py`: catálogo, oferta, cupos y edades mínimas.
- `tests/test_visitantes.py`: datos, cantidad y talles.
- `tests/test_inscripcion.py`: términos, solapamientos y confirmación.
- `tests/test_api.py`: integración de la interfaz con la API de inscripción.

