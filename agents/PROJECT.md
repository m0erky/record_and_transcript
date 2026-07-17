# PROJECT.md

## Projektziel

Die Anwendung ist eine lokale Windows-Desktop-App zur Aufnahme, Verbesserung, Wiedergabe, Transkription und optionalen Sprecher-Unterscheidung von Audio.

Ziel ist ein möglichst einfacher End-to-End-Workflow:
1. Audio aufnehmen oder laden
2. optional verbessern
3. mit Whisper transkribieren
4. optional Sprecher markieren
5. als TXT/DOCX und Session-Dateien speichern

Die Verarbeitung erfolgt lokal auf dem Rechner des Nutzers. Es gibt keine externe Web-API und keine Cloud-Abhängigkeit für die Kernfunktionen.

## Architektur

Die Anwendung ist in wenige klar getrennte Schichten gegliedert:

### Einstiegsschicht
- `main.py` startet die GUI.

### Präsentationsschicht
- `app/gui.py` enthält das Hauptfenster, die Bedienlogik und die UI-Steuerung.
- `app/waveform.py` zeichnet die Wellenform und die aktuelle Position.
- `app/widgets.py` stellt kleine UI-Hilfsfunktionen bereit.

### GUI-Verantwortlichkeiten und Analyse
`app/gui.py` ist aktuell der zentrale Orchestrator der Anwendung und bündelt mehrere Aufgaben:
- Initialisierung von Recorder, Player, Processor, Transcriber und Storage
- Aufbau der gesamten Oberfläche
- Geräte- und Loopback-Refresh
- Aufnahme starten, pausieren, stoppen und Datei laden
- Audio-Verbesserung manuell oder automatisch vor der Transkription
- Transkriptionsstart, Fortschrittsanzeige und Fehlerbehandlung
- Wiedergabesteuerung inklusive Waveform-Synchronisation
- Speichern und Exportieren von Aufnahme- und Transkriptartefakten
- Aktivieren und Deaktivieren von UI-Elementen in Abhängigkeit vom App-Zustand

Die aktuelle GUI-Struktur ist funktional, aber weiterhin verzahnt. Für spätere Refactors bietet sich eine Trennung in Zustandsverwaltung, Aufnahme-/Transkriptions-Workflow und Anzeige-/Callback-Logik an.
Der erste Schritt zur Zustandsentkopplung ist umgesetzt: `_set_busy(...)` arbeitet mit `_set_widgets_state(...)` und `_sync_recording_controls(...)`, um Busy-State und Aufnahmezustand zu trennen. Die Speaker-bezogenen Helfer `_speaker_settings(...)` und `_speaker_metadata(...)` sind ebenfalls zentralisiert. Die CUDA-Diagnose basiert jetzt auf GPU-Erkennung, relevanten PATH-Einträgen und einem echten Whisper/CTranslate2-Modelltest; zusätzlich gibt es einen CUDA-Diagnose-Dialog in der GUI.





### Fachlogik
- `core/audio_recorder.py` nimmt Mikrofon- und optional System-Audio auf.
- `core/audio_processor.py` verbessert Audio vor der Transkription.
- `core/audio_player.py` spielt Audio ab und steuert Play/Pause/Seek.
- `core/transcriber.py` lädt Whisper, transkribiert Audio und optional führt eine heuristische Sprecher-Diarisierung aus.
- `core/storage.py` speichert Session-Dateien und Exporte.
- `core/docx_exporter.py` erzeugt Word-Dokumente.

### Tests
- `tests/test_gui_smoke.py` prüft den Import von `app.gui` und `main`, ohne ein GUI-Fenster zu öffnen.
- `tests/test_transcriber.py` prüft die Transcriber-Logik, Speech-Region-Erkennung und Segment-Merging.


### Build-/Artefaktbereich
- `build/` und `dist/` enthalten Paketierungsartefakte, vermutlich aus PyInstaller-Builds.
- Generierte Artefakte, Bytecode-Caches und lokale Laufzeitdateien werden ueber `.gitignore` ausgeschlossen.

### Git-/Repository-Hygiene
- Versioniert werden sollen Quellcode, Tests, Dokumentation, `.spec`-Buildbeschreibungen und Lizenzdateien.
- Nicht versioniert werden sollen `__pycache__/`, `*.pyc`, `build/`, `dist/`, `output/`, virtuelle Umgebungen, Editor-Metadaten und sonstige temporaere Dateien.
- Vorher versehentlich versionierte Bytecode-Caches wurden aus dem Git-Index entfernt.


## Technologien

### Sprache und Laufzeit
- Python 3.10+ laut README
- im Build-Artefakt ist Python 3.13 erkennbar

### GUI
- `customtkinter`
- `tkinter`

### Audio
- `sounddevice`
- `soundfile`
- optional `soundcard` für Loopback-Erkennung unter Windows
- `numpy`
- `scipy`
- `noisereduce`

### Transkription
- `faster-whisper`
- `ctranslate2`

### Export
- `python-docx`

### Packaging / Runtime-Artefakte
- PyInstaller-ähnliche Build-Ausgabe ist im Repository vorhanden (`AudioTranskription.spec`, `AudioTranskription-OneFile.spec`)

## Verzeichnisstruktur

```text
record_and_transcript/
├── main.py
├── README.md
├── requirements.txt
├── LICENSE
├── agents/
│   ├── PROJECT.md
│   ├── TASKS.md
│   ├── CHANGELOG.md
│   └── AGENT_RULES.md
├── app/
│   ├── gui.py
│   ├── waveform.py
│   ├── widgets.py
│   └── __init__.py
├── core/
│   ├── audio_player.py
│   ├── audio_processor.py
│   ├── audio_recorder.py
│   ├── docx_exporter.py
│   ├── storage.py
│   ├── transcriber.py
│   └── __init__.py
├── tests/
│   ├── test_gui_smoke.py
│   └── test_transcriber.py

├── output/
│   └── sessions/
├── build/
├── dist/
└── *.spec
```

## Datenbankdesign

Es gibt aktuell **keine Datenbank**.

Stattdessen werden Daten dateibasiert gespeichert:
- Rohaufnahme als WAV
- verbesserte Aufnahme als WAV
- Transkript als TXT
- Transkript als DOCX
- Session-Ordner unter `output/sessions/<Zeitstempel>/`

### Datenmodell in der Anwendung

Wichtige Dataclasses sind:
- `InputDevice`
- `RecordingConfig`
- `EnhancementOptions`
- `EnhancementResult`
- `SpeechRegion`
- `TranscriptSegment`
- `TranscriptionResult`
- `SessionPaths`

### Dateispeicherstruktur einer Session

```text
output/sessions/<YYYY-MM-DD_HH-MM-SS>/
├── recording_raw.wav
├── recording_enhanced.wav
├── transcript.txt
└── transcript.docx
```

## APIs

Es gibt keine externe HTTP-API.

### Interne Kern-APIs

#### `AudioRecorder`
- `list_input_devices()`
- `list_loopback_devices()`
- `start(config)`
- `pause()` / `resume()`
- `stop()`
- `load_audio_file(path, target_sample_rate)`
- `get_audio()`

#### `AudioProcessor`
- `enhance(audio, options)`

#### `AudioPlayer`
- `load(audio)`
- `play()` / `pause()` / `stop()`
- `seek(seconds)` / `skip(seconds)`
- Callback-API für Positions- und Ende-Events

#### `WhisperTranscriber`
- `transcribe(...)`
- interne Hilfsfunktionen für Segment-Erzeugung, Speaker-Diarisierung, Clustering und Modellverwaltung

#### `SessionStorage`
- `create_session()`
- `save_wav(...)`
- `save_transcript_txt(...)`
- `save_transcript_docx(...)`
- `save_all(...)`

#### `export_to_docx(...)`
- erzeugt ein DOCX-Dokument aus Text und Metadaten

## Deployment-Konzept

### Lokaler Betrieb
1. Python-Umgebung erstellen
2. Abhängigkeiten aus `requirements.txt` installieren
3. `python main.py` ausführen

### Typischer Windows-Workflow
- Mikrofon auswählen
- optional System-Audio aktivieren (WASAPI/Loopback)
- Whisper-Modell wählen
- optional Audio verbessern
- transkribieren und exportieren

### Paketierung
- Im Repository sind `.spec`-Dateien sowie `build/` und `dist/` vorhanden.
- Das deutet auf einen PyInstaller-Workflow hin.
- Das Auslieferungsartefakt ist eine Desktop-EXE für Windows.

### Betriebsannahmen
- Fokus auf Windows 10/11
- Offline-/Local-First-Verarbeitung
- Modell-Download beim ersten Start bzw. ersten Transkriptionslauf

## Bekannte technische Entscheidungen

1. **Offline-first Whisper-Transkription**
   - Kein externer Transkriptionsdienst.
   - Vorteil: Datenschutz, geringe Abhängigkeiten, lokale Kontrolle.

2. **Heuristische Sprecher-Diarisierung statt Spezialmodell**
   - Aktuell wird Sprecherzuordnung aus Speech-Regionen, Embeddings und Clustering abgeleitet.
   - Das ist leichtgewichtig, aber weniger präzise als ein dediziertes Diarisierungsmodell.

3. **Dateibasierte Speicherung statt Datenbank**
   - Sitzungen werden direkt im Dateisystem abgelegt.
   - Das reduziert Komplexität und passt zum Desktop-/Einzelplatz-Szenario.

4. **Windows-spezifischer System-Audio-Support**
   - Loopback-Aufnahme wird unter Windows priorisiert.
   - Andere Plattformen haben nur eingeschränkten oder keinen Support.

5. **Lokale Audio-Verbesserung vor der Transkription**
   - Normalisierung, Hochpassfilter und Rauschreduktion werden lokal durchgeführt.

6. **UI-getriebene Workflow-Steuerung**
   - Die App ist bewusst als Desktop-GUI aufgebaut und nicht als CLI-/Server-Anwendung.

## Aktueller technischer Status

- Die Transcriber-Logik ist vorhanden und testbar.
- Es existieren Unit-Tests für die Sprecherlogik und ein GUI-Smoke-Test für die Modulimporte.
- Die Repository-Hygiene ist aufgeräumt: generierte Bytecode-Caches sind aus dem Git-Index entfernt und werden künftig ignoriert.
- Build-/Runtime-Artefakte bleiben ueber `.gitignore` aus der Versionierung heraus.
- Die GUI-Zustandssteuerung ist teilweise zentralisiert; Recording-, Transcription- und Lade-Workflows sind bereits in Hilfsmethoden zerlegt.
- Die Speaker-Control-Logik ist syntaktisch bereinigt; die nächste fachliche Aufgabe ist die Konzeption der Sprecher-UX und die Bewertung der heuristischen Diarisierung.
- `app/gui.py` ist syntaktisch korrekt; `compileall` und die Testsuite laufen erfolgreich.
- Die CUDA-Diagnose ist jetzt auf einen echten Whisper/CTranslate2-Modelltest ausgerichtet und ergänzt um PATH-Hinweise aus dem laufenden App-Prozess.
- Die GUI bietet zusätzlich einen CUDA-Diagnose-Dialog, der GPU-Erkennung, PATH-Hinweise und den Modelltest im laufenden App-Prozess anzeigt.

- Die aktuelle Testsuite umfasst 6 Tests und wurde im aktuellen Workspace erfolgreich verifiziert.



## Statuskorrektur 2026-07-16

- Der zuvor dokumentierte `IndentationError` in `app/gui.py` ist im aktuellen Workspace behoben.
- `app/gui.py` ist syntaktisch korrekt; `python -m compileall` und `python -m unittest discover -s record_and_transcript\tests -v` laufen erfolgreich.
- `tests/test_gui_smoke.py` ist vorhanden und prüft den Import von `app.gui` und `main`, ohne ein GUI-Fenster zu instanziieren.
- Die CUDA-Diagnose verwendet jetzt einen echten Modelltest statt einer harten DLL-Prüfung; Fehlermeldungen sind damit besser auf den App-Prozess bezogen.

- Der nächste inhaltliche Schritt liegt bei Sprecher-UX und Diarisierungsbewertung.






