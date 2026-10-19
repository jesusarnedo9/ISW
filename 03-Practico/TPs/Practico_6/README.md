# Práctico 6 - TDD: Inscribirme a actividad

> Como visitante quiero inscribirme a una actividad para reservar mi lugar en la misma.

La [matriz de equivalencias](Matriz_equivalencias_inscripcion_actividad.md) enumera condiciones externas, clases válidas e inválidas de entrada y salida, límites y casos de prueba. Las pruebas se derivaron de ella antes de ampliar el servicio.

## Ciclo Red → Green → Refactor

1. La rama comenzó con **79 pruebas aprobadas y 7 Red**. Esas siete documentaban validaciones faltantes de actividad, talle, DNI, duplicados y horario.
2. Se agregaron casos de la matriz: el checkpoint **Red** tuvo **93 aprobadas y 35 fallidas**. El commit Red conserva pruebas y matriz sin modificar `src/`.
3. En **Green** se implementaron las reglas y el comprobante. La suite pasó a **128 aprobadas**.
4. En **Refactor** se separó la validación de la solicitud de la construcción de la confirmación y se normalizaron los DNI de reservas existentes. Un caso adicional capturó los ceros iniciales y se completaron clases que no estaban aisladas: **134 aprobadas**.
5. Se precisó la regla de edad: **0** es un dato válido para Safari y Jardinería; en Tirolesa y Palestra incumple la edad mínima. Las pruebas quedaron reunidas por tema y la suite actual tiene **135 casos aprobados**.

## Ejecutar las pruebas

Desde este directorio, con Python 3.11 o posterior:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -q
```

`reportlab` genera un QR SVG real por participante. El servicio devuelve cada imagen como URI `data:image/svg+xml;base64,...`; `mostrar_confirmacion` arma un fragmento HTML que puede mostrarse en una interfaz. `enviar_email` simula el envío guardando la confirmación en `correos_enviados` y puede reemplazarse por un espía en las pruebas.

## Decisiones del grupo y alcance

- La inscripción a actividades se considera incluida con la entrada: subtotal y total adicionales de **$0**. La FAQ pide esos campos en el correo, pero no fija precios de actividades.
- Hay términos distintos por actividad. Los cuatro textos e identificadores se proponen en la matriz y quedan pendientes de validación por la cátedra/PO, como exige la FAQ.
- Edad **0** representa a un menor de un año y se admite en Safari y Jardinería, que son para todas las edades.
- La validación de correo exige un formato básico `nombre@dominio`. No se inventaron límites de longitud para DNI ni nombre.
- Este repositorio contiene el servicio Python, pruebas y un fragmento HTML de confirmación. No contiene una aplicación móvil completa ni un proveedor real de correo; la FAQ permite simular el envío.

## Archivos de pruebas

- `tests/test_horarios.py`: días, turnos y anticipación.
- `tests/test_actividades.py`: catálogo, oferta, cupos y edades mínimas.
- `tests/test_visitantes.py`: datos, cantidad y talles.
- `tests/test_inscripcion.py`: términos, solapamientos y confirmación.

