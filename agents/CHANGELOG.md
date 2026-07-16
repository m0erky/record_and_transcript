# CHANGELOG.md

## 2026-07-16 GUI-Syntax-Cleanup

- `app/gui.py` wurde syntaktisch bereinigt und die Speaker-Control-Hilfsmethoden bleiben konsistent eingebettet.
- `python -m compileall -q record_and_transcript\main.py record_and_transcript\app record_and_transcript\core record_and_transcript\tests` wurde erfolgreich ausgeführt.
- `python -m unittest discover -s record_and_transcript\tests -v` wurde erfolgreich ausgeführt: 4 Tests bestanden.
- Die aktuelle Dokumentation wurde an den verifizierten Stand angepasst.

## 2026-07-16 Dokumentations-Synchronisation

- Die wichtigsten Projekt-MD-Dateien wurden an den verifizierten Stand angepasst: `README.md`, `PROJECT.md`, `TASKS.md` und dieses Changelog.
- Der Projektstatus ist jetzt konsistent dokumentiert: GUI-Analyse, zentralisiertes Busy-/State-Handling, verifizierter Speaker-Control-Refactor und offene Sprecher-UX.
- Der nächste offene Schritt ist die konzeptionelle Sprecher-UX und die fachliche Bewertung der heuristischen Diarisierung.



## 2026-07-16 Speaker-Control-Start

- Die Speaker-Control-Logik wurde als nächste Refactor-Richtung identifiziert und syntaktisch bereinigt.
- Die Abgrenzung von Speaker-Settings und Sprecher-Metadaten ist umgesetzt.
- Der nächste inhaltliche Schritt liegt bei Sprecher-UX und Diarisierungsbewertung.



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

- Die nächste Arbeitsphase ist als Sprint in `TASKS.md` dokumentiert: Sprecher-UX konzipieren und Diarisierung bewerten.
- Der Sprint fokussiert auf Sprecherbearbeitung im UI, heuristische Diarisierung und Verifikation.


## 2026-07-16 Verifikation

- `app/gui.py` ist im aktuellen Workspace syntaktisch korrekt; der zuvor dokumentierte `IndentationError` ist nicht mehr reproduzierbar.
- `python -m compileall -q record_and_transcript\main.py record_and_transcript\app record_and_transcript\core record_and_transcript\tests` wurde erfolgreich ausgeführt.
- `python -m unittest discover -s record_and_transcript\tests -v` wurde erfolgreich ausgeführt: 4 Tests bestanden.
- `tests/test_gui_smoke.py` ist vorhanden und prüft Modulimporte, ohne ein Fenster zu instanziieren.
- `PROJECT.md`, `TASKS.md`, `README.md` und `CHANGELOG.md` wurden an diesen aktuellen Status angepasst.
- Der nächste inhaltliche Schritt ist die Sprecher-UX und die fachliche Bewertung der heuristischen Diarisierung.




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
- Offen sind vor allem die Sprecherbearbeitung im UI und die Bewertung der heuristischen Sprecher-Diarisierung.


