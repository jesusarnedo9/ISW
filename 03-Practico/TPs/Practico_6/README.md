# Práctico 6 - TDD: Inscribirme a actividad

> Como visitante quiero inscribirme a una actividad para reservar mi lugar en la misma.

La [matriz de equivalencias](Matriz_equivalencias_inscripcion_actividad.md) enumera condiciones externas, clases válidas e inválidas de entrada y salida, límites y casos de prueba. Las pruebas se derivaron de ella antes de ampliar el servicio.

## Ciclo Red → Green → Refactor

1. La rama comenzó con **79 pruebas aprobadas y 7 Red**. Esas siete documentaban validaciones faltantes de actividad, talle, DNI, duplicados y horario.
2. Se agregaron casos de la matriz en `tests/test_matriz_pendientes.py`: el checkpoint **Red** tuvo **93 aprobadas y 35 fallidas**. El commit Red conserva pruebas y matriz sin modificar `src/`.
3. En **Green** se implementaron las reglas y el comprobante. La suite pasó a **128 aprobadas**.
4. En **Refactor** se separó la validación de la solicitud de la construcción de la confirmación y se normalizaron los DNI de reservas existentes. Un caso adicional capturó los ceros iniciales y se completaron clases que no estaban aisladas: **134 aprobadas**.

## Ejecutar las pruebas

Desde este directorio, con Python 3.11 o posterior:

```powershell
python -m pip install -r requirements-dev.txt
python -m pytest -v
```

Actualmente la suite cuenta con **139 pruebas unitarias e integradas** que cubren el 100% de los casos de dominio y los endpoints de la API web.

## Ejecutar la Interfaz Web (HU en vivo)

El proyecto incluye una aplicación web interactiva, minimalista y profesional construida con Flask, HTML5, Vanilla CSS y JavaScript (sin dependencias de Node.js):

```powershell
python app.py
```

Luego, abrir en el navegador: **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

### Funcionalidades de la Interfaz:
- **Flujo guiado paso a paso:**
  1. *Fecha y Turno:* Calendario con bloqueo de lunes y feriados, grilla de turnos (09:00 a 17:00 hs) y control de anticipación (15 min a 24 hs).
  2. *Actividad:* Tarjetas interactivas con badges de edad mínima, vestimenta y cupos en tiempo real.
  3. *Participantes:* Stepper de cantidad de personas (1 a 12) y fichas dinámicas por visitante. El campo de **talle** solo se muestra si la actividad lo requiere (Tirolesa y Palestra).
  4. *Términos:* Texto legal dinámico según la actividad y checkbox obligatorio.
  5. *Comprobante:* Voucher con número de orden, total ($0) y **códigos QR reales en SVG** generados por ReportLab.
- **Barra de Pruebas Rápidas (QA Presets):**
  - Botones superiores para reproducir en un clic las 6 pruebas de usuario de la cátedra:
    - **CP1:** Flujo Válido Completo (Pasa).
    - **CP2:** Actividad Sin Cupo (Falla con alerta).
    - **CP3:** Omitir Talle en Safari (Pasa).
    - **CP4:** Parque Cerrado - Lunes/Feriado (Falla).
    - **CP5:** Sin Aceptar Términos (Falla).
    - **CP6:** Sin Talle en Tirolesa (Falla).
- **Herramientas de Evaluación:**
  - Selector de *Momento simulado (Ahora)* para probar anticipaciones sin cambiar la hora del sistema.
  - Visor de *Bandeja de Correos Simulados* (`/api/correos`).
  - Botón de *Reinicio de Datos* (`/api/reset`).

## Decisiones del grupo y alcance

- La inscripción a actividades se considera incluida con la entrada: subtotal y total adicionales de **$0**. La FAQ pide esos campos en el correo, pero no fija precios de actividades.
- Hay términos distintos por actividad. Los cuatro textos e identificadores se proponen en la matriz y quedan pendientes de validación por la cátedra/PO, como exige la FAQ.
- Edad **0** representa a un menor de un año y se admite en Safari y Jardinería, que son para todas las edades.
- La validación de correo exige un formato básico `nombre@dominio`. No se inventaron límites de longitud para DNI ni nombre.
- El envío de correos se simula en memoria (`correos_enviados`) permitiendo su inspección en la interfaz y en pruebas sin requerir un servidor SMTP externo.

## Archivos de pruebas

- `tests/test_horarios.py`: días, turnos y anticipación.
- `tests/test_actividades.py`: catálogo, oferta, cupos y edades mínimas.
- `tests/test_visitantes.py`: datos, cantidad y talles.
- `tests/test_inscripcion.py`: términos, solapamientos y confirmación.
- `tests/test_red_faltantes.py`: siete casos Red del primer ciclo.
- `tests/test_matriz_pendientes.py`: casos complementarios derivados de la matriz, incluidas las salidas.
- `tests/test_api.py`: pruebas de integración de la API REST y endpoints web.


