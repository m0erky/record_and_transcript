# CHANGELOG.md

## 2026-07-16 Dokumentations-Update

- Die wichtigsten Projekt-MD-Dateien wurden an den aktuellen Stand angepasst: `README.md`, `PROJECT.md`, `TASKS.md` und dieses Changelog.
- Der Projektstatus ist jetzt konsistent dokumentiert: GUI-Analyse, zentralisiertes Busy-/State-Handling, GUI-Smoke-Test und erfolgreiche Testsuite.
- Der nächste offene Schritt ist die Speaker-Control- und Sprecher-UX-Arbeit.

## 2026-07-16 Task-3-Refactor

- Recording-, Transcription- und UI-Update-Logik in `app/gui.py` wurde in kleinere Hilfsmethoden aufgeteilt.
- Wiederverwendbare Helfer kapseln jetzt das Zurücksetzen des Audio-Workflows, das Starten von Hintergrund-Workern und die Vorbereitung von Aufnahme-/Ladezuständen.
- Die GUI bleibt funktional, ist aber im Hauptfluss besser zerlegt.


## 2026-07-16 State-Refactor


- Busy-/State-Handling in `app/gui.py` wurde zentralisiert.
- `_set_busy(...)` nutzt jetzt gemeinsame Helfer fuer Widget-Zustand und Aufnahmezustand (`_set_widgets_state(...)` und `_sync_recording_controls(...)`).
- Die GUI bleibt funktional, ist aber beim Zustandshandling weniger doppelt kodiert.

## 2026-07-16 GUI-Analyse


- `app/gui.py` wurde auf Verantwortlichkeiten analysiert: Initialisierung, UI-Aufbau, Geräteverwaltung, Aufnahme, Audio-Verbesserung, Transkription, Wiedergabe, Speicherung und Zustandsteuerung liegen aktuell gemeinsam in der Hauptklasse.
- Als naechster Refactor-Schritt bietet sich eine Trennung in Zustandsverwaltung, Workflow-Logik und Anzeige-/Callback-Hilfen an.

## 2026-07-16 Sprintplanung


- Die naechste Arbeitsphase ist als Sprint in `TASKS.md` dokumentiert: GUI stabilisieren und modularisieren.
- Der Sprint fokussiert auf GUI-Struktur, Sprecher-UI, Diarisierungsbewertung und Verifikation.

## 2026-07-16 Verifikation

- `app/gui.py` ist im aktuellen Workspace syntaktisch korrekt; der zuvor dokumentierte `IndentationError` ist nicht mehr reproduzierbar.
- `python -m compileall -q record_and_transcript\main.py record_and_transcript\app record_and_transcript\core record_and_transcript\tests` wurde erfolgreich ausgefuehrt.
- `python -m unittest discover -s record_and_transcript\tests -v` wurde erfolgreich ausgefuehrt: 4 Tests bestanden.
- `tests/test_gui_smoke.py` ist vorhanden und prueft Modulimporte, ohne ein Fenster zu instanziieren.
- `PROJECT.md`, `TASKS.md`, `README.md` und `CHANGELOG.md` wurden an diesen aktuellen Status angepasst.
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

