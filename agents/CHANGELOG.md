# CHANGELOG.md

## 2026-07-16 Verifikation

- `app/gui.py` ist im aktuellen Workspace syntaktisch korrekt; der zuvor dokumentierte `IndentationError` ist nicht mehr reproduzierbar.
- `python -m compileall -q record_and_transcript\main.py record_and_transcript\app record_and_transcript\core record_and_transcript\tests` wurde erfolgreich ausgefuehrt.
- `python -m unittest discover -s record_and_transcript\tests -v` wurde erfolgreich ausgefuehrt: 4 Tests bestanden.
- GUI-Smoke-Test `tests/test_gui_smoke.py` ergaenzt.
- `PROJECT.md`, `TASKS.md` und `CHANGELOG.md` wurden an diesen aktuellen Status angepasst.
- Der GUI-Smoke-Test prueft Modulimporte und instanziiert kein Fenster.
- Die Testsuite wurde nach der Repository-Bereinigung erneut ausgefuehrt und besteht weiterhin aus 4 Tests.


## 2026-07-16 Repository-Hygiene

- Versehentlich versionierte Bytecode-Caches (`__pycache__/`, `*.pyc`) wurden aus dem Git-Index entfernt.
- `.gitignore` deckt generierte Artefakte, lokale Umgebungen und temporaere Dateien ab, damit spaetere Commits nur die relevanten Quell-, Test- und Dokumentationsdateien enthalten.
- `build/`, `dist/` und `output/` bleiben bewusst unversioniert.

Dieses Changelog dokumentiert die bisher erkannten Projektänderungen auf Basis des aktuellen Codebestands und der bereits durchgeführten Agent-Arbeit.

## Neue Features

- Lokale Whisper-Transkription über `faster-whisper` integriert.
- Optionale Sprecher-Unterscheidung hinzugefügt.
- Audioaufnahme über Mikrofon implementiert.
- Optionales Mitschneiden von System-Audio unter Windows implementiert.
- Audio-Verbesserung vor der Transkription ergänzt:
  - Normalisierung
  - Hochpassfilter
  - Rauschreduktion
- Wiedergabe mit Play/Pause/Seek/Skip implementiert.
- Wellenformanzeige für Audio integriert.
- Export von Transkripten als DOCX ergänzt.
- Session-basiertes Speichern von Rohaufnahme, verbesserter Aufnahme und Transkript ergänzt.
- Unit-Tests für die Transcriber-Logik hinzugefügt.

## Bugfixes

- Verbesserte Trennung von Speech-Regionen und Sprecherzuordnung in der Transcriber-Logik.
- Robustere Behandlung leerer oder sehr kurzer Audiobereiche in der Sprecherlogik.
- Stabilere Modellwahl und Fallback-Logik für Whisper-Modi.
- Die Transcriber-Tests decken die Kernpfade der Sprecherlogik ab.

## Refactorings

- Sprechererkennung in `core/transcriber.py` stärker in Einzelschritte zerlegt:
  - Segment-Sammlung
  - Text-Zusammenbau
  - Diarisierung
  - Speech-Region-Erkennung
  - Feature-Embedding
  - Clustering
- Datenklassen für Audio-, Transcript- und Session-Metadaten konsolidiert.
- GUI und Fachlogik sind in separate Module aufgeteilt.
- Dokumentationsbereich `agents/` für Projektstatus, Aufgaben und Agent-Regeln eingeführt.

## Aktueller Stand / bekannte Einschränkungen

- `app/gui.py` ist im aktuellen Workspace syntaktisch korrekt.
- Die restliche Kernlogik ist im Codebestand vorhanden und teilweise durch Tests abgedeckt.
- Weiterhin offen sind GUI-Refactor, Sprecherbearbeitung im UI und die Bewertung der heuristischen Sprecher-Diarisierung.

