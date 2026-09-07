# HOWTO: Lokale Entwicklungsumgebung einrichten

Dieses Dokument beschreibt die Einrichtung und Nutzung der lokalen Entwicklungsumgebung für das Projekt `xiao-flasher` (Seeed Studio XIAO-RP2040 Firmware Flasher).

---

## 1. Voraussetzungen

Vor Beginn der Einrichtung stellen Sie bitte sicher, dass folgende Softwarekomponenten installiert sind:

* **Python**: Version 3.10 oder neuer (`python3 --version`)
* **pip**: Aktuelle Version des Python Package Installers (`python3 -m pip --version`)
* **Bash**: Eine kompatible Shell (Linux, macOS, oder WSL/Git Bash unter Windows)
* **Git**: Für die Versionsverwaltung

---

## 2. Installation der Abhängigkeiten

Das Projekt stellt zweckgebundene Installationsskripte bereit, um Laufzeit- und Test-Abhängigkeiten getrennt und reproduzierbar zu installieren.

### 2.1 Laufzeitumgebung installieren

Installiert das `xiao-flasher` Paket sowie alle erforderlichen Laufzeit-Abhängigkeiten (`click`, `pyserial`, `psutil`, `pyusb`) im bearbeitbaren Modus (*editable mode*):

```bash
./src/install.sh
```

### 2.2 Testumgebung installieren

Installiert alle Werkzeuge für Tests und statische Code-Analyse (`pytest`, `pytest-cov`, `mypy`, `ruff`):

```bash
./test/install.sh
```

---

## 3. Lokale Entwicklung & Qualitätskontrolle

Nach erfolgreicher Installation stehen folgende Befehle für die Entwicklung und Qualitätssicherung zur Verfügung:

### 3.1 Unit-Tests ausführen

Führt die Testsuite mit `pytest` aus:

```bash
python3 -m pytest
```

### 3.2 Linter ausführen (Ruff)

Prüft den Quellcode auf Stil- und Syntaxfehler:

```bash
ruff check .
```

### 3.3 Typenprüfung ausführen (Mypy)

Führt eine statische Typenprüfung des Quellcodes im Ordner `src/` durch:

```bash
mypy src
```

---

## 4. CLI Verwendung

Nach Ausführung von `./src/install.sh` ist die CLI-Anwendung `xiao-flash` im System / in der Python-Umgebung registriert.

Hilfeanzeige aufrufen:

```bash
xiao-flash --help
```

---

## 5. Projektstruktur Übersicht

* `src/xiao_flasher/`: Hauptcodebasis der Python-Bibliothek und CLI
* `src/install.sh`: Installationsskript für Laufzeit-Abhängigkeiten
* `test/`: Testsuite und Testinfrastruktur
* `test/install.sh`: Installationsskript für Testwerkzeuge
* `pyproject.toml`: Zentrale Projekt- und Werkzeugkonfiguration
* `DESIGN.md`: Detaillierter Architekturentwurf und technische Entscheidungen
* `ROADMAP.md`: Projektfortschritt und Phasenplanung
* `TECHNICAL_DEBTS.md`: Erfasste technische Schulden
