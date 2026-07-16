# TASKS.md

## Kurzstatus

- Task 1 ist abgeschlossen: `app/gui.py` wurde analysiert und die großen Verantwortlichkeiten sind markiert.
- Task 2 ist abgeschlossen: Busy-/State-Handling ist zentralisiert.
- Die aktuelle Testsuite und der GUI-Smoke-Test laufen erfolgreich.
- Task 3 ist abgeschlossen: Recording-, Transcription- und UI-Update-Logik sind in Hilfsmethoden zerlegt.
- Nächster Fokus: Speaker-Control-Logik, Sprecher-UX und Diarisierungsbewertung.


## Nächster Sprint: GUI stabilisieren und modularisieren


### Sprint-Ziel
Die GUI soll in klarere, testbare Einheiten zerlegt werden, ohne die bestehende Kernlogik zu destabilisieren.

### Aufgaben

- [x] `app/gui.py` analysieren und große Verantwortlichkeiten markieren.

- [x] Busy-/State-Handling zentralisieren und aus dem Hauptfluss trennen.

- [x] Recording-, Transcription- und UI-Update-Logik in kleinere Hilfsmethoden aufteilen.

- [ ] Speaker-Control-Logik sauber von der restlichen GUI-Logik abgrenzen.
- [ ] Konzeption für Sprecherbearbeitung im UI festlegen:
  - [ ] Anzeige
  - [ ] Umbenennung
  - [ ] Zusammenführen
  - [ ] manuelle Korrektur
- [ ] Heuristische Sprecher-Diarisierung fachlich bewerten und dokumentieren.
- [x] GUI-Smoke-Test und Transcriber-Tests nach Änderungen ausführen.

- [x] `compileall` bzw. Importprüfung zur Verifikation ausführen.

- [x] `PROJECT.md`, `CHANGELOG.md` und `TASKS.md` nach Abschluss aktualisieren.


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
- Busy-/State-Handling ist jetzt teilweise zentralisiert über `_set_busy(...)`, `_sync_recording_controls(...)` und `_set_widgets_state(...)`.
- Recording-, Transcription- und Lade-Workflows sind in kleinere Hilfsmethoden aufgeteilt.


- Einstiegspunkt vorhanden: `main.py` startet die GUI.

- Audioaufnahme, Audioverbesserung, Wiedergabe und Storage sind im Kern implementiert.
- Lokale Whisper-Transkription ist integriert.
- Optionale Sprecher-Unterscheidung ist implementiert.
- Unit-Tests für die Transcriber-Logik sind vorhanden.
- Verzeichnisstruktur des Projekts analysiert.
- `app/gui.py` ist im aktuellen Workspace wieder syntaktisch korrekt; `python -m compileall` laeuft erfolgreich.
- GUI-Smoke-Test `tests/test_gui_smoke.py` ergaenzt; GUI- und Einstiegspunktmodule werden importgeprueft.
- Build-/Artefaktpflege geklärt: `build/`, `dist/` und andere generierte Artefakte bleiben unversioniert.
- Git-Hygiene hergestellt: versehentlich versionierte Bytecode-Caches (`__pycache__/`, `*.pyc`) wurden aus dem Git-Index entfernt.
- Dokumentation des aktuellen Projektzustands in `PROJECT.md`, `TASKS.md`, `CHANGELOG.md` und `AGENT_RULES.md` aktualisiert.
- Bewertung der aktuellen Architektur und der vorhandenen technischen Schulden durchgeführt.

## Statuskorrektur 2026-07-16

- `tests/test_gui_smoke.py` ist vorhanden und die Testsuite laeuft mit 4 bestandenen Tests.
- Task 2 und Task 3 können als erledigt betrachtet werden; die naechste Arbeit liegt bei Speaker-Control, Sprecher-UX und Diarisierungsbewertung.



