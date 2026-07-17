# TASKS.md

## Kurzstatus

- Task 1 ist abgeschlossen: `app/gui.py` wurde analysiert und die großen Verantwortlichkeiten sind markiert.
- Task 2 ist abgeschlossen: Busy-/State-Handling ist zentralisiert.
- Die aktuelle Testsuite und der GUI-Smoke-Test laufen erfolgreich; die Suite umfasst jetzt 9 Tests.

- Task 3 ist abgeschlossen: Recording-, Transcription- und UI-Update-Logik sind in Hilfsmethoden zerlegt.
- Task 4 ist syntaktisch bereinigt und verifiziert; die konzeptionelle Sprecherbearbeitung bleibt offen.
- Nächster Fokus: Sprecher-UX konzipieren und heuristische Diarisierung bewerten.
- CUDA-Diagnose für die Transkription ist umgesetzt; in der GUI gibt es zusätzlich einen CUDA-Diagnose-Dialog mit Modelltest.
- Die Transkription selbst meldet den tatsächlich verwendeten Rechenmodus in der GUI-Statuszeile; es gibt aktuell kein separates Logfile.
- Auf Windows werden CUDA-DLL-Verzeichnisse vor Whisper-Aufrufen automatisch registriert, damit Laufzeitbibliotheken wie `cublas64_12.dll` gefunden werden.
- CUDA-Laufzeitfehler werden im Standarddialog mit der echten Backend-Exception angezeigt, damit die Ursache direkt sichtbar ist.










## Nächster Sprint: Sprecher-UX konzipieren und Diarisierung bewerten


### Sprint-Ziel
Die Sprecherbearbeitung soll im UI klar beschrieben werden, bevor weitere GUI-Refactors durchgeführt werden.

### Aufgaben

- [x] `app/gui.py` analysieren und große Verantwortlichkeiten markieren.

- [x] Busy-/State-Handling zentralisieren und aus dem Hauptfluss trennen.

- [x] Recording-, Transcription- und UI-Update-Logik in kleinere Hilfsmethoden aufteilen.

- [ ] Speaker-Control-Logik sauber von der restlichen GUI-Logik abgrenzen.
- [x] Den aktuellen Speaker-Control-Refactor syntaktisch bereinigen und erneut verifizieren.
- [ ] Konzeption für Sprecherbearbeitung im UI festlegen:
  - [ ] Anzeige
  - [ ] Umbenennung
  - [ ] Zusammenführen
  - [ ] manuelle Korrektur
- [ ] Heuristische Sprecher-Diarisierung fachlich bewerten und dokumentieren.
- [x] GUI-Smoke-Test und Transcriber-Tests nach Änderungen ausführen.
- [x] `compileall` bzw. Importprüfung zur Verifikation ausführen.
- [x] `PROJECT.md`, `CHANGELOG.md` und `TASKS.md` nach Abschluss aktualisieren.
- [x] CUDA-Diagnose-Dialog in der GUI implementieren und verifizieren.
- [x] CUDA-Diagnose für die Transkription implementieren.
- [x] Aktive Whisper-Gerätelogik in der GUI-Statuszeile sichtbar machen.
- [x] Kein separates Logfile einführen; Status- und Fehlerausgabe bleiben GUI-basiert.
- [x] CUDA-/Whisper-Fehlerdialoge so anpassen, dass die echte Backend-Exception angezeigt wird.
- [x] CUDA-DLL-Suchpfade unter Windows automatisch registrieren, damit typische Laufzeitbibliotheken gefunden werden.








### Definition of Done
- `app/gui.py` ist übersichtlicher und besser strukturiert.
- Die wichtigsten GUI-Verantwortlichkeiten sind getrennt.
- Die Sprecher-UX ist konzeptionell sauber beschrieben.
- Die Diarisierungsstrategie ist bewertet.
- Tests und Importprüfung laufen erfolgreich.
- Die Dokumentation ist aktuell.

## Offene Aufgaben

- GUI-Refactor abschließen und in kleinere, testbare Bereiche aufteilen.
- Sprecherbearbeitung im UI ergänzen oder zumindest konzeptionell sauber vorbereiten.
- Prüfen, ob heuristische Sprecher-Diarisierung für Zielanwender ausreichend ist oder ob ein dediziertes Modell nötig wird.


## In Bearbeitung


- Keine aktuell.

## Erledigt

- GUI-Analyse abgeschlossen: `app/gui.py` bündelt aktuell Initialisierung, UI-Aufbau, Aufnahme, Transkription, Wiedergabe, Speicherlogik und Zustandsteuerung.
- Busy-/State-Handling ist jetzt zentralisiert über `_set_busy(...)`, `_sync_recording_controls(...)` und `_set_widgets_state(...)`.
- Recording-, Transcription- und Lade-Workflows sind in kleinere Hilfsmethoden aufgeteilt.
- Einstiegspunkt vorhanden: `main.py` startet die GUI.
- Audioaufnahme, Audioverbesserung, Wiedergabe und Storage sind im Kern implementiert.
- Lokale Whisper-Transkription ist integriert.
- Optionale Sprecher-Unterscheidung ist implementiert.
- Unit-Tests für die Transcriber-Logik sind vorhanden.
- Verzeichnisstruktur des Projekts analysiert.
- `app/gui.py` ist im aktuellen Workspace syntaktisch korrekt; `python -m compileall` und `python -m unittest discover -s record_and_transcript\tests -v` laufen erfolgreich.
- `tests/test_gui_smoke.py` ist vorhanden und importgeprüft `app.gui` sowie `main`, ohne ein GUI-Fenster zu instanziieren.
- Der Speaker-Control-Refactor ist syntaktisch bereinigt und verifiziert; die Sprecher-UX-Arbeit bleibt als nächster konzeptioneller Schritt offen.
- CUDA wird in der GUI anhand der GPU-Erkennung angeboten; die Diagnose selbst prüft zusätzlich einen echten Whisper-Modelltest.
- Die Transkription meldet den aktiven Rechenmodus über `on_progress(...)` an die GUI, damit CUDA-Nutzung nachvollziehbar bleibt.



- Build-/Artefaktpflege geklärt: `build/`, `dist/` und andere generierte Artefakte bleiben unversioniert.
- Git-Hygiene hergestellt: versehentlich versionierte Bytecode-Caches (`__pycache__/`, `*.pyc`) wurden aus dem Git-Index entfernt.
- Dokumentation des aktuellen Projektzustands in `PROJECT.md`, `README.md`, `TASKS.md`, `CHANGELOG.md` und `AGENT_RULES.md` aktualisiert.
- Bewertung der aktuellen Architektur und der vorhandenen technischen Schulden durchgeführt.

## Statuskorrektur 2026-07-16

- `tests/test_gui_smoke.py` ist vorhanden und die Testsuite läuft mit 5 bestandenen Tests.
- Task 2 und Task 3 sind erledigt; der nächste fachliche Schritt ist die Sprecher-UX und die Bewertung der heuristischen Diarisierung.
- Der Speaker-Control-Refactor ist syntaktisch bereinigt und verifiziert.
- CUDA-Fehler auf Windows werden jetzt über den realen Modelltest und die App-Umgebung diagnostiziert, statt über eine reine WinDLL-Prüfung.
- Die eigentliche Transkription nutzt den von Whisper verwendeten Modus direkt und macht ihn über Statusmeldungen sichtbar.
- CUDA-/Whisper-Fehlerdialoge zeigen die echte Exception, damit die Ursache nicht hinter einer generischen Meldung verborgen bleibt.
- CUDA-DLL-Suchpfade werden unter Windows automatisch registriert, um Laufzeitbibliotheken wie `cublas64_12.dll` auffindbar zu machen.













