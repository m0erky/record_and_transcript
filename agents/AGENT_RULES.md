# AGENT_RULES.md

## Arbeitsregeln für zukünftige Agent-Sessions

- Vor jeder Änderung zuerst den relevanten Codebestand und die aktuelle Dokumentation lesen.
- Größere Änderungen erst nach Architektur- und Abhängigkeitsanalyse durchführen.
- Wenn der Auftrag nur Dokumentation betrifft, keine funktionalen Codeänderungen vornehmen.
- Änderungen möglichst klein, atomar und nachvollziehbar halten.
- Bestehende Projektkonventionen, Benennungen und Stilrichtungen beibehalten.
- Keine Dateien löschen, verschieben oder umbenennen, ohne ausdrückliche Nutzerfreigabe.

## Dokumentationspflicht

- `PROJECT.md` aktuell halten, wenn Architektur, Technologien, Abläufe oder technische Entscheidungen sich ändern.
- `TASKS.md` pflegen, damit offene Punkte, In-Bearbeitung und erledigte Aufgaben sichtbar bleiben.
- `CHANGELOG.md` nach jeder relevanten Session aktualisieren.
- Technische Schulden, Einschränkungen, Fehlerzustände und Architekturentscheidungen transparent dokumentieren.
- Wenn ein Problem nicht behoben wird, den aktuellen Status klar festhalten statt ihn zu verschweigen.

## Coding Standards

- Typannotationen verwenden, wenn sie im Projektkontext sinnvoll sind.
- Dataclasses und modulare Trennung beibehalten.
- UI-Strings und Fehlermeldungen konsistent und verständlich formulieren.
- Komplexe Logik in kleine Hilfsmethoden aufteilen.
- Keine unnötigen Abhängigkeiten einführen.
- Plattformspezifische Besonderheiten, insbesondere Windows- und Audio-Laufzeit, explizit beachten.

## Sicherheitsregeln

- Keine Geheimnisse, Tokens, Passwörter oder persönlichen Daten in Dateien, Logs oder Antworten schreiben.
- Keine Netzwerkanfragen oder externen Dienste einführen, wenn die Anwendung lokal/offline bleiben soll.
- Audio- und Transkriptinhalte nur im Rahmen der Nutzeranfrage behandeln.
- Build-Artefakte und Exportdaten nur mit Bedacht anfassen.
- Bei System-Audio- oder Dateioperationen stets auf Datenverlust und Datenschutz achten.

## Git-Regeln

- Keine destruktiven Git-Aktionen ohne Auftrag.
- Keine Force-Pushes oder History-Rewrites ohne ausdrückliche Anweisung.
- Vor einem Commit den Diff prüfen und nur beabsichtigte Änderungen aufnehmen.
- Dokumentationsänderungen möglichst von funktionalen Änderungen trennen.
- Build-/Dist-Artefakte nur versionieren, wenn das Projekt es bewusst verlangt.
- Python-Bytecode-Caches (`__pycache__/`, `*.pyc`) niemals versionieren; falls sie bereits im Index liegen, aus dem Index entfernen.