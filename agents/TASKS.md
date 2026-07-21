# TASKS.md

## Aktuelle Prioritäten

- [ ] Sprecher-UX im UI festlegen und umsetzen

  - Anzeige der Sprecher
  - Umbenennung
  - Zusammenführen
  - manuelle Korrektur
- [ ] Heuristische Sprecher-Diarisierung fachlich bewerten und dokumentieren
- [ ] GUI-Refactor weiter auf kleinere, testbare Bereiche aufteilen

## Bereits umgesetzt

- [x] `app/gui.py` analysiert und die großen Verantwortlichkeiten markiert
- [x] Busy-/State-Handling zentralisiert
- [x] Recording-, Transcription- und UI-Update-Logik in Hilfsmethoden zerlegt
- [x] Speaker-Control-Refactor syntaktisch bereinigt und verifiziert
- [x] GUI-Smoke-Test und Transcriber-Tests ausgeführt
- [x] `compileall` bzw. Importprüfung ausgeführt
- [x] CUDA-Diagnose-Dialog in der GUI implementiert und verifiziert
- [x] CUDA-Diagnose für die Transkription implementiert
- [x] Aktive Whisper-Gerätelogik in der GUI-Statuszeile sichtbar gemacht
- [x] Kein separates Logfile eingeführt; Status- und Fehlerausgabe bleiben GUI-basiert
- [x] CUDA-/Whisper-Fehlerdialoge so angepasst, dass die echte Backend-Exception angezeigt wird
- [x] CUDA-DLL-Suchpfade unter Windows automatisch registriert
- [x] Transkriptions-Backends über eine gemeinsame Schnittstelle und Factory entkoppelt
- [x] Neue Backend-Architektur unter `app/backends/` inklusive persistenter Backend-Wahl in `app/settings.py`
- [x] Dokumentation nach den Verifikationen aktualisiert
- [x] Azure OpenAI Backend mit echter API-Kommunikation vorbereitet und getestet

## Offene Folgethemen

- Prüfen, ob heuristische Sprecher-Diarisierung für Zielanwender ausreicht oder ob ein dediziertes Modell sinnvoll wird.
- Überlegen, ob Session-Historie, Modellverwaltung oder Exportformate als nächstes den größten Nutzen bringen.
- Entscheiden, ob ein optionales Debug-Log für Supportfälle ergänzt werden soll.
- OpenAI-Backend mit echter API-Kommunikation ergänzen.
- Whisper.cpp-Backend mit Vulkan-Unterstützung und `transcribe`-Implementierung versehen.

## In Bearbeitung

- Keine aktuell.

## Definition of Done für den nächsten Sprint

- Die Sprecher-UX ist konzeptionell sauber beschrieben.
- Die Diarisierungsstrategie ist bewertet.
- Die wichtigsten GUI-Verantwortlichkeiten sind weiter getrennt.
- Tests und Importprüfung laufen erfolgreich.
- README, PROJECT und TASKS beschreiben denselben aktuellen Stand.

## Historische Notizen

- Die GUI ist funktionsfähig und die Kernpfade sind durch Tests abgesichert.
- CUDA-Diagnose basiert auf GPU-Erkennung, PATH-Hinweisen und einem echten Modelltest.
- Unter Windows registriert der Transcriber CUDA-DLL-Verzeichnisse vor Whisper-Aufrufen.
- Die aktuelle Testsuite umfasst 20 Tests.















