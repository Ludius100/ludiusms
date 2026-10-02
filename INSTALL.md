# Instalacja Ludius MS — build testowy r10

> **Uwaga:** Ludius MS jest w trakcie rozwoju. Poniższa instrukcja dotyczy **wersji testowej**, a nie gotowego wydania publicznego. Instalację sprawdzono na czystej maszynie testowej z Ubuntu Server 24.04. Przed uruchomieniem na ważnym serwerze zrób kopię danych.

## 1. Wymagania

- Serwer z Ubuntu Server **24.04** (zalecany do testów). Instalator rozpoznaje też Ubuntu 22.04 i systemy z rodziny Debian, ale nie wszystkie konfiguracje zostały przetestowane.
- Dostęp do konta z uprawnieniami `sudo` i możliwość połączenia przez SSH.
- Co najmniej **2 GB RAM** i **10 GB wolnego miejsca** na dysku systemowym; na pełne środowisko wraz z systemem i aktualizacjami warto przeznaczyć więcej.
- **Oddzielny dysk na multimedia** (np. dodatkowy wolumen Oracle Cloud), widoczny w systemie jako osobne urządzenie. Jego pojemność zależy od Twojej biblioteki.
- Dostęp do internetu na serwerze, potrzebny do pobrania zależności i obrazów Dockera.

Instalator potrafi doinstalować Docker Engine i Docker Compose. Wymagania przestrzeni są orientacyjne, a nie gwarantowanym minimum dla każdej konfiguracji.

**Ważne:** w kreatorze możesz wybrać formatowanie dysku danych jako ext4. **Formatowanie bezpowrotnie usuwa istniejące dane z wybranego urządzenia.** Sprawdź nazwę i rozmiar dysku. Nie wybieraj dysku systemowego ani dysku zawierającego potrzebne pliki. Testowy instalator nie przebudowuje dysków z istniejącymi partycjami.

## 2. Przygotuj serwer

Zaloguj się na serwer przez SSH. Zaktualizuj listę pakietów i doinstaluj narzędzia potrzebne do pobrania i zbudowania paczki:

```bash
sudo apt update
sudo apt install -y git python3 curl ca-certificates util-linux
```

Sprawdź dyski i punkt montowania katalogu głównego:

```bash
lsblk -o NAME,SIZE,TYPE,FSTYPE,MOUNTPOINTS
findmnt /
```

Zapisz, które urządzenie jest **dyskiem danych**. Nazwa `/dev/sdb` jest tylko przykładem — na Twoim serwerze może być inna. Nie formatuj niczego ręcznie.

W Oracle Cloud dodatkowy wolumen musi być wcześniej utworzony i podłączony do instancji. Nie otwieraj publicznie portu kreatora `8765`; do konfiguracji użyj tunelu SSH lub prywatnego połączenia Tailscale.

## 3. Pobierz kod i zbuduj paczkę instalatora

```bash
git clone https://github.com/Ludius100/ludiusms.git
cd ludiusms
python3 installer/build_bundle.py \
  --installer-source installer \
  --api-source dashboard-api \
  --homepage-source homepage \
  --output build/ludius-ms
```

Kreator paczki przygotuje pliki aplikacji oraz sprawdzi, czy do dystrybucji nie trafiły wykryte lokalne sekrety i prywatne adresy.

Możesz dodatkowo sprawdzić integralność utworzonej paczki:

```bash
cd build/ludius-ms
sha256sum -c MANIFEST.sha256
```

Wszystkie pozycje powinny mieć status `OK`.

## 4. Uruchom graficzny instalator

Pozostając w katalogu `build/ludius-ms`, uruchom:

```bash
sudo ./install.sh --local
```

Opcja `--local` ogranicza dostęp do kreatora do `127.0.0.1:8765` na serwerze. Instalator wyświetli adres z jednorazowym tokenem w postaci:

```text
http://127.0.0.1:8765/?token=...
```

**Nie udostępniaj tokenu ani zrzutów ekranu zawierających pełny adres.** Pozostaw terminal z instalatorem uruchomiony.

Na swoim komputerze otwórz drugi terminal i zestaw tunel SSH:

```bash
ssh -N -L 8765:127.0.0.1:8765 UZYTKOWNIK@ADRES_SERWERA
```

Zastąp `UZYTKOWNIK` i `ADRES_SERWERA` danymi swojego połączenia SSH. Jeśli korzystasz z niestandardowego portu SSH, dodaj `-p NUMER_PORTU`. Następnie otwórz **pełny adres z tokenem**, który wyświetlił instalator. Nie zamykaj terminalu z tunelem podczas konfiguracji.

Alternatywnie instalator uruchomiony bez `--local` może użyć Tailscale; ta ścieżka wymaga skonfigurowania i autoryzacji dostępu do prywatnej sieci.

## 5. Przejdź przez kreator

W kreatorze:

1. Opcjonalnie wpisz imię wyświetlane w dashboardzie.
2. Sprawdź wykryty serwer i **wybierz właściwy dysk danych**. Jeszcze raz zweryfikuj urządzenie i informację o ewentualnym formatowaniu.
3. Wybierz biblioteki (Filmy, Seriale, Anime) i sposób dostępu.
4. Skonfiguruj Jellyfin i qBittorrent, jeśli chcesz z nich korzystać.
5. Przeczytaj plan operacji i dopiero wtedy potwierdź instalację.

Niektóre kroki wymagają dodatkowej interakcji, np. autoryzacji Tailscale albo konfiguracji Jellyfin. Po zakończeniu kreator wyświetli podsumowanie i dane dostępowe — zapisz je w bezpiecznym miejscu, **nie publikuj ich na GitHubie**.

## 6. Otwórz dashboard

Domyślny port dashboardu to **3000**. Przy dostępie wyłącznie przez SSH uruchom na swoim komputerze:

```bash
ssh -N -L 3000:127.0.0.1:3000 UZYTKOWNIK@ADRES_SERWERA
```

Otwórz w przeglądarce: **http://127.0.0.1:3000/**.

Jeśli wybrano dostęp przez Tailscale, użyj adresu prywatnego serwera i odpowiedniego portu. Jellyfin korzysta domyślnie z portu `8096`, a qBittorrent z `8080`, o ile zostały zainstalowane i wystawione w wybranym trybie sieciowym.

## 7. Sprawdzenie instalacji i restartu

Na serwerze możesz sprawdzić stan usług:

```bash
sudo docker compose --project-directory /opt/lms --env-file /opt/lms/.env -f /opt/lms/compose.yaml ps
curl -fsS http://127.0.0.1:3000/api/health
findmnt /srv/lms-media
systemctl status lms-storage-guard.service
```

Ścieżka `/srv/lms-media` dotyczy nowego dysku sformatowanego przez kreator. Jeśli wykorzystałeś istniejący, wcześniej zamontowany dysk, sprawdź jego rzeczywisty punkt montowania.

Po pierwszej udanej instalacji warto wykonać kontrolowany restart serwera i ponownie sprawdzić dysk, dashboard oraz dostęp Jellyfin i qBittorrenta.

## Ograniczenia wersji testowej

- Funkcje mogą być niekompletne lub zawierać błędy.
- Nie ma jeszcze gotowego, publicznego procesu aktualizacji i przywracania poprzedniej wersji.
- Czysta instalacja została sprawdzona na VM z Ubuntu 24.04; nie oznacza to przetestowania wszystkich wariantów Oracle Cloud i urządzeń.
- Do czasu oficjalnego wydania zalecamy testowanie na maszynie bez ważnych danych.

Aktualny postęp projektu opisano w [ROADMAP.md](ROADMAP.md). Zgłoszenia błędów i uwagi dotyczące instalacji są mile widziane.
