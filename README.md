# Ludius MS

<img width="2172" height="724" alt="Obraz ChatGPT 29 wrz 2026, 21_25_26-1" src="https://github.com/user-attachments/assets/e3a691d5-1f62-4d65-b405-ee23182c9e3e" />


**Darmowa, samodzielnie hostowana platforma prywatnego serwera multimediów, tworzona z myślą o Oracle Cloud Always Free.**

> Projekt jest w trakcie rozwoju. Obecna wersja nie jest jeszcze przeznaczona do instalacji przez innych użytkowników.

## 👋 Czym jest Ludius MS?

LMS zaczynał jako bot muzyczny na discord, jednak przez błędy weryfikacji yt-dtl, przekształciłem go w mój prywatny serwer z lostmedia. Miałem wiele filmów i seriali, które teraz ciężko znaleźć, jak np. Galactik Football, Avatar Legenda Aanga, czy Stay Alive. Zaskoczony możliwościami darmowego planu Oracle, stworzyłem centrum rozrywki : Jellyfin, klient qB, monitoring Kuna, czy nawet własną wtyczkę gDrive<>NAS. Dodatkowo denerwowało mnie to, że żeby oglądać na chromecaście musiałem folder udostępniać w sieci, a szkoda mi było kupować NAS. Tak więc postawiłem na Oracle Cloud.

## 🎯 Cel projektu

Chcę rozwinąć ten eksperyment w prostą platformę, dzięki której inni też będą mogli postawić własny prywatny serwer multimediów.

- 🆓 **Darmowe oprogramowanie** — bez wersji Premium i funkcji za paywallem
- 🏠 **Twoje media, Twój serwer** — do samodzielnego hostowania
- ☁️ **Oracle Cloud Always Free** — główna platforma docelowa, w przyszłości planuję dodać bare-metal
- 🎬 **Media w jednym miejscu** — filmy, seriale, anime i inne zbiory
- 🧩 **Prosta obsługa** — docelowo minimum grzebania w terminalu
- ❤️ **Projekt dla frajdy i społeczności**

## 🚧 Aktualny stan

Bardzo wczesny etap. Serwer powstał najpierw na własne potrzeby — teraz porządkuję kod i architekturę, usuwam rozwiązania „na szybko" i przygotowuję projekt pod bezpieczną instalację na czystej instancji Oracle Cloud.

Pierwszy cel: wydanie **Ludius MS 0.1**, czyli pierwsza, działająca wersja z prostym instalatorem. Do tego czasu możliwe są duże zmiany i niedokończone funkcje.

Aktualnie rozwijany jest **LMS Installer** — webowy kreator pierwszego uruchomienia. Wykrywa host, storage i dostępne usługi, pozwala wybrać biblioteki i sposób dostępu, buduje plan instalacji oraz prowadzi przez wymagane interakcje. Kod zawiera też testy i privacy scan; pierwsze wykonanie pełnej instalacji będzie sprawdzane na czystej, jednorazowej instancji testowej.
**LMS Installer** planuje zrobić prosty i przejrzysty możliwie jak Tylko będę mógł. Wiem, ile czasu poświęciłem wraz z Chatem GPT na stworzenie kawałek po kawałku kodu sphagetti, więc nie chcę zrazić kogoś do projektu, tylko ze względu na mniejsze doświadczenie.

**Jeśli chcesz dołączyć i przetestować projekt, skontaktuj się ze mną.**


## 💡 Dlaczego to robię?

Zaczęło się od „postawię sobie bota na Discorda", potem „w sumie mam tu trochę miejsca, zrobię NAS", a skończyło na „chyba piszę własną platformę do serwera multimediów". ¯\\_(ツ)_/¯
Zawsze szybko łapałem bakcyla na takie projekty, ale mój słomiany zapał szybko je kończył. Tym razem, bogatszy o doświadczenie i chęci, postanowiłem postawić od A do Z. Nawet przy zerowym zainsteresowaniu, zamierzam bardziej, lub mniej ulepszać projekt.

---

**Support development when you can. Enjoy it anyway when you want.**
