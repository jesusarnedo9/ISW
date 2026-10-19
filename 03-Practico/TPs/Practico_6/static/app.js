(function () {
  "use strict";

  const state = {
    config: null,
    fechaSeleccionada: null,
    turnoSeleccionado: null,
    actividadSeleccionada: null,
    cantidadPersonas: 1,
    cuposTurnos: {},
    parqueAbierto: true,
    motivoCierre: null,
  };

  const dom = {
    qaAhoraInput: document.getElementById("qa-ahora-input"),
    btnVerCorreos: document.getElementById("btn-ver-correos"),
    correosContador: document.getElementById("correos-contador"),
    btnResetDatos: document.getElementById("btn-reset-datos"),
    presetButtons: document.querySelectorAll(".preset-btn"),

    formInscripcion: document.getElementById("form-inscripcion"),
    fechaVisita: document.getElementById("fecha-visita"),
    parqueEstadoBadge: document.getElementById("parque-estado-badge"),
    parqueEstadoTexto: document.getElementById("parque-estado-texto"),
    turnosGrid: document.getElementById("turnos-grid"),
    actividadesGrid: document.getElementById("actividades-grid"),

    btnDecrementar: document.getElementById("btn-decrementar"),
    btnIncrementar: document.getElementById("btn-incrementar"),
    cantidadPersonas: document.getElementById("cantidad-personas"),
    emailContacto: document.getElementById("email-contacto"),
    visitantesFichas: document.getElementById("visitantes-fichas"),

    terminosId: document.getElementById("terminos-id"),
    terminosTexto: document.getElementById("terminos-texto"),
    checkTerminos: document.getElementById("check-terminos"),
    alertaError: document.getElementById("alerta-error"),
    alertaErrorTexto: document.getElementById("alerta-error-texto"),
    btnConfirmar: document.getElementById("btn-confirmar"),

    modalComprobante: document.getElementById("modal-comprobante"),
    modalComprobanteBody: document.getElementById("modal-comprobante-body"),
    btnCerrarModal: document.getElementById("btn-cerrar-modal"),
    btnModalVerCorreo: document.getElementById("btn-modal-ver-correo"),
    btnModalNuevaReserva: document.getElementById("btn-modal-nueva-reserva"),

    modalCorreos: document.getElementById("modal-correos"),
    correosListaContainer: document.getElementById("correos-lista-container"),
    btnCerrarCorreos: document.getElementById("btn-cerrar-correos"),
  };

  function escapeHtml(str) {
    if (str === null || str === undefined) return "";
    return String(str)
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#39;");
  }

  async function init() {
    configurarEventos();
    await cargarConfiguracion();
    establecerFechaPredeterminada();
    await consultarCupos();
    actualizarContadorCorreos();
  }

  function configurarEventos() {
    dom.fechaVisita.addEventListener("change", async (e) => {
      state.fechaSeleccionada = e.target.value;
      state.turnoSeleccionado = null;
      await consultarCupos();
    });

    dom.qaAhoraInput.addEventListener("change", async () => {
      await consultarCupos();
    });
    dom.btnDecrementar.addEventListener("click", () => cambiarCantidadPersonas(-1));
    dom.btnIncrementar.addEventListener("click", () => cambiarCantidadPersonas(1));

    dom.btnResetDatos.addEventListener("click", resetearServicio);

    dom.btnVerCorreos.addEventListener("click", abrirModalCorreos);
    dom.btnCerrarCorreos.addEventListener("click", () => cerrarModal(dom.modalCorreos));
    dom.btnCerrarModal.addEventListener("click", () => cerrarModal(dom.modalComprobante));
    dom.btnModalVerCorreo.addEventListener("click", () => {
      cerrarModal(dom.modalComprobante);
      abrirModalCorreos();
    });
    dom.btnModalNuevaReserva.addEventListener("click", () => {
      cerrarModal(dom.modalComprobante);
      resetearFormulario();
    });

    dom.presetButtons.forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const presetId = e.currentTarget.getAttribute("data-preset");
        aplicarPresetPrueba(presetId);
      });
    });

    dom.formInscripcion.addEventListener("submit", procesarEnvioInscripcion);
  }

  async function cargarConfiguracion() {
    try {
      const res = await fetch("/api/config");
      if (!res.ok) throw new Error("Error al obtener la configuración de la API");
      state.config = await res.json();

      if (state.config.ahora_simulado) {
        dom.qaAhoraInput.value = state.config.ahora_simulado.substring(0, 16);
      }

      renderizarGrillaActividades();
    } catch (err) {
      mostrarErrorGlobal("No se pudo conectar con el servidor: " + err.message);
    }
  }

  async function consultarCupos() {
    if (!state.fechaSeleccionada) return;

    ocultarError();
    const ahoraParam = dom.qaAhoraInput.value;
    const url = `/api/cupos?fecha=${encodeURIComponent(state.fechaSeleccionada)}&ahora=${encodeURIComponent(ahoraParam)}`;

    try {
      const res = await fetch(url);
      const data = await res.json();

      if (!res.ok) {
        mostrarErrorGlobal(data.error || "Error al consultar cupos");
        return;
      }

      state.parqueAbierto = data.parque_abierto;
      state.motivoCierre = data.motivo_cierre;
      state.cuposTurnos = data.turnos || {};

      actualizarIndicadorParque();
      renderizarGrillaTurnos();
      actualizarTarjetasActividades();
    } catch (err) {
      mostrarErrorGlobal("Error al consultar disponibilidad: " + err.message);
    }
  }

  async function actualizarContadorCorreos() {
    try {
      const res = await fetch("/api/correos");
      if (res.ok) {
        const data = await res.json();
        dom.correosContador.textContent = data.total_enviados || 0;
      }
    } catch (e) {
      // Ignorar fallo no crítico de contador
    }
  }

  async function resetearServicio() {
    if (!confirm("¿Desea restablecer los cupos y datos en memoria a sus valores iniciales?")) return;
    try {
      const res = await fetch("/api/reset", { method: "POST" });
      if (res.ok) {
        await consultarCupos();
        await actualizarContadorCorreos();
        alert("Cupos y reservas restablecidos a sus valores iniciales.");
      }
    } catch (err) {
      alert("Error al restablecer: " + err.message);
    }
  }

  function establecerFechaPredeterminada() {
    const maniana = new Date();
    maniana.setDate(maniana.getDate() + 1);

    if (maniana.getDay() === 1) {
      maniana.setDate(maniana.getDate() + 1);
    }

    const yyyy = maniana.getFullYear();
    const mm = String(maniana.getMonth() + 1).padStart(2, "0");
    const dd = String(maniana.getDate()).padStart(2, "0");

    const fechaStr = `${yyyy}-${mm}-${dd}`;
    dom.fechaVisita.value = fechaStr;
    state.fechaSeleccionada = fechaStr;

    const hoy = new Date();
    const hoyStr = `${hoy.getFullYear()}-${String(hoy.getMonth() + 1).padStart(2, "0")}-${String(hoy.getDate()).padStart(2, "0")}`;
    dom.fechaVisita.min = hoyStr;
  }

  function actualizarIndicadorParque() {
    dom.parqueEstadoBadge.className = "status-indicator " + (state.parqueAbierto ? "open" : "closed");
    if (state.parqueAbierto) {
      dom.parqueEstadoTexto.textContent = "Parque Abierto (09:00 a 17:00)";
    } else {
      dom.parqueEstadoTexto.textContent = state.motivoCierre || "Parque Cerrado";
    }
  }

  function renderizarGrillaTurnos() {
    dom.turnosGrid.innerHTML = "";

    const turnosHoras = state.config ? state.config.turnos_horas : [9, 10, 11, 12, 13, 14, 15, 16, 17];
    let primerTurnoHabilitado = null;

    turnosHoras.forEach((h) => {
      const horaStr = `${String(h).padStart(2, "0")}:00`;
      const turnoInfo = state.cuposTurnos[horaStr];
      const habilitado = turnoInfo && turnoInfo.habilitado;

      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "turno-pill";
      btn.textContent = horaStr;
      btn.dataset.hora = horaStr;

      if (!habilitado) {
        btn.classList.add("disabled");
        btn.title = (turnoInfo && turnoInfo.motivo) || "Turno no disponible";
      } else {
        if (!primerTurnoHabilitado) primerTurnoHabilitado = horaStr;
        btn.addEventListener("click", () => seleccionarTurno(horaStr));
      }

      if (state.turnoSeleccionado === horaStr && habilitado) {
        btn.classList.add("selected");
      }

      dom.turnosGrid.appendChild(btn);
    });

    if (!state.turnoSeleccionado || !state.cuposTurnos[state.turnoSeleccionado]?.habilitado) {
      state.turnoSeleccionado = null;
      if (primerTurnoHabilitado) seleccionarTurno(primerTurnoHabilitado);
    }
  }

  function seleccionarTurno(horaStr) {
    if (!state.cuposTurnos[horaStr]?.habilitado) return;
    state.turnoSeleccionado = horaStr;

    // Actualizar clase seleccionada en pills
    dom.turnosGrid.querySelectorAll(".turno-pill").forEach((p) => {
      p.classList.toggle("selected", p.dataset.hora === horaStr);
    });

    actualizarTarjetasActividades();
  }

  function motivoSinHorarioDisponible() {
    if (!state.parqueAbierto) return state.motivoCierre || "El parque está cerrado ese día";
    const turnos = Object.values(state.cuposTurnos);
    if (!turnos.length) return "No hay turnos disponibles para esta fecha";
    const motivo = turnos[0].motivo;
    return motivo && turnos.every((turno) => turno.motivo === motivo)
      ? motivo
      : "No hay turnos reservables para esta fecha";
  }

  function renderizarGrillaActividades() {
    if (!state.config || !state.config.actividades) return;
    dom.actividadesGrid.innerHTML = "";

    state.config.actividades.forEach((act, index) => {
      const card = document.createElement("div");
      card.className = "actividad-card";
      card.dataset.nombre = act.nombre;

      const edadTxt = act.edad_minima > 0 ? `+${act.edad_minima} años` : "Todas las edades";
      const vestimentaTxt = act.requiere_vestimenta ? "Requiere talle" : "Sin talle";

      card.innerHTML = `
        <div class="actividad-header">
          <div class="actividad-name">${act.nombre}</div>
          <div class="actividad-badges">
            <span class="badge badge-neutral">${edadTxt}</span>
            <span class="badge ${act.requiere_vestimenta ? 'badge-primary' : 'badge-neutral'}">${vestimentaTxt}</span>
          </div>
        </div>
        <div class="cupo-pill disponible" id="cupo-pill-${act.id}">
          Consultando...
        </div>
      `;

      card.addEventListener("click", () => {
        if (!card.classList.contains("disabled")) {
          seleccionarActividad(act.nombre);
        }
      });

      dom.actividadesGrid.appendChild(card);

      // Autoseleccionar la primera actividad por defecto
      if (index === 0 && !state.actividadSeleccionada) {
        state.actividadSeleccionada = act.nombre;
      }
    });

    if (state.actividadSeleccionada) {
      actualizarDetallesActividad(state.actividadSeleccionada);
    }
  }

  function actualizarTarjetasActividades() {
    if (!state.config || !state.config.actividades) return;
    const turnoData = state.cuposTurnos[state.turnoSeleccionado];

    state.config.actividades.forEach((act) => {
      const card = dom.actividadesGrid.querySelector(`[data-nombre="${act.nombre}"]`);
      const pill = document.getElementById(`cupo-pill-${act.id}`);
      if (!card || !pill) return;

      const turnoHabilitado = state.parqueAbierto && turnoData?.habilitado;
      const actividadEnTurno = turnoData?.actividades?.[act.nombre];
      const ofrecida = actividadEnTurno?.ofrecida === true;
      const cupos = ofrecida ? actividadEnTurno.disponibles : 0;
      const noDisponible = !turnoHabilitado || !ofrecida || cupos <= 0;

      pill.textContent = !turnoHabilitado
        ? (turnoData?.motivo || motivoSinHorarioDisponible())
        : !ofrecida
          ? "No se ofrece en este horario"
          : cupos > 0 ? `${cupos} cupos disponibles` : "Agotado";

      pill.className = `cupo-pill ${noDisponible ? "agotado" : "disponible"}`;
      card.classList.toggle("disabled", noDisponible);

      // Si la actividad seleccionada quedó agotada, buscar otra disponible
      if (state.actividadSeleccionada === act.nombre) {
        card.classList.add("selected");
        if (noDisponible) {
          card.classList.remove("selected");
        }
      } else {
        card.classList.remove("selected");
      }
    });

    renderizarFichasVisitantes();
  }

  function seleccionarActividad(nombreActividad) {
    if (state.actividadSeleccionada !== nombreActividad) {
      dom.checkTerminos.checked = false;
    }
    state.actividadSeleccionada = nombreActividad;

    dom.actividadesGrid.querySelectorAll(".actividad-card").forEach((c) => {
      c.classList.toggle("selected", c.dataset.nombre === nombreActividad);
    });

    actualizarDetallesActividad(nombreActividad);
    renderizarFichasVisitantes();
  }

  function actualizarDetallesActividad(nombreActividad) {
    if (!state.config) return;
    const act = state.config.actividades.find((a) => a.nombre === nombreActividad);
    if (!act) return;

    // Actualizar términos específicos
    dom.terminosId.textContent = act.terminos.identificador;
    dom.terminosTexto.textContent = act.terminos.texto;
  }

  // ==========================================================================
  // Gestión de Participantes (Paso 3)
  // ==========================================================================

  function cambiarCantidadPersonas(delta) {
    let nuevaCantidad = state.cantidadPersonas + delta;
    if (nuevaCantidad < 1) nuevaCantidad = 1;
    if (nuevaCantidad > 12) nuevaCantidad = 12;

    state.cantidadPersonas = nuevaCantidad;
    dom.cantidadPersonas.value = nuevaCantidad;
    renderizarFichasVisitantes();
  }

  function renderizarFichasVisitantes() {
    const act = state.config?.actividades.find((a) => a.nombre === state.actividadSeleccionada);
    const requiereVestimenta = act ? act.requiere_vestimenta : false;
    const talles = state.config ? state.config.talles_disponibles : ["XS", "S", "M", "L", "XL", "XXL"];

    // Guardar valores ingresados previamente para no borrarlos al cambiar la cantidad
    const valoresActuales = [];
    dom.visitantesFichas.querySelectorAll(".visitante-card").forEach((card) => {
      valoresActuales.push({
        nombre: card.querySelector(".input-nombre")?.value || "",
        dni: card.querySelector(".input-dni")?.value || "",
        edad: card.querySelector(".input-edad")?.value || "",
        talla: card.querySelector(".select-talla")?.value || "",
      });
    });

    dom.visitantesFichas.innerHTML = "";

    for (let i = 0; i < state.cantidadPersonas; i++) {
      const val = valoresActuales[i] || {
        nombre: i === 0 ? "Ana Pérez" : `Acompañante ${i + 1}`,
        dni: i === 0 ? "30123456" : `3500000${i}`,
        edad: i === 0 ? "25" : "20",
        talla: "M",
      };

      const card = document.createElement("div");
      card.className = "visitante-card";
      card.dataset.index = i;

      let opcionesTalles = talles.map((t) => `<option value="${escapeHtml(t)}" ${t === val.talla ? "selected" : ""}>${escapeHtml(t)}</option>`).join("");

      card.innerHTML = `
        <div class="visitante-header">
          <span>Participante ${i + 1}</span>
          ${act && act.edad_minima > 0 ? `<span class="badge badge-neutral">Mínimo ${act.edad_minima} años</span>` : ""}
        </div>
        <div class="visitante-grid">
          <div class="form-group">
            <label class="form-label">Nombre y Apellido:</label>
            <input type="text" class="form-control input-nombre" value="${escapeHtml(val.nombre)}" placeholder="Ej. Juan Pérez" required>
          </div>
          <div class="form-group">
            <label class="form-label">DNI (solo números):</label>
            <input type="text" class="form-control input-dni" value="${escapeHtml(val.dni)}" placeholder="Ej. 30123456" inputmode="numeric" required>
          </div>
          <div class="form-group">
            <label class="form-label">Edad:</label>
            <input type="number" class="form-control input-edad" value="${escapeHtml(val.edad)}" min="0" max="120" placeholder="Ej. 25" required>
          </div>
          ${requiereVestimenta
          ? `
            <div class="form-group field-talla">
              <label class="form-label">Talle de Vestimenta:</label>
              <select class="form-control select-talla" required>
                <option value="">Seleccione talle...</option>
                ${opcionesTalles}
              </select>
            </div>
            `
          : ""
        }
        </div>
      `;

      dom.visitantesFichas.appendChild(card);
    }
  }

  async function procesarEnvioInscripcion(e) {
    e.preventDefault();
    ocultarError();

    if (!state.turnoSeleccionado) {
      mostrarError(motivoSinHorarioDisponible());
      return;
    }

    if (!state.cuposTurnos[state.turnoSeleccionado]?.habilitado) {
      mostrarError(state.cuposTurnos[state.turnoSeleccionado]?.motivo || motivoSinHorarioDisponible());
      return;
    }

    if (!state.actividadSeleccionada) {
      mostrarError("Debe seleccionar una actividad.");
      return;
    }

    // Recopilar datos de participantes
    const visitantes = [];
    const fichas = dom.visitantesFichas.querySelectorAll(".visitante-card");

    for (let f of fichas) {
      const nombre = f.querySelector(".input-nombre").value.trim();
      const dniStr = f.querySelector(".input-dni").value.trim();
      const edadStr = f.querySelector(".input-edad").value.trim();
      const tallaSelect = f.querySelector(".select-talla");
      const talla = tallaSelect ? tallaSelect.value : null;

      visitantes.push({
        nombre: nombre,
        dni: dniStr,
        edad: edadStr === "" ? null : Number(edadStr),
        talla: talla || null,
      });
    }

    const actInfo = state.config?.actividades.find((a) => a.nombre === state.actividadSeleccionada);
    const idTerminos = actInfo ? actInfo.terminos.identificador : null;

    const payload = {
      actividad: state.actividadSeleccionada,
      fecha: state.fechaSeleccionada,
      hora: state.turnoSeleccionado,
      cantidad_personas: state.cantidadPersonas,
      visitantes: visitantes,
      acepta_terminos: dom.checkTerminos.checked,
      id_terminos_aceptados: idTerminos,
      email: dom.emailContacto.value.trim(),
      ahora: dom.qaAhoraInput.value || null,
    };

    setBotonCargando(true);

    try {
      const res = await fetch("/api/inscribir", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      const data = await res.json();

      if (!res.ok || !data.exito) {
        mostrarError(data.mensaje || "Error al procesar la inscripción.");
        return;
      }

      // Éxito: desplegar modal con voucher y códigos QR
      mostrarComprobanteExitoso(data.confirmacion);
      await consultarCupos();
      actualizarContadorCorreos();
    } catch (err) {
      mostrarError("Error en la conexión con el servidor: " + err.message);
    } finally {
      setBotonCargando(false);
    }
  }

  function mostrarComprobanteExitoso(confirmacion) {
    let qrCardsHtml = "";
    if (confirmacion.codigos_qr && confirmacion.codigos_qr.length > 0) {
      qrCardsHtml = confirmacion.codigos_qr
        .map((uri, idx) => `
          <div class="qr-item">
            <img src="${escapeHtml(uri)}" alt="Código QR Participante ${idx + 1}">
            <span class="qr-caption">Pase QR #${idx + 1}</span>
          </div>
        `)
        .join("");
    }

    dom.modalComprobanteBody.innerHTML = `
      <div class="voucher-card">
        <div class="voucher-order-num">ORDEN: ${escapeHtml(confirmacion.numero_orden)}</div>
        <div class="voucher-summary">${escapeHtml(confirmacion.resumen)}</div>
        <div class="voucher-total-row">
          <span>Total Adicional a la Entrada:</span>
          <span>$${escapeHtml(confirmacion.total)} (Incluido)</span>
        </div>
      </div>
      <div>
        <h3 class="form-label" style="margin-bottom: 0.5rem;">Códigos QR de Acceso al Parque:</h3>
        <div class="qr-gallery">
          ${qrCardsHtml}
        </div>
      </div>
    `;

    abrirModal(dom.modalComprobante);
  }

  async function abrirModalCorreos() {
    try {
      const res = await fetch("/api/correos");
      if (!res.ok) throw new Error("No se pudo obtener la bandeja de correos");
      const data = await res.json();

      dom.correosListaContainer.innerHTML = "";
      if (!data.correos || data.correos.length === 0) {
        dom.correosListaContainer.innerHTML = `<p style="text-align: center; color: var(--text-muted); padding: 2rem;">No se han enviado correos todavía.</p>`;
      } else {
        data.correos.forEach((c) => {
          const item = document.createElement("div");
          item.className = "email-item";
          item.innerHTML = `
            <div class="email-meta">
              <span>Para: <span class="email-destinatario">${escapeHtml(c.destinatario)}</span></span>
              <span>Orden: <strong>${escapeHtml(c.numero_orden)}</strong></span>
            </div>
            <div class="email-body">${escapeHtml(c.resumen)}</div>
            <div style="font-size: 0.75rem; color: var(--text-muted);">Adjuntos: ${escapeHtml(c.cantidad_qr)} código(s) QR generado(s).</div>
          `;
          dom.correosListaContainer.appendChild(item);
        });
      }

      abrirModal(dom.modalCorreos);
    } catch (err) {
      alert("Error al cargar correos: " + err.message);
    }
  }

  async function aplicarPresetPrueba(presetId) {
    ocultarError();

    // Fecha base: próximo martes
    const fecha = new Date();
    fecha.setDate(fecha.getDate() + 2);
    while (fecha.getDay() === 1) fecha.setDate(fecha.getDate() + 1); // evitar lunes
    const fechaStr = `${fecha.getFullYear()}-${String(fecha.getMonth() + 1).padStart(2, "0")}-${String(fecha.getDate()).padStart(2, "0")}`;

    // Fijar momento simulado 2 horas antes de las 10:00 del día elegido
    const ahoraStr = `${fechaStr}T08:00`;
    dom.qaAhoraInput.value = ahoraStr;

    switch (presetId) {
      case "1": // CP1: Flujo feliz completo (Tirolesa con cupo, talle M, términos aceptados)
        dom.fechaVisita.value = fechaStr;
        state.fechaSeleccionada = fechaStr;
        await consultarCupos();
        seleccionarTurno("10:00");
        seleccionarActividad("Tirolesa");
        state.cantidadPersonas = 1;
        dom.cantidadPersonas.value = 1;
        renderizarFichasVisitantes();
        dom.visitantesFichas.querySelectorAll(".select-talla").forEach((sel) => {
          sel.value = "M";
        });
        dom.checkTerminos.checked = true;
        break;

      case "2": // CP2: Sin cupo (Palestra a las 15:00 sembrada con 0 cupos)
        const maniana = new Date();
        maniana.setDate(maniana.getDate() + 1);
        while (maniana.getDay() === 1) maniana.setDate(maniana.getDate() + 1); // evitar lunes
        const manianaStr = `${maniana.getFullYear()}-${String(maniana.getMonth() + 1).padStart(2, "0")}-${String(maniana.getDate()).padStart(2, "0")}`;
        dom.fechaVisita.value = manianaStr;
        state.fechaSeleccionada = manianaStr;
        dom.qaAhoraInput.value = `${manianaStr}T08:00`;
        await consultarCupos();
        seleccionarTurno("15:00");
        seleccionarActividad("Palestra");
        dom.checkTerminos.checked = true;
        break;

      case "3": // CP3: Omitir talle en Safari (debe pasar sin pedir talle)
        dom.fechaVisita.value = fechaStr;
        state.fechaSeleccionada = fechaStr;
        await consultarCupos();
        seleccionarTurno("15:00");
        seleccionarActividad("Safari");
        state.cantidadPersonas = 1;
        dom.cantidadPersonas.value = 1;
        renderizarFichasVisitantes();
        dom.checkTerminos.checked = true;
        break;

      case "4": // CP4: Parque cerrado (Seleccionar un lunes)
        const lunes = new Date();
        lunes.setDate(lunes.getDate() + ((1 + 7 - lunes.getDay()) % 7 || 7)); // siguiente lunes
        const lunesStr = `${lunes.getFullYear()}-${String(lunes.getMonth() + 1).padStart(2, "0")}-${String(lunes.getDate()).padStart(2, "0")}`;
        dom.fechaVisita.value = lunesStr;
        state.fechaSeleccionada = lunesStr;
        await consultarCupos();
        break;

      case "5": // CP5: Sin aceptar términos y condiciones
        dom.fechaVisita.value = fechaStr;
        state.fechaSeleccionada = fechaStr;
        await consultarCupos();
        seleccionarTurno("10:00");
        seleccionarActividad("Tirolesa");
        dom.checkTerminos.checked = false; // desmarcado intencionalmente
        break;

      case "6": // CP6: Sin talle en Tirolesa (debe fallar por requerir talle)
        dom.fechaVisita.value = fechaStr;
        state.fechaSeleccionada = fechaStr;
        await consultarCupos();
        seleccionarTurno("10:00");
        seleccionarActividad("Tirolesa");
        state.cantidadPersonas = 1;
        dom.cantidadPersonas.value = 1;
        renderizarFichasVisitantes();
        const selectTalla = dom.visitantesFichas.querySelector(".select-talla");
        if (selectTalla) selectTalla.value = ""; // talle vacío intencional
        dom.checkTerminos.checked = true;
        break;
    }
  }

  function resetearFormulario() {
    dom.checkTerminos.checked = false;
    ocultarError();
    establecerFechaPredeterminada();
    consultarCupos();
  }

  function mostrarError(mensaje) {
    dom.alertaErrorTexto.textContent = mensaje;
    dom.alertaError.style.display = "flex";
    dom.alertaError.scrollIntoView({ behavior: "smooth", block: "center" });
  }

  function mostrarErrorGlobal(mensaje) {
    mostrarError(mensaje);
  }

  function ocultarError() {
    dom.alertaError.style.display = "none";
  }

  function setBotonCargando(cargando) {
    dom.btnConfirmar.disabled = cargando;
    dom.btnConfirmar.querySelector(".btn-text").style.display = cargando ? "none" : "inline";
    dom.btnConfirmar.querySelector(".spinner").style.display = cargando ? "inline-block" : "none";
  }

  function abrirModal(modalEl) {
    modalEl.style.display = "flex";
    document.body.style.overflow = "hidden";
  }

  function cerrarModal(modalEl) {
    modalEl.style.display = "none";
    document.body.style.overflow = "";
  }

  // Iniciar la app al cargar el DOM
  document.addEventListener("DOMContentLoaded", init);
})();
