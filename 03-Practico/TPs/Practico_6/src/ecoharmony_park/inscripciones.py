"""Inscripción a actividades de EcoHarmony Park.

Implementación de la fase Green del ciclo TDD: el código mínimo necesario para
que las pruebas automatizadas de la historia "Inscribirme a actividad" pasen.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Mapping, Sequence
from uuid import uuid4


class Actividad(str, Enum):
    TIROLESA = "Tirolesa"
    SAFARI = "Safari"
    PALESTRA = "Palestra"
    JARDINERIA = "Jardinería"


class ErrorInscripcion(ValueError):
    """Error base de una inscripción inválida."""


class HorarioInvalido(ErrorInscripcion):
    pass


class SinCupo(ErrorInscripcion):
    pass


class DatosVisitanteInvalidos(ErrorInscripcion):
    pass


class EdadNoPermitida(ErrorInscripcion):
    pass


class TerminosNoAceptados(ErrorInscripcion):
    pass


class InscripcionDuplicada(ErrorInscripcion):
    pass


@dataclass(frozen=True)
class Visitante:
    nombre: object
    dni: object
    edad: object
    talla: object | None = None


@dataclass(frozen=True)
class SolicitudInscripcion:
    actividad: Actividad
    horario: datetime
    cantidad_personas: int
    visitantes: Sequence[Visitante]
    acepta_terminos: bool
    email: str = "visitante@example.com"


@dataclass(frozen=True)
class Confirmacion:
    numero_orden: str
    destinatario: str
    resumen: str
    codigos_qr: Sequence[str]


class ServicioInscripcion:
    """Punto de entrada del caso de uso de inscripción a actividades."""

    HORA_APERTURA = 9
    HORA_CIERRE = 17
    ANTICIPACION_MINIMA = timedelta(minutes=15)
    ANTICIPACION_MAXIMA = timedelta(hours=24)
    FERIADOS = {(12, 25), (1, 1)}
    EDAD_MINIMA = {Actividad.TIROLESA: 8, Actividad.PALESTRA: 12}
    ACTIVIDADES_CON_VESTIMENTA = (Actividad.TIROLESA, Actividad.PALESTRA)

    def __init__(
        self,
        cupos: Mapping[tuple[Actividad, datetime], int] | None = None,
        inscripciones_existentes: Mapping[tuple[str, datetime], Actividad] | None = None,
    ) -> None:
        self.cupos = dict(cupos or {})
        self.inscripciones_existentes = dict(inscripciones_existentes or {})

    def seleccionar_horario(self, horario: datetime, ahora: datetime) -> datetime:
        anticipacion = horario - ahora
        if anticipacion < self.ANTICIPACION_MINIMA:
            raise HorarioInvalido("El horario ya pasó o no cumple la anticipación mínima")
        if anticipacion > self.ANTICIPACION_MAXIMA:
            raise HorarioInvalido("El horario supera la anticipación máxima de 24 horas")
        if horario.minute != 0 or horario.second != 0 or horario.microsecond != 0:
            raise HorarioInvalido("Los turnos comienzan en hora exacta")
        if not self.HORA_APERTURA <= horario.hour <= self.HORA_CIERRE:
            raise HorarioInvalido("El turno está fuera del horario de atención")
        if horario.weekday() == 0:
            raise HorarioInvalido("El parque permanece cerrado los lunes")
        if (horario.month, horario.day) in self.FERIADOS:
            raise HorarioInvalido("El parque permanece cerrado en feriados")
        return horario

    def seleccionar_actividad(
        self,
        actividad: Actividad,
        horario_actividad: datetime,
        horario_seleccionado: datetime,
        cantidad_personas: int = 1,
    ) -> Actividad:
        if horario_actividad != horario_seleccionado:
            raise HorarioInvalido("La actividad no se ofrece en el horario seleccionado")
        cupo = self.cupos.get((actividad, horario_seleccionado), 0)
        if cupo < cantidad_personas:
            raise SinCupo("No hay cupos suficientes para la actividad en ese horario")
        return actividad

    def validar_visitante(self, visitante: Visitante, actividad: Actividad) -> None:
        if not isinstance(visitante.nombre, str) or not visitante.nombre.strip():
            raise DatosVisitanteInvalidos("El nombre es obligatorio")
        if isinstance(visitante.dni, bool) or not self._dni_valido(visitante.dni):
            raise DatosVisitanteInvalidos("El DNI debe contener solo dígitos")
        if isinstance(visitante.edad, bool) or not isinstance(visitante.edad, int) or visitante.edad <= 0:
            raise DatosVisitanteInvalidos("La edad debe ser un entero positivo")
        if actividad in self.ACTIVIDADES_CON_VESTIMENTA:
            if not isinstance(visitante.talla, str) or not visitante.talla.strip():
                raise DatosVisitanteInvalidos("Esta actividad requiere talle de vestimenta")
        elif visitante.talla is not None and not isinstance(visitante.talla, str):
            raise DatosVisitanteInvalidos("El talle debe ser una cadena de caracteres")
        edad_minima = self.EDAD_MINIMA.get(actividad)
        if edad_minima is not None and visitante.edad < edad_minima:
            raise EdadNoPermitida("El visitante no alcanza la edad mínima de la actividad")

    def validar_participantes(self, cantidad_personas: int, visitantes: Sequence[Visitante]) -> None:
        if isinstance(cantidad_personas, bool) or not isinstance(cantidad_personas, int) or cantidad_personas < 1:
            raise DatosVisitanteInvalidos("La cantidad de personas debe ser al menos 1")
        if len(visitantes) != cantidad_personas:
            raise DatosVisitanteInvalidos("Debe indicarse un visitante por cada persona")

    def inscribir(self, solicitud: SolicitudInscripcion, ahora: datetime) -> Confirmacion:
        if not solicitud.acepta_terminos:
            raise TerminosNoAceptados("Debe aceptar los términos y condiciones de la actividad")
        self.validar_participantes(solicitud.cantidad_personas, solicitud.visitantes)
        self.seleccionar_horario(solicitud.horario, ahora)
        self.seleccionar_actividad(
            solicitud.actividad,
            solicitud.horario,
            solicitud.horario,
            solicitud.cantidad_personas,
        )
        for visitante in solicitud.visitantes:
            if (str(visitante.dni), solicitud.horario) in self.inscripciones_existentes:
                raise InscripcionDuplicada("El visitante ya tiene una actividad en ese horario")
            self.validar_visitante(visitante, solicitud.actividad)

        self.cupos[(solicitud.actividad, solicitud.horario)] -= solicitud.cantidad_personas
        for visitante in solicitud.visitantes:
            self.inscripciones_existentes[(str(visitante.dni), solicitud.horario)] = solicitud.actividad

        nombres = ", ".join(str(v.nombre) for v in solicitud.visitantes)
        confirmacion = Confirmacion(
            numero_orden=f"ORD-{uuid4().hex[:8].upper()}",
            destinatario=solicitud.email,
            resumen=(
                f"Inscripción a {solicitud.actividad.value} "
                f"el {solicitud.horario.strftime('%d/%m/%Y')} "
                f"a las {solicitud.horario.strftime('%H:%M')}. "
                f"Participantes: {nombres}"
            ),
            codigos_qr=[f"QR-{uuid4().hex[:8].upper()}" for _ in solicitud.visitantes],
        )
        self.enviar_email(confirmacion)
        return confirmacion

    def enviar_email(self, confirmacion: Confirmacion) -> None:
        """Punto de integración del envío de correo (reemplazable en pruebas)."""

    @staticmethod
    def _dni_valido(dni: object) -> bool:
        if isinstance(dni, bool):
            return False
        if isinstance(dni, int):
            return True
        if isinstance(dni, str):
            return dni.strip().isdigit()
        return False

