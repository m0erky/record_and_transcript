# PROJECT.md

## Projektziel

Die Anwendung ist eine lokale Windows-Desktop-App für Aufnahme, Audioverbesserung, Wiedergabe, Whisper-Transkription und optionale Sprecher-Unterscheidung.

Der geplante End-to-End-Workflow ist bewusst einfach gehalten:
1. Audio aufnehmen oder laden
2. optional verbessern
3. lokal mit Whisper transkribieren
4. optional Sprecher markieren
5. Ergebnisse als TXT, DOCX und Session-Dateien speichern

Die Kernverarbeitung bleibt lokal auf dem Rechner des Nutzers. Für die Hauptfunktionen ist keine externe Web-API vorgesehen.

## Architektur

### Einstieg
- `main.py` startet die GUI.

### Präsentation / UI
- `app/gui.py` enthält Hauptfenster, Bedienlogik und Zustandssteuerung.
- `app/waveform.py` zeichnet die Wellenform und die Abspielposition.
- `app/widgets.py` bündelt kleine UI-Hilfen.

### Fachlogik
- `core/audio_recorder.py` nimmt Mikrofon- und optional System-Audio auf.
- `core/audio_processor.py` verbessert Audio vor der Transkription.
- `core/audio_player.py` spielt Audio ab und steuert Play/Pause/Seek.
- `core/transcriber.py` lädt Whisper, transkribiert Audio und erzeugt optional heuristische Sprecherzuordnungen.
- `core/storage.py` verwaltet Sessions und Artefakte.
- `core/docx_exporter.py` erzeugt DOCX-Dateien.

### Tests
- `tests/test_gui_smoke.py` prüft Modulimporte ohne Fenster.
- `tests/test_transcriber.py` deckt Kernpfade der Transcriber- und Sprecherlogik ab.

## Datenmodell und Speicherung

Es gibt keine Datenbank. Stattdessen werden Sessions dateibasiert gespeichert:
- Rohaufnahme als WAV
- verbesserte Aufnahme als WAV
- Transkript als TXT
- Transkript als DOCX
- Session-Ordner unter `output/sessions/<Zeitstempel>/`

Wichtige Dataclasses im Projekt sind:
- `InputDevice`
- `RecordingConfig`
- `EnhancementOptions`
- `EnhancementResult`
- `SpeechRegion`
- `TranscriptSegment`
- `TranscriptionResult`
- `SessionPaths`

## Technologische Entscheidungen

1. **Offline-first Whisper-Verarbeitung**
   - Keine Cloud-Abhängigkeit für die Kernfunktion.
   - Datenschutz und Kontrolle bleiben lokal.

2. **Heuristische Sprecher-Diarisierung**
   - Leichtgewichtig und lokal umsetzbar.
   - Für präzise Mehrsprecher-Szenarien vermutlich nur eingeschränkt ausreichend.

3. **Dateibasierte Sessions statt Datenbank**
   - Weniger Komplexität.
   - Gut geeignet für einen Desktop-Einzelplatz-Workflow.

4. **Windows-Fokus**
   - System-Audio über WASAPI-Loopback wird speziell unter Windows unterstützt.
   - CUDA-Diagnose und DLL-Registrierung sind Windows-spezifisch umgesetzt.

5. **GUI-gesteuerter Workflow**
   - Die Anwendung ist als Desktop-App statt als CLI oder Server gedacht.

## Aktueller technischer Stand

- Die GUI ist funktionsfähig und strukturell bereits teilweise entkoppelt.
- Busy-/State-Handling wurde in Hilfsfunktionen aufgeteilt.
- Recording-, Transcription- und Ladeflüsse sind in kleinere Methoden zerlegt.
- Die Whisper-Transkription meldet den aktiven Rechenmodus über GUI-Statusmeldungen.
- Es gibt einen CUDA-Diagnose-Dialog mit GPU-Erkennung, PATH-Hinweisen und echtem Modelltest.
- Unter Windows registriert der Transcriber CUDA-DLL-Verzeichnisse vor Whisper-Aufrufen automatisch.
- CUDA- und Whisper-Fehler werden mit der echten Backend-Exception angezeigt.
- Ein separates Logfile ist bewusst nicht vorgesehen; die Oberfläche bleibt die primäre Rückmeldung.
- Die aktuelle Testsuite umfasst 10 Tests und wurde im Workspace verifiziert.

## Bekannte offene Punkte

- Sprecher-UX ist noch offen und soll konzeptionell und technisch weiter ausgearbeitet werden.
- Die heuristische Sprecher-Diarisierung ist noch nicht fachlich abschließend bewertet.
- Eine mögliche Erweiterung ist ein optionales Debug-Log für Supportfälle.
- Weitere mögliche Ausbauschritte sind Session-Historie, Modellverwaltung und zusätzliche Exportformate.






