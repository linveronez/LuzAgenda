document.addEventListener("DOMContentLoaded", () => {
  const infoModal = document.getElementById("infoModal");
  if (infoModal) new bootstrap.Modal(infoModal).show();

  document.querySelectorAll("[data-token-field]").forEach((field) => {
    const type = field.dataset.tokenType || field.closest("form")?.dataset.scheduleType;
    field.value = localStorage.getItem(`luzagenda_${type}_token`) || "";
  });

  document.querySelectorAll("[data-autocomplete]").forEach((input) => {
    const hidden = input.closest("form").querySelector("[data-paciente-id]");
    const list = input.parentElement.querySelector(".autocomplete-list");
    let timer;
    input.addEventListener("input", () => {
      clearTimeout(timer);
      hidden.value = "";
      timer = setTimeout(async () => {
        if (input.value.trim().length < 2) {
          list.innerHTML = "";
          return;
        }
        const res = await fetch(`/api/pacientes?q=${encodeURIComponent(input.value)}`);
        const data = await res.json();
        list.innerHTML = data.map((p) => `<button type="button" data-id="${p.id}" data-name="${p.nome}">${p.nome}</button>`).join("");
      }, 250);
    });
    list.addEventListener("click", (event) => {
      const btn = event.target.closest("button");
      if (!btn) return;
      hidden.value = btn.dataset.id;
      input.value = btn.dataset.name;
      list.innerHTML = "";
    });
  });

  const refreshCompanionButtons = () => {
    const rows = [...document.querySelectorAll(".companion-row")];
    const adults = rows.filter((row) => row.dataset.type === "adulto").length;
    const children = rows.filter((row) => row.dataset.type === "crianca").length;
    document.querySelectorAll('[data-add-companion="adulto"]').forEach((btn) => btn.disabled = adults >= 4);
    document.querySelectorAll('[data-add-companion="crianca"]').forEach((btn) => btn.disabled = children >= 2);
  };
  document.querySelectorAll("[data-add-companion]").forEach((addCompanion) => {
    addCompanion.addEventListener("click", () => {
      const area = document.querySelector("[data-companions]");
      const type = addCompanion.dataset.addCompanion;
      const rows = [...document.querySelectorAll(".companion-row")];
      const current = rows.filter((row) => row.dataset.type === type).length;
      if ((type === "adulto" && current >= 4) || (type === "crianca" && current >= 2)) return;
      const row = document.createElement("div");
      row.className = "companion-row";
      row.dataset.type = type;
      row.innerHTML = `
        <input class="form-control" name="ac_nome[]" placeholder="Nome">
        <select class="form-select" name="ac_parentesco[]"><option>Pai</option><option>Mãe</option><option>Irmã(o)</option><option>Tia(o)</option><option>Avó/Avô</option><option>Esposa(o)</option><option>Filha(o)</option><option>Outros</option></select>
        <input type="hidden" name="ac_tipo[]" value="${type}">
        <span class="companion-kind">${type === "crianca" ? "Criança" : "Adulto"}</span>
        <button class="btn btn-outline-danger" type="button">×</button>`;
      row.querySelector("button").addEventListener("click", () => {
        row.remove();
        refreshCompanionButtons();
      });
      area.appendChild(row);
      refreshCompanionButtons();
    });
  });

  const callDate = document.querySelector("[data-call-date]");
  if (callDate) {
    callDate.addEventListener("change", async () => {
      const res = await fetch(`/api/ligacoes/slots?data=${callDate.value}`);
      const slots = await res.json();
      slots.forEach((slot) => {
        const label = document.querySelector(`.slot input[value="${slot.horario}"]`)?.closest(".slot");
        if (!label) return;
        label.classList.toggle("one", slot.ocupados === 1);
        label.classList.toggle("full", slot.lotado);
        label.querySelector("input").disabled = slot.lotado;
      });
    });
  }

  const visitDuration = document.querySelector('select[name="duracao"]');
  const visitStart = document.querySelector('select[name="horario_inicio"]');
  if (visitDuration && visitStart) {
    const updateVisitTimes = () => {
      const duration = Number(visitDuration.value);
      [...visitStart.options].forEach((option) => {
        const [hour, minute] = option.value.split(":").map(Number);
        const endMinutes = (hour + duration) * 60 + minute;
        option.disabled = endMinutes > 16 * 60;
      });
      if (visitStart.selectedOptions[0]?.disabled) {
        visitStart.value = [...visitStart.options].find((option) => !option.disabled)?.value || "";
      }
    };
    visitDuration.addEventListener("change", updateVisitTimes);
    updateVisitTimes();
  }
});

if ("serviceWorker" in navigator) {
  window.addEventListener("load", () => navigator.serviceWorker.register("/static/service-worker.js"));
}
