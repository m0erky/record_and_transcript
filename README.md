# Audio-Transkription

Windows-Desktop-App zum Aufnehmen, Verbessern, Abspielen und Transkribieren von Sprache mit Whisper.

## Funktionen

- Mikrofonaufnahme mit Geräteauswahl sowie Pause/Fortsetzen
- Optionales Mitschneiden von System-Audio über WASAPI-Loopback
- Vorhandene Audiodateien laden und direkt transkribieren
- Wellenformanzeige und einfache Wiedergabesteuerung
- Audioverbesserung vor der Transkription:
  - Normalisierung
  - Hochpassfilter
  - Rauschreduktion
  - manuell oder automatisch vor der Transkription
- Lokale Whisper-Transkription ohne Cloud-Abhängigkeit
- Optionale heuristische Sprecher-Unterscheidung im Transkript
- Export als TXT und DOCX
- Speichern von Rohaufnahme, verbesserter Aufnahme und Transkript pro Session

## Voraussetzungen

- Windows 10/11
- Python 3.10 oder neuer
- Mikrofon
- Optional: FFmpeg, empfohlen für `faster-whisper`

## Installation

```powershell
cd record_and_transcript
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Start

```powershell
python main.py
```

## Typischer Ablauf

1. Mikrofon und Whisper-Modell wählen
2. Optional System-Audio aktivieren und Ausgabegerät wählen
3. Gewünschte Audio-Verbesserungen aktivieren
4. Aufnahme starten, bei Bedarf pausieren, dann stoppen
5. Alternativ eine vorhandene Audiodatei laden
6. Aufnahme in der Wellenform prüfen und bei Bedarf abspielen
7. Optional manuell verbessern oder die automatische Verbesserung nutzen
8. Optional Sprecher-Unterscheidung aktivieren
9. Transkribieren
10. Als DOCX exportieren oder alles speichern

## Speicherort der Ergebnisse

Beim Speichern einer Session legt die App die Dateien unter `output/sessions/<Zeitstempel>/` ab:

```text
recording_raw.wav
recording_enhanced.wav   (falls vorhanden)
transcript.txt
transcript.docx
```

## Hinweise

- Beim ersten Transkribieren wird das gewählte Whisper-Modell heruntergeladen.
- Für Deutsch ist `small` meist ein guter Startpunkt.
- Über die App können `auto`, `cpu` oder `cuda` gewählt werden, sofern die CUDA-12-Laufzeit auf Windows verfügbar ist.
- Die GUI zeigt den von Whisper gemeldeten Rechenmodus während der Transkription in der Statuszeile an.
- Für CUDA gibt es einen Diagnose-Dialog mit GPU-Erkennung, PATH-Hinweisen und einem echten Modelltest.
- Wenn der CUDA-Modus trotz erkannter GPU scheitert, hilft oft ein Neustart der App, damit Laufzeit-DLLs sauber registriert werden.
- Fehlerdialoge zeigen die konkrete Whisper-/CUDA-Exception an.
- Es gibt bewusst kein separates Logfile; Laufzeitmeldungen bleiben in der GUI.
- Sprecher-Unterscheidung ist aktuell heuristisch und lokal; sie eignet sich für einfache Zuordnung, ist aber nicht so präzise wie spezialisierte Diarisierung.
- System-Audio funktioniert unter Windows über WASAPI-Loopback. Wähle dafür das Ausgabegerät, über das der Ton tatsächlich läuft.

## Entwicklung und Tests

```powershell
python -m compileall -q main.py app core tests
python -m unittest discover -s tests -v
```

## Projektstand in Kurzform

- Lokale Windows-Desktop-Anwendung mit Whisper-Transkription
- GUI-basierter Workflow ohne externe API
- Datei- und sessionbasiertes Speichern
- CUDA-Diagnose und CUDA-DLL-Registrierung unter Windows vorhanden
- Sprecher-UX und die Bewertung der heuristischen Diarisierung sind weiterhin ein offener Ausbaubereich



