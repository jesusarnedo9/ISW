"""Contrato inicial para la fase Red de la inscripción a actividades.

No contiene lógica de negocio. Los métodos levantan ``NotImplementedError`` de
forma deliberada para que cada prueba especifique primero el comportamiento.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Mapping, Sequence


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
    """Punto de entrada del caso de uso todavía sin implementar."""

    def __init__(
        self,
        cupos: Mapping[tuple[Actividad, datetime], int] | None = None,
        inscripciones_existentes: Mapping[tuple[str, datetime], Actividad] | None = None,
    ) -> None:
        self.cupos = dict(cupos or {})
        self.inscripciones_existentes = dict(inscripciones_existentes or {})

    def seleccionar_horario(self, horario: datetime, ahora: datetime) -> datetime:
        raise NotImplementedError("Fase Red: falta implementar la selección de horario")

    def seleccionar_actividad(
        self,
        actividad: Actividad,
        horario_actividad: datetime,
        horario_seleccionado: datetime,
        cantidad_personas: int = 1,
    ) -> Actividad:
        raise NotImplementedError("Fase Red: falta implementar la selección de actividad")

    def validar_visitante(self, visitante: Visitante, actividad: Actividad) -> None:
        raise NotImplementedError("Fase Red: falta implementar la validación del visitante")

    def validar_participantes(self, cantidad_personas: int, visitantes: Sequence[Visitante]) -> None:
        raise NotImplementedError("Fase Red: falta implementar la cantidad de participantes")

    def inscribir(self, solicitud: SolicitudInscripcion, ahora: datetime) -> Confirmacion:
        raise NotImplementedError("Fase Red: falta implementar la inscripción")

