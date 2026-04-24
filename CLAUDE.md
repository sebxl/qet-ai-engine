# QET-AI Engine

## Projektziel

Deterministische Python-Engine die aus JSON-Spezifikation vollstaendige,
professionelle industrielle Elektro-Schaltplaene als QElectroTech-Projektdateien
(.qet) erzeugt. Kein LLM in der Erzeugungskette -- rein algorithmisch.

## Architektur

```
JSON (qet-ai/v1) --> Python-Engine --> .qet-Datei --> QElectroTech oeffnen
```

Claude erzeugt JSON, die Engine baut den Plan, QET zeigt ihn an.
Am QET-Quellcode wird nichts geaendert.

## Tech-Stack

- **Sprache:** Python
- **XML:** xml.etree.ElementTree fuer .qet/.elmt-Parsing und -Erzeugung
- **Tests:** pytest, TDD (Spec -> Tests -> Implementation)
- **Methodik:** Determinismus, Self-Verification via SVG-Rendering

## Wichtige Pfade

| Was | Pfad |
|-----|------|
| Projektroot | `C:\Users\User\Documents\Projekte\QET` |
| QET-Quellcode (Referenz) | `qelectrotech-source-mirror/` |
| QET-Elementsammlung | `qelectrotech-source-mirror/elements/` |
| Source-Code-Analyse | `docs/qet-internals.md` |
| Projektplan | `QET-AI-ENGINE-PLAN.md` |
| Engine-Code (Ziel) | `src/` |
| Tests (Ziel) | `tests/` |

## Linear-Projekt

**Team:** QET AI Engine
**Projekt:** QET-AI Engine
**URL:** https://linear.app/projekte-seb/project/qet-ai-engine-00b25e0fb469

### Issues

| Issue | Titel | Milestone | Status |
|-------|-------|-----------|--------|
| QET-1 | Element-Parser & Terminal-Datenbank | Foundation | Backlog |
| QET-2 | QET-XML-Writer | Foundation | Backlog |
| QET-3 | SVG-Renderer (Self-Verification) | Foundation | Backlog |
| QET-4 | Motorstarter Hauptstromkreis | First Template | Backlog |
| QET-5 | Motorstarter Steuerstromkreis & Querverweise | First Template | Backlog |
| QET-6 | Engine-Integration & E2E-Validierung | First Template | Backlog |

### Abhaengigkeiten

```
QET-1 Element-Parser ---+---> QET-3 SVG-Renderer ----------+
                        |                                   |
                        +---> QET-4 Hauptstrom --> QET-5 Steuer --> QET-6 E2E
QET-2 XML-Writer -------+
```

## Self-Verification Loop

1. **Tests (pytest):** Exakte Werte -- Terminal-IDs, Positionen, Verbindungen
2. **Validator (Python):** Regeln -- offene Terminals, Ueberlappungen, Duplikate
3. **SVG-Renderer:** Visuell -- Claude liest gerendertes SVG als Bild
4. **Kalibrierung:** SVG-Output muss gegen QET-Screenshot abgeglichen werden (QET-3)
5. **Benutzer-Check:** Finale Pruefung -- .qet in QElectroTech oeffnen

## Wichtige Erkenntnisse (aus Source-Code-Analyse)

- .qet-Root: `<project title="..." version="0.90">`
- Elemente via `common://`-Pfade referenzieren (nicht einbetten)
- UUIDs im Format `{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}`
- Terminal-Position auf Folio: `element_pos + rotate(orientation * 90) * terminal_pos`
- Conductor braucht: terminal1/2 (UUID), element1/2 (UUID), Segmente
- Master/Slave via `<links_uuids>` gegenseitig verknuepfen
- Standard-Folio: 17 Spalten x 60px, 8 Zeilen x 80px, Raster 10x10px
- Orientation: 0=0deg, 1=90deg, 2=180deg, 3=270deg
- Details: siehe `docs/qet-internals.md`
