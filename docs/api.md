# API LMS

Ludius MS udostępnia backend przez HTTP API w formacie JSON pod ścieżką `/api`.

API nadal należy do linii rozwojowej 0.x. Podczas refaktorów zachowywane jest obecne działanie frontendu, ale publiczny kontrakt API nie jest jeszcze zamrożony.

## Wykrywanie możliwości

### GET /api/health

Podstawowe sprawdzenie stanu procesu.

Przykładowa odpowiedź:

```json
{
  "status": "ok"
}
```

### GET /api/modules

Zwraca moduły znane tej wersji LMS oraz informację, czy są włączone.

Przykład:

```json
{
  "modules": {
    "jellyfin": {
      "name": "Jellyfin",
      "enabled": true,
      "apiPrefix": "/api/jellyfin"
    },
    "qbittorrent": {
      "name": "qBittorrent",
      "enabled": true,
      "apiPrefix": "/api/qbittorrent"
    }
  }
}
```

Wyłączony moduł pozostaje widoczny w tym manifeście z `enabled: false`, ale jego routes nie są rejestrowane.

## Podstawowe API

| Metoda | Ścieżka | Przeznaczenie |
| --- | --- | --- |
| GET | `/api/activity?limit=20` | Ostatnia aktywność LMS. Limit jest ograniczany do zakresu 1-100. |
| GET | `/api/system` | Podsumowanie CPU, RAM, pamięci masowej i uptime. |
| GET | `/api/status` | Dostępność i opóźnienie skonfigurowanych usług. |
| GET | `/api/modules` | Manifest modułów. |
| GET | `/api/health` | Podstawowe sprawdzenie stanu. |

Opcjonalne usługi statusowe bez skonfigurowanego URL są pomijane w `/api/status`.

## Moduł Jellyfin

Poniższy route istnieje tylko wtedy, gdy moduł Jellyfin jest włączony.

### GET /api/jellyfin

Zwraca podsumowanie dashboardu LMS zbudowane na podstawie liczników i sesji Jellyfin.

Obecne pola obejmują:

- `online`
- `movies`
- `series`
- `episodes`
- `songs`
- `activeSessions`

Niedostępny backend Jellyfin powoduje zwrócenie HTTP 503 z `online: false`.

## Moduł qBittorrent

Poniższe routes istnieją tylko wtedy, gdy moduł qBittorrent jest włączony.

| Metoda | Ścieżka | Przeznaczenie |
| --- | --- | --- |
| GET | `/api/qbittorrent` | Dane dashboardu/statusu qBittorrent. |
| GET | `/api/qbittorrent/libraries` | Dostępne miejsca docelowe pobierania. |
| POST | `/api/qbittorrent/add` | Przygotowuje magnet i zwraca informacje o torrencie/plikach. |
| POST | `/api/qbittorrent/start` | Uruchamia przygotowany torrent z wybranymi indeksami plików. |

Żądanie przygotowania:

```json
{
  "magnet": "magnet:?xt=...",
  "library": "downloads"
}
```

Żądanie uruchomienia:

```json
{
  "hash": "torrent-hash",
  "selected": [0, 1, 4]
}
```

Przepływ prepare/start celowo oddziela sprawdzenie metadanych od operacji, która faktycznie rozpoczyna pobieranie.

## API mediów

### GET /api/media/titles

Parametry zapytania:

- `library` — jeden ze skonfigurowanych identyfikatorów lokalnych bibliotek mediów

Zwraca foldery tytułów znalezione w danej bibliotece.

### GET /api/media/last-episode

Parametry zapytania:

- `library`
- `title`
- `season` (domyślnie 1)

Frontend używa tego endpointu do ustalenia najnowszego istniejącego odcinka dla serialu lub anime.

### POST /api/media/plan

Buduje plan operacji na systemie plików bez przenoszenia ani przesyłania plików.

Najczęściej używane pola:

- `type` — `movie` lub `series`
- `library`
- `title`
- `files` — tablica obiektów plików zawierających co najmniej `name`; akceptowane jest również `size`

Plany filmów mogą zawierać `year`.

Plany seriali mogą zawierać `season` oraz `firstEpisode`. Poszczególne pliki mogą nadpisywać `season` i `episode`.

Wyniki planera obejmują bibliotekę docelową, zaplanowane elementy, konflikty/sprawdzenia, flagę `ready` oraz reprezentację drzewa dla frontendu.

Planner sam nie wykonuje końcowego zapisu.

## API uploadu fragmentami

Duże pliki przesyłane z przeglądarki korzystają ze wznawialnych sesji po stronie serwera.

### POST /api/media/upload/init

Tworzy sesję uploadu.

Przykładowe żądanie:

```json
{
  "library": "movies",
  "folder": "Example (2026)",
  "originalName": "example.mkv",
  "targetName": "Example (2026).mkv",
  "size": 123456789
}
```

Zwraca HTTP 201 wraz z `uploadId`, oczekiwanym rozmiarem, aktualną liczbą odebranych bajtów i maksymalnym rozmiarem fragmentu.

### GET /api/media/upload/<upload_id>

Zwraca aktualny stan sesji. Klient może użyć wartości `received` jako offsetu przy wznawianiu.

### POST /api/media/upload/<upload_id>/chunk

Przesyła kolejny binarny fragment.

Wymagany nagłówek:

```text
X-Upload-Offset: <current server offset>
```

Serwer odrzuca offset, który nie odpowiada aktualnemu rozmiarowi pliku po jego stronie.

### POST /api/media/upload/<upload_id>/finalize

Finalizuje kompletny upload i przenosi plik do zaplanowanego miejsca docelowego.

### DELETE /api/media/upload/<upload_id>

Anuluje sesję i usuwa jej częściowo przesłany plik ze stagingu.

### POST /api/media/upload

Awaryjny/testowy uploader małych plików korzystający z `multipart/form-data`.

Obecne pola formularza:

- `file`
- `library`
- `folder`
- `targetName`

## Błędy

Błędy walidacji domenowej zazwyczaj zwracają status 4xx z odpowiedzią JSON zawierającą:

```json
{
  "ok": false,
  "error": "..."
}
```

Konflikty, takie jak już istniejący element docelowy, mogą zwracać HTTP 409.

Nieoczekiwane błędy backendu zwykle zwracają HTTP 500 lub 503, zależnie od endpointu.

## CORS i cache

API globalnie stosuje skonfigurowaną wartość `HOMEPAGE_ORIGIN`.

Obecnie dozwolone metody:

```text
GET, POST, DELETE, OPTIONS
```

Obecnie dozwolone nagłówki żądań:

```text
Content-Type, X-Upload-Offset
```

Odpowiedzi API wysyłają obecnie `Cache-Control: no-store`.

## Obecne grupy routes

Aplikacja Flask jest składana z Blueprintów:

- core
- media
- moduł Jellyfin
- moduł qBittorrent

Rejestr modułów decyduje, które opcjonalne Blueprinty modułów oraz collectory działające w tle są ładowane.
