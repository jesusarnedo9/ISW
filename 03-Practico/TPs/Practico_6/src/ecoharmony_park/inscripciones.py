"""Reglas de inscripción a actividades de EcoHarmony Park."""

from base64 import b64encode
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from enum import Enum
from html import escape
import re
from typing import Mapping, Sequence
from uuid import uuid4

from reportlab.graphics import renderSVG
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing


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
class TerminosActividad:
    identificador: str
    texto: str


@dataclass(frozen=True)
class SolicitudInscripcion:
    actividad: Actividad
    horario: datetime
    cantidad_personas: int
    visitantes: Sequence[Visitante]
    acepta_terminos: bool
    email: str = "visitante@example.com"
    id_terminos_aceptados: str | None = None


@dataclass(frozen=True)
class Confirmacion:
    numero_orden: str
    destinatario: str
    resumen: str
    codigos_qr: Sequence[str]
    subtotales: tuple[int, ...]
    total: int


class ServicioInscripcion:
    """Punto de entrada del caso de uso de inscripción a actividades."""

    HORA_APERTURA = 9
    HORA_CIERRE = 17
    ANTICIPACION_MINIMA = timedelta(minutes=15)
    ANTICIPACION_MAXIMA = timedelta(hours=24)
    FERIADOS = {(12, 25), (1, 1)}
    EDAD_MINIMA = {Actividad.TIROLESA: 8, Actividad.PALESTRA: 12}
    ACTIVIDADES_CON_VESTIMENTA = (Actividad.TIROLESA, Actividad.PALESTRA)
    TALLES = frozenset({"XS", "S", "M", "L", "XL", "XXL"})
    CUPO_MAXIMO = {
        Actividad.SAFARI: 8,
        Actividad.TIROLESA: 10,
        Actividad.PALESTRA: 12,
        Actividad.JARDINERIA: 12,
    }
    TERMINOS = {
        Actividad.TIROLESA: TerminosActividad(
            "TYC-TIRO-v1",
            "Tengo al menos 8 años, usaré el equipo de seguridad provisto y seguiré las indicaciones del personal.",
        ),
        Actividad.SAFARI: TerminosActividad(
            "TYC-SAF-v1",
            "Permaneceré en el recorrido autorizado y seguiré las indicaciones del guía.",
        ),
        Actividad.PALESTRA: TerminosActividad(
            "TYC-PAL-v1",
            "Tengo al menos 12 años, usaré el equipo de seguridad provisto y seguiré las indicaciones del personal.",
        ),
        Actividad.JARDINERIA: TerminosActividad(
            "TYC-JAR-v1",
            "Usaré las herramientas bajo supervisión y respetaré las plantas y las indicaciones del personal.",
        ),
    }

    def __init__(
        self,
        cupos: Mapping[tuple[Actividad, datetime], int] | None = None,
        inscripciones_existentes: Mapping[tuple[str, datetime], Actividad] | None = None,
    ) -> None:
        self.cupos = dict(cupos or {})
        self.inscripciones_existentes = dict(inscripciones_existentes or {})
        self.correos_enviados: list[Confirmacion] = []
        for (actividad, _), disponibles in self.cupos.items():
            if actividad in self.CUPO_MAXIMO and (
                isinstance(disponibles, bool)
                or not isinstance(disponibles, int)
                or disponibles < 0
                or disponibles > self.CUPO_MAXIMO[actividad]
            ):
                raise ValueError("El cupo configurado excede el máximo o es inválido")

    def fecha_habilitada(self, dia: date) -> bool:
        return (
            isinstance(dia, date)
            and dia.weekday() != 0
            and (dia.month, dia.day) not in self.FERIADOS
        )

    def cupos_disponibles(self, actividad: Actividad, horario: datetime) -> int:
        return self.cupos.get((actividad, horario), 0)

    def terminos_para(self, actividad: Actividad) -> TerminosActividad:
        if not isinstance(actividad, Actividad):
            raise ValueError("Debe seleccionar una actividad del catálogo")
        return self.TERMINOS[actividad]

    def seleccionar_horario(self, horario: datetime, ahora: datetime) -> datetime:
        if not isinstance(horario, datetime) or not isinstance(ahora, datetime):
            raise HorarioInvalido("Debe seleccionar un horario válido")
        anticipacion = horario - ahora
        if anticipacion < self.ANTICIPACION_MINIMA:
            raise HorarioInvalido("El horario ya pasó o no cumple la anticipación mínima")
        if anticipacion > self.ANTICIPACION_MAXIMA:
            raise HorarioInvalido("El horario supera la anticipación máxima de 24 horas")
        if horario.minute != 0 or horario.second != 0 or horario.microsecond != 0:
            raise HorarioInvalido("Los turnos comienzan en hora exacta")
        if not self.HORA_APERTURA <= horario.hour <= self.HORA_CIERRE:
            raise HorarioInvalido("El turno está fuera del horario de atención")
        if not self.fecha_habilitada(horario):
            raise HorarioInvalido("El parque permanece cerrado ese día")
        return horario

    def seleccionar_actividad(
        self,
        actividad: Actividad,
        horario_actividad: datetime,
        horario_seleccionado: datetime,
        cantidad_personas: int = 1,
    ) -> Actividad:
        if not isinstance(actividad, Actividad):
            raise ValueError("Debe seleccionar una actividad del catálogo")
        if horario_actividad != horario_seleccionado:
            raise HorarioInvalido("La actividad no se ofrece en el horario seleccionado")
        if (actividad, horario_seleccionado) not in self.cupos:
            raise HorarioInvalido("La actividad no se ofrece en el horario seleccionado")
        cupo = self.cupos[(actividad, horario_seleccionado)]
        if cupo < cantidad_personas:
            raise SinCupo("No hay cupos suficientes para la actividad en ese horario")
        return actividad

    def validar_visitante(self, visitante: Visitante, actividad: Actividad) -> None:
        if not isinstance(visitante, Visitante):
            raise DatosVisitanteInvalidos("Debe informar los datos de cada visitante")
        if not isinstance(visitante.nombre, str) or not visitante.nombre.strip():
            raise DatosVisitanteInvalidos("El nombre es obligatorio")
        if isinstance(visitante.dni, bool) or not self._dni_valido(visitante.dni):
            raise DatosVisitanteInvalidos("El DNI debe contener solo dígitos")
        if isinstance(visitante.edad, bool) or not isinstance(visitante.edad, int) or visitante.edad < 0:
            raise DatosVisitanteInvalidos("La edad debe ser un entero no negativo")
        if visitante.edad == 0 and actividad in self.EDAD_MINIMA:
            raise DatosVisitanteInvalidos("La edad no alcanza el mínimo de la actividad")
        if actividad in self.ACTIVIDADES_CON_VESTIMENTA:
            if not isinstance(visitante.talla, str) or not visitante.talla.strip():
                raise DatosVisitanteInvalidos("Esta actividad requiere talle de vestimenta")
            if visitante.talla not in self.TALLES:
                raise DatosVisitanteInvalidos("El talle no pertenece al catálogo")
        edad_minima = self.EDAD_MINIMA.get(actividad)
        if edad_minima is not None and visitante.edad < edad_minima:
            raise EdadNoPermitida("El visitante no alcanza la edad mínima de la actividad")

    def validar_participantes(self, cantidad_personas: int, visitantes: Sequence[Visitante]) -> None:
        if isinstance(cantidad_personas, bool) or not isinstance(cantidad_personas, int) or cantidad_personas < 1:
            raise DatosVisitanteInvalidos("La cantidad de personas debe ser al menos 1")
        if not isinstance(visitantes, Sequence) or isinstance(visitantes, (str, bytes)):
            raise DatosVisitanteInvalidos("Debe informar una lista de visitantes")
        if len(visitantes) != cantidad_personas:
            raise DatosVisitanteInvalidos("Debe indicarse un visitante por cada persona")
        if any(not isinstance(visitante, Visitante) for visitante in visitantes):
            raise DatosVisitanteInvalidos("Cada participante debe tener una ficha válida")

    @staticmethod
    def _validar_email(email: object) -> None:
        if not isinstance(email, str) or not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", email):
            raise DatosVisitanteInvalidos("Debe informar un correo electrónico válido")

    def inscribir(self, solicitud: SolicitudInscripcion, ahora: datetime) -> Confirmacion:
        terminos = self.terminos_para(solicitud.actividad)
        if solicitud.acepta_terminos is not True or (
            solicitud.id_terminos_aceptados is not None
            and solicitud.id_terminos_aceptados != terminos.identificador
        ):
            raise TerminosNoAceptados("Debe aceptar los términos y condiciones de la actividad")
        self.validar_participantes(solicitud.cantidad_personas, solicitud.visitantes)
        self._validar_email(solicitud.email)
        self.seleccionar_horario(solicitud.horario, ahora)
        self.seleccionar_actividad(
            solicitud.actividad,
            solicitud.horario,
            solicitud.horario,
            solicitud.cantidad_personas,
        )
        dnis_solicitud = set()
        for visitante in solicitud.visitantes:
            self.validar_visitante(visitante, solicitud.actividad)
            dni = self._normalizar_dni(visitante.dni)
            if dni in dnis_solicitud or (dni, solicitud.horario) in self.inscripciones_existentes:
                raise InscripcionDuplicada("El visitante ya tiene una actividad en ese horario")
            dnis_solicitud.add(dni)

        numero_orden = f"ORD-{uuid4().hex[:8].upper()}"
        subtotales = tuple(0 for _ in solicitud.visitantes)
        detalle = "\n".join(
            f"{v.nombre} - DNI {v.dni} - Edad {v.edad}"
            + (f" - Talle {v.talla}" if solicitud.actividad in self.ACTIVIDADES_CON_VESTIMENTA else "")
            + " - Subtotal $0"
            for v in solicitud.visitantes
        )
        confirmacion = Confirmacion(
            numero_orden=numero_orden,
            destinatario=solicitud.email,
            resumen=(
                f"Orden {numero_orden}. Inscripción a {solicitud.actividad.value} "
                f"el {solicitud.horario.strftime('%d/%m/%Y')} "
                f"a las {solicitud.horario.strftime('%H:%M')}.\n"
                f"Participantes:\n{detalle}\nTotal $0"
            ),
            codigos_qr=tuple(
                self._crear_qr_uri(f"{numero_orden}:{self._normalizar_dni(v.dni)}:{uuid4().hex}")
                for v in solicitud.visitantes
            ),
            subtotales=subtotales,
            total=sum(subtotales),
        )
        self.cupos[(solicitud.actividad, solicitud.horario)] -= solicitud.cantidad_personas
        for dni in dnis_solicitud:
            self.inscripciones_existentes[(dni, solicitud.horario)] = solicitud.actividad
        self.enviar_email(confirmacion)
        return confirmacion

    def enviar_email(self, confirmacion: Confirmacion) -> None:
        """Simulación local del envío, reemplazable por un emisor real."""
        self.correos_enviados.append(confirmacion)

    @staticmethod
    def mostrar_confirmacion(confirmacion: Confirmacion) -> str:
        """Fragmento HTML que presenta al visitante los QR generados."""
        imagenes = "".join(
            f'<img alt="QR de acceso {indice}" src="{escape(uri, quote=True)}">'
            for indice, uri in enumerate(confirmacion.codigos_qr, start=1)
        )
        return f"<section><pre>{escape(confirmacion.resumen)}</pre>{imagenes}</section>"

    @staticmethod
    def _crear_qr_uri(contenido: str) -> str:
        qr = QrCodeWidget(contenido)
        qr.barWidth = 120
        qr.barHeight = 120
        dibujo = Drawing(120, 120)
        dibujo.add(qr)
        svg = renderSVG.drawToString(dibujo).encode("utf-8")
        return "data:image/svg+xml;base64," + b64encode(svg).decode("ascii")

    @staticmethod
    def _normalizar_dni(dni: int | str) -> str:
        return str(int(dni))

    @staticmethod
    def _dni_valido(dni: object) -> bool:
        if isinstance(dni, bool):
            return False
        if isinstance(dni, int):
            return dni > 0
        if isinstance(dni, str):
            return dni.isascii() and dni.isdigit() and int(dni) > 0
        return False

