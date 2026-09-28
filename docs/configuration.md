# Model konfiguracji

Ludius MS rozdziela domyślne wartości repozytorium, konfigurację instalacji, sekrety oraz dane stanu aplikacji.

## Konfiguracja lokalna i Git

Repozytorium zawiera w katalogu głównym wyłącznie plik `.env.example`, który służy jako szablon.

Dla obecnego układu Docker Compose:

1. skopiuj `.env.example` z katalogu głównego repozytorium do `dashboard-api/.env`
2. dostosuj wartości do lokalnego serwera
3. właściwy plik `.env` przechowuj wyłącznie lokalnie

Pliki `.env`, katalogi `secrets/`, dane runtime, częściowo przesłane pliki oraz lokalne kopie zapasowe są ignorowane przez Git.

## 1. Moduły

Obecne moduły opcjonalne:

- Jellyfin
- qBittorrent

Są kontrolowane przez:

```env
ENABLE_JELLYFIN=true
ENABLE_QBITTORRENT=true
```

Wyłączony moduł nie jest rejestrowany w API LMS. Jego route nie istnieje, a praca w tle specyficzna dla tego modułu nie jest uruchamiana.

Aktualny manifest modułów jest dostępny pod:

```text
GET /api/modules
```

Dzięki temu frontend może wykrywać obsługiwane moduły bez zgadywania na podstawie odpowiedzi 404.

## 2. Runtime API i dostęp frontendu

Najważniejsze wartości:

- `LMS_BIND` — adres i port używane przez Gunicorn
- `LMS_WORKERS` — liczba workerów Gunicorn
- `LMS_THREADS` — liczba wątków na worker
- `HOMEPAGE_ORIGIN` — origin frontendu dozwolony przez CORS
- `TZ` — strefa czasowa kontenera

Obraz Dockera nie zawiera adresów IP specyficznych dla konkretnej instalacji. Adresy sieciowe należą do lokalnego pliku `.env`.

## 3. Endpointy usług

Główne endpointy modułów:

- `JELLYFIN_URL`
- `QBITTORRENT_URL`

Opcjonalne usługi używane wyłącznie do sprawdzania statusu:

- `GDRIVE_URL`
- `KUMA_URL`
- `NTFY_URL`

Jeśli URL opcjonalnej usługi statusowej jest pusty, usługa jest pomijana w `GET /api/status`.

## 4. Sekrety

Sekretów nigdy nie należy commitować do Git.

### Jellyfin

Klucz API Jellyfin jest przechowywany w lokalnym pliku.

- `JELLYFIN_API_KEY_HOST_PATH` — ścieżka na hoście
- `JELLYFIN_API_KEY_FILE` — zamontowana ścieżka wewnątrz dashboard-api

### qBittorrent

Dane logowania qBittorrent są przechowywane w:

```text
dashboard-api/secrets/qbittorrent.env
```

w postaci:

```env
QBITTORRENT_USERNAME=...
QBITTORRENT_PASSWORD=...
```

Usługa Compose wczytuje ten plik oddzielnie od zwykłej konfiguracji instalacji.

## 5. Pamięć masowa i uprawnienia

`NAS_HOST_PATH` to ścieżka do pamięci masowej na hoście.

`NAS_ROOT` wskazuje tę samą pamięć masową widzianą wewnątrz dashboard-api.

Przykład:

```env
NAS_HOST_PATH=/srv/storage/NAS
NAS_ROOT=/nas
```

Media tworzone przez LMS korzystają z centralnie skonfigurowanych właściciela i trybów uprawnień:

- `NAS_UID`
- `NAS_GID`
- `NAS_DIRECTORY_MODE`
- `NAS_FILE_MODE`

Ścieżki bibliotek mediów można nadpisać niezależnie:

- `LIBRARY_MOVIES_PATH`
- `LIBRARY_SERIES_PATH`
- `LIBRARY_ANIME_PATH`
- `LIBRARY_ANIME_MOVIES_PATH`
- `LIBRARY_DOWNLOADS_PATH`

Puste wartości bibliotek powodują użycie obecnego układu folderów Ludius MS znajdującego się pod `NAS_ROOT`.

## 6. Dane stanu aplikacji

Trwałe dane stanu LMS są montowane oddzielnie od pamięci z mediami:

- `LMS_DATA_HOST_PATH` — katalog na hoście
- `LMS_DATA_DIR` — ścieżka wewnątrz dashboard-api

Obejmują one m.in. historię aktywności, stan collectora Jellyfin oraz sesje uploadu.

Stałe implementacyjne, takie jak rozmiar fragmentu uploadu, limit historii aktywności, interwał collectora oraz obsługiwane rozszerzenia mediów, pozostają ustawieniami na poziomie aplikacji.

## Kierunek kreatora pierwszego uruchomienia

Przyszły instalator powinien generować lokalną konfigurację zamiast modyfikować pliki Pythona. Powinien zebrać ustawienia sieciowe, włączone moduły, dane logowania i endpointy usług, ścieżki pamięci masowej oraz uprawnienia; utworzyć wymagane pliki i katalogi, a następnie przed zakończeniem konfiguracji sprawdzić łączność.
