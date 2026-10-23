# Источники и воспроизводимость R1

Проверка 23.10.2026. Документация подтверждает параметры/назначение выводов, а не работоспособность конкретной собранной платы. Исторические документы и хеши сохраняются в [реестре v0.5](../research-v0.5/source-register.csv).

| Источник | Использованное основание |
|---|---|
| [Olimex ESP32-P4-DevKit manual, rev 2.1, April 2026](https://raw.githubusercontent.com/OLIMEX/ESP32-P4-DevKit/main/DOCUMENTS/ESP32-P4-DevKit-user-manual.pdf) | Модуль 72×30 мм, память, назначение разъёмов, ввод +5VP |
| [Olimex Rev.D1, официальный CAD](https://github.com/OLIMEX/ESP32-P4-DevKit/tree/main/HARDWARE/ESP32-P4-DevKit-Rev.D1) | Геометрия разъёмов, физические номера/GPIO, FET2 USB power path; upstream PCB и PDF прочитаны |
| [AD9708 datasheet](https://www.analog.com/media/en/technical-documentation/data-sheets/AD9708.pdf) | Физические выводы 28-pin, AVDD/DVDD, Rset, IOUT, clock, COMP/REF |
| [THS7314 datasheet](https://www.ti.com/lit/ds/symlink/ths7314.pdf) | 8-pin SOIC, усиление 2, 8,5 МГц LPF, смещение 285 мВ |
| [TPS54302 datasheet](https://www.ti.com/lit/ds/symlink/tps54302.pdf) | Buck, 6-pin mapping, сеть feedback/EN/BOOT и требования к компоновке |
| [TMUX1511 datasheet, SCDS390B](https://www.ti.com/lit/ds/symlink/tmux1511.pdf) | TSSOP-14 pinout, четыре SPST, signal range и ограничения powered-off isolation |
| [MCP3204/3208](https://www.microchip.com/en-us/product/MCP3204) | 12 бит, SPI, 14-pin SOIC MCP3204, VREF/AGND/DGND |
| [ESP-IDF v5.5.1 PARLIO TX](https://github.com/espressif/esp-idf/blob/v5.5.1/docs/en/api-reference/peripherals/parlio/parlio_tx.rst) | Интерфейс видеовыдачи, внешний clock и DMA; проверять ограничения на физическом P4 |
| [OPA2197](https://www.ti.com/product/OPA2197), [CD74HC4067](https://www.ti.com/product/CD74HC4067), [MCP23017](https://www.microchip.com/en-us/product/MCP23017) | Кандидаты аналогового/управляющего тракта; финальное procurement/pinout review обязательно |
| [Waveshare 2.4inch LCD Module](https://www.waveshare.com/wiki/2.4inch_LCD_Module) | Кандидат TFT; **точная аппаратная ревизия и механика не квалифицированы** |
| [KiCad footprints](https://gitlab.com/kicad/libraries/kicad-footprints) | Встроенная геометрия корпусов и координаты валов; окончательная проверка по datasheet выбранного MPN |

Для новых загруженных источников сохранён [source-hashes.csv](source-hashes.csv). PDF производителей не переиздаются в архиве проекта. Ссылки на ветку `main` могут измениться; SHA-256 фиксирует прочитанные байты, но не гарантирует сохранность удалённой версии.

Входная ёмкость 22 мкФ/35 В, дроссель SRP7028A-6R8M и ALPS-потенциометры в BOM — **кандидаты**, не утверждённые закупочные позиции. Получить datasheet дросселя с сайта Bourns в текущей сессии не удалось (HTTP 403); Isat не объявлен подтверждённым. Нельзя принять корпус библиотеки как достаточное доказательство соответствия выбранного заказа.

Системные инструменты: KiCad 9.0.2, Node.js 24.19, Chromium, C-компилятор, shared libngspice. WASM собирается wasi-sdk 25 (Clang 19.1.5); SHA-256 Linux x86_64 архива: `52640dde13599bf127a95499e61d6d640256119456d1af8897ab6725bcf3d89c`. Для первоначальной разводки использован Freerouting 2.1.0 и локальная доработка трасс; готовые PCB являются главным результатом, их не нужно заново маршрутизировать для открытия.

KiCad footprints © KiCad Community, CC BY-SA 4.0 с исключением для электронных проектов: [текст лицензии](https://www.kicad.org/libraries/license/). Исходные PCB проекта Olimex не включены в поставку VideoSynth; использованы опубликованные технические сведения. Playwright устанавливается как зависимость разработки; SDK, браузер и автороутер не включены в репозиторий.
