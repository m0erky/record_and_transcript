# AGENT_RULES.md

## Arbeitsprinzipien

- Vor Änderungen zuerst den relevanten Codebestand und die passenden Dokumente lesen.
- Größere Änderungen erst nach kurzer Architektur- und Abhängigkeitsanalyse durchführen.
- Wenn ein Auftrag nur Dokumentation betrifft, keine funktionalen Codeänderungen vornehmen.
- Änderungen klein, atomar und nachvollziehbar halten.
- Bestehende Projektkonventionen, Benennungen und Stilrichtungen beibehalten.
- Keine Dateien löschen, verschieben oder umbenennen, ohne ausdrückliche Nutzerfreigabe.

## Dokumentationsrollen

- `README.md` ist die benutzerorientierte Einstiegshilfe.
- `PROJECT.md` beschreibt Architektur, Entscheidungen und technischen Stand.
- `TASKS.md` enthält offene Aufgaben, Prioritäten und erledigte Arbeit.
- `CHANGELOG.md` dokumentiert Änderungen chronologisch.
- Nach relevanten Codeänderungen die sichtbare Doku konsistent halten.
- Technische Schulden, Einschränkungen und offene Fehler transparent dokumentieren.
- Wenn etwas nicht behoben wird, den Status klar und ehrlich festhalten.

## Coding Standards

- Typannotationen verwenden, wenn sie im Projektkontext sinnvoll sind.
- Dataclasses und modulare Trennung beibehalten.
- UI-Strings und Fehlermeldungen klar und konsistent formulieren.
- Komplexe Logik in kleine Hilfsmethoden aufteilen.
- Keine unnötigen Abhängigkeiten einführen.
- Plattformspezifische Besonderheiten, vor allem unter Windows, explizit beachten.

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


