[Reading 796 lines from start (total: 796 lines, 0 remaining)]

const $ = (q) => document.querySelector(q);
const setupToken = new URLSearchParams(window.location.search).get("token") || "";

async function apiFetch(path, options = {}) {
  const headers = new Headers(options.headers || {});
  headers.set("X-LMS-Setup-Token", setupToken);
  if (options.body && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  return fetch(path, {...options, headers, cache: "no-store"});
}

let hostData = null;
let currentPlan = null;
let installJobId = null;
let installPollTimer = null;
let step = 1;
let selectedDisk = null;
const selectedLibraries = new Set(["movies", "series", "anime"]);
const servicePlans = {
  tailscale: null,
  jellyfin: null,
  qbittorrent: null
};
let networkMode = "tailscale";
let tailscaleAuth = "interactive";
const libraryDefs = [
  {id: "movies", name: "Filmy", paths: ["Filmy/"], jellyfin: "Movies"},
  {id: "series", name: "Seriale", paths: ["Seriale/"], jellyfin: "Shows"},
  {id: "anime", name: "Anime", paths: ["Anime/Filmy/", "Anime/Seriale/"], jellyfin: "Movies + Shows"}
];
const serviceDefs = [
  {id: "tailscale", name: "Tailscale", role: "Zdalny, prywatny dostęp do LMS", recommended: true},
  {id: "jellyfin", name: "Jellyfin", role: "Biblioteka i odtwarzanie multimediów", recommended: true},
  {id: "qbittorrent", name: "qBittorrent", role: "Pobieranie i obsługa torrentów", recommended: true}
];

const fmtBytes = (n) => {
  if (!Number.isFinite(Number(n)) || Number(n) <= 0) return "—";
  const units = ["B", "KB", "MB", "GB", "TB"];
  let v = Number(n), i = 0;
  while (v >= 1000 && i < units.length - 1) { v /= 1000; i++; }
  return `${v >= 10 || i === 0 ? v.toFixed(0) : v.toFixed(1)} ${units[i]}`;
};

const esc = (v) => String(v ?? "—").replace(/[&<>"']/g, (c) => ({
  "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"
}[c]));

const disksOnly = (disks) => (disks || []).filter((disk) => disk.type === "disk");

function infoCard(label, value, small = "") {
  const details = small ? `<small>${esc(small)}</small>` : "";
  return `<article class="info-card"><span>${esc(label)}</span><strong>${esc(value)}</strong>${details}</article>`;
}
function setActiveStep(value) {
  step = value;
  document.querySelectorAll(".step").forEach((el, index) => {
    el.classList.toggle("active", index === value - 1);
  });
  document.querySelector(".progress-ring strong").textContent = String(value);
  $("#backBtn").hidden = value === 1;
  if (value !== 7) $("#nextBtn").textContent = "Dalej →";
}

function renderChecks(data) {
  const disks = disksOnly(data.disks);
  const rows = [
    ["System Linux", true],
    ["Docker", Boolean(data.docker?.installed)],
    ["Docker Compose", Boolean(data.docker?.compose_installed)],
    ["Dysk dostępny", disks.some((disk) => !disk.read_only && !disk.is_system)],
    ["Tailscale", Boolean(data.components?.tailscale?.installed)],
    ["Jellyfin", Boolean(data.components?.jellyfin?.installed)],
    ["qBittorrent", Boolean(data.components?.qbittorrent?.installed)]
  ];
  $("#checks").innerHTML = rows.map(([name, ok]) =>
    `<div class="check ${ok ? "ok" : "warn"}">${esc(name)} — ${ok ? "wykryto" : "do konfiguracji"}</div>`
  ).join("");
}

function renderServer(data) {
  setActiveStep(1);
  const oracle = data.cloud?.oracle || {};
  const disks = disksOnly(data.disks);
  $("#serverCards").className = "cards";
  $("#serverCards").innerHTML =
    infoCard("System", data.os?.name, `${data.os?.arch || ""} • kernel ${data.os?.kernel || "—"}`) +
    infoCard("Procesor", `${data.cpu?.logical_cores || 0} vCPU`, data.cpu?.model || "") +
    infoCard("Pamięć RAM", fmtBytes(data.memory?.total_bytes)) +
    infoCard(
      "Chmura",
      oracle.detected ? "Oracle Cloud" : "Nie wykryto",
      oracle.detected ? [oracle.region, oracle.shape].filter(Boolean).join(" • ") : "Tryb Generic Linux"
    ) +
    infoCard(
      "Docker",
      data.docker?.installed ? "Wykryty" : "Brak",
      data.docker?.compose_installed ? "Compose dostępny" : "Compose niewykryty"
    ) +
    infoCard(
      "Dyski",
      `${disks.length} wykryte`,
      disks.map((disk) => `${disk.path} • ${fmtBytes(disk.size_bytes)}`).join(" | ")
    );
  renderChecks(data);
  $("#hint").textContent = oracle.detected
    ? "Oracle Cloud wykryty. Możemy przejść do wyboru dysku."
    : "Tryb Generic Linux. Możemy przejść do wyboru dysku.";
  $("#nextBtn").disabled = false;
}
function diskDetails(disk) {
  const parts = [];
  if (disk.filesystem) parts.push(disk.filesystem);
  if (disk.mountpoints?.length) parts.push(`zamontowany: ${disk.mountpoints.join(", ")}`);
  if (!disk.filesystem) parts.push("brak systemu plików");
  if (disk.is_system) parts.push("dysk systemowy");
  return parts.join(" • ");
}

function renderDisks(data) {
  setActiveStep(2);
  const disks = disksOnly(data.disks);
  const candidates = disks.filter((disk) => !disk.read_only && !disk.is_system);
  const recommended = [...candidates].sort((a, b) => Number(b.size_bytes) - Number(a.size_bytes))[0];

  if (!selectedDisk && recommended) selectedDisk = recommended.path;
  $("#serverCards").className = "disk-grid";
  $("#serverCards").innerHTML = disks.map((disk) => {
    const disabled = disk.read_only || disk.is_system;
    const selected = selectedDisk === disk.path;
    const badge = recommended?.path === disk.path ? '<span class="badge">zalecany</span>' : "";
    return `<button class="disk-option ${selected ? "selected" : ""}" data-disk="${esc(disk.path)}" type="button" ${disabled ? "disabled" : ""}>
      <span class="disk-radio" aria-hidden="true"></span>
      <span class="disk-main"><strong>${esc(disk.path)} ${badge}</strong><small>${esc(diskDetails(disk))}</small></span>
      <span class="disk-size">${esc(fmtBytes(disk.size_bytes))}</span>
    </button>`;
  }).join("");
  document.querySelectorAll(".disk-option:not(:disabled)").forEach((button) => {
    button.addEventListener("click", () => {
      selectedDisk = button.dataset.disk;
      renderDisks(data);
    });
  });

  $("#checks").innerHTML = selectedDisk
    ? '<div class="check ok">Wybrano magazyn dla LMS</div><div class="check muted">Systemowy dysk jest chroniony i nie można go wybrać w tym szkicu.</div>'
    : '<div class="check warn">Brak bezpiecznego kandydata na magazyn.</div>';
  $("#hint").textContent = selectedDisk
    ? `Wybrany dysk: ${selectedDisk}. Nic nie zostało jeszcze sformatowane ani zmienione.`
    : "Podłącz lub przygotuj dodatkowy dysk.";
  $("#nextBtn").disabled = !selectedDisk;
}

function renderLibraries() {
  setActiveStep(3);
  $("#serverCards").className = "library-grid";
  $("#serverCards").innerHTML = libraryDefs.map((library) => {
    const selected = selectedLibraries.has(library.id);
    const pathList = library.paths.map((path) => `<code>${esc(path)}</code>`).join("");
    return `<button class="library-option ${selected ? "selected" : ""}" data-library="${esc(library.id)}" type="button" aria-pressed="${selected}">
      <span class="library-check" aria-hidden="true">${selected ? "✓" : ""}</span>
      <span class="library-main">
        <strong>${esc(library.name)}</strong>
        <small>${pathList}</small>
        <span class="library-jellyfin">Jellyfin: ${esc(library.jellyfin)}</span>
      </span>
    </button>`;
  }).join("");

  document.querySelectorAll(".library-option").forEach((button) => {
    button.addEventListener("click", () => {
      const id = button.dataset.library;
      if (selectedLibraries.has(id)) {
        if (selectedLibraries.size > 1) selectedLibraries.delete(id);
      } else {
        selectedLibraries.add(id);
      }
      renderLibraries();
    });
  });

  const selectedNames = libraryDefs
    .filter((library) => selectedLibraries.has(library.id))
    .map((library) => library.name);

  $("#checks").innerHTML =
    '<div class="check ok">Domyślny układ bibliotek gotowy</div>' +
    '<div class="check muted">Anime zostanie rozdzielone wewnętrznie na filmy i seriale dla Jellyfin.</div>' +
    `<div class="check muted">Wybrane: ${esc(selectedNames.join(", "))}</div>`;

  $("#hint").textContent = "To tylko konfiguracja szkicu — żadne katalogi nie są jeszcze tworzone.";
  $("#nextBtn").disabled = selectedLibraries.size === 0;
}

function initServicePlans(data) {
  serviceDefs.forEach((service) => {
    if (servicePlans[service.id]) return;
    const detected = Boolean(data.components?.[service.id]?.installed);
    servicePlans[service.id] = detected ? "existing" : "install";
  });
}

function serviceStatus(component) {
  if (!component?.installed) return "Nie wykryto";
  if (component.running === true) return "Wykryto • działa";
  if (component.running === false) return "Wykryto • zatrzymany";
  return "Wykryto";
}

function serviceActionLabel(plan) {
  if (plan === "existing") return "Użyj istniejącego";
  if (plan === "install") return "Zainstaluj podczas instalacji";
  return "Pomiń";
}

function renderServices(data) {
  setActiveStep(4);
  initServicePlans(data);
  const safeMode = data.installer?.changes_allowed === false;

  $("#serverCards").className = "service-grid";
  $("#serverCards").innerHTML = serviceDefs.map((service) => {
    const component = data.components?.[service.id] || {};
    const current = servicePlans[service.id];
    const detected = Boolean(component.installed);
    const options = detected
      ? [["existing", "Użyj istniejącego"], ["skip", "Pomiń"]]
      : [["install", "Zainstaluj"], ["skip", "Pomiń"]];

    const buttons = options.map(([value, label]) =>
      `<button class="service-choice ${current === value ? "selected" : ""}" data-service="${esc(service.id)}" data-plan="${esc(value)}" type="button">${esc(label)}</button>`
    ).join("");

    return `<article class="service-card">
      <div class="service-head">
        <div>
          <strong>${esc(service.name)}</strong>
          <small>${esc(service.role)}</small>
        </div>
        <span class="service-status ${detected ? "ok" : "missing"}">${esc(serviceStatus(component))}</span>
      </div>
      <div class="service-actions">${buttons}</div>
      <div class="service-plan">Plan: <strong>${esc(serviceActionLabel(current))}</strong></div>
    </article>`;
  }).join("");

  document.querySelectorAll(".service-choice").forEach((button) => {
    button.addEventListener("click", () => {
      servicePlans[button.dataset.service] = button.dataset.plan;
      renderServices(data);
    });
  });

  const installCount = Object.values(servicePlans).filter((plan) => plan === "install").length;
  const existingCount = Object.values(servicePlans).filter((plan) => plan === "existing").length;
  $("#checks").innerHTML =
    `<div class="check ok">${existingCount} usług użyje istniejącej instalacji</div>` +
    `<div class="check ${installCount ? "warn" : "muted"}">${installCount} usług zaplanowano do instalacji</div>` +
    (safeMode
      ? '<div class="check muted">Tryb developerski: zmiany systemowe są zablokowane.</div>'
      : "");

  $("#hint").textContent = safeMode
    ? "Przyciski układają plan. Na tym serwerze nic nie zostanie zainstalowane ani przeinstalowane."
    : "Wybrane instalacje zostaną wykonane dopiero po zatwierdzeniu podsumowania.";
  $("#nextBtn").disabled = false;
}

function renderNetwork() {
  setActiveStep(5);
  const tailscaleSkipped = servicePlans.tailscale === "skip";
  if (tailscaleSkipped && networkMode === "tailscale") networkMode = "direct";

  $("#serverCards").className = "network-grid";
  $("#serverCards").innerHTML = `
    <button class="network-option ${networkMode === "tailscale" ? "selected" : ""}" data-network="tailscale" type="button" ${tailscaleSkipped ? "disabled" : ""}>
      <strong>Tailscale <span class="badge">zalecane</span></strong>
      <small>Prywatny dostęp do LMS bez wystawiania panelu bezpośrednio do Internetu.</small>
    </button>
    <button class="network-option ${networkMode === "direct" ? "selected" : ""}" data-network="direct" type="button">
      <strong>Dostęp bez Tailscale</strong>
      <small>W testowym buildzie LMS pozostanie na localhost. Dostęp z komputera zrobisz przez tunel SSH.</small>
    </button>
  `;

  document.querySelectorAll(".network-option:not(:disabled)").forEach((button) => {
    button.addEventListener("click", () => {
      networkMode = button.dataset.network;
      renderNetwork();
    });
  });

  $("#checks").innerHTML = networkMode === "tailscale"
    ? '<div class="check ok">Tailscale wybrany jako metoda dostępu</div><div class="check muted">Autoryzacja: logowanie w przeglądarce podczas instalacji.</div>'
    : '<div class="check muted">Tailscale pominięty. LMS nie będzie sam wystawiał dodatkowych portów w Oracle Cloud.</div>';

  $("#hint").textContent = "Na tym etapie wybierasz tylko sposób dostępu. Reguły sieciowe nie są zmieniane.";
  $("#nextBtn").disabled = false;
}

function summaryRow(label, value) {
  return `<div class="summary-row"><span>${esc(label)}</span><strong>${esc(value)}</strong></div>`;
}

function buildSelectionPayload() {
  return {
    disk: selectedDisk,
    libraries: Array.from(selectedLibraries),
    services: {...servicePlans},
    network: networkMode
  };
}

function renderPlanActions(plan) {
  return plan.actions.map((action, index) => {
    const flags = [
      action.destructive ? '<span class="plan-flag danger">destrukcyjne</span>' : "",
      action.interaction ? '<span class="plan-flag">wymaga kliknięcia</span>' : ""
    ].join("");
    return `<div class="plan-action">
      <span class="plan-index">${index + 1}</span>
      <span class="plan-copy"><strong>${esc(action.title)}</strong><small>${esc(action.phase)}</small></span>
      <span class="plan-flags">${flags}</span>
    </div>`;
  }).join("");
}

async function renderSummary() {
  setActiveStep(6);
  currentPlan = null;
  $("#nextBtn").disabled = true;
  $("#serverCards").className = "summary-card";
  $("#serverCards").innerHTML = '<div class="summary-loading">Backend sprawdza plan instalacji…</div>';
  $("#checks").innerHTML = '<div class="check muted">Walidacja konfiguracji…</div>';

  try {
    const response = await apiFetch("/api/plan", {
      method: "POST",
      body: JSON.stringify(buildSelectionPayload())
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    currentPlan = data.plan;

    const cfg = currentPlan.config;
    const libraryNames = cfg.libraries.map((id) => libraryDefs.find((item) => item.id === id)?.name || id);
    $("#serverCards").innerHTML =
      '<div class="summary-overview">' +
        summaryRow("Dysk", cfg.disk) +
        summaryRow("Tryb dysku", cfg.storage.mode === "format-ext4" ? "Nowy ext4" : "Istniejący system plików") +
        summaryRow("Punkt montowania", cfg.storage.mountpoint) +
        summaryRow("Biblioteki", libraryNames.join(", ")) +
        summaryRow("Sieć", cfg.network === "tailscale" ? "Tailscale" : "Bez Tailscale") +
      '</div>' +
      '<div class="plan-title">Plan operacji</div>' +
      '<div class="plan-actions">' + renderPlanActions(currentPlan) + '</div>';

    $("#checks").innerHTML =
      '<div class="check ok">Backend zaakceptował konfigurację</div>' +
      (currentPlan.destructive
        ? '<div class="check warn">Plan zawiera operację destrukcyjną i będzie wymagał dodatkowego potwierdzenia.</div>'
        : '<div class="check ok">Plan nie wymaga formatowania dysku.</div>') +
      '<div class="check muted">Na tym hoście wykonanie pozostaje zablokowane.</div>';

    $("#hint").textContent = `Zweryfikowano ${currentPlan.actions.length} operacji. Możesz przejść do podglądu instalacji.`;
    $("#nextBtn").disabled = false;
  } catch (error) {
    $("#serverCards").innerHTML = summaryRow("Błąd planu", error.message);
    $("#checks").innerHTML = '<div class="check warn">Backend odrzucił konfigurację.</div>';
    $("#hint").textContent = "Wróć i popraw wybory.";
  }
}

function stopInstallPolling() {
  if (installPollTimer) {
    clearTimeout(installPollTimer);
    installPollTimer = null;
  }
}

function renderJobProgress(job, active = false) {
  const actions = currentPlan?.actions || [];
  const completed = Number(job.next_action_index || 0);
  const statusNames = {
    queued: "Oczekuje",
    running: "Instalowanie",
    waiting: "Wymaga działania",
    failed: "Błąd",
    done: "Gotowe"
  };

  const rows = actions.map((action, index) => {
    let state = "pending";
    if (index < completed) state = "done";
    else if (index === completed && job.status !== "done") state = "current";
    return `<div class="install-step ${state}">
      <span class="install-step-dot">${state === "done" ? "✓" : index + 1}</span>
      <span><strong>${esc(action.title)}</strong><small>${esc(action.phase)}</small></span>
    </div>`;
  }).join("");

  let interaction = "";
  if (job.status === "waiting" && job.waiting_for) {
    const wait = job.waiting_for;
    const kind = wait.interaction || "";

    if (kind === "qbittorrent-credentials" || kind === "jellyfin-credentials") {
      const serviceName = kind === "qbittorrent-credentials" ? "qBittorrent" : "Jellyfin";
      const note = kind === "jellyfin-credentials"
        ? "Hasło posłuży tylko do uzyskania tokenu Jellyfin i nie zostanie zapisane."
        : "Dane zostaną zapisane lokalnie w pliku secrets z uprawnieniami 0600.";

      interaction = `<div class="install-interaction">
        <strong>Połącz z istniejącym ${esc(serviceName)}</strong>
        <p>${esc(note)}</p>
        <div class="credential-form">
          <label>
            <span>Login</span>
            <input id="existingServiceUsername" type="text" autocomplete="username" spellcheck="false">
          </label>
          <label>
            <span>Hasło</span>
            <input id="existingServicePassword" type="password" autocomplete="current-password">
          </label>
          <button class="primary-btn" id="submitCredentialsBtn" type="button">Sprawdź i połącz</button>
        </div>
      </div>`;
    } else {
      const link = wait.auth_url
        ? `<a class="primary-btn inline-btn" href="${esc(wait.auth_url)}" target="_blank" rel="noopener">Otwórz autoryzację</a>`
        : "";
      interaction = `<div class="install-interaction">
        <strong>Potrzebne działanie użytkownika</strong>
        <p>${esc(kind || "Dokończ wymagany krok, a potem wznów instalację.")}</p>
        <div class="install-interaction-actions">
          ${link}
          <button class="ghost-btn" id="resumeInstallBtn" type="button">Wznów</button>
        </div>
      </div>`;
    }
  }

  if (job.status === "failed") {
    interaction = `<div class="install-interaction error-box">
      <strong>Instalacja zatrzymana</strong>
      <p>${esc(job.error || "Nieznany błąd")}</p>
      <button class="ghost-btn" id="retryInstallBtn" type="button">Ponów ten krok</button>
    </div>`;
  }

  if (job.status === "done") {
    interaction = `<div class="install-interaction success-box">
      <strong>LMS jest gotowy</strong>
      <p>Dane logowania do usług zarządzanych przez LMS są ukryte. Pokaż je dopiero, gdy chcesz je skopiować.</p>
      <button class="ghost-btn" id="revealCredentialsBtn" type="button">Pokaż dane logowania</button>
      <div id="finalCredentials" class="final-credentials" hidden></div>
    </div>`;
  }

  $("#serverCards").className = "install-job";
  $("#serverCards").innerHTML = `
    <div class="install-job-head">
      <div>
        <span class="eyebrow">Instalacja LMS</span>
        <h3>${esc(statusNames[job.status] || job.status)}</h3>
      </div>
      <strong>${completed} / ${actions.length}</strong>
    </div>
    <div class="install-progress"><span style="width:${actions.length ? Math.round(completed / actions.length * 100) : 0}%"></span></div>
    <div class="install-steps">${rows}</div>
    ${interaction}
  `;

  $("#checks").innerHTML =
    job.status === "done"
      ? '<div class="check ok">Instalacja zakończona pomyślnie</div>'
      : `<div class="check ${job.status === "failed" ? "warn" : "muted"}">Status: ${esc(statusNames[job.status] || job.status)}</div>` +
        (active ? '<div class="check muted">Backend wykonuje kolejną akcję…</div>' : "");

  $("#nextBtn").disabled = true;
  $("#nextBtn").textContent = job.status === "done" ? "Gotowe ✓" : "Instalacja trwa";

  $("#resumeInstallBtn")?.addEventListener("click", () => transitionInstallJob("resume"));
  $("#retryInstallBtn")?.addEventListener("click", () => transitionInstallJob("retry"));
  $("#submitCredentialsBtn")?.addEventListener("click", submitInstallCredentials);
  $("#revealCredentialsBtn")?.addEventListener("click", revealFinalCredentials);
}

async function copyCredential(value, button) {
  try {
    await navigator.clipboard.writeText(value);
    const original = button.textContent;
    button.textContent = "Skopiowano ✓";
    setTimeout(() => {
      button.textContent = original;
    }, 1200);
  } catch {
    $("#hint").textContent = "Nie udało się skopiować automatycznie. Zaznacz wartość ręcznie.";
  }
}

async function revealFinalCredentials() {
  if (!installJobId) return;
  const button = $("#revealCredentialsBtn");
  const target = $("#finalCredentials");
  if (!target) return;

  if (button) {
    button.disabled = true;
    button.textContent = "Pobieranie…";
  }

  try {
    const response = await apiFetch(
      `/api/jobs/${encodeURIComponent(installJobId)}/credentials`
    );
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }

    const labels = {
      jellyfin: "Jellyfin",
      qbittorrent: "qBittorrent"
    };
    const entries = Object.entries(data.credentials || {});

    target.hidden = false;
    if (!entries.length) {
      target.innerHTML = '<div class="check muted">Brak wygenerowanych danych logowania do pokazania.</div>';
    } else {
      target.innerHTML = entries.map(([id, credential], index) => `
        <article class="credential-result">
          <strong>${esc(labels[id] || id)}</strong>
          <div class="credential-value">
            <span>Login</span>
            <code>${esc(credential.username)}</code>
          </div>
          <div class="credential-value">
            <span>Hasło</span>
            <code>${esc(credential.password)}</code>
            <button class="ghost-btn copy-secret-btn" data-secret-index="${index}" type="button">Kopiuj hasło</button>
          </div>
        </article>
      `).join("");

      target.querySelectorAll(".copy-secret-btn").forEach((copyButton) => {
        const index = Number(copyButton.dataset.secretIndex);
        const credential = entries[index]?.[1];
        if (!credential) return;
        copyButton.addEventListener("click", () => {
          copyCredential(credential.password, copyButton);
        });
      });
    }

    if (button) {
      button.textContent = "Dane pokazane";
      button.disabled = true;
    }
  } catch (error) {
    $("#hint").textContent = error.message;
    if (button) {
      button.disabled = false;
      button.textContent = "Pokaż dane logowania";
    }
  }
}

async function submitInstallCredentials() {
  if (!installJobId) return;

  const usernameInput = $("#existingServiceUsername");
  const passwordInput = $("#existingServicePassword");
  const button = $("#submitCredentialsBtn");
  const username = usernameInput?.value || "";
  const password = passwordInput?.value || "";

  if (!username.trim() || !password) {
    $("#hint").textContent = "Podaj login i hasło.";
    return;
  }

  if (button) {
    button.disabled = true;
    button.textContent = "Sprawdzanie…";
  }

  try {
    const response = await apiFetch(
      `/api/jobs/${encodeURIComponent(installJobId)}/input`,
      {
        method: "POST",
        body: JSON.stringify({username, password})
      }
    );

    if (passwordInput) passwordInput.value = "";
    const data = await response.json();
    if (!response.ok || !data.ok) {
      throw new Error(data.error || `HTTP ${response.status}`);
    }

    $("#hint").textContent = "Dane poprawne. Wznawiam instalację…";
    pollInstallJob();
  } catch (error) {
    if (passwordInput) passwordInput.value = "";
    $("#hint").textContent = error.message;
    if (button) {
      button.disabled = false;
      button.textContent = "Sprawdź i połącz";
    }
  }
}

async function pollInstallJob() {
  if (!installJobId) return;
  stopInstallPolling();
  try {
    const response = await apiFetch(`/api/jobs/${encodeURIComponent(installJobId)}`);
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    renderJobProgress(data.job, data.active);
    if (!["done", "failed", "waiting"].includes(data.job.status)) {
      installPollTimer = setTimeout(pollInstallJob, 900);
    }
  } catch (error) {
    $("#hint").textContent = `Nie udało się odświeżyć postępu: ${error.message}`;
  }
}

async function transitionInstallJob(mode) {
  if (!installJobId) return;
  try {
    const response = await apiFetch(
      `/api/jobs/${encodeURIComponent(installJobId)}/${mode}`,
      {method: "POST"}
    );
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    $("#hint").textContent = mode === "retry" ? "Ponawiam zatrzymany krok…" : "Wznawiam instalację…";
    pollInstallJob();
  } catch (error) {
    $("#hint").textContent = error.message;
  }
}

async function startInstallJob() {
  if (!currentPlan || installJobId) return;
  const destructive = Boolean(currentPlan.destructive);
  const confirmed = !destructive || Boolean($("#destructiveConfirm")?.checked);
  if (!confirmed) {
    $("#hint").textContent = "Potwierdź formatowanie dysku, aby rozpocząć.";
    return;
  }

  $("#nextBtn").disabled = true;
  $("#nextBtn").textContent = "Uruchamianie…";
  try {
    const response = await apiFetch("/api/jobs/start", {
      method: "POST",
      body: JSON.stringify({
        config: buildSelectionPayload(),
        confirm_destructive: destructive && confirmed
      })
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    installJobId = data.job.id;
    renderJobProgress(data.job, true);
    pollInstallJob();
  } catch (error) {
    $("#hint").textContent = error.message;
    $("#nextBtn").disabled = false;
    $("#nextBtn").textContent = "Rozpocznij instalację";
  }
}

function renderInstallPreview(data) {
  setActiveStep(7);
  stopInstallPolling();

  const changesAllowed = data.installer?.changes_allowed === true;
  const executionReady = data.installer?.execution_ready === true;
  const blocked = !changesAllowed || !executionReady;
  const blockReason = data.installer?.block_reason ||
    (!executionReady ? "Silnik wykonawczy nie jest jeszcze gotowy do testów." : "");

  if (installJobId) {
    pollInstallJob();
    return;
  }

  $("#serverCards").className = "install-preview";
  $("#serverCards").innerHTML = `
    <div class="install-icon">${blocked ? "🔒" : "✓"}</div>
    <h3>${blocked ? "Instalacja zablokowana" : "Gotowe do instalacji"}</h3>
    <p>${blocked
      ? esc(blockReason)
      : "Backend ponownie zweryfikuje host i wykona przygotowany plan krok po kroku."}</p>
    ${!blocked && currentPlan?.destructive ? `
      <label class="destructive-confirm">
        <input id="destructiveConfirm" type="checkbox">
        <span>Rozumiem, że wybrany dysk zostanie sformatowany i jego dane zostaną usunięte.</span>
      </label>` : ""}
  `;

  $("#checks").innerHTML = blocked
    ? '<div class="check ok">Zabezpieczenia installera są aktywne.</div><div class="check muted">Żadna operacja systemowa nie zostanie wykonana.</div>'
    : '<div class="check ok">Plan i host zostały zweryfikowane.</div><div class="check warn">Instalacja będzie wykonywana etapami z możliwością wznowienia.</div>';

  $("#hint").textContent = blocked
    ? "Na tym hoście możesz bezpiecznie testować tylko kreator i plan."
    : "Po starcie postęp będzie zapisywany po każdym kroku.";
  $("#nextBtn").disabled = blocked || Boolean(currentPlan?.destructive);
  $("#nextBtn").textContent = blocked ? "Instalacja zablokowana" : "Rozpocznij instalację";

  $("#destructiveConfirm")?.addEventListener("change", (event) => {
    $("#nextBtn").disabled = !event.target.checked;
  });
}

async function scan() {
  const btn = $("#rescanBtn");
  btn.disabled = true;
  $("#nextBtn").disabled = true;
  $("#scanState").innerHTML = '<span class="dot"></span>Wykrywanie serwera…';
  $("#serverCards").className = "cards";
  $("#serverCards").innerHTML = '<div class="skeleton"></div><div class="skeleton"></div><div class="skeleton"></div>';
  $("#checks").innerHTML = '<div class="check muted">Sprawdzanie systemu…</div>';
  try {
    if (!setupToken) throw new Error("Brak tokenu sesji Setup");
    const response = await apiFetch("/api/detect");
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    hostData = await response.json();
    $("#scanState").innerHTML = '<span class="dot" style="background:var(--ok)"></span>Skan zakończony';
    if (step === 7) renderInstallPreview(hostData);
    else if (step === 6) renderSummary();
    else if (step === 5) renderNetwork();
    else if (step === 4) renderServices(hostData);
    else if (step === 3) renderLibraries();
    else if (step === 2) renderDisks(hostData);
    else renderServer(hostData);
  } catch (error) {
    $("#scanState").innerHTML = '<span class="dot" style="background:#dc7e7e"></span>Błąd skanowania';
    $("#serverCards").innerHTML = infoCard("Błąd", "Nie udało się pobrać danych hosta", error.message);
    $("#checks").innerHTML = '<div class="check warn">Autodetect nie zakończył się poprawnie.</div>';
    $("#hint").textContent = "Uruchom skan ponownie.";
  } finally {
    btn.disabled = false;
  }
}

$("#rescanBtn").addEventListener("click", scan);
$("#backBtn").addEventListener("click", () => {
  if (!hostData) return;
  if (step === 7) renderSummary();
  else if (step === 6) renderNetwork();
  else if (step === 5) renderServices(hostData);
  else if (step === 4) renderLibraries();
  else if (step === 3) renderDisks(hostData);
  else renderServer(hostData);
});
$("#nextBtn").addEventListener("click", () => {
  if (!hostData) return;
  if (step === 1) {
    renderDisks(hostData);
    return;
  }
  if (step === 2) {
    renderLibraries();
    return;
  }
  if (step === 3) {
    renderServices(hostData);
    return;
  }
  if (step === 4) {
    renderNetwork();
    return;
  }
  if (step === 5) {
    renderSummary();
    return;
  }
  if (step === 6) {
    renderInstallPreview(hostData);
    return;
  }
  if (step === 7) {
    startInstallJob();
  }
});

scan();

[executed on device: nas-server (67000a68-9cef-4872-b788-2a95d730eb83)]