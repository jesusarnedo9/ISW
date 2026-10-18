# EcoHarmony Park — Inscribirme a actividad

## Matriz de clases de equivalencia y casos de prueba

**Estado:** matriz aplicada en Red → Green → Refactor, 18/10/2026; el grupo confirmó las decisiones de implementación y los textos de términos quedan sujetos a validación docente/PO. **Alcance:** la historia «Como visitante quiero inscribirme a una actividad para reservar mi lugar en la misma».

### Cómo leer esta matriz

La cátedra separa **condiciones externas de entrada**, **clases de equivalencia de salida** y **casos de prueba**. Una clase agrupa valores que deberían provocar el mismo comportamiento. Un caso toma un representante de una clase, mantiene válidas las demás entradas y comprueba una salida. Los valores límite (por ejemplo, 15 minutos exactos y 14 minutos 59 segundos) merecen casos propios aunque pertenezcan a clases contiguas. No hace falta probar el producto cartesiano de todas las clases.

- **CEV**: clase de equivalencia válida de entrada. **CEI**: clase inválida de entrada.
- **CSV**: salida esperada ante entradas válidas. **CSI**: respuesta de rechazo esperada ante entradas inválidas. Un mensaje de error es una respuesta correcta del sistema para una entrada inválida.
- **[FAQ]**: regla expresada en las preguntas frecuentes; **[US]**: historia y criterios entregados; **[DEC]**: decisión propuesta del grupo que no está fijada por la cátedra; **[PEND]**: requiere validación o definición.

Fuentes: historia y criterios de aceptación compartidos por el grupo; `C:\Carrera\4to\ISW\Repositorio\FAQ PO TDD EcoHarmony Park.pdf` (preguntas 1, 2, 5, 8–16, 18, 23, 28–32); `C:\Carrera\4to\ISW\Repositorio\ISW\03-Practico\Guia_Ejercicios_Resueltos.pdf` (páginas 62, 65–66, 72–73 y 84–86). La matriz previa se usó para comparar el formato; las reglas de esta versión se cotejaron con la FAQ.

### Reglas de negocio verificadas

1. Las actividades son **Tirolesa, Safari, Palestra y Jardinería** [US]. Los turnos duran una hora, comienzan en punto de **09:00 a 17:00 inclusive**; a las 18:00 no hay turno [FAQ 12]. El horario del parque (08:30–19:00) no amplía los turnos de actividades [FAQ 11–12].
2. El parque cierra los lunes, el 25 de diciembre y el 1 de enero. En calendario, esos días deben estar deshabilitados [FAQ 1–2].
3. La reserva se realiza desde **24 horas antes hasta 15 minutos antes** del comienzo del turno, incluyendo ambos extremos [FAQ 23, 30; interpretación de los límites].
4. Cupos por turno: Safari **8**, Tirolesa **10**, Palestra **12**, Jardinería **12** [FAQ 13]. El visitante puede ver los cupos [FAQ 8]. No hay otro máximo por transacción: puede inscribir tantos participantes como cupos queden [FAQ 31].
5. Safari y Jardinería admiten todas las edades; Tirolesa desde 8 años y Palestra desde 12 [FAQ 15]. Tirolesa y Palestra requieren talle entre **XS, S, M, L, XL, XXL** [FAQ 9, 14].
6. Cada participante informa nombre, DNI y edad; talle si corresponde [US]. Solo se usa DNI, no pasaporte [FAQ 32]. Una persona no puede estar inscripta en dos actividades del mismo horario [FAQ 29].
7. Cada actividad tiene términos propios, que el grupo debe diseñar y enviar a validar [FAQ 16]. Deben aceptarse para inscribir [US].
8. La confirmación debe llegar por correo con número de orden, detalle de visitantes, resumen, QR, subtotales y total [FAQ 18, 28]. La simulación del envío está permitida [FAQ 5]. La interfaz debe mostrar el resultado y el QR de acceso [US/interpretación para presentación]. No hay máximo de visitantes por día [FAQ 20].

### Caso base para aislar las clases

Salvo que el caso indique otra cosa: solicitud el **martes 20/10/2026 a las 08:00** para **Tirolesa a las 10:00**; hay 2 cupos; participa Ana Pérez (DNI 30123456, 25 años, talle M); cantidad 1; sin otra reserva a las 10:00; términos de Tirolesa aceptados; correo `ana@example.com`. Al variar una clase inválida, los demás datos permanecen válidos. Los casos de capacidad crean un turno con el cupo remanente indicado.

## 1. Clases de equivalencia de entrada

| Condición externa | Clases válidas (CEV) | Clases inválidas (CEI) | Fronteras / observaciones |
|---|---|---|---|
| **Actividad elegida** | **CEV01** Tirolesa; **CEV02** Safari; **CEV03** Palestra; **CEV04** Jardinería. Se separan porque cambian cupo, edad o talle. | **CEI05** ninguna actividad; **CEI06** valor ajeno al catálogo. | Lista discreta: probar las cuatro opciones y un valor ajeno. [US] |
| **Fecha del turno / apertura** | **CEV07** martes a domingo que no sea feriado indicado. | **CEI08** fecha no elegida; **CEI09** lunes; **CEI10** 25/12; **CEI11** 01/01. | El calendario deshabilita CEI09–11; el servicio igualmente rechaza esas fechas. [FAQ 1–2] |
| **Hora del turno** | **CEV12** cualquiera de 09:00, 10:00, …, 17:00, en punto. | **CEI13** hora no elegida; **CEI14** antes de 09:00; **CEI15** 18:00 o posterior; **CEI16** hora con minutos/segundos intermedios. | 08:59 / **09:00** y **17:00** / 18:00. El horario del parque no cambia esta regla. [FAQ 11–12] |
| **Anticipación respecto al turno** | **CEV17** entre 15 minutos y 24 horas antes, extremos incluidos. | **CEI18** turno iniciado o pasado; **CEI19** futuro, pero faltan menos de 15 minutos; **CEI20** faltan más de 24 horas. | **24 h** / 24 h + 1 s; **15 min** / 14 min 59 s. [FAQ 23, 30] |
| **Oferta de la actividad en ese turno** | **CEV21** la actividad seleccionada está programada en el horario elegido. | **CEI22** la actividad no tiene ningún turno programado; **CEI23** tiene turnos, pero solo en horarios distintos del elegido. | Elegir un horario válido del parque no basta: debe estar disponible para esa actividad. [US] |
| **Cupo remanente del turno** | **CEV24** quedan al menos tantos lugares como participantes solicitados. | **CEI25** cupo agotado (0); **CEI26** quedan lugares, pero menos que la cantidad solicitada. | Cupo máximo configurado: Safari 8, Tirolesa 10, Palestra/Jardinería 12. Los máximos son del turno; no son un límite adicional por transacción. [FAQ 13, 31] |
| **Cantidad de participantes** | **CEV27** entero ≥ 1, sujeto al cupo de CEV24. | **CEI28** omitida o 0; **CEI29** negativa; **CEI30** valor no entero (texto, fracción o booleano). | 1 válido; 0 inválido. Si es mayor que el cupo, corresponde CEI26. [US, FAQ 31] |
| **Datos de participantes** | **CEV31** se informa un conjunto con exactamente un registro por cada participante indicado. | **CEI32** conjunto omitido o vacío con cantidad positiva; **CEI33** conjunto no vacío con menos registros que la cantidad; **CEI34** más registros; **CEI35** algún registro es estructuralmente incorrecto, por ejemplo `None` en lugar de una ficha. | Para cantidad 2, comparar listas de 1, 2 y 3 participantes. Los campos individuales se prueban en las filas siguientes. [US] |
| **Nombre de cada participante** | **CEV36** texto no vacío que identifica a la persona. | **CEI37** ausente, vacío o solo espacios; **CEI38** dato de otro tipo. | No se fija longitud ni se exige alfabeto ASCII: nombres con acentos, espacios o guiones deben poder usarse. Una regla que prohíba dígitos dentro del texto requiere acuerdo adicional. [US] |
| **DNI de cada participante** | **CEV39** número positivo expresado con dígitos, como entero o cadena numérica. | **CEI40** ausente/vacío; **CEI41** contiene letras u otros caracteres; **CEI42** 0 o negativo; **CEI43** otro tipo de dato (incluido booleano). | No se inventa una longitud fija porque la FAQ no la define. No se admite pasaporte. [FAQ 32; validación de formato propuesta] |
| **Edad de cada participante** | **CEV44** Safari/Jardinería: edad entera ≥ 0; **CEV45** Tirolesa: entera ≥ 8; **CEV46** Palestra: entera ≥ 12. | **CEI47** ausente; **CEI48** negativa; **CEI49** no entera; **CEI50** Tirolesa de 0 a 7; **CEI51** Palestra de 0 a 11. | 7/8 y 11/12. Edad 0 representa a un menor de un año y es válida en las actividades «todas las edades», conforme a la decisión del grupo y FAQ 15. |
| **Talle de cada participante** | **CEV52** en Tirolesa/Palestra, uno de XS, S, M, L, XL, XXL; **CEV53** en Safari/Jardinería, campo omitido. | **CEI54** falta talle donde se exige; **CEI55** talle fuera del catálogo; **CEI56** valor de tipo incorrecto donde se exige. | En Safari/Jardinería el formulario no necesita pedir talle. Si llega uno por API, se propone ignorarlo; no es un motivo de rechazo definido por la FAQ. [FAQ 9, 14] |
| **Términos de la actividad** | **CEV57** el visitante acepta expresamente la versión de términos correspondiente a la actividad elegida. | **CEI58** rechaza los términos; **CEI59** no responde; **CEI60** acepta términos de otra actividad o una versión no vigente. | **[DEC]** Identificar los términos con un ID/version por actividad; un booleano aislado no permite comprobar CEI60. [FAQ 16, US] |
| **Reservas previas del DNI** | **CEV61** no hay otra reserva en ese horario; **CEV62** existe reserva del mismo DNI en un horario distinto. | **CEI63** el DNI ya está reservado en ese mismo horario, sea para igual u otra actividad; **CEI64** el DNI aparece dos veces en la solicitud actual para el mismo horario. | Las actividades duran una hora; el choque se evalúa sobre el horario de inicio. [FAQ 12, 29] |
| **Correo de destino** | **CEV65** dirección informada con formato mínimo `nombre@dominio`. | **CEI66** dirección ausente o vacía; **CEI67** formato claramente inválido. | **[DEC]** La historia exige enviar el correo, pero no define reglas de formato ni si el correo ya está registrado. La comprobación sintáctica es una decisión del grupo. [US, FAQ 18, 28] |

**Nota sobre exhaustividad:** estas clases cubren las decisiones observables de la historia y la FAQ, no todos los objetos o cadenas que Python permite construir. Una clase como «otro tipo» representa todos los tipos con el mismo comportamiento. Las reglas sin definición oficial se identifican como [DEC] o [PEND], en vez de presentarlas como exigencias de la cátedra.

## 2. Clases de equivalencia de salida

| Condición externa de salida | Clases válidas de salida (CSV) | Clases de rechazo / salida inválida (CSI) |
|---|---|---|
| **Resultado de inscripción** | **CSV01** reserva confirmada con número de orden; **CSV02** un registro por DNI y turno; **CSV03** cupo disminuido exactamente en la cantidad de participantes. | **CSI01** actividad ausente/ajena al catálogo; **CSI02** falta fecha; **CSI03** parque cerrado ese día; **CSI04** falta hora; **CSI05** hora fuera de los turnos o no exacta; **CSI06** reserva más de 24 h antes; **CSI07** reserva con menos de 15 min o turno pasado; **CSI08** actividad no ofrecida en ese horario; **CSI09** cupo insuficiente; **CSI10** cantidad/lista de participantes inválida; **CSI11** nombre inválido; **CSI12** DNI inválido; **CSI13** edad no informada o de formato inválido; **CSI14** edad menor que la permitida para la actividad; **CSI15** talle inválido o faltante; **CSI16** términos no aceptados o no correspondientes; **CSI17** inscripción solapada o DNI repetido; **CSI18** correo ausente o inválido **[DEC]**. |
| **Estado después de rechazar** | **CSV04** tras una inscripción válida, los lugares y registros reflejan solo esa inscripción. | **CSI19** ante cualquier rechazo: cupos y reservas permanecen iguales; no se genera ni envía confirmación. La salida de error es correcta, pero la operación no produce efectos parciales. |
| **Comprobante y QR** | **CSV05** resumen con actividad, fecha, horario, nombre, DNI, edad y talle cuando corresponda de todos los participantes, más número de orden; **CSV06** un QR de acceso por participante, generado y asociado a la reserva **[DEC: cantidad de QR]**; **CSV07** QR visible en la confirmación de la interfaz. | **CSI20** no se presenta comprobante/QR de acceso para una solicitud rechazada. Un texto arbitrario con prefijo `QR-` no demuestra que exista una imagen QR escaneable. |
| **Correo de confirmación** | **CSV08** se invoca una vez el envío simulado al correo indicado, con resumen, número de orden, detalle de participantes y sus QR; **CSV09** el mensaje contiene subtotal(es) y total. | **CSI21** no se invoca envío si la inscripción se rechaza. El comportamiento ante falla técnica del emisor no fue especificado **[PEND]**. |
| **Calendario y cupos visibles** | **CSV10** solo pueden seleccionarse días abiertos; **CSV11** se muestran los cupos disponibles del turno. | **CSI22** lunes, 25/12 y 01/01 aparecen deshabilitados; **CSI23** un turno agotado o no ofrecido no se puede confirmar. Estas son salidas de interfaz, no de la clase Python actual. [FAQ 2, 8] |

Para **CSV09**, el grupo acordó **[DEC] inscripción sin cargo adicional**, incluida con la entrada: subtotal por participante `$0` y total `$0`. La FAQ exige esos campos pero no informa precios de actividades ni un pago dentro de esta historia. No se reutilizan los precios de entradas (VIP/común) como si fueran precios de actividades.

### Términos propuestos para poder probar CEV57 y CEI60

Los textos siguientes son **[DEC] propuestas del grupo, pendientes de enviar a validar**, como solicita la FAQ. La aceptación guardaría el identificador correspondiente a la actividad elegida.

| Actividad | ID propuesto | Texto breve propuesto |
|---|---|---|
| Tirolesa | `TYC-TIRO-v1` | «Tengo al menos 8 años, usaré el equipo de seguridad provisto y seguiré las indicaciones del personal». |
| Safari | `TYC-SAF-v1` | «Permaneceré en el recorrido autorizado y seguiré las indicaciones del guía». |
| Palestra | `TYC-PAL-v1` | «Tengo al menos 12 años, usaré el equipo de seguridad provisto y seguiré las indicaciones del personal». |
| Jardinería | `TYC-JAR-v1` | «Usaré las herramientas bajo supervisión y respetaré las plantas y las indicaciones del personal». |

## 3. Casos de prueba derivados de la matriz

En todos los casos se parte del **caso base**; cada fila modifica solo la condición indicada. Un caso parametrizado en `pytest` puede recorrer varios representantes. Los resultados de rechazo incluyen siempre `CSI19` (sin efectos parciales), salvo que se indique una regla de interfaz.

| ID / prioridad | Clases cubiertas y datos de prueba | Resultado esperado |
|---|---|---|
| **CP01 / Alta** | CEV01–04: inscripción válida de cada actividad, con edad/talle adecuados y cupo. | CSV01–03, CSV05–09. |
| **CP02 / Alta** | CEI05–06: ninguna actividad; `"Montaña rusa"`. | CSI01, CSI19. Ya existen pruebas Red para estos dos representantes. |
| **CP03 / Alta** | CEV07 y CEI08–11: día abierto; sin fecha; lunes; 25/12; 01/01. | Éxito para abierto; CSI02 o CSI03/CSI22 para los demás. |
| **CP04 / Alta** | CEV12, CEI13–16: 09:00 y 17:00; sin horario; 08:59; 18:00; 10:30. | Éxito en extremos válidos; CSI04 o CSI05 en los demás. El horario omitido ya tiene prueba Red. |
| **CP05 / Alta** | CEV17, CEI18–20: exactamente 24 h, 24 h + 1 s, exactamente 15 min, 14 min 59 s y turno pasado. | Éxito en los dos límites incluidos; CSI06 o CSI07 en los demás. |
| **CP06 / Alta** | CEV21 y CEI22–23: actividad ofrecida; sin oferta; oferta solo en otro turno. | Éxito o CSI08 según corresponda. |
| **CP07 / Alta** | CEV24 y CEI25–26: cupo exactamente igual a N; 0; remanente N−1. | Cupo justo confirma; los otros producen CSI09/CSI23. |
| **CP08 / Alta** | CEV27, CEI28–30: cantidad 1; 0/omitida; −1; `"dos"` o `1.5`. | Éxito o CSI10. |
| **CP09 / Alta** | CEV31 y CEI32–35: cantidad 2 con 2, 0, 1 o 3 fichas; una ficha incompleta. | Éxito solo con dos fichas completas; CSI10 en los demás. |
| **CP10 / Media** | CEV36 y CEI37–38: `"Ana Pérez"`; `"   "`; `None`; número en lugar de texto. | Éxito o CSI11. |
| **CP11 / Alta** | CEV39 y CEI40–43: DNI numérico; vacío; `"30A23456"`; 0; −1; booleano. | Éxito o CSI12. El DNI negativo ya tiene prueba Red. |
| **CP12 / Alta** | CEV44–46, CEI47–51: Safari/Jardinería edad 0; Tirolesa 7/8; Palestra 11/12; edad ausente, negativa o no entera. | Éxito en 0/8/12 según actividad; CSI13 o CSI14 en inválidos. |
| **CP13 / Alta** | CEV52–53 y CEI54–56: seis talles permitidos; omisión en Safari/Jardinería; omisión, `"XXXL"` o número en Tirolesa/Palestra. | Éxito o CSI15. `"XXXL"` ya tiene dos casos Red. |
| **CP14 / Alta** | CEV57 y CEI58–60: acepta versión propia; rechaza; no responde; acepta ID de otra actividad. | Éxito solo con aceptación correspondiente; CSI16 en el resto. El servicio admite un ID de términos además del booleano de aceptación. |
| **CP15 / Alta** | CEV61–62 y CEI63–64: sin reserva previa; reserva a otra hora; reserva a la misma hora; DNI duplicado en la solicitud. | Éxito en los dos primeros; CSI17 y CSI19 en los demás. El duplicado en la solicitud ya tiene prueba Red. |
| **CP16 / Media** | CEV65 y CEI66–67: `ana@example.com`; vacío; `"ana-sin-arroba"`. | Éxito/CSV08 con correo válido; CSI18 y CSI21 con inválidos si se adopta [DEC]. |
| **CP17 / Alta** | Una inscripción válida con N=2 y emisor simulado observado por un espía. | Un número de orden, detalle de las 2 personas, 2 QR generados, subtotales `$0`, total `$0` y una sola invocación de envío: CSV05–09. |
| **CP18 / Alta** | Repetir un representante de cada rechazo con cupos, registros y espía de correo inicializados. | Error correspondiente, cupos/registros sin cambios y cero envíos: CSI19–21. |
| **CP19 / Media** | Vista de calendario con lunes, 25/12 y 01/01; vista de actividad con cupos. | CSV10–11, CSI22–23. El servicio expone días habilitados y cupos; la interfaz móvil completa queda fuera de este repositorio. |
| **CP20 / Media** | Inscripción válida observada desde la confirmación. | CSV07: el QR generado se incluye en un fragmento HTML mostrable. La aplicación móvil completa queda fuera de este repositorio. |

### Ejemplo concreto: de la matriz a Python

**CP05** toma la clase válida CEV17 en el límite exacto de 15 minutos y la clase inválida CEI19 un segundo después. El test no se reemplaza al pasar de Red a Green: se escribe una vez, falla con el código incompleto y luego se cambia la implementación hasta que pase.

```python
turno = datetime(2026, 10, 20, 15, 0)
assert servicio.seleccionar_horario(turno, datetime(2026, 10, 20, 14, 45)) == turno

with pytest.raises(HorarioInvalido):
    servicio.seleccionar_horario(turno, datetime(2026, 10, 20, 14, 45, 1))
```

## 4. Decisiones del grupo y puntos pendientes de validación

1. **Validación docente/PO de los cuatro textos de términos.** La FAQ exige enviarlos para validación. Hasta contar con ese visto bueno, los textos e ID/version son propuestas del grupo, no reglas oficiales.
2. **Actividad sin cargo adicional.** El grupo decidió que la inscripción está incluida con la entrada. Los subtotales y el total adicionales son `$0`. Si la cátedra define precios de actividades, habrá que actualizar CSV09 y CP17.
3. **Edad 0 en Safari/Jardinería.** El grupo confirmó que «todas las edades» incluye bebés menores de un año. Tirolesa y Palestra conservan los límites de 8 y 12 años fijados en la FAQ.
4. **Formato de correo y nombres.** El grupo confirmó validaciones mínimas sin reglas arbitrarias de longitud.
5. **Interfaz móvil completa.** El servicio genera QR SVG reales y un fragmento HTML que los muestra. La aplicación y el frontend quedan para el equipo que los implementará; las pruebas de pantalla requieren esa capa de interfaz.
6. **Falla técnica del envío de correo.** La FAQ admite simular el envío, pero no define reintentos ni si la reserva se revierte cuando el emisor falla. No se agregará una clase de rechazo con rollback sin decidir antes esa política.

### Estado respecto del repositorio actual

La rama `test/inscripciones-red-faltantes` partió de **79 aprobadas y 7 Red**. Al agregar los casos de esta matriz, el checkpoint Red quedó en **93 aprobadas y 35 Red**. Tras Green, un caso adicional sobre DNI con ceros iniciales y casos de cobertura de clases antes implícitas, la suite completa queda en **134 aprobadas**. Los cambios están separados en commits Red, Green y Refactor para que se vea el ciclo TDD.
