(() => {
    const API = "http://100.127.67.28:8090";
    const WALLPAPER_API = "http://100.127.67.28:8088";

    const SERVICES = {
        jellyfin: {
            name: "Jellyfin",
            description: "Filmy • Seriale • Anime",
            url: "http://100.127.67.28:8096",
            icon: "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/jellyfin.png"
        },
        gdrive: {
            name: "GDrive → NAS",
            description: "Transfer plików",
            url: "http://100.127.67.28:8088",
            icon: "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/google-drive.png"
        },
        kuma: {
            name: "Uptime Kuma",
            description: "Monitoring usług",
            url: "http://100.127.67.28:3001",
            icon: "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/uptime-kuma.png"
        },
        ntfy: {
            name: "ntfy",
            description: "Powiadomienia",
            url: "http://100.127.67.28:8089",
            icon: "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/ntfy.png"
        }
    };


    function serviceCard(id) {
        const s = SERVICES[id];

        return `
            <a class="nas-service-card"
               id="card-${id}"
               href="${s.url}">

                <div class="nas-card-top">
                    <div class="nas-service-icon">
                        <img src="${s.icon}" alt="">
                    </div>

                    <div class="nas-card-status">
                        <span class="nas-dot" id="dot-${id}"></span>
                        <span id="card-status-${id}">
                            Sprawdzanie
                        </span>
                    </div>
                </div>

                <div class="nas-card-content">
                    <h3>${s.name}</h3>
                    <p>${s.description}</p>

                    <div
                        class="nas-card-info"
                        id="info-${id}">
                        Ładowanie danych…
                    </div>
                </div>

                <div class="nas-card-bottom">
                    <span id="latency-${id}">— ms</span>
                    <span class="nas-open">↗</span>
                </div>
            </a>
        `;
    }


    function buildDashboard() {
        const old =
            document.getElementById("nas-dashboard");

        if (old) {
            old.remove();
        }

        const dashboard =
            document.createElement("div");

        dashboard.id = "nas-dashboard";

        dashboard.innerHTML = `
            <div class="nas-background"></div>
            <div class="nas-background-overlay"></div>

            <div class="nas-shell">

                <header class="nas-header">

                    <div class="nas-welcome">

                        <div class="nas-logo">
                            ☁
                        </div>

                        <div>
                            <div class="nas-greeting">
                                <span id="nas-greeting">
                                    Witaj
                                </span>,
                                <strong>Remigiusz</strong>
                            </div>

                            <div class="nas-global-status">
                                <span
                                    class="nas-dot online"
                                    id="global-dot">
                                </span>

                                <span id="global-status">
                                    Sprawdzanie systemu…
                                </span>
                            </div>
                        </div>

                    </div>


                    <div class="nas-header-actions">

                        <div class="nas-date-block">
                            <strong id="nas-time">
                                --:--
                            </strong>

                            <span id="nas-date">
                                ---
                            </span>
                        </div>


                        <button
                            class="nas-action"
                            id="nas-refresh"
                            title="Odśwież dane">
                            ↻
                        </button>


                        <button
                            class="nas-action"
                            id="nas-wallpaper"
                            title="Zmień tapetę">
                            ◈
                        </button>

                    </div>

                </header>


                <main class="nas-main">

                    <section class="nas-services-panel">

                        <div class="nas-section-heading">

                            <div>
                                <span class="nas-eyebrow">
                                    TWOJA CHMURA
                                </span>

                                <h1>Usługi</h1>
                            </div>

                            <span
                                class="nas-section-status"
                                id="services-summary">
                                Sprawdzanie…
                            </span>

                        </div>


                        <div class="nas-services-grid">
                            ${serviceCard("jellyfin")}
                            ${serviceCard("gdrive")}
                            ${serviceCard("kuma")}
                            ${serviceCard("ntfy")}
                        </div>

                    </section>


                    <section class="nas-lower-grid">

                        <article
                            class="nas-panel nas-status-panel">

                            <div class="nas-panel-heading">

                                <div>
                                    <span class="nas-eyebrow">
                                        MONITORING
                                    </span>

                                    <h2>Status usług</h2>
                                </div>

                                <span class="nas-panel-symbol">
                                    ⌁
                                </span>

                            </div>


                            <div class="nas-status-list">

                                ${Object.entries(SERVICES)
                                    .map(([id, service]) => `
                                        <div class="nas-status-row">

                                            <div>
                                                <span
                                                    class="nas-dot"
                                                    id="status-dot-${id}">
                                                </span>

                                                <span>
                                                    ${service.name}
                                                </span>
                                            </div>

                                            <div>
                                                <strong
                                                    id="status-text-${id}">
                                                    —
                                                </strong>

                                                <span
                                                    id="status-latency-${id}">
                                                    —
                                                </span>
                                            </div>

                                        </div>
                                    `).join("")}

                            </div>

                        </article>


                        <article
                            class="nas-panel nas-resource-panel">

                            <div class="nas-panel-heading">

                                <div>
                                    <span class="nas-eyebrow">
                                        SERWER
                                    </span>

                                    <h2>Wykorzystanie NAS</h2>
                                </div>

                                <span class="nas-panel-symbol">
                                    ◫
                                </span>

                            </div>


                            <div class="nas-resource">

                                <div class="nas-resource-label">
                                    <span>CPU</span>
                                    <strong id="cpu-value">
                                        —%
                                    </strong>
                                </div>

                                <div class="nas-progress">
                                    <div id="cpu-progress"></div>
                                </div>

                            </div>


                            <div class="nas-resource">

                                <div class="nas-resource-label">
                                    <span>RAM</span>
                                    <strong id="ram-value">
                                        —%
                                    </strong>
                                </div>

                                <div class="nas-progress">
                                    <div id="ram-progress"></div>
                                </div>

                            </div>


                            <div class="nas-resource">

                                <div class="nas-resource-label">
                                    <span>Dysk NAS</span>
                                    <strong id="disk-value">
                                        —%
                                    </strong>
                                </div>

                                <div class="nas-progress">
                                    <div id="disk-progress"></div>
                                </div>

                                <div
                                    class="nas-disk-detail"
                                    id="disk-detail">
                                    — GB / — GB
                                </div>

                            </div>


                            <div class="nas-uptime">
                                <span>Uptime serwera</span>

                                <strong id="uptime-value">
                                    —
                                </strong>
                            </div>

                        </article>


                        <article
                            class="nas-panel nas-links-panel">

                            <div class="nas-panel-heading">

                                <div>
                                    <span class="nas-eyebrow">
                                        SKRÓTY
                                    </span>

                                    <h2>Szybkie linki</h2>
                                </div>

                                <span class="nas-panel-symbol">
                                    ⌘
                                </span>

                            </div>


                            <div class="nas-quick-links">

                                ${Object.entries(SERVICES)
                                    .map(([id, service]) => `
                                        <a href="${service.url}">
                                            <img
                                                src="${service.icon}"
                                                alt="">

                                            <span>
                                                ${service.name}
                                            </span>

                                            <strong>↗</strong>
                                        </a>
                                    `).join("")}

                            </div>

                        </article>

                    </section>

                </main>


                <footer class="nas-footer">

                    <span>
                        NAS • Oracle Cloud
                    </span>

                    <span id="footer-system">
                        Łączenie z serwerem…
                    </span>

                </footer>

            </div>


            <input
                type="file"
                id="wallpaper-input"
                accept="image/jpeg,image/png,image/webp"
                hidden
            >
        `;

        document.body.appendChild(dashboard);
    }


    function updateClock() {
        const now = new Date();
        const hour = now.getHours();

        let greeting = "Witaj";

        if (hour >= 5 && hour < 12) {
            greeting = "Dzień dobry";
        } else if (hour >= 12 && hour < 18) {
            greeting = "Miłego popołudnia";
        } else if (hour >= 18 && hour < 23) {
            greeting = "Dobry wieczór";
        } else {
            greeting = "Dobranoc";
        }

        document.getElementById(
            "nas-greeting"
        ).textContent = greeting;


        document.getElementById(
            "nas-time"
        ).textContent =
            now.toLocaleTimeString(
                "pl-PL",
                {
                    hour: "2-digit",
                    minute: "2-digit"
                }
            );


        document.getElementById(
            "nas-date"
        ).textContent =
            now.toLocaleDateString(
                "pl-PL",
                {
                    weekday: "long",
                    day: "numeric",
                    month: "long"
                }
            );
    }


    function formatUptime(seconds) {
        if (
            seconds === undefined ||
            seconds === null
        ) {
            return "—";
        }

        const days =
            Math.floor(seconds / 86400);

        const hours =
            Math.floor(
                (seconds % 86400) / 3600
            );

        const minutes =
            Math.floor(
                (seconds % 3600) / 60
            );

        if (days > 0) {
            return `${days} d ${hours} h`;
        }

        if (hours > 0) {
            return `${hours} h ${minutes} min`;
        }

        return `${minutes} min`;
    }


    async function getJSON(endpoint) {
        const response =
            await fetch(
                `${API}${endpoint}?_=${Date.now()}`,
                {
                    cache: "no-store"
                }
            );

        if (!response.ok) {
            throw new Error(
                `${endpoint}: HTTP ${response.status}`
            );
        }

        return response.json();
    }


    function setProgress(id, value) {
        const element =
            document.getElementById(id);

        if (!element) return;

        const safe =
            Math.max(
                0,
                Math.min(
                    100,
                    Number(value) || 0
                )
            );

        element.style.width =
            `${safe}%`;

        element.classList.toggle(
            "warning",
            safe >= 75 && safe < 90
        );

        element.classList.toggle(
            "danger",
            safe >= 90
        );
    }


    function renderSystem(data) {
        document.getElementById(
            "cpu-value"
        ).textContent =
            `${data.cpu}%`;

        document.getElementById(
            "ram-value"
        ).textContent =
            `${data.ram}%`;

        document.getElementById(
            "disk-value"
        ).textContent =
            `${data.disk}%`;

        document.getElementById(
            "disk-detail"
        ).textContent =
            `${data.diskUsedGB} GB / ${data.diskTotalGB} GB`;

        document.getElementById(
            "uptime-value"
        ).textContent =
            formatUptime(
                data.uptimeSeconds
            );

        setProgress(
            "cpu-progress",
            data.cpu
        );

        setProgress(
            "ram-progress",
            data.ram
        );

        setProgress(
            "disk-progress",
            data.disk
        );
    }


    function renderJellyfin(data) {
        const element =
            document.getElementById(
                "info-jellyfin"
            );

        if (!data.online) {
            element.textContent =
                "Jellyfin niedostępny";

            return;
        }

        element.innerHTML = `
            <span>
                <strong>${data.movies}</strong>
                filmów
            </span>

            <span>
                <strong>${data.series}</strong>
                seriali
            </span>

            <span>
                <strong>${data.episodes}</strong>
                odc.
            </span>
        `;
    }


    function renderStatus(status) {
        let onlineCount = 0;

        Object.entries(SERVICES)
            .forEach(([id]) => {

                const data =
                    status[id];

                if (!data) return;

                const online =
                    Boolean(data.online);

                if (online) {
                    onlineCount++;
                }


                [
                    `dot-${id}`,
                    `status-dot-${id}`
                ].forEach(elementId => {

                    const dot =
                        document.getElementById(
                            elementId
                        );

                    if (!dot) return;

                    dot.classList.toggle(
                        "online",
                        online
                    );

                    dot.classList.toggle(
                        "offline",
                        !online
                    );
                });


                document.getElementById(
                    `card-status-${id}`
                ).textContent =
                    online
                        ? "Online"
                        : "Offline";


                document.getElementById(
                    `status-text-${id}`
                ).textContent =
                    online
                        ? "Online"
                        : "Offline";


                const latency =
                    data.latency !== null
                        ? `${data.latency} ms`
                        : "—";


                document.getElementById(
                    `latency-${id}`
                ).textContent =
                    latency;


                document.getElementById(
                    `status-latency-${id}`
                ).textContent =
                    latency;


                document.getElementById(
                    `card-${id}`
                ).classList.toggle(
                    "offline",
                    !online
                );
            });


        document.getElementById(
            "services-summary"
        ).textContent =
            `${onlineCount} / 4 online`;


        const everythingOnline =
            onlineCount === 4;


        document.getElementById(
            "global-status"
        ).textContent =
            everythingOnline
                ? "Wszystkie systemy działają"
                : `${onlineCount} z 4 usług online`;


        const globalDot =
            document.getElementById(
                "global-dot"
            );

        globalDot.classList.toggle(
            "online",
            everythingOnline
        );

        globalDot.classList.toggle(
            "offline",
            !everythingOnline
        );
    }


    function renderStaticServiceInfo() {
        document.getElementById(
            "info-gdrive"
        ).innerHTML =
            `<span>Google Drive</span><span>→ NAS</span>`;


        document.getElementById(
            "info-kuma"
        ).innerHTML =
            `<span><strong>4</strong> monitory</span>`;


        document.getElementById(
            "info-ntfy"
        ).innerHTML =
            `<span>Alerty NAS</span>`;
    }


    async function loadData() {
        const refresh =
            document.getElementById(
                "nas-refresh"
            );

        refresh?.classList.add(
            "loading"
        );


        const results =
            await Promise.allSettled([
                getJSON("/api/system"),
                getJSON("/api/jellyfin"),
                getJSON("/api/status")
            ]);


        let success = 0;


        if (
            results[0].status ===
            "fulfilled"
        ) {
            renderSystem(
                results[0].value
            );

            success++;
        }


        if (
            results[1].status ===
            "fulfilled"
        ) {
            renderJellyfin(
                results[1].value
            );

            success++;
        }


        if (
            results[2].status ===
            "fulfilled"
        ) {
            renderStatus(
                results[2].value
            );

            success++;
        }


        document.getElementById(
            "footer-system"
        ).textContent =
            success === 3
                ? "Dashboard API • Online"
                : "Dashboard API • Częściowy błąd";


        refresh?.classList.remove(
            "loading"
        );
    }


    function applyWallpaper() {
        const background =
            document.querySelector(
                ".nas-background"
            );

        if (!background) return;

        background.style.backgroundImage =
            `url("${WALLPAPER_API}/wallpaper?t=${Date.now()}")`;

        background.classList.add(
            "has-wallpaper"
        );
    }


    function setupActions() {
        const refreshButton =
            document.getElementById(
                "nas-refresh"
            );

        const wallpaperButton =
            document.getElementById(
                "nas-wallpaper"
            );

        const wallpaperInput =
            document.getElementById(
                "wallpaper-input"
            );


        refreshButton.addEventListener(
            "click",
            loadData
        );


        wallpaperButton.addEventListener(
            "click",
            () => wallpaperInput.click()
        );


        wallpaperInput.addEventListener(
            "change",
            async () => {

                const file =
                    wallpaperInput.files?.[0];

                if (!file) return;


                wallpaperButton.classList.add(
                    "loading"
                );


                try {
                    const form =
                        new FormData();

                    form.append(
                        "wallpaper",
                        file
                    );


                    const response =
                        await fetch(
                            `${WALLPAPER_API}/api/wallpaper`,
                            {
                                method: "POST",
                                body: form
                            }
                        );


                    if (!response.ok) {
                        throw new Error(
                            `HTTP ${response.status}`
                        );
                    }


                    applyWallpaper();


                } catch (error) {

                    console.error(
                        "Wallpaper upload error:",
                        error
                    );

                    alert(
                        "Nie udało się zmienić tapety."
                    );

                } finally {

                    wallpaperButton.classList.remove(
                        "loading"
                    );

                    wallpaperInput.value = "";
                }
            }
        );


        /*
         * Wczytaj tapetę zapisaną
         * wcześniej na NAS-ie.
         */
        applyWallpaper();
    }


    function init() {
        buildDashboard();

        renderStaticServiceInfo();

        updateClock();

        setupActions();

        loadData();


        setInterval(
            updateClock,
            1000
        );


        setInterval(
            loadData,
            30000
        );
    }


    if (
        document.readyState ===
        "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            init
        );
    } else {
        init();
    }

})();

/* ============================================================
   qBITTORRENT DOWNLOAD PANEL
   ============================================================ */

(() => {
    const QBT_API = "http://100.127.67.28:8090";

    let pendingMagnet = "";
    let qbtTimer = null;


    function formatBytes(bytes) {
        const value = Number(bytes) || 0;

        if (value < 1024) {
            return `${value} B`;
        }

        if (value < 1024 ** 2) {
            return `${(value / 1024).toFixed(1)} KB`;
        }

        if (value < 1024 ** 3) {
            return `${(value / 1024 ** 2).toFixed(1)} MB`;
        }

        return `${(value / 1024 ** 3).toFixed(2)} GB`;
    }


    function formatSpeed(bytes) {
        return `${formatBytes(bytes)}/s`;
    }


    function formatEta(seconds) {
        if (
            seconds === null ||
            seconds === undefined ||
            !Number.isFinite(Number(seconds))
        ) {
            return "—";
        }

        seconds = Number(seconds);

        if (seconds < 60) {
            return `${Math.max(1, Math.round(seconds))} s`;
        }

        if (seconds < 3600) {
            return `${Math.round(seconds / 60)} min`;
        }

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.round(
            (seconds % 3600) / 60
        );

        return `${hours} h ${minutes} min`;
    }


    function stateLabel(state) {
        const states = {
            downloading: "Pobieranie",
            metaDL: "Pobieranie metadanych",
            forcedDL: "Wymuszone pobieranie",
            stalledDL: "Oczekiwanie na peerów",
            checkingDL: "Sprawdzanie",
            allocating: "Przydzielanie miejsca",

            uploading: "Seedowanie",
            stalledUP: "Seedowanie",
            forcedUP: "Seedowanie",

            pausedDL: "Wstrzymano",
            pausedUP: "Wstrzymano",
            stoppedDL: "Zatrzymano",
            stoppedUP: "Zatrzymano",

            queuedDL: "W kolejce",
            queuedUP: "W kolejce",

            checkingUP: "Sprawdzanie",
            moving: "Przenoszenie",
            error: "Błąd",
            missingFiles: "Brak plików"
        };

        return states[state] || state || "Nieznany";
    }


    function createPanel() {
        if (
            document.getElementById(
                "nas-download-panel"
            )
        ) {
            return true;
        }

        const services =
            document.querySelector(
                "#nas-dashboard .nas-services-panel"
            );

        if (!services) {
            return false;
        }

        const panel =
            document.createElement("section");

        panel.className =
            "nas-download-panel";

        panel.id =
            "nas-download-panel";

        panel.innerHTML = `
            <div class="nas-download-heading">

                <div>
                    <span class="nas-eyebrow">
                        QBITTORRENT
                    </span>

                    <h2>Pobieranie</h2>
                </div>

                <div class="nas-qbt-status">
                    <span
                        class="nas-dot"
                        id="qbt-dot">
                    </span>

                    <span id="qbt-status">
                        Łączenie…
                    </span>
                </div>

            </div>


            <div class="nas-magnet-row">

                <div class="nas-magnet-input-wrap">

                    <span class="nas-magnet-icon">
                        ↘
                    </span>

                    <input
                        type="text"
                        id="nas-magnet-input"
                        placeholder="Wklej link magnet…"
                        autocomplete="off"
                        spellcheck="false"
                    >

                </div>

                <button
                    type="button"
                    id="nas-magnet-submit"
                    class="nas-download-button">
                    Pobierz
                </button>

            </div>


            <div
                class="nas-download-message"
                id="nas-download-message">
            </div>


            <div
                class="nas-transfer-summary"
                id="nas-transfer-summary">

                <div>
                    <span>↓</span>

                    <strong id="qbt-global-down">
                        0 B/s
                    </strong>
                </div>

                <div>
                    <span>↑</span>

                    <strong id="qbt-global-up">
                        0 B/s
                    </strong>
                </div>

                <div>
                    <span>Aktywne</span>

                    <strong id="qbt-active">
                        0
                    </strong>
                </div>

            </div>


            <div
                class="nas-torrent-list"
                id="nas-torrent-list">
            </div>


            <div
                class="nas-download-empty"
                id="nas-download-empty">

                <span>✓</span>

                <div>
                    <strong>
                        Brak aktywnych pobrań
                    </strong>

                    <small>
                        Wklej magnet powyżej, aby rozpocząć.
                    </small>
                </div>

            </div>
        `;

        services.insertAdjacentElement(
            "afterend",
            panel
        );

        createLibraryModal();
        setupQbtActions();

        return true;
    }


    function createLibraryModal() {
        if (
            document.getElementById(
                "nas-library-modal"
            )
        ) {
            return;
        }

        const modal =
            document.createElement("div");

        modal.id =
            "nas-library-modal";

        modal.className =
            "nas-library-modal";

        modal.innerHTML = `
            <div class="nas-library-dialog">

                <div class="nas-library-dialog-top">

                    <div>
                        <span class="nas-eyebrow">
                            MIEJSCE DOCELOWE
                        </span>

                        <h2>
                            Gdzie zapisać?
                        </h2>
                    </div>

                    <button
                        type="button"
                        class="nas-library-close"
                        id="nas-library-close">
                        ×
                    </button>

                </div>


                <p class="nas-library-description">
                    qBittorrent pobierze pliki bezpośrednio
                    do wybranej biblioteki NAS.
                </p>


                <div class="nas-library-grid">

                    <button
                        type="button"
                        class="nas-library-choice"
                        data-library="movies">

                        <span class="nas-library-emoji">
                            🎬
                        </span>

                        <div>
                            <strong>Filmy</strong>
                            <small>Biblioteka filmów</small>
                        </div>

                    </button>


                    <button
                        type="button"
                        class="nas-library-choice"
                        data-library="series">

                        <span class="nas-library-emoji">
                            📺
                        </span>

                        <div>
                            <strong>Seriale</strong>
                            <small>Biblioteka seriali</small>
                        </div>

                    </button>


                    <button
                        type="button"
                        class="nas-library-choice"
                        data-library="anime">

                        <span class="nas-library-emoji">
                            🌸
                        </span>

                        <div>
                            <strong>Anime</strong>
                            <small>Serie anime</small>
                        </div>

                    </button>


                    <button
                        type="button"
                        class="nas-library-choice"
                        data-library="animeMovies">

                        <span class="nas-library-emoji">
                            🎞️
                        </span>

                        <div>
                            <strong>Anime Filmy</strong>
                            <small>Filmy anime</small>
                        </div>

                    </button>


                    <button
                        type="button"
                        class="nas-library-choice nas-library-downloads"
                        data-library="downloads">

                        <span class="nas-library-emoji">
                            📥
                        </span>

                        <div>
                            <strong>Downloads</strong>
                            <small>Bez przypisywania do biblioteki</small>
                        </div>

                    </button>

                </div>

            </div>
        `;

        document.body.appendChild(modal);
    }


    function openLibraryModal() {
        document
            .getElementById("nas-library-modal")
            ?.classList.add("open");
    }


    function closeLibraryModal() {
        document
            .getElementById("nas-library-modal")
            ?.classList.remove("open");
    }


    function showMessage(
        message,
        type = ""
    ) {
        const element =
            document.getElementById(
                "nas-download-message"
            );

        if (!element) {
            return;
        }

        element.textContent = message;

        element.className =
            `nas-download-message ${type}`;

        if (message) {
            setTimeout(() => {
                if (
                    element.textContent ===
                    message
                ) {
                    element.textContent = "";
                    element.className =
                        "nas-download-message";
                }
            }, 5000);
        }
    }


    async function addMagnet(library) {
        const button =
            document.getElementById(
                "nas-magnet-submit"
            );

        const metadataLoader =
            document.getElementById(
                "nas-metadata-loader"
            );

        button.disabled = true;
        button.textContent = "Ładowanie…";

        /*
         * Biblioteka została już wybrana.
         * Zamykamy jej modal NATYCHMIAST.
         */
        closeLibraryModal();

        /*
         * I od razu pokazujemy użytkownikowi,
         * że qBittorrent pobiera metadata.
         */
        if (metadataLoader) {
            metadataLoader.classList.add("open");
        }

        try {
            const response = await fetch(
                `${QBT_API}/api/qbittorrent/add`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        magnet: pendingMagnet,
                        library
                    })
                }
            );

            const data =
                await response.json();

            if (
                !response.ok ||
                !data.ok
            ) {
                throw new Error(
                    data.error ||
                    `HTTP ${response.status}`
                );
            }

            /*
             * Backend zwrócił metadata.
             *
             * File-picker, który dodaliśmy wcześniej,
             * przechwytuje tę samą odpowiedź fetch()
             * i otworzy modal z listą plików.
             */
            const input =
                document.getElementById(
                    "nas-magnet-input"
                );

            input.value = "";
            pendingMagnet = "";

            showMessage(
                `✓ Metadane gotowe: ${data.libraryName}`,
                "success"
            );

            setTimeout(
                loadQbtData,
                800
            );

        } catch (error) {
            console.error(
                "qBittorrent add error:",
                error
            );

            showMessage(
                `Nie udało się dodać: ${error.message}`,
                "error"
            );

        } finally {

            /*
             * Niezależnie od wyniku requestu
             * spinner musi zniknąć.
             */
            if (metadataLoader) {
                metadataLoader.classList.remove("open");
            }

            button.disabled = false;
            button.textContent = "Pobierz";
        }
    }


    function setupQbtActions() {
        const input =
            document.getElementById(
                "nas-magnet-input"
            );

        const button =
            document.getElementById(
                "nas-magnet-submit"
            );

        const modal =
            document.getElementById(
                "nas-library-modal"
            );

        const close =
            document.getElementById(
                "nas-library-close"
            );


        function prepareMagnet() {
            const magnet =
                input.value.trim();

            if (!magnet) {
                showMessage(
                    "Najpierw wklej link magnet.",
                    "error"
                );

                input.focus();
                return;
            }

            if (
                !magnet
                    .toLowerCase()
                    .startsWith("magnet:?")
            ) {
                showMessage(
                    "To nie wygląda jak link magnet.",
                    "error"
                );

                input.focus();
                return;
            }

            pendingMagnet = magnet;

            openLibraryModal();
        }


        button.addEventListener(
            "click",
            prepareMagnet
        );


        input.addEventListener(
            "keydown",
            event => {
                if (
                    event.key === "Enter"
                ) {
                    event.preventDefault();
                    prepareMagnet();
                }
            }
        );


        close.addEventListener(
            "click",
            closeLibraryModal
        );


        modal.addEventListener(
            "click",
            event => {
                if (
                    event.target === modal
                ) {
                    closeLibraryModal();
                }
            }
        );


        document
            .querySelectorAll(
                ".nas-library-choice"
            )
            .forEach(choice => {

                choice.addEventListener(
                    "click",
                    () => {
                        addMagnet(
                            choice.dataset.library
                        );
                    }
                );

            });


        document.addEventListener(
            "keydown",
            event => {
                if (
                    event.key === "Escape"
                ) {
                    closeLibraryModal();
                }
            }
        );
    }


    function renderTorrent(torrent) {
        const progress =
            Math.max(
                0,
                Math.min(
                    100,
                    Number(
                        torrent.progress
                    ) || 0
                )
            );

        return `
            <div class="nas-torrent">

                <div class="nas-torrent-top">

                    <div class="nas-torrent-name">
                        ${escapeHtml(
                            torrent.name ||
                            "Pobieranie metadanych…"
                        )}
                    </div>

                    <strong class="nas-torrent-percent">
                        ${progress.toFixed(1)}%
                    </strong>

                </div>


                <div class="nas-torrent-progress">
                    <div
                        style="width:${progress}%">
                    </div>
                </div>


                <div class="nas-torrent-details">

                    <span>
                        ${stateLabel(torrent.state)}
                    </span>

                    <span>
                        ↓ ${formatSpeed(
                            torrent.downloadSpeed
                        )}
                    </span>

                    <span>
                        ↑ ${formatSpeed(
                            torrent.uploadSpeed
                        )}
                    </span>

                    <span>
                        ${formatBytes(
                            torrent.downloaded
                        )}
                        /
                        ${formatBytes(
                            torrent.size
                        )}
                    </span>

                    <span>
                        ETA ${formatEta(
                            torrent.eta
                        )}
                    </span>

                </div>

            </div>
        `;
    }


    function escapeHtml(value) {
        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }


    function renderQbt(data) {
        const dot =
            document.getElementById(
                "qbt-dot"
            );

        const status =
            document.getElementById(
                "qbt-status"
            );

        if (!dot || !status) {
            return;
        }

        dot.classList.toggle(
            "online",
            Boolean(data.online)
        );

        dot.classList.toggle(
            "offline",
            !data.online
        );

        status.textContent =
            data.online
                ? "Online"
                : "Offline";


        document.getElementById(
            "qbt-global-down"
        ).textContent =
            formatSpeed(
                data.downloadSpeed
            );


        document.getElementById(
            "qbt-global-up"
        ).textContent =
            formatSpeed(
                data.uploadSpeed
            );


        document.getElementById(
            "qbt-active"
        ).textContent =
            data.active ?? 0;


        const list =
            document.getElementById(
                "nas-torrent-list"
            );

        const empty =
            document.getElementById(
                "nas-download-empty"
            );


        /*
         * Pokazujemy torrenty, które nie są
         * jeszcze ukończone.
         *
         * Seedujące zakończone zadania nie
         * zapychają dashboardu.
         */
        const visible =
            (data.torrents || [])
                .filter(torrent =>
                    Number(torrent.progress) < 100
                );


        if (!visible.length) {
            list.innerHTML = "";
            list.style.display = "none";
            empty.style.display = "flex";

            return;
        }


        empty.style.display = "none";
        list.style.display = "grid";

        list.innerHTML =
            visible
                .map(renderTorrent)
                .join("");
    }


    async function loadQbtData() {
        try {
            const response =
                await fetch(
                    `${QBT_API}/api/qbittorrent?_=${Date.now()}`,
                    {
                        cache: "no-store"
                    }
                );

            if (!response.ok) {
                throw new Error(
                    `HTTP ${response.status}`
                );
            }

            const data =
                await response.json();

            renderQbt(data);

        } catch (error) {
            console.error(
                "qBittorrent dashboard error:",
                error
            );

            const dot =
                document.getElementById(
                    "qbt-dot"
                );

            const status =
                document.getElementById(
                    "qbt-status"
                );

            dot?.classList.remove(
                "online"
            );

            dot?.classList.add(
                "offline"
            );

            if (status) {
                status.textContent =
                    "Offline";
            }
        }
    }


    function initQbtPanel() {
        if (!createPanel()) {
            setTimeout(
                initQbtPanel,
                100
            );

            return;
        }

        loadQbtData();

        if (qbtTimer) {
            clearInterval(qbtTimer);
        }

        /*
         * Transfer odświeżamy częściej niż
         * resztę dashboardu, żeby prędkość
         * i progress wyglądały na żywe.
         */
        qbtTimer =
            setInterval(
                loadQbtData,
                3000
            );
    }


    if (
        document.readyState ===
        "loading"
    ) {
        document.addEventListener(
            "DOMContentLoaded",
            initQbtPanel
        );
    } else {
        initQbtPanel();
    }

})();

/* ============================================================
   qBittorrent File Picker
   ============================================================ */

(() => {
    const API = "http://100.127.67.28:8090";

    let preparedTorrent = null;

    function formatFileSize(bytes) {
        if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";

        const units = ["B", "KB", "MB", "GB", "TB"];
        let value = bytes;
        let unit = 0;

        while (value >= 1024 && unit < units.length - 1) {
            value /= 1024;
            unit++;
        }

        return `${value.toFixed(unit >= 3 ? 2 : 1)} ${units[unit]}`;
    }

    function escapeFileHtml(value) {
        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function createFilePicker() {
        if (document.querySelector("#nas-file-picker")) return;

        const modal = document.createElement("div");
        modal.id = "nas-file-picker";
        modal.className = "nas-file-picker-overlay";

        modal.innerHTML = `
            <div class="nas-file-picker-dialog">

                <div class="nas-file-picker-header">
                    <div>
                        <div class="nas-file-picker-eyebrow">
                            QBITTORRENT
                        </div>

                        <h2>Wybierz pliki</h2>

                        <div
                            id="nas-file-picker-torrent"
                            class="nas-file-picker-torrent"
                        ></div>
                    </div>

                    <button
                        id="nas-file-picker-close"
                        class="nas-file-picker-close"
                        type="button"
                        title="Zamknij"
                    >
                        ×
                    </button>
                </div>

                <div class="nas-file-picker-toolbar">
                    <button
                        id="nas-files-smart"
                        class="nas-file-toolbar-button"
                        type="button"
                    >
                        Polecane
                    </button>

                    <button
                        id="nas-files-all"
                        class="nas-file-toolbar-button"
                        type="button"
                    >
                        Zaznacz wszystko
                    </button>

                    <button
                        id="nas-files-none"
                        class="nas-file-toolbar-button"
                        type="button"
                    >
                        Odznacz wszystko
                    </button>

                    <div
                        id="nas-files-summary"
                        class="nas-files-summary"
                    ></div>
                </div>

                <div
                    id="nas-file-picker-list"
                    class="nas-file-picker-list"
                ></div>

                <div class="nas-file-picker-footer">
                    <div
                        id="nas-file-picker-message"
                        class="nas-file-picker-message"
                    ></div>

                    <button
                        id="nas-file-picker-start"
                        class="nas-file-picker-start"
                        type="button"
                    >
                        Rozpocznij pobieranie
                    </button>
                </div>

            </div>
        `;

        document.body.appendChild(modal);

        modal
            .querySelector("#nas-file-picker-close")
            .addEventListener("click", closeFilePicker);

        modal
            .querySelector("#nas-files-all")
            .addEventListener("click", () => {
                setAllFiles(true);
            });

        modal
            .querySelector("#nas-files-none")
            .addEventListener("click", () => {
                setAllFiles(false);
            });

        modal
            .querySelector("#nas-files-smart")
            .addEventListener("click", () => {
                applyRecommendedSelection();
            });

        modal
            .querySelector("#nas-file-picker-start")
            .addEventListener("click", startPreparedTorrent);

        modal.addEventListener("click", event => {
            if (event.target === modal) {
                closeFilePicker();
            }
        });
    }

    function openFilePicker(data) {
        createFilePicker();

        preparedTorrent = data;

        const modal =
            document.querySelector("#nas-file-picker");

        const title =
            document.querySelector("#nas-file-picker-torrent");

        const list =
            document.querySelector("#nas-file-picker-list");

        const message =
            document.querySelector("#nas-file-picker-message");

        title.textContent =
            `${data.name || "Torrent"} → ${data.libraryName || ""}`;

        message.textContent = "";

        list.innerHTML = "";

        for (const file of data.files || []) {
            const row = document.createElement("label");

            row.className = "nas-file-picker-row";

            row.dataset.index = String(file.index);
            row.dataset.defaultSelected =
                file.selected ? "1" : "0";
            row.dataset.size = String(file.size || 0);

            row.innerHTML = `
                <div class="nas-file-checkbox-wrap">
                    <input
                        type="checkbox"
                        class="nas-file-checkbox"
                        value="${file.index}"
                        ${file.selected ? "checked" : ""}
                    >

                    <span class="nas-file-checkmark"></span>
                </div>

                <div class="nas-file-info">
                    <div class="nas-file-name">
                        ${escapeFileHtml(file.name)}
                    </div>

                    <div class="nas-file-meta">
                        ${formatFileSize(file.size || 0)}
                    </div>
                </div>
            `;

            const checkbox =
                row.querySelector(".nas-file-checkbox");

            checkbox.addEventListener(
                "change",
                updateFileSummary
            );

            list.appendChild(row);
        }

        modal.classList.add("open");

        updateFileSummary();
    }

    function closeFilePicker() {
        const modal =
            document.querySelector("#nas-file-picker");

        if (modal) {
            modal.classList.remove("open");
        }
    }

    function getFileRows() {
        return [
            ...document.querySelectorAll(
                "#nas-file-picker-list .nas-file-picker-row"
            )
        ];
    }

    function setAllFiles(checked) {
        for (const row of getFileRows()) {
            const checkbox =
                row.querySelector(".nas-file-checkbox");

            checkbox.checked = checked;
        }

        updateFileSummary();
    }

    function applyRecommendedSelection() {
        for (const row of getFileRows()) {
            const checkbox =
                row.querySelector(".nas-file-checkbox");

            checkbox.checked =
                row.dataset.defaultSelected === "1";
        }

        updateFileSummary();
    }

    function updateFileSummary() {
        const rows = getFileRows();

        let selectedCount = 0;
        let selectedSize = 0;

        for (const row of rows) {
            const checkbox =
                row.querySelector(".nas-file-checkbox");

            if (checkbox.checked) {
                selectedCount++;
                selectedSize += Number(
                    row.dataset.size || 0
                );
            }
        }

        const summary =
            document.querySelector("#nas-files-summary");

        if (summary) {
            summary.textContent =
                `${selectedCount} / ${rows.length} plików • ` +
                formatFileSize(selectedSize);
        }

        const start =
            document.querySelector("#nas-file-picker-start");

        if (start) {
            start.disabled = selectedCount === 0;
        }
    }

    async function startPreparedTorrent() {
        if (!preparedTorrent?.hash) return;

        const selected = getFileRows()
            .filter(row => {
                return row.querySelector(
                    ".nas-file-checkbox"
                ).checked;
            })
            .map(row => Number(row.dataset.index));

        if (!selected.length) return;

        const button =
            document.querySelector("#nas-file-picker-start");

        const message =
            document.querySelector("#nas-file-picker-message");

        button.disabled = true;
        button.textContent = "Uruchamianie…";

        message.textContent = "";

        try {
            const response = await fetch(
                `${API}/api/qbittorrent/start`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify({
                        hash: preparedTorrent.hash,
                        selected
                    })
                }
            );

            const data = await response.json();

            if (!response.ok || !data.ok) {
                throw new Error(
                    data.error ||
                    "Nie udało się uruchomić pobierania"
                );
            }

            message.textContent =
                `✓ Pobieranie rozpoczęte — ` +
                `${data.selected} plików`;

            button.textContent = "Uruchomiono ✓";

            setTimeout(() => {
                closeFilePicker();
                preparedTorrent = null;
            }, 900);

        } catch (error) {
            message.textContent =
                `✕ ${error.message}`;

            button.disabled = false;
            button.textContent =
                "Rozpocznij pobieranie";
        }
    }

    /*
     * Existing qBittorrent panel calls fetch() directly.
     * Intercept only successful /api/qbittorrent/add responses.
     *
     * The response is cloned, so the existing panel can still
     * consume its own response normally.
     */
    const originalFetch = window.fetch.bind(window);

    // Legacy picker interceptor disabled; Torrent V5 owns this flow.
    const legacyFilePickerInterceptor = async (...args) => {
        const response = await originalFetch(...args);

        try {
            const target =
                typeof args[0] === "string"
                    ? args[0]
                    : args[0]?.url || "";

            if (
                target.includes("/api/qbittorrent/add") &&
                response.ok
            ) {
                const clone = response.clone();
                const data = await clone.json();

                if (
                    data?.ok &&
                    data?.prepared &&
                    data?.hash &&
                    Array.isArray(data?.files)
                ) {
                    setTimeout(() => {
                        openFilePicker(data);
                    }, 50);
                }
            }
        } catch (error) {
            console.error(
                "qBittorrent file picker:",
                error
            );
        }

        return response;
    };

    createFilePicker();

    console.log(
        "NAS qBittorrent file picker loaded"
    );
})();


/* ============================================================
   AURORA MEDIA HUB V2
   Replaces the visible qBittorrent panel with:
   Quick Add + Recent Activity.
   The old qBittorrent panel remains hidden as the compatibility
   engine for its existing library modal / file picker flow.
   ============================================================ */

(() => {
    const API = "http://100.127.67.28:8090";
    let activityTimer = null;
    let qbtMirrorTimer = null;

    function esc(value) {
        return String(value ?? "")
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function formatBytesV2(bytes) {
        let value = Number(bytes || 0);
        if (!Number.isFinite(value) || value <= 0) return "0 B";
        const units = ["B", "KB", "MB", "GB", "TB"];
        const index = Math.min(units.length - 1, Math.floor(Math.log(value) / Math.log(1024)));
        const amount = value / (1024 ** index);
        return `${amount.toFixed(index < 2 ? 0 : 1)} ${units[index]}`;
    }

    function createHub() {
        if (document.querySelector("#nas-media-hub-v2")) return true;

        const services = document.querySelector("#nas-dashboard .nas-services-panel");
        if (!services) return false;

        const hub = document.createElement("section");
        hub.id = "nas-media-hub-v2";
        hub.className = "nas-media-hub-v2";

        hub.innerHTML = `
            <div class="nas-media-add-panel">
                <div class="nas-media-v2-heading">
                    <div>
                        <span class="nas-eyebrow">DODAJ MEDIA</span>
                        <h2>Szybkie dodawanie</h2>
                    </div>
                    <span class="nas-media-v2-chevron">›</span>
                </div>

                <div class="nas-media-quick-grid">
                    <div class="nas-media-quick-slot movie">
                        <button type="button" class="nas-media-quick-card movie" id="nas-v2-movie">
                            <span class="nas-media-quick-icon">▣</span><strong>Film lokalny</strong><small>Dodaj film z komputera</small><span class="nas-media-card-arrow">→</span>
                        </button>
                        <div class="nas-card-transfers" id="nas-movie-transfers"></div>
                    </div>

                    <div class="nas-media-quick-slot series">
                        <button type="button" class="nas-media-quick-card series" id="nas-v2-series">
                            <span class="nas-media-quick-icon">▤</span><strong>Serial lokalny</strong><small>Dodaj odcinki z folderu lub plików</small><span class="nas-media-card-arrow">→</span>
                        </button>
                        <div class="nas-card-transfers" id="nas-series-transfers"></div>
                    </div>

                    <div class="nas-media-quick-slot torrent">
                        <button type="button" class="nas-media-quick-card torrent" id="nas-v2-torrent">
                            <span class="nas-media-quick-icon">↓</span><strong>Torrent</strong><small>Wklej magnet i wybierz bibliotekę</small><span class="nas-media-card-arrow">→</span>
                        </button>
                        <div class="nas-card-transfers" id="nas-torrent-transfers"></div>
                    </div>
                </div>

                <div class="nas-active-transfer-v2" id="nas-active-transfer-v2"></div>
            </div>

            <div class="nas-activity-panel">
                <div class="nas-activity-v2-heading">
                    <div>
                        <span class="nas-eyebrow">OSTATNIA AKTYWNOŚĆ</span>
                        <h2>Ostatnia aktywność</h2>
                    </div>
                    <button type="button" class="nas-activity-more">Najnowsze</button>
                </div>

                <div class="nas-activity-list-v2" id="nas-activity-list-v2">
                    <div class="nas-activity-empty-v2">Ładowanie aktywności…</div>
                </div>
            </div>
        `;

        services.insertAdjacentElement("afterend", hub);
        createTorrentModal();
        wireHubActions();
        return true;
    }

    function createTorrentModal() {
        if (document.querySelector("#nas-torrent-quick-modal")) return;

        const modal = document.createElement("div");
        modal.id = "nas-torrent-quick-modal";
        modal.className = "nas-torrent-quick-modal";
        modal.innerHTML = `
            <div class="nas-torrent-quick-dialog">
                <div class="nas-torrent-quick-top">
                    <div>
                        <span class="nas-eyebrow">TORRENT</span>
                        <h2>Dodaj pobieranie</h2>
                    </div>
                    <button type="button" class="nas-torrent-quick-close" id="nas-torrent-quick-close">×</button>
                </div>

                <div class="nas-torrent-quick-input">
                    <input id="nas-v2-magnet" type="text" placeholder="Wklej link magnet…" autocomplete="off" spellcheck="false">
                    <button id="nas-v2-magnet-go" type="button">Dalej →</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);

        modal.querySelector("#nas-torrent-quick-close").addEventListener("click", closeTorrentModal);
        modal.addEventListener("click", e => {
            if (e.target === modal) closeTorrentModal();
        });
        modal.querySelector("#nas-v2-magnet-go").addEventListener("click", submitV2Magnet);
        modal.querySelector("#nas-v2-magnet").addEventListener("keydown", e => {
            if (e.key === "Enter") {
                e.preventDefault();
                submitV2Magnet();
            }
        });
    }

    function openTorrentModal() {
        const modal = document.querySelector("#nas-torrent-quick-modal");
        const input = document.querySelector("#nas-v2-magnet");
        modal?.classList.add("open");
        setTimeout(() => input?.focus(), 50);
    }

    function closeTorrentModal() {
        document.querySelector("#nas-torrent-quick-modal")?.classList.remove("open");
    }

    function submitV2Magnet() {
        const source = document.querySelector("#nas-v2-magnet");
        const magnet = source?.value.trim() || "";

        if (!magnet.toLowerCase().startsWith("magnet:?")) {
            source?.focus();
            return;
        }

        const oldInput = document.querySelector("#nas-magnet-input");
        const oldButton = document.querySelector("#nas-magnet-submit");

        if (!oldInput || !oldButton) return;

        oldInput.value = magnet;
        closeTorrentModal();

        // Existing qBittorrent code opens the existing library picker.
        oldButton.click();
        source.value = "";
    }

    function wireHubActions() {
        document.querySelector("#nas-v2-torrent")?.addEventListener("click", openTorrentModal);
        document.querySelector("#nas-v2-series")?.addEventListener("click", () => {
            window.dispatchEvent(new CustomEvent("nas:local-media", {detail: {type: "series"}}));
        });
        document.querySelector("#nas-v2-movie")?.addEventListener("click", () => {
            window.dispatchEvent(new CustomEvent("nas:local-media", {detail: {type: "movie"}}));
        });
    }

    function activityIcon(event) {
        const raw = `${event.type || ""} ${event.kind || ""} ${event.title || ""}`.toLowerCase();
        if (raw.includes("episode") || raw.includes("odcinek")) return ["episode", "▣"];
        if (raw.includes("movie") || raw.includes("film")) return ["movie", "▦"];
        if (raw.includes("torrent") || raw.includes("download") || raw.includes("pobier")) return ["download", "↓"];
        return ["generic", "•"];
    }

    function activityTitle(event) {
        return event.label || event.action || event.title || "Aktywność NAS";
    }

    function activitySubtitle(event) {
        return event.subtitle || event.name || event.item || event.detail || "";
    }

    function relativeTime(event) {
        const value = event.createdAt || event.created_at || event.timestamp || event.time;
        if (!value) return "";

        let numeric = Number(value);
        const normalized = Number.isFinite(numeric) && numeric > 0 && numeric < 100000000000
            ? numeric * 1000
            : value;
        const date = new Date(normalized);
        if (Number.isNaN(date.getTime())) return "";

        const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
        if (seconds < 60) return "teraz";
        if (seconds < 3600) return `${Math.floor(seconds / 60)} min temu`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)} godz. temu`;
        return `${Math.floor(seconds / 86400)} d temu`;
    }

    function normalizeActivityPayload(data) {
        if (Array.isArray(data)) return data;
        if (Array.isArray(data.events)) return data.events;
        if (Array.isArray(data.activity)) return data.activity;
        if (Array.isArray(data.items)) return data.items;
        return [];
    }

    async function loadActivityV2() {
        const list = document.querySelector("#nas-activity-list-v2");
        if (!list) return;

        try {
            const response = await fetch(`${API}/api/activity`, {cache: "no-store"});
            if (!response.ok) throw new Error(`HTTP ${response.status}`);
            const data = await response.json();
            const events = normalizeActivityPayload(data).slice(0, 5);

            if (!events.length) {
                list.innerHTML = `<div class="nas-activity-empty-v2">Brak zapisanej aktywności.<br>Nowe zdarzenia pojawią się tutaj automatycznie.</div>`;
                return;
            }

            list.innerHTML = events.map(event => {
                const [kind, icon] = activityIcon(event);
                return `
                    <div class="nas-activity-item-v2">
                        <span class="nas-activity-icon-v2 ${kind}">${icon}</span>
                        <div class="nas-activity-copy-v2">
                            <strong>${esc(activityTitle(event))}</strong>
                            <small>${esc(activitySubtitle(event))}</small>
                        </div>
                        <span class="nas-activity-time-v2">${esc(relativeTime(event))}</span>
                    </div>
                `;
            }).join("");
        } catch (error) {
            list.innerHTML = `<div class="nas-activity-empty-v2">Nie udało się pobrać aktywności.</div>`;
        }
    }

    async function mirrorQbtV2() {
        const box = document.querySelector("#nas-torrent-transfers");
        if (!box) return;
        try {
            const response = await fetch(`${API}/api/qbittorrent`, {cache: "no-store"});
            if (!response.ok) throw new Error();
            const data = await response.json();
            const torrents = (Array.isArray(data.torrents) ? data.torrents : []).filter(t => {
                const state=String(t.state||"").toLowerCase(), progress=Number(t.progress||0);
                return progress < 100 && !["error","missingfiles"].includes(state);
            });
            box.innerHTML=torrents.map(t=>{
                const pct=Math.max(0,Math.min(100,Number(t.progress||0)));
                return `<div class="nas-card-transfer"><div class="nas-card-transfer-line"><strong>${esc(t.name||"Torrent")}</strong><b>${pct.toFixed(1)}%</b></div><div class="nas-card-transfer-bar"><i style="width:${pct}%"></i></div><small>↓ ${formatBytesV2(t.downloadSpeed||0)}/s • ${formatBytesV2(t.downloaded||0)} / ${formatBytesV2(t.size||0)}</small></div>`;
            }).join("");
            box.classList.toggle("visible", torrents.length>0);
        } catch (error) {
            console.error("qBittorrent transfer mirror error:", error);
            box.classList.remove("visible");
            box.innerHTML="";
        }
    }

    function initHubV2() {
        if (!createHub()) {
            setTimeout(initHubV2, 120);
            return;
        }

        loadActivityV2();
        mirrorQbtV2();

        clearInterval(activityTimer);
        clearInterval(qbtMirrorTimer);
        activityTimer = setInterval(loadActivityV2, 30000);
        qbtMirrorTimer = setInterval(mirrorQbtV2, 3000);
        window.addEventListener("nas:qbt-started", mirrorQbtV2);
    }

    if (document.readyState === "loading") {
        document.addEventListener("DOMContentLoaded", initHubV2);
    } else {
        initHubV2();
    }

    console.log("Aurora Media Hub V2 loaded");
})();


/* ============================================================
   AURORA LOCAL MEDIA V4
   Inline workspace + searchable NAS titles + background queue.
   ============================================================ */
(() => {
    const API = "http://100.127.67.28:8090";
    const CHUNK_SIZE = 8 * 1024 * 1024;

    const wizard = { type: null, files: [], plan: null, setup: null };
    const transfer = { jobs: [], active: null, running: false, completed: [] };

    const esc = v => String(v ?? "")
        .replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;")
        .replaceAll('"',"&quot;").replaceAll("'","&#039;");

    function fmtBytes(bytes) {
        let n = Number(bytes || 0);
        if (!n) return "0 B";
        const u = ["B","KB","MB","GB","TB"];
        const i = Math.min(u.length - 1, Math.floor(Math.log(n) / Math.log(1024)));
        return `${(n / 1024 ** i).toFixed(i < 2 ? 0 : 1)} ${u[i]}`;
    }
    function fmtSpeed(bps) { return bps > 0 ? `${fmtBytes(bps)}/s` : "—"; }
    function fmtEta(sec) {
        if (!Number.isFinite(sec) || sec <= 0) return "—";
        if (sec < 60) return `${Math.ceil(sec)} s`;
        const m = Math.ceil(sec / 60);
        return m < 60 ? `${m} min` : `${Math.floor(m/60)} h ${m%60} min`;
    }
    async function apiJson(url, options={}) {
        const r = await fetch(url, options);
        const d = await r.json().catch(() => ({}));
        if (!r.ok || d.ok === false) throw new Error(d.error || `HTTP ${r.status}`);
        return d;
    }

    function main() { return document.querySelector("#nas-dashboard .nas-main"); }
    function hub() { return document.querySelector("#nas-media-hub-v2"); }

    function ensureWorkspace() {
        let el = document.querySelector("#nas-media-workspace-v4");
        if (el) return el;
        el = document.createElement("section");
        el.id = "nas-media-workspace-v4";
        el.className = "nas-media-workspace-v4";
        main()?.appendChild(el);
        return el;
    }
    function setSubpage(on) {
        document.querySelector("#nas-dashboard")?.classList.toggle("nas-v4-subpage", !!on);
        ensureWorkspace().classList.toggle("open", !!on);
    }
    function goHome() {
        setSubpage(false);
        ensureWorkspace().innerHTML = "";
        hub()?.scrollIntoView({behavior:"smooth", block:"center"});
    }
    function stepbar(step) {
        const names = ["Pliki","Poczekalnia","Kolejka"];
        return `<div class="nas-v4-stepbar">${names.map((n,i)=>`
            <span class="${i+1===step?"active":i+1<step?"done":""}"><b>${i+1}</b>${n}</span>
            ${i<2?`<i class="${i+1<step?"done":""}"></i>`:""}`).join("")}</div>`;
    }
    function header(title, subtitle) {
        return `<div class="nas-v4-head">
          <div><span class="nas-eyebrow">DODAJ MEDIA</span><h2>${esc(title)}</h2><p>${esc(subtitle)}</p></div>
          <button type="button" class="nas-v4-close" id="nas-v4-close" title="Wróć do dashboardu">×</button>
        </div>`;
    }

    function openWizard(type) {
        wizard.type = type === "movie" ? "movie" : "series";
        wizard.files = []; wizard.plan = null; wizard.setup = null;
        renderSetup();
    }

    function renderSetup(saved=null) {
        const movie = wizard.type === "movie";
        const el = ensureWorkspace();
        setSubpage(true);
        el.innerHTML = `
          ${header(movie?"Film lokalny":"Serial lokalny",
            movie?"Wybierz plik, bibliotekę i sprawdź plan przed wysłaniem."
                 :"Wybierz folder lub pliki, ustaw numerację i sprawdź poczekalnię przed wysłaniem.")}
          ${stepbar(1)}
          <div class="nas-v4-card">
            <div class="nas-v4-form ${movie?"movie":""}">
              <div class="nas-v4-field nas-v4-title-field">
                <span>${movie?"Tytuł filmu":"Tytuł serialu"}</span>
                <div class="nas-v4-combo">
                  <input id="nas-v4-title" autocomplete="off" placeholder="${movie?"np. Pacific Rim":"Szukaj na NAS lub wpisz nowy tytuł…"}">
                  <div class="nas-v4-title-menu" id="nas-v4-title-menu"></div>
                </div>
                <small id="nas-v4-title-state">Wpisz nazwę lub wybierz istniejący folder z NAS.</small>
              </div>
              ${movie?`
                <label class="nas-v4-field"><span>Rok <em>opcjonalnie</em></span><input id="nas-v4-year" type="number" min="1888" max="2200" placeholder="2026"></label>
                <label class="nas-v4-field"><span>Biblioteka</span><select id="nas-v4-library"><option value="movies">🎬 Filmy</option><option value="animeMovies">🎌 Anime Filmy</option></select></label>
              `:`
                <label class="nas-v4-field"><span>Biblioteka</span><select id="nas-v4-library"><option value="series">📺 Seriale</option><option value="anime">🎌 Anime</option></select></label>
                <label class="nas-v4-field"><span>Sezon</span><input id="nas-v4-season" type="number" min="0" max="999" value="1"></label>
                <label class="nas-v4-field"><span>Pierwszy odcinek</span><input id="nas-v4-first" type="number" min="0" max="9999" value="1"></label>
                <div id="nas-v6-episode-hint" class="nas-v6-episode-hint"><span>Wybierz istniejący tytuł, aby sprawdzić ostatni odcinek.</span></div>
              `}
            </div>
            <div class="nas-v4-picker">
              <div><strong id="nas-v4-file-summary">Nie wybrano plików</strong><small>${movie?"Wideo i ewentualne napisy":"Możesz wskazać cały folder sezonu albo pojedyncze pliki"}</small></div>
              <div class="nas-v4-picker-actions">${movie?"":`<button id="nas-v4-folder">Wybierz folder</button>`}<button id="nas-v4-files">Wybierz pliki</button></div>
            </div>
            <div id="nas-v4-selected" class="nas-v4-selected"></div>
            <div id="nas-v4-error" class="nas-v4-error"></div>
            <div class="nas-v4-footer"><span></span><button class="primary" id="nas-v4-plan" disabled>Przygotuj poczekalnię →</button></div>
          </div>
          <input id="nas-v4-file-input" type="file" multiple hidden>
          <input id="nas-v4-folder-input" type="file" webkitdirectory directory multiple hidden>`;

        el.querySelector("#nas-v4-close").onclick = goHome;
        el.querySelector("#nas-v4-files").onclick = () => { const x=el.querySelector("#nas-v4-file-input"); x.value=""; x.click(); };
        el.querySelector("#nas-v4-folder")?.addEventListener("click",()=>{const x=el.querySelector("#nas-v4-folder-input");x.value="";x.click();});
        el.querySelector("#nas-v4-file-input").onchange=e=>acceptFiles(e.target.files);
        el.querySelector("#nas-v4-folder-input").onchange=e=>acceptFiles(e.target.files);
        el.querySelector("#nas-v4-plan").onclick=requestPlan;

        const lib=el.querySelector("#nas-v4-library");
        const title=el.querySelector("#nas-v4-title");
        lib.onchange=()=>{ loadTitles(true); refreshEpisodeHint(true); };
        title.onfocus=()=>loadTitles(false);
        title.oninput=()=>{ renderTitleChoices(); refreshEpisodeHint(false); };
        const seasonInput=el.querySelector("#nas-v4-season");
        if(seasonInput) seasonInput.onchange=()=>refreshEpisodeHint(true);
        document.addEventListener("click", closeComboOutside, {once:true});

        if(saved) {
            title.value=saved.title||"";
            lib.value=saved.library||lib.value;
            if(movie) el.querySelector("#nas-v4-year").value=saved.year||"";
            else {el.querySelector("#nas-v4-season").value=saved.season??1;el.querySelector("#nas-v4-first").value=saved.firstEpisode??1;}
        }
        if(wizard.files.length) acceptFiles(wizard.files);
        loadTitles(true);
        if(!movie) refreshEpisodeHint(!saved);
    }

    let titlesCache = [];
    async function loadTitles(force=false) {
        const el=ensureWorkspace(), lib=el.querySelector("#nas-v4-library");
        if(!lib) return;
        const menu=el.querySelector("#nas-v4-title-menu");
        menu.classList.add("open");
        menu.innerHTML=`<div class="nas-v4-combo-note">Ładowanie folderów z NAS…</div>`;
        try {
            const d=await apiJson(`${API}/api/media/titles?library=${encodeURIComponent(lib.value)}`, {cache:"no-store"});
            titlesCache=Array.isArray(d.titles)?d.titles:[];
            renderTitleChoices();
        } catch(e) {
            titlesCache=[];
            menu.innerHTML=`<div class="nas-v4-combo-note error">${esc(e.message)}</div>`;
        }
    }
    function renderTitleChoices() {
        const el=ensureWorkspace(), input=el.querySelector("#nas-v4-title"), menu=el.querySelector("#nas-v4-title-menu");
        if(!input||!menu) return;
        const q=input.value.trim().toLocaleLowerCase("pl");
        const exact=titlesCache.find(x=>x.toLocaleLowerCase("pl")===q);
        const found=titlesCache.filter(x=>!q||x.toLocaleLowerCase("pl").includes(q)).slice(0,12);
        menu.innerHTML = `
          ${found.map(x=>`<button type="button" data-title="${esc(x)}"><span>▤</span><strong>${esc(x)}</strong><small>✓ Istnieje na NAS</small></button>`).join("")}
          ${q&&!exact?`<button type="button" class="create" data-title="${esc(input.value.trim())}"><span>＋</span><strong>Utwórz nowy: „${esc(input.value.trim())}”</strong><small>Nowy folder</small></button>`:""}
          ${!found.length&&!q?`<div class="nas-v4-combo-note">Brak folderów w tej bibliotece.</div>`:""}`;
        menu.classList.add("open");
        menu.querySelectorAll("[data-title]").forEach(b=>b.onclick=()=>{
            input.value=b.dataset.title;
            menu.classList.remove("open");
            updateTitleState();
            refreshEpisodeHint(true);
        });
        updateTitleState();
    }
    function updateTitleState() {
        const el=ensureWorkspace(), input=el.querySelector("#nas-v4-title"), state=el.querySelector("#nas-v4-title-state");
        if(!input||!state)return;
        const exact=titlesCache.some(x=>x.toLocaleLowerCase("pl")===input.value.trim().toLocaleLowerCase("pl"));
        state.textContent=input.value.trim()?(exact?"✓ Istniejący folder na NAS":"＋ Zostanie utworzony nowy folder"):"Wpisz nazwę lub wybierz istniejący folder z NAS.";
        state.className=exact?"existing":input.value.trim()?"new":"";
    }
    function closeComboOutside(e) {
        if(!e.target.closest?.(".nas-v4-combo")) document.querySelector("#nas-v4-title-menu")?.classList.remove("open");
    }


    let episodeLookupTimer = null;
    async function refreshEpisodeHint(autoSet=true) {
        if (wizard.type !== "series") return;
        const el=ensureWorkspace();
        const title=el.querySelector("#nas-v4-title")?.value.trim();
        const library=el.querySelector("#nas-v4-library")?.value;
        const season=Number(el.querySelector("#nas-v4-season")?.value || 1);
        const first=el.querySelector("#nas-v4-first");
        const hint=el.querySelector("#nas-v6-episode-hint");
        if(!hint || !first) return;

        clearTimeout(episodeLookupTimer);
        if(!title || !["series","anime"].includes(library)){
            hint.innerHTML="<span>Wybierz istniejący tytuł, aby sprawdzić ostatni odcinek.</span>";
            return;
        }

        episodeLookupTimer=setTimeout(async()=>{
            hint.innerHTML="<span>Sprawdzam bibliotekę NAS…</span>";
            try{
                const d=await apiJson(`${API}/api/media/last-episode?library=${encodeURIComponent(library)}&title=${encodeURIComponent(title)}&season=${encodeURIComponent(season)}`,{cache:"no-store"});
                if(!d.exists){
                    hint.innerHTML=`<span class="new">＋ Nowy tytuł • proponuję <strong>S${String(season).padStart(2,"0")}E01</strong></span>`;
                    if(autoSet) first.value=1;
                    return;
                }
                if(d.lastEpisode==null){
                    hint.innerHTML=`<span class="existing">✓ Tytuł istnieje • brak rozpoznanych odcinków sezonu ${season} • proponuję <strong>E01</strong></span>`;
                    if(autoSet) first.value=1;
                    return;
                }
                const last=`S${String(season).padStart(2,"0")}E${String(d.lastEpisode).padStart(2,"0")}`;
                const next=`S${String(season).padStart(2,"0")}E${String(d.nextEpisode).padStart(2,"0")}`;
                hint.innerHTML=`<span class="existing">✓ Ostatni: <strong>${last}</strong></span><span class="next">Następny: <strong>${next}</strong></span>`;
                if(autoSet) first.value=d.nextEpisode;
            }catch(e){
                hint.innerHTML=`<span class="error">Nie udało się sprawdzić ostatniego odcinka.</span>`;
            }
        },180);
    }

    function acceptFiles(list) {
        wizard.files=Array.from(list||[]).sort((a,b)=>(a.webkitRelativePath||a.name).localeCompare((b.webkitRelativePath||b.name),undefined,{numeric:true,sensitivity:"base"}));
        const el=ensureWorkspace(), total=wizard.files.reduce((s,f)=>s+f.size,0);
        el.querySelector("#nas-v4-file-summary").textContent=wizard.files.length?`${wizard.files.length} plików • ${fmtBytes(total)}`:"Nie wybrano plików";
        el.querySelector("#nas-v4-selected").innerHTML=wizard.files.slice(0,8).map(f=>`<span>${esc(f.name)} <small>${fmtBytes(f.size)}</small></span>`).join("")+(wizard.files.length>8?`<span>+ ${wizard.files.length-8} kolejnych</span>`:"");
        el.querySelector("#nas-v4-plan").disabled=!wizard.files.length;
    }
    function setupPayload() {
        const el=ensureWorkspace(), title=el.querySelector("#nas-v4-title").value.trim();
        if(!title) throw new Error("Wybierz lub wpisz tytuł.");
        if(!wizard.files.length) throw new Error("Wybierz pliki.");
        const files=wizard.files.map(f=>({name:f.name,size:f.size}));
        const library=el.querySelector("#nas-v4-library").value;
        if(wizard.type==="movie") return {type:"movie",title,library,year:el.querySelector("#nas-v4-year").value||"",files};
        return {type:"series",title,library,season:Number(el.querySelector("#nas-v4-season").value||1),firstEpisode:Number(el.querySelector("#nas-v4-first").value||1),files};
    }
    async function requestPlan() {
        const el=ensureWorkspace(), err=el.querySelector("#nas-v4-error"), btn=el.querySelector("#nas-v4-plan");
        err.textContent="";
        try { wizard.setup=setupPayload(); } catch(e){err.textContent=e.message;return;}
        btn.disabled=true;btn.textContent="Analizuję…";
        try {
            wizard.plan=await apiJson(`${API}/api/media/plan`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(wizard.setup)});
            renderWaiting();
        } catch(e){err.textContent=e.message;btn.disabled=false;btn.textContent="Przygotuj poczekalnię →";}
    }
    function statusMarkup(item) {
        if(item.status==="conflict")return`<span class="nas-v4-status bad">⛔ Konflikt</span>`;
        if(item.status==="check")return`<span class="nas-v4-status warn">⚠ Sprawdź</span>`;
        if(item.status==="ignored")return`<span class="nas-v4-status mute">— Pomijam</span>`;
        return`<span class="nas-v4-status ok">✓ OK</span>`;
    }
    function renderWaiting() {
        const p=wizard.plan, el=ensureWorkspace();
        const jobs=p.items.filter(x=>x.targetName&&(x.kind==="video"||x.kind==="subtitle"));
        const total=jobs.reduce((s,x)=>s+Number(x.size||0),0);
        el.innerHTML=`
          ${header(p.mediaType==="movie"?"Film lokalny":"Serial lokalny","Sprawdź plan. Po dodaniu do kolejki możesz od razu wrócić do dashboardu.")}
          ${stepbar(2)}
          <div class="nas-v4-card">
            <div class="nas-v4-summary">
              <div><span>Biblioteka</span><strong>${esc(p.libraryName)}</strong></div><div><span>Pliki</span><strong>${jobs.length}</strong></div>
              <div><span>Łącznie</span><strong>${fmtBytes(total)}</strong></div><div><span>Stan</span><strong class="${p.ready?"good":"attention"}">${p.ready?"Gotowe":"Wymaga uwagi"}</strong></div>
            </div>
            <div class="nas-v4-table-wrap"><table class="nas-v4-table"><thead><tr><th>Oryginał</th>${p.mediaType==="series"?"<th>Sezon</th><th>Odcinek</th>":""}<th>Nazwa docelowa</th><th>Status</th></tr></thead><tbody>
              ${p.items.map((item,i)=>`<tr class="${esc(item.status)}"><td><strong>${esc(item.originalName)}</strong><small>${esc(item.kind)} • ${fmtBytes(item.size)}</small></td>
              ${p.mediaType==="series"?`<td>${item.season??"—"}</td><td>${item.episode??"—"}</td>`:""}
              <td>${item.targetName?`<input class="nas-v4-target" data-target="${i}" value="${esc(item.targetName)}">`:`<span class="muted">${esc(item.reason||"—")}</span>`}</td><td>${statusMarkup(item)}</td></tr>`).join("")}
            </tbody></table></div>
            <div class="nas-v4-tree"><span class="nas-eyebrow">PODGLĄD NAS</span><strong>▾ ${esc(p.libraryName)}</strong>${(p.tree?.paths||[]).slice(0,18).map(x=>`<small>└─ ${esc(x)}</small>`).join("")}</div>
            <div class="nas-v4-error">${p.ready?"":"Usuń konflikty lub pozycje wymagające sprawdzenia."}</div>
            <div class="nas-v4-footer"><button id="nas-v4-prev">← Wróć</button><button class="primary" id="nas-v4-enqueue" ${p.ready?"":"disabled"}>Wyślij w tle • ${fmtBytes(total)} →</button></div>
          </div>`;
        el.querySelector("#nas-v4-close").onclick=goHome;
        el.querySelector("#nas-v4-prev").onclick=()=>renderSetup(wizard.setup);
        el.querySelectorAll("[data-target]").forEach(inp=>inp.oninput=e=>wizard.plan.items[Number(e.target.dataset.target)].targetName=e.target.value.trim());
        el.querySelector("#nas-v4-enqueue").onclick=enqueuePlan;
    }

    function browserFileFor(item) { return wizard.files.find(f=>f.name===item.originalName)||null; }
    function folderFor(item) {
        const path=String(item.targetPath||"").replaceAll("\\","/");
        const marker=`/nas/${wizard.plan.libraryName}/`;
        if(!path.startsWith(marker)) throw new Error(`Nie rozpoznaję ścieżki: ${path}`);
        const parts=path.slice(marker.length).split("/");parts.pop();return parts.join("/");
    }
    function enqueuePlan() {
        const jobs=[];
        for(const item of wizard.plan.items) {
            if(!item.targetName || !["video","subtitle"].includes(item.kind)) continue;
            const file=browserFileFor(item);
            if(!file) { ensureWorkspace().querySelector(".nas-v4-error").textContent=`Nie mam dostępu do pliku ${item.originalName}.`;return; }
            jobs.push({
                id:`local-${Date.now()}-${jobs.length}`, file, item,
                library:wizard.plan.library, libraryName:wizard.plan.libraryName, mediaType:wizard.type,
                folder:folderFor(item), targetName:item.targetName,
                status:"queued", sent:0, speed:0, eta:null, uploadId:null, error:null
            });
        }
        transfer.jobs.push(...jobs);
        ensureTransferPanel();
        renderTransferPanel();
        goHome();
        runQueue();
    }

    function ensureTransferPanel() {
        return document.querySelector("#nas-media-hub-v2");
    }
    function renderTransferPanel() {
        const all=[...(transfer.active?[transfer.active]:[]),...transfer.jobs.filter(x=>x.status==="queued")];
        for(const type of ["movie","series"]){
            const box=document.querySelector(type==="movie"?"#nas-movie-transfers":"#nas-series-transfers");
            if(!box)continue;
            const jobs=all.filter(x=>x.mediaType===type);
            box.innerHTML=jobs.map(job=>{
                const active=job.status==="uploading", pct=job.file.size?Math.min(100,job.sent/job.file.size*100):0;
                return `<div class="nas-card-transfer"><div class="nas-card-transfer-line"><strong>${active?"↑ ":"◷ "}${esc(job.targetName)}</strong><b>${active?pct.toFixed(0)+"%":"kolejka"}</b></div>${active?`<div class="nas-card-transfer-bar"><i style="width:${pct}%"></i></div><small>${fmtBytes(job.sent)} / ${fmtBytes(job.file.size)} • ${fmtSpeed(job.speed)}</small>`:`<small>${fmtBytes(job.file.size)}</small>`}</div>`;
            }).join("");
            box.classList.toggle("visible",jobs.length>0);
        }
    }

    async function sendChunk(job, blob, offset) {
        const r=await fetch(`${API}/api/media/upload/${encodeURIComponent(job.uploadId)}/chunk`,{method:"POST",headers:{"Content-Type":"application/octet-stream","X-Upload-Offset":String(offset)},body:blob});
        const d=await r.json().catch(()=>({}));
        if(!r.ok||d.ok===false)throw new Error(d.error||`HTTP ${r.status}`);
        return d;
    }
    async function uploadJob(job) {
        const init=await apiJson(`${API}/api/media/upload/init`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
            library:job.library,folder:job.folder,originalName:job.file.name,targetName:job.targetName,size:job.file.size
        })});
        job.uploadId=init.uploadId;
        let offset=Number(init.received||0), lastT=performance.now(), lastB=offset;
        while(offset<job.file.size) {
            const end=Math.min(offset+CHUNK_SIZE,job.file.size), blob=job.file.slice(offset,end);
            let ok=false, error;
            for(let attempt=0;attempt<3&&!ok;attempt++){
                try {
                    const d=await sendChunk(job,blob,offset);
                    offset=Number(d.received??end);ok=true;
                } catch(e) {
                    error=e;
                    try {
                        const s=await apiJson(`${API}/api/media/upload/${encodeURIComponent(job.uploadId)}`,{cache:"no-store"});
                        offset=Number(s.received||offset);
                        if(offset>=end)ok=true;
                    } catch {}
                    if(!ok) await new Promise(r=>setTimeout(r,700*(attempt+1)));
                }
            }
            if(!ok)throw error||new Error("Nie udało się wysłać fragmentu pliku");
            const now=performance.now(), dt=(now-lastT)/1000;
            if(dt>=0.35){job.speed=Math.max(0,(offset-lastB)/dt);lastT=now;lastB=offset;}
            job.sent=offset;job.eta=job.speed>0?(job.file.size-offset)/job.speed:null;renderTransferPanel();
        }
        await apiJson(`${API}/api/media/upload/${encodeURIComponent(job.uploadId)}/finalize`,{method:"POST"});
        job.sent=job.file.size;job.status="done";
    }
    async function runQueue() {
        if(transfer.running)return;
        transfer.running=true;
        try {
            while(true) {
                const job=transfer.jobs.find(x=>x.status==="queued");
                if(!job)break;
                transfer.active=job;job.status="uploading";renderTransferPanel();
                try { await uploadJob(job); }
                catch(e) {
                    job.status="error";job.error=e.message;
                    if(job.uploadId) fetch(`${API}/api/media/upload/${encodeURIComponent(job.uploadId)}`,{method:"DELETE"}).catch(()=>{});
                }
                transfer.completed.push(job);
                transfer.jobs=transfer.jobs.filter(x=>x!==job);
                transfer.active=null;renderTransferPanel();
            }
        } finally { transfer.running=false;transfer.active=null;renderTransferPanel(); }
    }

    window.addEventListener("nas:local-media",e=>openWizard(e.detail?.type==="movie"?"movie":"series"));
    const boot=setInterval(()=>{if(document.querySelector("#nas-media-hub-v2")){clearInterval(boot);ensureWorkspace();ensureTransferPanel();}},250);
    console.log("Aurora Local Media V4 loaded");
})();


/* ============================================================
   AURORA TORRENT V5 — Magnet + .torrent
   ============================================================ */
(() => {
  const API="http://100.127.67.28:8090";
  const state={kind:"magnet",magnet:"",file:null,library:"downloads",meta:null,libraries:[]};
  const esc=v=>String(v??"").replaceAll("&","&amp;").replaceAll("<","&lt;").replaceAll(">","&gt;").replaceAll('"',"&quot;");
  const fmt=n=>{n=Number(n||0);if(!n)return"0 B";const u=["B","KB","MB","GB","TB"],i=Math.min(4,Math.floor(Math.log(n)/Math.log(1024)));return`${(n/1024**i).toFixed(i<2?0:1)} ${u[i]}`};
  async function req(url,opt={}){const r=await fetch(url,opt),d=await r.json().catch(()=>({}));if(!r.ok||d.ok===false)throw new Error(d.error||`HTTP ${r.status}`);return d}
  function ws(){let e=document.querySelector("#nas-torrent-v5");if(e)return e;e=document.createElement("section");e.id="nas-torrent-v5";e.className="nas-media-workspace-v4";document.querySelector("#nas-dashboard .nas-main")?.appendChild(e);return e}
  function show(){document.querySelector("#nas-dashboard")?.classList.add("nas-v4-subpage");ws().classList.add("open")}
  function close(){document.querySelector("#nas-dashboard")?.classList.remove("nas-v4-subpage");ws().classList.remove("open");ws().innerHTML="";document.querySelector("#nas-media-hub-v2")?.scrollIntoView({behavior:"smooth",block:"center"})}
  const head=()=>`<div class="nas-v4-head"><div><span class="nas-eyebrow">DODAJ MEDIA</span><h2>Torrent</h2><p>Magnet albo lokalny plik .torrent — potem wybór plików i biblioteki.</p></div><button class="nas-v4-close" id="tv5-close">×</button></div>`;
  const steps=n=>`<div class="nas-v4-stepbar"><span class="${n===1?"active":"done"}"><b>1</b>Źródło</span><i class="${n>1?"done":""}"></i><span class="${n===2?"active":n>2?"done":""}"><b>2</b>Pliki</span><i></i><span class="${n===3?"active":""}"><b>3</b>Pobieranie</span></div>`;
  async function open(){
    Object.assign(state,{kind:"magnet",magnet:"",file:null,library:"downloads",meta:null,libraries:[]});
    show();
    try{
      const data=await req(`${API}/api/qbittorrent/libraries`,{cache:"no-store"});
      state.libraries=Array.isArray(data.libraries)?data.libraries:[];
      if(state.libraries.length&&!state.libraries.some(x=>x.id===state.library))state.library=state.libraries[0].id;
    }catch(x){state.libraries=[]}
    source();
  }
  function source(){
    const e=ws();
    const libraryOptions=(state.libraries.length?state.libraries:[
      {id:"movies",name:"Filmy"},{id:"series",name:"Seriale"},{id:"anime",name:"Anime"},{id:"animeMovies",name:"Anime Filmy"},{id:"downloads",name:"Downloads"}
    ]).map(x=>`<option value="${esc(x.id)}">${esc(x.name)}</option>`).join("");
    e.innerHTML=`${head()}${steps(1)}<div class="nas-v4-card">
      <div class="tv5-tabs"><button data-tv5="magnet" class="${state.kind=="magnet"?"active":""}">🔗 Magnet</button><button data-tv5="file" class="${state.kind=="file"?"active":""}">📄 Plik .torrent</button></div>
      ${state.kind=="magnet"?`<label class="nas-v4-field"><span>Magnet link</span><textarea id="tv5-magnet" placeholder="magnet:?xt=urn:btih:...">${esc(state.magnet)}</textarea></label>`:
      `<div class="tv5-file"><div><strong>${state.file?esc(state.file.name):"Nie wybrano pliku .torrent"}</strong><small>${state.file?fmt(state.file.size):"Wskaż plik z komputera"}</small></div><button id="tv5-pick">Wybierz .torrent</button><input id="tv5-file" type="file" accept=".torrent,application/x-bittorrent" hidden></div>`}
      <label class="nas-v4-field tv5-lib"><span>Biblioteka docelowa</span><select id="tv5-library">${libraryOptions}</select></label>
      <div id="tv5-error" class="nas-v4-error"></div><div class="nas-v4-footer"><span></span><button class="primary" id="tv5-load">Załaduj metadane →</button></div>
    </div>`;
    e.querySelector("#tv5-close").onclick=close;
    e.querySelectorAll("[data-tv5]").forEach(b=>b.onclick=()=>{state.kind=b.dataset.tv5;source()});
    e.querySelector("#tv5-library").value=state.library;e.querySelector("#tv5-library").onchange=x=>state.library=x.target.value;
    const m=e.querySelector("#tv5-magnet");if(m)m.oninput=x=>state.magnet=x.target.value.trim();
    const pick=e.querySelector("#tv5-pick"),file=e.querySelector("#tv5-file");if(pick)pick.onclick=()=>file.click();if(file)file.onchange=x=>{state.file=x.target.files?.[0]||null;source()};
    e.querySelector("#tv5-load").onclick=load;
  }
  async function load(){
    const e=ws(),err=e.querySelector("#tv5-error"),b=e.querySelector("#tv5-load");err.textContent="";
    if(state.kind==="magnet"&&!state.magnet.startsWith("magnet:?")){err.textContent="Wklej poprawny magnet.";return}
    if(state.kind==="file"&&!state.file){err.textContent="Wybierz plik .torrent.";return}
    b.disabled=true;b.textContent="Ładowanie metadanych…";
    try{
      if(state.kind==="magnet")state.meta=await req(`${API}/api/qbittorrent/add`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({magnet:state.magnet,library:state.library})});
      else{const f=new FormData();f.append("library",state.library);f.append("torrent",state.file,state.file.name);state.meta=await req(`${API}/api/qbittorrent/add-file`,{method:"POST",body:f})}
      files();
    }catch(x){err.textContent=x.message;b.disabled=false;b.textContent="Załaduj metadane →"}
  }
  function files(){
    const e=ws(),m=state.meta,fs=m.files||[];
    e.innerHTML=`${head()}${steps(2)}<div class="nas-v4-card"><div class="tv5-meta"><div><span class="nas-eyebrow">TORRENT</span><h3>${esc(m.name||"Torrent")}</h3><small>${fs.length} plików • ${fmt(fs.reduce((s,x)=>s+Number(x.size||0),0))}</small></div><strong>${esc(m.libraryName||"")}</strong></div>
    <div class="tv5-files">${fs.map((x,i)=>`<label><input type="checkbox" data-tv5-file="${i}" ${x.selected?"checked":""}><span><strong>${esc(x.name)}</strong><small>${fmt(x.size)}</small></span></label>`).join("")}</div>
    <div id="tv5-error" class="nas-v4-error"></div><div class="nas-v4-footer"><button id="tv5-back">← Wróć</button><button class="primary" id="tv5-start">Rozpocznij pobieranie →</button></div></div>`;
    e.querySelector("#tv5-close").onclick=close;e.querySelector("#tv5-back").onclick=source;e.querySelector("#tv5-start").onclick=start;
  }
  async function start(){
    const e=ws(),err=e.querySelector("#tv5-error"),b=e.querySelector("#tv5-start"),sel=[...e.querySelectorAll("[data-tv5-file]:checked")].map(x=>Number(x.dataset.tv5File));
    if(!sel.length){err.textContent="Wybierz przynajmniej jeden plik.";return}
    b.disabled=true;b.textContent="Uruchamiam…";
    try{await req(`${API}/api/qbittorrent/start`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({hash:state.meta.hash,selected:sel})});window.dispatchEvent(new CustomEvent("nas:qbt-started"));close()}
    catch(x){err.textContent=x.message;b.disabled=false;b.textContent="Rozpocznij pobieranie →"}
  }

  // Intercept the existing Torrent quick-add card before legacy modal code.
  document.addEventListener("click",e=>{
    const candidates=[...document.querySelectorAll("#nas-media-hub-v2 button,#nas-media-hub-v2 [role=button],#nas-media-hub-v2 .nas-quick-card,#nas-media-hub-v2 .nas-media-card")];
    const card=e.target.closest?.("button,[role=button],.nas-quick-card,.nas-media-card");
    if(card&&candidates.includes(card)&&/torrent/i.test(card.textContent||"")){e.preventDefault();e.stopImmediatePropagation();open()}
  },true);
})();