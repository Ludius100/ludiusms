# Ludius MS — Roadmap

> **Private Media Server for Oracle Cloud**

Roadmapa przedstawia planowany kierunek rozwoju projektu. Kolejność i zakres mogą zmieniać się wraz z testami i opiniami użytkowników.

## 🧪 0.1 — Pierwszy działający publiczny build
**Cel: 17.10.2026**

Pierwsza wersja możliwa do samodzielnego zainstalowania na czystej instancji Oracle Cloud.

- ~~refaktor i uporządkowanie Core~~
- ~~bootstrap installer~~
- ~~Web Setup pierwszego uruchomienia~~
- ~~konfiguracja storage i Tailscale~~
- ~~prosty / zaawansowany kreator Jellyfin~~
- ~~Dashboard~~
- ~~qBittorrent~~
- ~~lokalny upload mediów~~
- ~~tworzenie graficznego instalatora na platformie Oracle Cloud w formie WEB~~
- ~~testy instalatora na czystej instancji Oracle~~
- **testy zewnętrznych użytkowników**

## 🔧 0.2 — Poprawa stabilności

Stabilizacja po pierwszym publicznym wydaniu.

- poprawki zgłoszonych błędów
- ulepszenia instalatora i Web Setup
- niezawodne wznawianie transferów
- lepsza obsługa błędów
- aktualizacje, backup i rollback

## 🖼 0.3 - Poprawki UX

Stworzenie obsługi motywów, personalizacji
- poprawki i ulepszenie obecnego UX
- dodanie motywów
- integracja systemu wg spójności motywów

## 📊 0.4 — Diagnostics

Narzędzia do zarządzania i diagnozowania serwera.

- logi usług
- historia CPU / RAM / storage
- top procesów
- status kontenerów i usług
- Diagnostic Report
- automatyczne usuwanie sekretów z raportów

## ☁️ 0.5 — Google Drive

Właściwa integracja Google Drive zastępująca obecny prototyp.

- OAuth 2.0
- Drive → NAS / NAS → Drive
- przeglądanie plików
- integracja z Transfer Managerem

## 🖥️ 0.6 — Ludius Desktop

Opcjonalny klient ułatwiający dostęp do serwera.

- Windows jako pierwsza platforma
- konfiguracja Tailscale
- wykrywanie Ludius MS
- Transfer Manager Agent
- skróty do Dashboardu i NAS
- później status serwera i transferów

## 🧩 0.7 — LudiusAPI

Stabilny interfejs pomiędzy Core a rozszerzeniami.

- Storage
- Media
- Transfers
- Services
- Notifications
- System

Fundament przyszłego systemu modułów.

## 🧱 0.8 — Modules

Pierwsza wersja architektury modułowej.

- manifest modułu
- zależności i uprawnienia
- instalacja / usuwanie modułów
- oficjalne i społecznościowe rozszerzenia
- Core niezależny od opcjonalnych integracji

## 🧪 0.9 — LudiusLab

Repozytorium modułów Ludius MS.

- Official Modules
- Community Modules
- instalacja z Dashboardu
- informacje o autorze i uprawnieniach
- dobrowolne wsparcie twórców bez paywalli

## 🧹 0.9.X Preparation

Ostatni etap generacji 0.x.

- stabilizacja API i modułów
- analiza doświadczeń użytkowników
- porządki architektoniczne
- określenie założeń drugiej generacji

## 🚀 1.0 — Official LMS 1.0

Nowa, zoptymalizowana architektura oparta na doświadczeniach zdobytych podczas całej serii `0.x`.

Nie zakładamy, że rozwiązania stworzone podczas prototypowania muszą zostać z nami na zawsze.

### ❤️ Philosophy

Ludius MS pozostaje darmowy i dostępny dla wszystkich.

**No Premium. No Pro. No subscriptions. No ads.**

> **Support development when you can. Enjoy it anyway when you want.**
