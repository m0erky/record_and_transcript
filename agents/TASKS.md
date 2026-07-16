# TASKS.md

## Offene Aufgaben

- GUI-Refactor abschließen und in kleinere, testbare Bereiche aufteilen.
- Sprecherbearbeitung im UI ergänzen oder zumindest konzeptionell sauber vorbereiten.
- Prüfen, ob heuristische Sprecher-Diarisierung für Zielanwender ausreichend ist oder ob ein dediziertes Modell nötig wird.

## In Bearbeitung

- Keine aktuell.

## Erledigt

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

- Falls der GUI-Smoke-Test oben noch als offen aufgefuehrt ist, ist diese Zeile ueberholt: `tests/test_gui_smoke.py` ist vorhanden und die Testsuite laeuft mit 4 bestandenen Tests.

