[README.md](https://github.com/user-attachments/files/29960831/README.md)
# Audio-Transkription

Windows-Desktop-App zum Aufnehmen, Verbessern und Transkribieren von Sprache mit Whisper.

## Funktionen

- Audio-Aufnahme vom Mikrofon (Geräteauswahl) mit **Pause/Fortsetzen**

- **Optional: System-Audio mitschneiden** (Teams, Browser etc. über WASAPI-Loopback)
- **Vorhandene Audiodatei laden** und direkt transkribieren

- **Wiedergabe mit Steuerung**: Abspielen, Pause, ±10 s spulen, Klick in Wellenform zum Springen
- **Wellenform-Visualisierung** der Aufnahme
- **Audio-Verbesserung** vor der Transkription:
  - Lautstärke-Normalisierung
  - Hochpassfilter (entfernt tieffrequentes Rauschen)
  - Rauschreduktion
  - manuell („Jetzt verbessern“) oder automatisch vor Transkription
- Lokale Whisper-Transkription (offline)
- **Optionale Sprecher-Unterscheidung** im Transkript (`Sprecher 1`, `Sprecher 2`, ...)
- Export als Word-Dokument (`.docx`)

- Speichern von Roh-Aufnahme, verbesserter Aufnahme und Transkript

## Voraussetzungen

- Windows 10/11
- Python 3.10 oder neuer
- Mikrofon
- Optional: FFmpeg (empfohlen für `faster-whisper`)

## Installation

```powershell
cd audio_transk
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

## Start

```powershell
python main.py
```

## Ablauf

1. Mikrofon und Whisper-Modell wählen
2. Optional: **System-Audio mitschneiden** aktivieren und Ausgabegerät wählen (z. B. Lautsprecher/Headset)
3. Gewünschte Audio-Verbesserungen aktivieren
4. Entweder **Aufnahme starten** → bei Bedarf **Pause/Fortsetzen** → **Aufnahme stoppen**
5. Oder **Aufnahme laden** und eine vorhandene Audiodatei auswählen
6. Aufnahme in der **Wellenform** prüfen, mit Play/Pause/Spulen anhören
7. Optional: **Jetzt verbessern** oder automatische Verbesserung bei Transkription
8. Optional: **Sprecher unterscheiden** aktivieren und maximale Sprecherzahl wählen
9. **Transkribieren**
10. **Als DOCX exportieren** oder **Alles speichern**



Beim „Alles speichern“ werden Dateien unter `output/sessions/<Zeitstempel>/` abgelegt:

```
recording_raw.wav
recording_enhanced.wav   (falls verbessert)
transcript.txt
transcript.docx
```

## Hinweise

- Beim ersten Transkribieren wird das Whisper-Modell heruntergeladen (je nach Größe ca. 75–1500 MB).
- Für Deutsch empfiehlt sich das Modell `small`.
- Die Transkription läuft auf der CPU (`int8`). Über die App kann auch `auto` oder `cuda` gewählt werden.
- **Sprecher-Unterscheidung** arbeitet vollständig lokal und heuristisch auf Basis der Whisper-Segmente. Sie ist nützlich für Meetings/Interviews, aber nicht so präzise wie spezialisierte Diarisierungsmodelle.
- **System-Audio**: Funktioniert unter Windows über WASAPI-Loopback. Wähle das Ausgabegerät, über das Teams/Browser Ton ausgibt (meist deine Lautsprecher oder Kopfhörer).

