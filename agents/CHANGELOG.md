# CHANGELOG.md

## 2026-07-21

### Modularisierung und Backend-Konfiguration

- Die gesamte Transkriptions-Architektur wurde von `core/backends/` nach `app/backends/` verschoben; dort beherbergen `base.py`, die konkreten Backends und die Factory nun die Schnittstelle und Implementierungen.
- `app/backends/base.py` definiert die `TranscriptionBackend`-Schnittstelle samt Datentypen, das Backend-Interface selbst wurde um `initialize`, `supports_*` und `cleanup` erweitert.
- `app/settings.py` speichert die gewünschte Backend-Auswahl im Nutzerordner, die GUI bietet eine Option zur Laufzeitwahl und lädt die Konfiguration beim Start.
- `WhisperCppBackend`, `OpenAIBackend` und `AzureOpenAIBackend` liefern vorbereitete Stubs; `FasterWhisperBackend` ist auf die neue Struktur angepasst und bietet weiterhin CUDA-Diagnose sowie Diarisierung.
- Die Tests wurden auf die neuen Pfade angepasst, und die GUI greift ausschließlich über das Interface auf die Backends zu.

## 2026-07-20

### Modularisierung der Transkriptions-Backends

- Die bisher monolithische `core/transcriber.py` wurde aufgelöst. Stattdessen bieten `core/transcription.py` und das Verzeichnis `core/backends/` eine gemeinsame Schnittstelle plus konkrete Backends.
- `FasterWhisperBackend` verwaltet weiterhin die Whisper-Logik sowie CUDA-Diagnosen, lebt aber jetzt in einem dedizierten Backend-Modul.
- `TranscriptionBackendFactory` ermöglicht die Auswahl eines Backends über Konfiguration, während die GUI und Business-Logik nur die gemeinsame Schnittstelle nutzen.
- Stubs für `WhisperCppBackend`, `OpenAIBackend` und `AzureOpenAIBackend` wurden ergänzt, um zukünftige Erweiterungen vorzubereiten.
- Die GUI importiert nun die Factory und nutzt deren Standard-Backend; Tests wurden entsprechend auf `FasterWhisperBackend` aktualisiert.

## 2026-07-17

### CUDA-Transkriptionslogging

- Die Whisper-Transkription meldet den tatsächlich verwendeten Rechenmodus über `on_progress(...)` an die GUI-Statuszeile.
- Die App verwendet keinen separaten Logfile-Workflow für Transkriptionsstatus.
- Fehler werden direkt an die Oberfläche gemeldet; CUDA-/Whisper-Exceptions bleiben sichtbar.
- Unter Windows werden CUDA-DLL-Verzeichnisse aus typischen Installationspfaden und Prozessvariablen automatisch registriert.
- `python -m compileall record_and_transcript` wurde erfolgreich ausgeführt.
- `python -m unittest discover -s record_and_transcript\tests -v` wurde erfolgreich ausgeführt: 10 Tests bestanden.

### CUDA-Diagnose-Dialog
- In `app/gui.py` existiert ein modaler CUDA-Diagnose-Dialog mit Runtime-Details und Kopierfunktion.
- Der Dialog zeigt CTranslate2-Status, GPU-Anzahl, relevante PATH-Einträge und einen echten Whisper-Modelltest im App-Kontext an.

## 2026-07-16

### GUI-Syntax-Cleanup
- `app/gui.py` wurde syntaktisch bereinigt.
- `python -m compileall -q record_and_transcript\main.py record_and_transcript\app record_and_transcript\core record_and_transcript\tests` wurde erfolgreich ausgeführt.
- `python -m unittest discover -s record_and_transcript\tests -v` wurde erfolgreich ausgeführt: 4 Tests bestanden.

### Dokumentations-Synchronisation
- `README.md`, `PROJECT.md`, `TASKS.md` und `CHANGELOG.md` wurden an den verifizierten Stand angepasst.

### Speaker-Control-Start
- Die Speaker-Control-Logik wurde als nächste Refactor-Richtung identifiziert und syntaktisch bereinigt.
- Die Abgrenzung von Speaker-Settings und Sprecher-Metadaten ist umgesetzt.

### Task-3-Refactor
- Recording-, Transcription- und UI-Update-Logik in `app/gui.py` wurde in kleinere Hilfsmethoden aufgeteilt.

### State-Refactor
- Busy-/State-Handling in `app/gui.py` wurde zentralisiert.
- `_set_busy(...)` verwendet gemeinsame Helfer für Widget-Zustand und Aufnahmezustand.

### GUI-Analyse
- `app/gui.py` wurde als zentraler Orchestrator der Anwendung analysiert.
- Als nächster Refactor-Schritt wurde eine Trennung in Zustandsverwaltung, Workflow-Logik und Anzeige-/Callback-Hilfen identifiziert.

### Sprintplanung
- Der nächste größere Arbeitsschritt wurde als Sprint in `TASKS.md` festgehalten: Sprecher-UX konzipieren und Diarisierung bewerten.

### Verifikation
- `app/gui.py` ist syntaktisch korrekt.
- `python -m compileall` und `python -m unittest discover -s record_and_transcript\tests -v` liefen erfolgreich.
- `tests/test_gui_smoke.py` prüft Modulimporte ohne Fenster.

### Repository-Hygiene
- Versehentlich versionierte Bytecode-Caches wurden aus dem Git-Index entfernt.
- `.gitignore` deckt generierte Artefakte, lokale Umgebungen und temporäre Dateien ab.
- `build/`, `dist/` und `output/` bleiben unversioniert.

### CUDA-Preflight
- Die CUDA-Diagnose wurde auf einen echten Whisper/CTranslate2-Modelltest umgestellt.
- Relevante PATH-Einträge aus dem App-Prozess werden angezeigt.
- Die Transkription meldet den aktiven Rechenmodus über die GUI-Statuszeile.

## Projekt-Historie in Kurzform

- Lokale Whisper-Transkription über `faster-whisper` integriert.
- Optionale Sprecher-Unterscheidung hinzugefügt.
- Audioaufnahme, System-Audio-Mitschnitt, Audio-Verbesserung, Wiedergabe, Wellenformanzeige und DOCX-Export ergänzt.
- Session-basiertes Speichern von Rohaufnahme, verbesserter Aufnahme und Transkript ergänzt.
- Unit-Tests für die Transcriber-Logik hinzugefügt.
- Sprechererkennung, Segment-Verarbeitung, Clustering und Modellverwaltung in `core/transcriber.py` strukturiert.
- GUI und Fachlogik in separate Module aufgeteilt.
- Dokumentationsbereich `agents/` für Projektstatus, Aufgaben und Regeln eingeführt.

## Aktuelle Einschränkungen / offene Punkte

- Sprecherbearbeitung im UI ist noch offen.
- Die heuristische Sprecher-Diarisierung ist noch nicht fachlich abschließend bewertet.
- CUDA-Fehler auf Windows werden nun vor der Modellinitialisierung transparent gemeldet, wenn Laufzeit-DLLs fehlen.





