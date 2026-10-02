(() => {
    const API = "";
    const WALLPAPER_API = null;

    const serviceUrl = (port) =>
        `${window.location.protocol}//${window.location.hostname}:${port}`;

    const SERVICES = {
        jellyfin: {
            name: "Jellyfin",
            description: "Filmy • Seriale • Anime",
            url: serviceUrl(8096),
            icon: "https://cdn.jsdelivr.net/gh/homarr-labs/dashboard-icons/png/jellyfin.png"
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
                                <strong>LMS</strong>
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
                        LMS Server
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
        const totalServices = Object.keys(SERVICES).length;

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
            `${onlineCount} / ${totalServices} online`;


        const everythingOnline =
            onlineCount === totalServices;


        document.getElementById(
            "global-status"
        ).textContent =
            everythingOnline
                ? "Wszystkie systemy działają"
                : `${onlineCount} z ${totalServices} usług online`;


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
        // Optional personal services are intentionally omitted in distribution builds.
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
        if (!WALLPAPER_API) return;
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

        if (!WALLPAPER_API) {
            wallpaperButton?.remove();
            wallpaperInput?.remove();
            refreshButton.addEventListener("click", loadData);
            return;
        }


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
    const QBT_API = "";

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
    const API = "";

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
    const API = "";
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
            window.dispatchEvent(new CustomEvent("nas:qbt-progress", {detail:data.torrents||[]}));
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
    const API = "";
    const CHUNK_SIZE = 8 * 1024 * 1024;

    const wizard = { type: null, files: [], plan: null, setup: null,
        identification: null, skipIdentify: false, seriesYear: null };
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
        wizard.identification = null; wizard.skipIdentify = false; wizard.seriesYear = null;
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
        lib.onchange=()=>{ wizard.identification=null;wizard.skipIdentify=false;wizard.seriesYear=null;loadTitles(true); refreshEpisodeHint(true); };
        title.onfocus=()=>loadTitles(false);
        title.oninput=()=>{ wizard.identification=null;wizard.skipIdentify=false;wizard.seriesYear=null;renderTitleChoices(); refreshEpisodeHint(false); };
        const seasonInput=el.querySelector("#nas-v4-season");
        if(seasonInput) seasonInput.onchange=()=>refreshEpisodeHint(true);
        document.addEventListener("click", closeComboOutside, {once:true});

        if(saved) {
            wizard.identification=saved.tmdbId?{tmdbId:String(saved.tmdbId),title:saved.title,year:saved.year||null}:null;
            wizard.skipIdentify=!saved.tmdbId;
            wizard.seriesYear=saved.year||null;
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
            wizard.identification=null;
            wizard.skipIdentify=!b.classList.contains("create");
            wizard.seriesYear=null;
            updateTitleState();
            refreshEpisodeHint(true);
            if(b.classList.contains("create")) openIdentification();
        });
        updateTitleState();
    }
    async function openIdentification() {
        const title=ensureWorkspace().querySelector("#nas-v4-title")?.value.trim();
        if(!title)return;
        document.querySelector("#nas-tmdb-overlay")?.remove();
        const overlay=document.createElement("div");
        overlay.id="nas-tmdb-overlay";
        overlay.className="nas-tmdb-overlay";
        overlay.innerHTML=`<div class="nas-tmdb-dialog" role="dialog" aria-modal="true" aria-labelledby="nas-tmdb-heading">
            <div class="nas-tmdb-head"><div><span class="nas-eyebrow">IDENTYFIKACJA MEDIÓW</span>
            <h3 id="nas-tmdb-heading">Wybierz właściwy tytuł</h3><p>${esc(title)} • ${wizard.type==="movie"?"Film":"Serial"}</p></div>
            <button type="button" class="nas-tmdb-close" aria-label="Zamknij">×</button></div>
            <div class="nas-tmdb-results" aria-live="polite"><p>Wyszukuję w metadanych Jellyfin/TMDB…</p></div>
            <div class="nas-tmdb-actions"><button type="button" class="nas-tmdb-skip">Pomiń identyfikację</button></div>
        </div>`;
        document.body.appendChild(overlay);
        const close=()=>overlay.remove();
        overlay.querySelector(".nas-tmdb-close").onclick=close;
        overlay.onclick=e=>{if(e.target===overlay)close();};
        overlay.querySelector(".nas-tmdb-skip").onclick=()=>{
            wizard.identification=null;wizard.skipIdentify=true;wizard.seriesYear=null;
            updateTitleState();close();
        };
        const results=overlay.querySelector(".nas-tmdb-results");
        try {
            const response=await apiJson(`${API}/api/media/identify?type=${encodeURIComponent(wizard.type)}&title=${encodeURIComponent(title)}`,{cache:"no-store"});
            if(!overlay.isConnected)return;
            const matches=Array.isArray(response.results)?response.results:[];
            if(!matches.length){results.innerHTML="<p>Nie znaleziono tytułu z ID TMDB. Możesz zmienić nazwę lub pominąć identyfikację.</p>";return;}
            results.innerHTML=matches.map((item,i)=>`<button type="button" class="nas-tmdb-result" data-result="${i}">
                ${item.poster?`<img src="${esc(item.poster)}" alt="" loading="lazy" referrerpolicy="no-referrer">`:'<span class="nas-tmdb-no-poster">▤</span>'}
                <span><strong>${esc(item.title)}</strong><small>${esc(item.year||"Rok nieznany")} • ${item.type==="movie"?"Film":"Serial"} • TMDB ${esc(item.tmdbId)}</small></span>
                <b>Wybierz →</b></button>`).join("");
            results.querySelectorAll("[data-result]").forEach(button=>button.onclick=()=>{
                const item=matches[Number(button.dataset.result)];
                wizard.identification=item;wizard.skipIdentify=false;wizard.seriesYear=item.year||null;
                const workspace=ensureWorkspace(), input=workspace.querySelector("#nas-v4-title");
                input.value=item.title;
                if(wizard.type==="movie"&&item.year)workspace.querySelector("#nas-v4-year").value=item.year;
                workspace.querySelector("#nas-v4-title-menu")?.classList.remove("open");
                updateTitleState();refreshEpisodeHint(true);close();
            });
        } catch(error) {
            if(overlay.isConnected)results.innerHTML=`<p class="nas-tmdb-error">${esc(error.message)}. Możesz pominąć identyfikację.</p>`;
        }
    }

    function updateTitleState() {
        const el=ensureWorkspace(), input=el.querySelector("#nas-v4-title"), state=el.querySelector("#nas-v4-title-state");
        if(!input||!state)return;
        const exact=titlesCache.some(x=>x.toLocaleLowerCase("pl")===input.value.trim().toLocaleLowerCase("pl"));
        state.textContent=wizard.identification?`✓ TMDB ID: ${wizard.identification.tmdbId} • ${wizard.identification.title}`:
            input.value.trim()?(exact?"✓ Istniejący folder na NAS":"＋ Zostanie utworzony nowy folder"):"Wpisz nazwę lub wybierz istniejący folder z NAS.";
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
        const tmdbId=wizard.identification?.tmdbId||null;
        if(wizard.type==="movie") return {type:"movie",title,library,year:el.querySelector("#nas-v4-year").value||"",tmdbId,files};
        return {type:"series",title,library,year:wizard.seriesYear||"",tmdbId,
            season:Number(el.querySelector("#nas-v4-season").value||1),firstEpisode:Number(el.querySelector("#nas-v4-first").value||1),files};
    }
    async function requestPlan() {
        const el=ensureWorkspace(), err=el.querySelector("#nas-v4-error"), btn=el.querySelector("#nas-v4-plan");
        err.textContent="";
        try { wizard.setup=setupPayload(); } catch(e){err.textContent=e.message;return;}
        const exact=titlesCache.some(x=>x.toLocaleLowerCase("pl")===wizard.setup.title.toLocaleLowerCase("pl"));
        if(!exact&&!wizard.identification&&!wizard.skipIdentify){openIdentification();return;}
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
          ${wizard.identification?`<div class="nas-tmdb-confirm">
              ${wizard.identification.poster?`<img src="${esc(wizard.identification.poster)}" alt="" referrerpolicy="no-referrer">`:""}
              <div><strong>${esc(wizard.identification.title)} (${esc(wizard.identification.year||"—")})</strong>
              <small>✓ Identyfikacja TMDB: ${esc(wizard.identification.tmdbId)} • folder oznaczony dla Jellyfina</small></div>
          </div>`:""}
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
        const marker=`${String(wizard.plan.libraryRoot||"").replaceAll("\\","/").replace(/\/$/,"")}/`;
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
        window.dispatchEvent(new CustomEvent("nas:dashboard-home"));
        runQueue();
    }

    function ensureTransferPanel() {
        return document.querySelector("#nas-media-hub-v2");
    }
    function renderTransferPanel() {
        const all=[...(transfer.active?[transfer.active]:[]),...transfer.jobs.filter(x=>["queued","paused"].includes(x.status)),...transfer.completed.slice(-6).reverse()];
        for(const type of ["movie","series"]){
            const box=document.querySelector(type==="movie"?"#nas-movie-transfers":"#nas-series-transfers");
            if(!box)continue;
            const jobs=all.filter(x=>x.mediaType===type);
            box.innerHTML=jobs.map(job=>{
                const active=job.status==="uploading", done=job.status==="done", failed=job.status==="error";
                const pct=job.file.size?Math.min(100,job.sent/job.file.size*100):0;
                const label=active?`${pct.toFixed(0)}%`:done?"Wysłano ✓":failed?"Błąd":"Kolejka";
                const details=failed?esc(job.error||"Upload nieudany"):
                    active?`${fmtBytes(job.sent)} / ${fmtBytes(job.file.size)} • ${fmtSpeed(job.speed)} • ETA ${fmtEta(job.eta)}`:
                    done?`${fmtBytes(job.file.size)} • gotowe`:fmtBytes(job.file.size);
                return `<div class="nas-card-transfer ${failed?"error":done?"completed":""}"><div class="nas-card-transfer-line"><strong>${active?"↑ ":done?"✓ ":failed?"! ":"◷ "}${esc(job.targetName)}</strong><b>${label}</b></div>${active?`<div class="nas-card-transfer-bar"><i style="width:${pct}%"></i></div>`:""}<small>${details}</small></div>`;
            }).join("");
            box.classList.toggle("visible",jobs.length>0);
        }
        const manager=document.querySelector("#nas-active-transfer-v2");
        if(manager){
            manager.classList.toggle("visible",all.length>0);
            manager.innerHTML=all.length?`<div class="nas-active-transfer-top"><strong>MENEDŻER TRANSFERÓW</strong><span>${transfer.active?"Wysyłanie":"Ostatnie zadania"} • ${transfer.jobs.filter(j=>j.status==="queued").length} w kolejce</span></div>
                ${all.slice(0,7).map(job=>{
                    const active=["uploading","pausing","cancelling"].includes(job.status),done=job.status==="done",bad=job.status==="error",paused=job.status==="paused";
                    const pct=job.file.size?Math.min(100,100*job.sent/job.file.size):0;
                    const label=job.status==="pausing"?"Wstrzymuję":job.status==="cancelling"?"Anuluję":active?pct.toFixed(0)+"%":paused?"Pauza":done?"Wysłano":job.status==="cancelled"?"Anulowano":bad?"Błąd":"W kolejce";
                    const actions=["uploading","queued","paused"].includes(job.status)?`<div class="lms-transfer-actions"><button type="button" data-lms-upload="${paused?"resume":"pause"}" data-job="${job.id}">${paused?"▶ Wznów":"Ⅱ Pauza"}</button><button type="button" class="stop" data-lms-upload="cancel" data-job="${job.id}">■ Zatrzymaj</button></div>`:"";
                    return `<div class="nas-transfer-job ${bad?"error":done?"done":""}">
                        <div><strong>${active?"↑ ":done?"✓ ":bad?"! ":"◷ "}${esc(job.targetName)}</strong><b>${label}</b></div>
                        ${!done&&!bad&&job.status!=="cancelled"?`<div class="nas-card-transfer-bar"><i style="width:${pct}%"></i></div>`:""}
                        <small>${bad?esc(job.error||"Błąd wysyłania"):done||job.status==="cancelled"?fmtBytes(job.sent):`${fmtBytes(job.sent)} / ${fmtBytes(job.file.size)}${active?` • ${fmtSpeed(job.speed)} • ETA ${fmtEta(job.eta)}`:""}`}</small>${actions}
                    </div>`;
                }).join("")}`:"";
        }
        // Nowy dashboard 1:1 ma własną historię; pokazuj w niej też żywe transfery.
        const activityCard=document.querySelector(".lms1-activity-card");
        const activityList=document.querySelector("#lms1-home-activity");
        if(activityCard&&activityList){
            let live=document.querySelector("#lms1-live-transfers");
            if(!live){
                live=document.createElement("div");
                live.id="lms1-live-transfers";
                activityCard.insertBefore(live,activityList);
            }
            live.innerHTML=manager?.innerHTML||"";
            live.hidden=!all.length;
            activityCard.classList.toggle("has-live-transfers",all.length>0);
            const hasHistory=!!activityList.querySelector(".lms1-activity-row");
            const qbtVisible=!!document.querySelector("#lms1-qbt-transfers:not([hidden])");
            activityList.hidden=(all.length>0||qbtVisible)&&!hasHistory;
        }
    }

    function sendChunk(job, blob, offset) {
        return new Promise((resolve,reject)=>{
            const xhr=new XMLHttpRequest();
            xhr.open("POST",`${API}/api/media/upload/${encodeURIComponent(job.uploadId)}/chunk`);
            xhr.setRequestHeader("Content-Type","application/octet-stream");
            xhr.setRequestHeader("X-Upload-Offset",String(offset));
            xhr.timeout=120000;
            const start=performance.now(), baseline=offset;
            xhr.upload.onprogress=e=>{
                if(!e.lengthComputable)return;
                job.sent=Math.min(job.file.size,baseline+e.loaded);
                const seconds=(performance.now()-start)/1000;
                if(seconds>0.25)job.speed=e.loaded/seconds;
                job.eta=job.speed>0?(job.file.size-job.sent)/job.speed:null;
                renderTransferPanel();
            };
            xhr.onload=()=>{
                let data={};try{data=JSON.parse(xhr.responseText||"{}");}catch{}
                if(xhr.status<200||xhr.status>=300||data.ok===false){reject(new Error(data.error||`HTTP ${xhr.status}`));return;}
                resolve(data);
            };
            xhr.onerror=()=>reject(new Error("Utracono połączenie podczas uploadu"));
            xhr.ontimeout=()=>reject(new Error("Przekroczono czas wysyłania fragmentu"));
            xhr.send(blob);
        });
    }
    async function uploadJob(job) {
        const init=job.uploadId?
            await apiJson(`${API}/api/media/upload/${encodeURIComponent(job.uploadId)}`,{cache:"no-store"}):
            await apiJson(`${API}/api/media/upload/init`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({
                library:job.library,folder:job.folder,originalName:job.file.name,targetName:job.targetName,size:job.file.size
            })});
        job.uploadId=init.uploadId;
        let offset=Number(init.received||0), lastT=performance.now(), lastB=offset;
        job.sent=offset;
        if(job.status==="pausing"){job.status="paused";renderTransferPanel();return;}
        if(job.status==="cancelling")return;
        while(offset<job.file.size) {
            if(job.status==="pausing"){job.status="paused";renderTransferPanel();return;}
            if(job.status==="cancelling")return;
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
        if(job.status==="pausing"){job.status="paused";renderTransferPanel();return;}
        if(job.status==="cancelling")return;
        job.status="finalizing";renderTransferPanel();
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
                    if(job.status!=="cancelling"){job.status="error";job.error=e.message;}
                }
                if(job.status==="cancelling")job.status="cancelled";
                if(job.status==="cancelled"||job.status==="error"){
                    if(job.uploadId)await fetch(`${API}/api/media/upload/${encodeURIComponent(job.uploadId)}`,{method:"DELETE"}).catch(()=>{});
                }
                if(job.status!=="paused"){
                    transfer.completed.push(job);
                    if(transfer.completed.length>6)transfer.completed.shift();
                    transfer.jobs=transfer.jobs.filter(x=>x!==job);
                }
                transfer.active=null;renderTransferPanel();
            }
        } finally { transfer.running=false;transfer.active=null;renderTransferPanel(); }
    }

    document.addEventListener("click",event=>{
        const button=event.target.closest?.("#lms1-live-transfers [data-lms-upload]");
        if(!button)return;
        const job=transfer.jobs.find(x=>x.id===button.dataset.job);
        if(!job)return;
        const action=button.dataset.lmsUpload;
        if(action==="cancel"){
            if(!window.confirm("Anulować upload? Wysłane fragmenty tymczasowe zostaną usunięte."))return;
            if(job.status==="queued"||job.status==="paused"){
                job.status="cancelled";
                transfer.jobs=transfer.jobs.filter(x=>x!==job);
                transfer.completed.push(job);
                if(transfer.completed.length>6)transfer.completed.shift();
                if(job.uploadId)fetch(`${API}/api/media/upload/${encodeURIComponent(job.uploadId)}`,{method:"DELETE"}).catch(()=>{});
            }else if(["uploading","pausing"].includes(job.status))job.status="cancelling";
        }else if(action==="pause"){
            if(job.status==="uploading")job.status="pausing";
            else if(job.status==="queued")job.status="paused";
        }else if(action==="resume"&&job.status==="paused"){
            job.status="queued";
            runQueue();
        }
        renderTransferPanel();
    });

    window.addEventListener("nas:local-media",e=>openWizard(e.detail?.type==="movie"?"movie":"series"));
    const boot=setInterval(()=>{if(document.querySelector("#nas-media-hub-v2")){clearInterval(boot);ensureWorkspace();ensureTransferPanel();}},250);
    console.log("Aurora Local Media V4 loaded");
})();


/* ============================================================
   AURORA TORRENT V5 — Magnet + .torrent
   ============================================================ */
(() => {
  const API="";
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
    try{await req(`${API}/api/qbittorrent/start`,{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({hash:state.meta.hash,selected:sel})});window.dispatchEvent(new CustomEvent("nas:qbt-started"));close();window.dispatchEvent(new CustomEvent("nas:dashboard-home"))}
    catch(x){err.textContent=x.message;b.disabled=false;b.textContent="Rozpocznij pobieranie →"}
  }

  // Intercept the existing Torrent quick-add card before legacy modal code.
  document.addEventListener("click",e=>{
    const candidates=[...document.querySelectorAll("#nas-media-hub-v2 button,#nas-media-hub-v2 [role=button],#nas-media-hub-v2 .nas-quick-card,#nas-media-hub-v2 .nas-media-card")];
    const card=e.target.closest?.("button,[role=button],.nas-quick-card,.nas-media-card");
    if(card&&candidates.includes(card)&&/torrent/i.test(card.textContent||"")){e.preventDefault();e.stopImmediatePropagation();open()}
  },true);
})();
/* LUDIUS MS 1TO1 DASHBOARD — 2026-09-30 */
(() => {
  "use strict";

  const API = "";
  const URLS = {
    jellyfin: `${window.location.protocol}//${window.location.hostname}:8096`,
    gdrive: "",
    kuma: "",
    ntfy: ""
  };

  const state = {
    page: "dashboard",
    system: null,
    uptimeSampleMs: null,
    status: null,
    jellyfin: null,
    qbt: null,
    activity: [],
    recent: [],
    history: { cpu: [], ram: [], disk: [], net: [] }
  };

  const serviceMeta = [
    ["jellyfin", "Jellyfin", "play", URLS.jellyfin],
    ["qbittorrent", "qBittorrent", "download", null]
  ];

  const pageCopy = {
    dashboard: ["Dashboard", ""],
    media: ["Media", "Dodawaj filmy, seriale i torrenty"],
    downloads: ["Pobieranie", "Aktywne transfery i kolejka"],
    server: ["Serwer", "Zasoby i usługi Ludius MS"],
    activity: ["Aktywność", "Ostatnie zdarzenia w bibliotece"],
    settings: ["Ustawienia", "Dashboard i skróty administracyjne"]
  };

  function esc(value) {
    return String(value == null ? "" : value)
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function icon(name) {
    const map = {
      home: '<svg viewBox="0 0 24 24"><path d="M3 11.5 12 4l9 7.5v8.5H14.5v-6h-5v6H3z"/></svg>',
      media: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="m10 8 6 4-6 4z"/></svg>',
      download: '<svg viewBox="0 0 24 24"><path d="M12 3v11m0 0 4-4m-4 4-4-4M5 19h14"/></svg>',
      library: '<svg viewBox="0 0 24 24"><path d="M3.5 6h6l1.5 2H21v10.5a1.5 1.5 0 0 1-1.5 1.5H4.5A1.5 1.5 0 0 1 3 18.5V7.5A1.5 1.5 0 0 1 4.5 6z"/></svg>',
      server: '<svg viewBox="0 0 24 24"><rect x="3.5" y="4" width="17" height="6" rx="1.5"/><rect x="3.5" y="14" width="17" height="6" rx="1.5"/><path d="M7 7h.01M7 17h.01M11 7h6M11 17h6"/></svg>',
      pulse: '<svg viewBox="0 0 24 24"><path d="M2.5 12h4l2-6 4 12 2-6h7"/></svg>',
      settings: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.3 13.5a7.7 7.7 0 0 0 0-3l2-1.5-2-3.5-2.5 1a8 8 0 0 0-2.6-1.5L13.8 2h-4l-.4 3a8 8 0 0 0-2.6 1.5l-2.5-1-2 3.5 2 1.5a7.7 7.7 0 0 0 0 3l-2 1.5 2 3.5 2.5-1A8 8 0 0 0 9.4 19l.4 3h4l.4-3a8 8 0 0 0 2.6-1.5l2.5 1 2-3.5z"/></svg>',
      bell: '<svg viewBox="0 0 24 24"><path d="M18 8a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9M10 21h4"/></svg>',
      moon: '<svg viewBox="0 0 24 24"><path d="M20 15.5A8.5 8.5 0 0 1 8.5 4 8.5 8.5 0 1 0 20 15.5z"/></svg>',
      search: '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="6.5"/><path d="m16 16 4 4"/></svg>',
      cpu: '<svg viewBox="0 0 24 24"><rect x="6" y="6" width="12" height="12" rx="2"/><path d="M9 9h6v6H9M9 2v4m6-4v4M9 18v4m6-4v4M2 9h4m-4 6h4m12-6h4m-4 6h4"/></svg>',
      ram: '<svg viewBox="0 0 24 24"><rect x="3" y="7" width="18" height="10" rx="2"/><path d="M7 10v4m4-4v4m4-4v4m4-4v4M6 17v2m12-2v2"/></svg>',
      disk: '<svg viewBox="0 0 24 24"><path d="M6 4h12l3 14H3z"/><circle cx="12" cy="14" r="2"/><path d="M8 8h8"/></svg>',
      network: '<svg viewBox="0 0 24 24"><path d="M12 3v18M6 8l6-5 6 5M6 16l6 5 6-5M4 12h16"/></svg>',
      clock: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/></svg>',
      folder: '<svg viewBox="0 0 24 24"><path d="M3 6h7l2 2h9v11H3z"/></svg>',
      terminal: '<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="16" rx="2"/><path d="m7 9 3 3-3 3m6 0h4"/></svg>',
      external: '<svg viewBox="0 0 24 24"><path d="M14 5h5v5M19 5l-8 8"/><path d="M18 13v6H5V6h6"/></svg>',
      refresh: '<svg viewBox="0 0 24 24"><path d="M20 7v5h-5M4 17v-5h5"/><path d="M18 9a7 7 0 0 0-12-2L4 9m2 6a7 7 0 0 0 12 2l2-2"/></svg>'
    };
    return map[name] || "";
  }

  function formatBytes(bytes) {
    let n = Number(bytes || 0);
    if (!Number.isFinite(n) || n <= 0) return "0 B";
    const units = ["B", "KB", "MB", "GB", "TB"];
    const i = Math.min(units.length - 1, Math.floor(Math.log(n) / Math.log(1024)));
    return (n / Math.pow(1024, i)).toFixed(i < 2 ? 0 : 1) + " " + units[i];
  }

  function formatSpeed(bytes) {
    return formatBytes(bytes) + "/s";
  }

  function formatUptime(seconds) {
    const n = Math.max(0, Math.floor(Number(seconds) || 0));
    const days = Math.floor(n / 86400);
    const hours = String(Math.floor((n % 86400) / 3600)).padStart(2,"0");
    const minutes = String(Math.floor((n % 3600) / 60)).padStart(2,"0");
    const secs = String(n % 60).padStart(2,"0");
    return (days ? days + " d " : "") + `${hours}:${minutes}:${secs}`;
  }

  function updateUptimeLive() {
    if (!state.system || state.uptimeSampleMs == null) return;
    const elapsed = Math.max(0, Math.floor((Date.now() - state.uptimeSampleMs) / 1000));
    const uptime = formatUptime(Number(state.system.uptimeSeconds || 0) + elapsed);
    const card = document.querySelector("#lms1-up-value");
    const sidebar = document.querySelector("#lms1-side-uptime");
    const server = document.querySelector(".lms1-resource-uptime strong");
    if (card) card.textContent = uptime;
    if (sidebar) sidebar.textContent = "uptime " + uptime;
    if (server) server.textContent = uptime;
  }

  function bootDate(seconds) {
    const d = new Date(Date.now() - Number(seconds || 0) * 1000);
    return d.toLocaleDateString("pl-PL") + ", " + d.toLocaleTimeString("pl-PL", {hour:"2-digit", minute:"2-digit"});
  }

  function relativeTime(event) {
    const raw = event.timestamp || event.createdAt || event.created_at || event.time;
    if (!raw) return "";
    let numeric = Number(raw);
    const value = Number.isFinite(numeric) && numeric < 100000000000 ? numeric * 1000 : raw;
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return "";
    const seconds = Math.max(0, Math.floor((Date.now() - date.getTime()) / 1000));
    if (seconds < 60) return "teraz";
    if (seconds < 3600) return Math.floor(seconds / 60) + " min temu";
    if (seconds < 86400) return Math.floor(seconds / 3600) + " godz. temu";
    return Math.floor(seconds / 86400) + " d temu";
  }

  async function getJSON(path) {
    const response = await fetch(API + path, {cache: "no-store"});
    if (!response.ok) throw new Error(path + ": HTTP " + response.status);
    return response.json();
  }

  function navButton(page, label, glyph) {
    return '<button type="button" data-page="' + page + '">' + icon(glyph) + '<span>' + label + '</span><b></b></button>';
  }

  function buildApp() {
    const root = document.querySelector("#nas-dashboard");
    if (!root || document.querySelector("#lms-1to1-app")) return;

    const app = document.createElement("div");
    app.id = "lms-1to1-app";
    app.innerHTML =
      '<aside class="lms1-sidebar">' +
        '<div class="lms1-brand">' +
          '<div class="lms1-logo"><img src="/lms-assets/lms-logo.webp" alt="LMS"></div>' +
          '<div class="lms1-brand-copy"><strong>LUDIUS <em>MS</em></strong><span>MEDIA SERVER</span></div>' +
        '</div>' +
        '<div class="lms1-build-notice" role="note"><strong><i aria-hidden="true"></i> Wersja testowa</strong><small>Projekt w trakcie rozwoju. Niektóre funkcje mogą być niedostępne lub działać nieprawidłowo.</small></div>' +
        '<nav class="lms1-nav">' +
          navButton("dashboard","Dashboard","home") +
          navButton("media","Media","media") +
          navButton("downloads","Pobieranie","download") +
          '<button type="button" data-external="jellyfin">' + icon("library") + '<span>Biblioteka</span><b></b></button>' +
          navButton("server","Serwer","server") +
          navButton("activity","Aktywność","pulse") +
          navButton("settings","Ustawienia","settings") +
        '</nav>' +
        '<button class="lms1-server-pill" type="button" data-page="server"><i></i><div><strong id="lms1-server-state">Serwer online</strong><small id="lms1-side-uptime">uptime —</small></div><b>›</b></button>' +
      '</aside>' +
      '<section class="lms1-stage">' +
        '<header class="lms1-topbar">' +
          '<div class="lms1-search">' + icon("search") + '<input id="lms1-search" type="search" placeholder="Szukaj filmów, seriali, anime..." autocomplete="off"><kbd>Ctrl K</kbd></div>' +
          '<div class="lms1-page-title"><strong id="lms1-page-title">Dashboard</strong><small id="lms1-page-subtitle"></small></div>' +
          '<div class="lms1-head-actions">' +
            '<button type="button" id="lms1-bell" title="Powiadomienia">' + icon("bell") + '<i></i></button>' +
            '<span class="lms1-divider"></span>' +
            '<button type="button" id="lms1-theme" title="Przygaś interfejs">' + icon("moon") + '</button>' +
            '<span class="lms1-divider"></span>' +
            '<span class="lms1-avatar" id="lms1-avatar">L</span>' +
          '</div>' +
        '</header>' +
        '<main class="lms1-main">' +
          '<section class="lms1-view" data-view="dashboard"></section>' +
          '<section class="lms1-view" data-view="media"></section>' +
          '<section class="lms1-view" data-view="downloads"></section>' +
          '<section class="lms1-view" data-view="server"></section>' +
          '<section class="lms1-view" data-view="activity"></section>' +
          '<section class="lms1-view" data-view="settings"></section>' +
        '</main>' +
      '</section>';

    root.appendChild(app);
    buildDashboardView();
    buildMediaView();
    buildDownloadsView();
    buildServerView();
    buildActivityView();
    buildSettingsView();
    wireApp();
    setPage("dashboard");
  }

  function buildDashboardView() {
    const view = document.querySelector('[data-view="dashboard"]');
    view.innerHTML =
      '<section class="lms1-hero">' +
        '<img class="lms1-hero-image" src="/lms-assets/lms-hero.webp" alt="">' +
        '<div class="lms1-hero-fade"></div>' +
        '<div class="lms1-hero-copy"><span id="lms1-greeting">Dobry wieczór,</span><h1><span id="lms1-display-name"></span><i id="lms1-name-cursor"></i></h1><p><b></b><span id="lms1-global-status">Sprawdzanie systemu…</span></p></div>' +
        '<div class="lms1-clock"><small id="lms1-date">—</small><strong id="lms1-time">--:--</strong><blockquote>„Twoja prywatna<br>biblioteka, zawsze<br>pod ręką.”<em>LUDIUS MS</em></blockquote></div>' +
      '</section>' +
      '<section class="lms1-metrics">' +
        metricCard("cpu","CPU","cpu","Oracle Cloud","blue") +
        metricCard("ram","RAM","ram","Pamięć systemowa","blue") +
        metricCard("disk","Dysk","disk","NAS","green") +
        metricCard("net","Sieć","network","↓ 0 B/s  ·  ↑ 0 B/s","purple") +
        '<article class="lms1-metric uptime"><div class="lms1-metric-head">' + icon("clock") + '<span>Uptime</span></div><strong id="lms1-up-value">—</strong><small id="lms1-up-boot">od —</small></article>' +
      '</section>' +
      '<div class="lms1-section-label"><h2>Szybki dostęp</h2></div>' +
      '<section class="lms1-quick">' +
        quickCard("jellyfin","Otwórz Jellyfin","Filmy · Seriale · Anime","media","blue","external") +
        quickCard("library","Biblioteka","Przeglądaj swoją kolekcję","library","violet","external") +
        quickCard("server","Zarządzaj serwerem","Usługi · Ustawienia","server","green","page") +
        quickCard("settings","Ustawienia","Konfiguracja Ludius MS","settings","plain","page") +
      '</section>' +
      '<section class="lms1-library-grid">' +
        '<article class="lms1-recent"><div class="lms1-panel-head"><h2>Ostatnio dodane</h2><button type="button" data-external="jellyfin">Zobacz wszystkie →</button></div><div id="lms1-recent-row" class="lms1-recent-row"><div class="lms1-loading">Ładowanie biblioteki…</div></div></article>' +
        '<article class="lms1-activity-card"><div class="lms1-panel-head"><h2>Ostatnia aktywność</h2><button type="button" data-page="activity">Zobacz wszystkie →</button></div><div id="lms1-home-activity" class="lms1-activity-list"><div class="lms1-loading">Ładowanie…</div></div></article>' +
      '</section>' +
      '<section class="lms1-services-strip"><div class="lms1-panel-head"><h2>Usługi online</h2><span id="lms1-service-count">— / 5</span></div><div id="lms1-services-row" class="lms1-services-row"></div></section>';
  }

  function metricCard(id, title, glyph, subtitle, tone) {
    return '<article class="lms1-metric ' + tone + '">' +
      '<div class="lms1-metric-head">' + icon(glyph) + '<span>' + title + '</span></div>' +
      '<strong id="lms1-' + id + '-value">—</strong>' +
      '<svg class="lms1-spark" viewBox="0 0 100 32" preserveAspectRatio="none"><polyline id="lms1-' + id + '-spark" points=""></polyline></svg>' +
      '<small id="lms1-' + id + '-sub">' + subtitle + '</small>' +
      '<div class="lms1-meter"><i id="lms1-' + id + '-bar"></i></div>' +
    '</article>';
  }

  function quickCard(action, title, subtitle, glyph, tone, kind) {
    const attr = kind === "external" ? 'data-external="jellyfin"' : 'data-page="' + action + '"';
    return '<button type="button" class="lms1-quick-card ' + tone + '" ' + attr + '><span>' + icon(glyph) + '</span><div><strong>' + title + '</strong><small>' + subtitle + '</small></div><b>›</b></button>';
  }

  function buildMediaView() {
    const view = document.querySelector('[data-view="media"]');
    view.innerHTML =
      pageIntro("DODAJ MEDIA","Media","Wybierz źródło. Dotychczasowe workflow plików, poczekalni i torrentów pozostaje podpięte.") +
      '<div class="lms1-media-actions">' +
        '<button type="button" id="lms1-add-movie"><span>▣</span><div><strong>Film lokalny</strong><small>Dodaj film z komputera</small></div><b>→</b></button>' +
        '<button type="button" id="lms1-add-series"><span>▤</span><div><strong>Serial lokalny</strong><small>Dodaj odcinki lub cały folder</small></div><b>→</b></button>' +
        '<button type="button" id="lms1-add-torrent"><span>↓</span><div><strong>Torrent</strong><small>Magnet lub plik .torrent</small></div><b>→</b></button>' +
      '</div>' +
      '<div class="lms1-subcard"><div class="lms1-panel-head"><h2>Biblioteka</h2><button type="button" data-external="jellyfin">Otwórz Jellyfin →</button></div><p>Filmy, seriale i anime po dodaniu trafiają do bibliotek NAS i są widoczne w Jellyfinie.</p></div>';
  }

  function buildDownloadsView() {
    const view = document.querySelector('[data-view="downloads"]');
    view.innerHTML = pageIntro("QBITTORRENT","Pobieranie","Pełna kontrola nad aktywnymi transferami i miejscem docelowym.");
    const legacy = document.querySelector("#nas-download-panel");
    if (legacy) {
      legacy.classList.add("lms1-qbt-panel");
      view.appendChild(legacy);
    }
  }

  function buildServerView() {
    const view = document.querySelector('[data-view="server"]');
    view.innerHTML =
      pageIntro("LUDIUS MS","Serwer","Stan usług, wykorzystanie NAS i skróty administracyjne.") +
      '<div class="lms1-server-grid">' +
        '<article class="lms1-subcard"><div class="lms1-panel-head"><h2>Zasoby</h2><button type="button" id="lms1-refresh">' + icon("refresh") + ' Odśwież</button></div><div id="lms1-server-resources" class="lms1-resource-list"></div></article>' +
        '<article class="lms1-subcard"><div class="lms1-panel-head"><h2>Usługi</h2><span id="lms1-server-services-count">—</span></div><div id="lms1-server-services" class="lms1-server-services"></div></article>' +
      '</div>';
  }

  function buildActivityView() {
    const view = document.querySelector('[data-view="activity"]');
    view.innerHTML = pageIntro("HISTORIA","Aktywność","Ostatnie zdarzenia zapisane przez Ludius MS.") + '<article class="lms1-subcard"><div id="lms1-activity-full" class="lms1-activity-list full"></div></article>';
  }

  function buildSettingsView() {
    const view = document.querySelector('[data-view="settings"]');
    view.innerHTML =
      pageIntro("KONFIGURACJA","Ustawienia","Najczęstsze opcje dashboardu i usług.") +
      '<div class="lms1-settings-grid">' +
        settingsCard("refresh","Odśwież dane","Pobierz aktualny stan serwera","refresh") +
        settingsLink(URLS.jellyfin,"Jellyfin","Biblioteka multimediów","media") +
      '</div>';
  }

  function pageIntro(kicker, title, subtitle) {
    return '<div class="lms1-page-intro"><span>' + kicker + '</span><h1>' + title + '</h1><p>' + subtitle + '</p></div>';
  }

  function settingsCard(action, title, subtitle, glyph) {
    return '<button type="button" data-setting="' + action + '"><span>' + icon(glyph) + '</span><div><strong>' + title + '</strong><small>' + subtitle + '</small></div><b>›</b></button>';
  }

  function settingsLink(url, title, subtitle, glyph) {
    return '<a href="' + url + '" target="_blank" rel="noopener"><span>' + icon(glyph) + '</span><div><strong>' + title + '</strong><small>' + subtitle + '</small></div><b>↗</b></a>';
  }

  function wireApp() {
    const app = document.querySelector("#lms-1to1-app");

    app.addEventListener("click", event => {
      const page = event.target.closest("[data-page]");
      if (page) {
        event.preventDefault();
        setPage(page.dataset.page);
      }

      const external = event.target.closest("[data-external]");
      if (external) window.open(URLS.jellyfin, "_blank", "noopener");

      const poster = event.target.closest("[data-jellyfin-id]");
      if (poster) {
        window.open(URLS.jellyfin + "/web/#/details?id=" + encodeURIComponent(poster.dataset.jellyfinId), "_blank", "noopener");
      }

      const setting = event.target.closest("[data-setting]");
      if (setting && setting.dataset.setting === "wallpaper") document.querySelector("#nas-wallpaper")?.click();
      if (setting && setting.dataset.setting === "refresh") refreshAll(true);
    });

    document.querySelector("#lms1-add-movie").addEventListener("click", () => window.dispatchEvent(new CustomEvent("nas:local-media", {detail:{type:"movie"}})));
    document.querySelector("#lms1-add-series").addEventListener("click", () => window.dispatchEvent(new CustomEvent("nas:local-media", {detail:{type:"series"}})));
    document.querySelector("#lms1-add-torrent").addEventListener("click", () => document.querySelector("#nas-v2-torrent")?.click());
    document.querySelector("#lms1-refresh").addEventListener("click", () => refreshAll(true));
    document.querySelector("#lms1-bell")?.remove();

    const search = document.querySelector("#lms1-search");
    search.addEventListener("keydown", event => {
      if (event.key === "Enter" && search.value.trim()) {
        window.open(URLS.jellyfin + "/web/#/search.html?query=" + encodeURIComponent(search.value.trim()), "_blank", "noopener");
      }
    });

    document.addEventListener("keydown", event => {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
        event.preventDefault();
        search.focus();
      }
    });

    const theme = document.querySelector("#lms1-theme");
    theme.addEventListener("click", () => {
      document.querySelector("#lms-1to1-app").classList.toggle("low-light");
      localStorage.setItem("lms-low-light", document.querySelector("#lms-1to1-app").classList.contains("low-light") ? "1" : "0");
    });

    if (localStorage.getItem("lms-low-light") === "1") document.querySelector("#lms-1to1-app").classList.add("low-light");
  }

  function setPage(page) {
    if (!pageCopy[page]) return;
    state.page = page;

    document.querySelectorAll(".lms1-nav [data-page]").forEach(button => button.classList.toggle("active", button.dataset.page === page));
    document.querySelectorAll(".lms1-view").forEach(view => view.classList.toggle("active", view.dataset.view === page));

    const title = document.querySelector("#lms1-page-title");
    const subtitle = document.querySelector("#lms1-page-subtitle");
    title.textContent = pageCopy[page][0];
    subtitle.textContent = pageCopy[page][1];

    document.querySelector(".lms1-page-title").classList.toggle("show", page !== "dashboard");
    document.querySelector(".lms1-main").scrollTo({top:0, behavior:"smooth"});
    if (page === "activity") renderActivity();
    if (page === "server") renderServer();
  }

  async function loadProfile() {
    try {
      const response = await fetch("/lms-assets/lms-profile.json", {cache:"no-store"});
      if (!response.ok) return;
      const profile = await response.json();
      const name = typeof profile.displayName === "string" ? profile.displayName.trim().slice(0,40) : "";
      const target = document.querySelector("#lms1-display-name");
      const avatar = document.querySelector("#lms1-avatar");
      if (target) target.textContent = name;
      const cursor = document.querySelector("#lms1-name-cursor");
      if (cursor) cursor.textContent = name ? "_" : "";
      if (avatar) avatar.textContent = name ? name[0].toLocaleUpperCase("pl-PL") : "L";
    } catch (error) { console.warn("Profil LMS jest niedostępny:", error); }
  }

  function updateClock() {
    const now = new Date();
    const hour = now.getHours();
    const greeting = hour < 5 ? "Dobranoc," : hour < 12 ? "Dzień dobry," : hour < 18 ? "Dobre popołudnie," : hour < 23 ? "Dobry wieczór," : "Dobranoc,";
    const g = document.querySelector("#lms1-greeting");
    const time = document.querySelector("#lms1-time");
    const date = document.querySelector("#lms1-date");
    if (g) g.textContent = greeting;
    if (time) time.textContent = now.toLocaleTimeString("pl-PL",{hour:"2-digit",minute:"2-digit"});
    if (date) date.textContent = now.toLocaleDateString("pl-PL",{weekday:"long",day:"numeric",month:"long"});
  }

  function pushHistory(key, value) {
    const list = state.history[key];
    list.push(Number(value || 0));
    while (list.length > 26) list.shift();
  }

  function renderSpark(id, values, fixedMax) {
    const line = document.querySelector("#lms1-" + id + "-spark");
    if (!line || !values.length) return;
    const max = fixedMax || Math.max(1, ...values);
    const points = values.map((value, index) => {
      const x = values.length === 1 ? 0 : index / (values.length - 1) * 100;
      const y = 29 - Math.min(1, Number(value || 0) / max) * 25;
      return x.toFixed(1) + "," + y.toFixed(1);
    }).join(" ");
    line.setAttribute("points", points);
  }

  function renderMetrics() {
    if (!state.system) return;
    const s = state.system;
    const q = state.qbt || {};
    const net = Number(q.downloadSpeed || 0) + Number(q.uploadSpeed || 0);

    pushHistory("cpu",s.cpu);
    pushHistory("ram",s.ram);
    pushHistory("disk",s.disk);
    pushHistory("net",net);

    document.querySelector("#lms1-cpu-value").textContent = s.cpu + "%";
    document.querySelector("#lms1-ram-value").textContent = s.ram + "%";
    document.querySelector("#lms1-disk-value").textContent = s.disk + "%";
    document.querySelector("#lms1-disk-sub").textContent = s.diskUsedGB + " / " + s.diskTotalGB + " GB";
    document.querySelector("#lms1-net-value").textContent = formatSpeed(q.downloadSpeed || 0);
    document.querySelector("#lms1-net-sub").textContent = "↓ " + formatSpeed(q.downloadSpeed || 0) + "  ·  ↑ " + formatSpeed(q.uploadSpeed || 0);
    updateUptimeLive();
    document.querySelector("#lms1-up-boot").textContent = "od " + bootDate(s.uptimeSeconds);

    [["cpu",s.cpu],["ram",s.ram],["disk",s.disk]].forEach(pair => {
      const bar = document.querySelector("#lms1-" + pair[0] + "-bar");
      if (bar) bar.style.width = Math.max(0,Math.min(100,Number(pair[1]))) + "%";
    });

    const netMax = Math.max(1,...state.history.net);
    const netBar = document.querySelector("#lms1-net-bar");
    if (netBar) netBar.style.width = Math.min(100,net / netMax * 100) + "%";

    renderSpark("cpu",state.history.cpu,100);
    renderSpark("ram",state.history.ram,100);
    renderSpark("disk",state.history.disk,100);
    renderSpark("net",state.history.net,netMax);
  }

  function renderStatus() {
    if (!state.status) return;
    const rows = serviceMeta;
    const online = rows.filter(row => state.status[row[0]]?.online).length;
    const all = online === rows.length;

    document.querySelector("#lms1-global-status").textContent = all ? "Ludius MS działa poprawnie." : online + " z " + rows.length + " usług online.";
    document.querySelector("#lms1-server-state").textContent = all ? "Serwer online" : online + "/" + rows.length + " usług online";
    document.querySelector("#lms1-service-count").textContent = online + " / " + rows.length;
    document.querySelector("#lms1-server-services-count").textContent = online + " / " + rows.length + " online";
    document.querySelector(".lms1-server-pill").classList.toggle("warning",!all);

    const box = document.querySelector("#lms1-services-row");
    box.innerHTML = rows.map(row => {
      const data = state.status[row[0]] || {};
      return '<button type="button" ' + (row[3] ? 'data-url="' + row[3] + '"' : 'data-page="downloads"') + '>' +
        '<span class="lms1-service-icon">' + icon(row[2]) + '</span>' +
        '<div><strong>' + esc(row[1]) + '</strong><small><i class="' + (data.online ? "online" : "offline") + '"></i>' + (data.online ? "Online" : "Offline") + '</small></div>' +
        '<em>' + (data.latency == null ? "—" : data.latency + " ms") + '</em>' +
      '</button>';
    }).join("");

    box.querySelectorAll("[data-url]").forEach(button => button.addEventListener("click",() => window.open(button.dataset.url,"_blank","noopener")));
  }

  function renderRecent() {
    const box = document.querySelector("#lms1-recent-row");
    const items = Array.isArray(state.recent) ? state.recent.slice(0,6) : [];
    if (!items.length) {
      box.innerHTML = '<div class="lms1-loading">Brak pozycji do wyświetlenia.</div>';
      return;
    }

    box.innerHTML = items.map((item,index) => {
      const image = item.hasImage ? '<img loading="lazy" src="' + API + '/api/jellyfin/image/' + encodeURIComponent(item.id) + '" alt="">' : '<span class="lms1-poster-fallback">LMS</span>';
      const badge = index === 0 || index === 2 ? '<b class="lms1-badge">NOWE</b>' : "";
      return '<button type="button" class="lms1-poster" data-jellyfin-id="' + esc(item.id) + '">' +
        '<span class="lms1-poster-art">' + image + badge + '</span>' +
        '<strong>' + esc(item.name) + '</strong>' +
        '<small>' + esc(item.year || (item.type === "Series" ? "Serial" : "Film")) + '</small>' +
      '</button>';
    }).join("");
  }

  function activityLabel(event) {
    const type = String(event.type || "").toLowerCase();
    if (type.includes("episode")) return ["Dodano odcinek","media"];
    if (type.includes("movie")) return ["Dodano do biblioteki","folder"];
    if (type.includes("download") || type.includes("torrent")) return ["Zakończono pobieranie","download"];
    return ["Aktywność serwera","settings"];
  }

  function activityRows(limit) {
    return state.activity.slice(0,limit).map(event => {
      const meta = activityLabel(event);
      return '<div class="lms1-activity-row"><span>' + icon(meta[1]) + '</span><div><strong>' + meta[0] + '</strong><small>' + esc(event.title || "") + (event.detail ? " · " + esc(event.detail) : "") + '</small></div><time>' + relativeTime(event) + '</time></div>';
    }).join("");
  }

  function renderActivity() {
    const home = document.querySelector("#lms1-home-activity");
    const full = document.querySelector("#lms1-activity-full");
    const empty = '<div class="lms1-loading">Brak zapisanej aktywności.</div>';
    if (home) home.innerHTML = state.activity.length ? activityRows(4) : empty;
    if (full) full.innerHTML = state.activity.length ? activityRows(30) : empty;
  }

  function renderServer() {
    const res = document.querySelector("#lms1-server-resources");
    if (state.system && res) {
      res.innerHTML =
        resourceRow("CPU",state.system.cpu + "%",state.system.cpu) +
        resourceRow("RAM",state.system.ram + "%",state.system.ram) +
        resourceRow("Dysk NAS",state.system.diskUsedGB + " / " + state.system.diskTotalGB + " GB",state.system.disk) +
        '<div class="lms1-resource-uptime"><span>Uptime</span><strong>' + formatUptime(state.system.uptimeSeconds) + '</strong></div>';
    }

    const services = document.querySelector("#lms1-server-services");
    if (state.status && services) {
      services.innerHTML = serviceMeta.map(row => {
        const data = state.status[row[0]] || {};
        return '<a ' + (row[3] ? 'href="' + row[3] + '" target="_blank" rel="noopener"' : 'href="#" data-page="downloads"') + '><span>' + icon(row[2]) + '</span><div><strong>' + row[1] + '</strong><small>' + (data.online ? "Online · " + (data.latency == null ? "—" : data.latency + " ms") : "Offline") + '</small></div><i class="' + (data.online ? "online" : "offline") + '"></i></a>';
      }).join("");
    }
  }

  function resourceRow(label,value,percent) {
    return '<div class="lms1-resource-row"><div><span>' + label + '</span><strong>' + value + '</strong></div><i><b style="width:' + Math.max(0,Math.min(100,Number(percent || 0))) + '%"></b></i></div>';
  }

  async function refreshAll(manual) {
    const results = await Promise.allSettled([
      getJSON("/api/system"),
      getJSON("/api/status"),
      getJSON("/api/jellyfin"),
      getJSON("/api/qbittorrent"),
      getJSON("/api/activity"),
      getJSON("/api/jellyfin/recent?limit=8")
    ]);

    if (results[0].status === "fulfilled") {
      state.system = results[0].value;
      state.uptimeSampleMs = Date.now();
    }
    if (results[1].status === "fulfilled") state.status = results[1].value;
    if (results[2].status === "fulfilled") state.jellyfin = results[2].value;
    if (results[3].status === "fulfilled") state.qbt = results[3].value;
    if (results[4].status === "fulfilled") {
      const data = results[4].value;
      state.activity = Array.isArray(data) ? data : (data.events || data.activity || data.items || []);
    }
    if (results[5].status === "fulfilled") state.recent = results[5].value.items || [];

    renderMetrics();
    renderStatus();
    renderRecent();
    renderActivity();
    renderServer();

    if (manual) {
      const title = document.querySelector("#lms1-page-title");
      title.classList.add("pulse");
      setTimeout(() => title.classList.remove("pulse"),500);
    }
  }

  function init() {
    const root = document.querySelector("#nas-dashboard");
    const qbt = document.querySelector("#nas-download-panel");
    const hub = document.querySelector("#nas-media-hub-v2");

    if (!root || !qbt || !hub) {
      setTimeout(init,120);
      return;
    }

    buildApp();
    loadProfile();
    window.addEventListener("nas:dashboard-home", () => setPage("dashboard"));
    updateClock();
    refreshAll(false);
    setInterval(updateClock,1000);
    setInterval(updateUptimeLive,2000);
    setInterval(() => refreshAll(false),10000);
    console.log("Ludius MS 1TO1 dashboard loaded");
  }

  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded",init);
  else init();
})();

/* Pobieranie qBittorrent w aktywności nowego dashboardu. */
(() => {
  const esc = value => String(value ?? "").replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
  const bytes = n => { const v = Math.max(0, Number(n) || 0); if (!v) return "0 B"; const i = Math.min(4, Math.floor(Math.log(v) / Math.log(1024))); return `${(v / 1024 ** i).toFixed(i >= 2 ? 1 : 0)} ${["B", "KB", "MB", "GB", "TB"][i]}`; };
  const observed=new Set();
  function show(torrents) {
    const card=document.querySelector(".lms1-activity-card"), history=document.querySelector("#lms1-home-activity");
    if (!card || !history) return;
    let box=document.querySelector("#lms1-qbt-transfers");
    if (!box) { box=document.createElement("div"); box.id="lms1-qbt-transfers"; card.insertBefore(box,history); }
    const ongoing=(Array.isArray(torrents)?torrents:[]).filter(t => {
      const state=String(t.state||"").toLowerCase(), pct=Number(t.progress||0);
      if(pct>=100||["error", "missingfiles"].includes(state))return false;
      if(!state.startsWith("stopped")&&!state.startsWith("paused"))observed.add(t.hash);
      return !(state.startsWith("stopped")&&pct===0&&!observed.has(t.hash));
    }).slice(0,5);
    box.hidden=!ongoing.length;
    box.innerHTML=ongoing.length?'<div class="lms1-qbt-heading">POBIERANIE TORRENTÓW</div>'+ongoing.map(t => {
      const pct=Math.max(0,Math.min(100,Number(t.progress||0))), state=String(t.state||"").toLowerCase();
      const paused=state.startsWith("stopped")||state.startsWith("paused");
      const label=paused?"Wstrzymano":state.includes("stall")||state.includes("queued")?"Oczekiwanie":state.includes("check")?"Sprawdzanie":"Pobieranie";
      const hash=String(t.hash||"");
      const controls=/^[a-f0-9]{40}$|^[a-f0-9]{64}$/.test(hash)?`<div class="lms-transfer-actions"><button type="button" data-lms-qbt="${paused?"resume":"pause"}" data-hash="${hash}">${paused?"▶ Wznów":"Ⅱ Pauza"}</button><button type="button" class="stop" data-lms-qbt="cancel" data-hash="${hash}">■ Zatrzymaj</button></div>`:"";
      return `<div class="nas-transfer-job lms1-qbt-job"><div><strong>↓ ${esc(t.name||"Torrent")}</strong><b>${pct.toFixed(1)}%</b></div><div class="nas-card-transfer-bar"><i style="width:${pct}%"></i></div><small>${label} • ${bytes(t.downloaded)} / ${bytes(t.size)} • ↓ ${bytes(t.downloadSpeed)}/s</small>${controls}</div>`;
    }).join(""):"";
    const local=document.querySelector("#lms1-live-transfers:not([hidden])");
    const hasHistory=!!history.querySelector(".lms1-activity-row");
    history.hidden=(ongoing.length>0||!!local)&&!hasHistory;
    card.classList.toggle("has-live-transfers",ongoing.length>0||!!local);
  }
  window.addEventListener("nas:qbt-progress",event=>show(event.detail));
  const pending=new Set();
  document.addEventListener("click",async event=>{
    const button=event.target.closest?.("#lms1-qbt-transfers [data-lms-qbt]");
    if(!button)return;
    const hash=button.dataset.hash,action=button.dataset.lmsQbt;
    if(!/^[a-f0-9]{40}$|^[a-f0-9]{64}$/.test(hash)||pending.has(hash))return;
    if(action==="cancel"&&!window.confirm("Usunąć torrent z kolejki? Pobrane pliki pozostaną na dysku."))return;
    pending.add(hash);button.disabled=true;
    try{
      const response=await fetch("/api/qbittorrent/control",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({hash,action})});
      const result=await response.json().catch(()=>({}));
      if(!response.ok||result.ok===false)throw new Error(result.error||`HTTP ${response.status}`);
      const latest=await fetch("/api/qbittorrent",{cache:"no-store"});
      if(latest.ok){const data=await latest.json();window.dispatchEvent(new CustomEvent("nas:qbt-progress",{detail:data.torrents||[]}));}
    }catch(error){window.alert(error.message||"Nie udało się zmienić stanu torrenta.");}
    finally{pending.delete(hash);button.disabled=false;}
  });
})();
