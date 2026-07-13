[README.md](https://github.com/user-attachments/files/29960831/README.md)
# Audio-Transkription

Windows-Desktop-App zum Aufnehmen, Verbessern und Transkribieren von Sprache mit Whisper.

## Funktionen

- Audio-Aufnahme vom Mikrofon (Geräteauswahl)
- **Optional: System-Audio mitschneiden** (Teams, Browser etc. über WASAPI-Loopback)
- **Wiedergabe mit Steuerung**: Abspielen, Pause, ±10 s spulen, Klick in Wellenform zum Springen
- **Wellenform-Visualisierung** der Aufnahme
- **Audio-Verbesserung** vor der Transkription:
  - Lautstärke-Normalisierung
  - Hochpassfilter (entfernt tieffrequentes Rauschen)
  - Rauschreduktion
  - manuell („Jetzt verbessern“) oder automatisch vor Transkription
- Lokale Whisper-Transkription (offline)
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
4. **Aufnahme starten** → sprechen/hören → **Aufnahme stoppen**
5. Aufnahme in der **Wellenform** prüfen, mit Play/Pause/Spulen anhören
6. Optional: **Jetzt verbessern** oder automatische Verbesserung bei Transkription
7. **Transkribieren**
8. **Als DOCX exportieren** oder **Alles speichern**

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
- Die Transkription läuft auf der CPU (`int8`). Bei NVIDIA-GPU kann in `core/transcriber.py` auf `cuda` umgestellt werden.
- **System-Audio**: Funktioniert unter Windows über WASAPI-Loopback. Wähle das Ausgabegerät, über das Teams/Browser ton ausgibt (meist deine Lautsprecher oder Kopfhörer).
