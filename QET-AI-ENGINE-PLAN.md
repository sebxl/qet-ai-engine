# QET-AI Engine — Projektplan

## Projektziel

Entwicklung einer **deterministischen Engine**, die aus einer strukturierten JSON-Beschreibung
vollständige, professionelle industrielle Elektro-Schaltpläne als QElectroTech-Projektdateien (.qet)
erzeugt. Die Engine arbeitet rein algorithmisch — kein LLM in der Erzeugungskette.

Ein LLM (Claude Opus) dient ausschließlich als **Eingabe-Frontend**: Der Benutzer beschreibt
per Sprache oder Text die gewünschte Schaltung, Opus erzeugt daraus ein JSON nach festem Schema,
die Engine baut den Plan.

Das Konzept folgt dem Ansatz von LEAP 71 (Computational Engineering): Ingenieurwissen wird in
Code codiert, nicht in einem neuronalen Netz approximiert. Das LLM ist ein komfortables Interface,
nicht das Herzstück.

---

## Architektur

```
Benutzer (Sprache/Text)
    │
    ▼
Claude Opus (Planung)
    │  Versteht Normen, wählt Komponenten,
    │  kennt Schaltungstopologien
    │
    ▼
JSON-Spezifikation (schema: qet-ai/v1)
    │  Deklarativ: WAS gebaut werden soll
    │  Nicht: WIE (keine Positionen, keine Terminal-IDs)
    │
    ▼
┌─────────────────────────────────────────────┐
│              QET-AI ENGINE                   │
│                                             │
│  ┌─────────────┐  ┌──────────────────────┐  │
│  │ Element-DB   │  │ Template-Engine      │  │
│  │ (geparste    │  │ (Motorstarter,       │  │
│  │  .elmt-      │  │  Wendeschütz,        │  │
│  │  Sammlung)   │  │  Sicherheitskreis,   │  │
│  │              │  │  SPS-Anbindung, ...) │  │
│  └──────┬───────┘  └──────────┬───────────┘  │
│         │                     │              │
│  ┌──────▼─────────────────────▼───────────┐  │
│  │         Layout-Engine                   │  │
│  │  (Auto-Positionierung, Leiter-Routing,  │  │
│  │   Folio-Aufteilung)                     │  │
│  └──────────────────┬─────────────────────┘  │
│                     │                        │
│  ┌──────────────────▼─────────────────────┐  │
│  │         Validator / DRC                 │  │
│  │  (Offene Terminals, fehlender Schutz,   │  │
│  │   BMK-Duplikate, Querschnitte, ...)     │  │
│  └──────────────────┬─────────────────────┘  │
│                     │                        │
│  ┌──────────────────▼─────────────────────┐  │
│  │         QET-XML-Generator               │  │
│  │  (Erzeugt valide .qet-Projektdatei)     │  │
│  └──────────────────┬─────────────────────┘  │
│                     │                        │
│  ┌──────────────────▼─────────────────────┐  │
│  │         SVG-Renderer                    │  │
│  │  (Rendert Folios als SVG zur            │  │
│  │   Self-Verification)                    │  │
│  └─────────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
    │
    ▼
Ausgabe: .qet-Datei → QElectroTech öffnen → fertiger Plan
```

---

## Kernprinzipien

### 1. Determinismus
Gleiche Eingabe → exakt gleiche Ausgabe. Keine Zufallselemente, keine LLM-Varianz.
Die Engine ist ein Compiler: JSON rein, .qet raus.

### 2. Constraints über Freiheit
Je weniger Freiheitsgrade das JSON-Schema lässt, desto zuverlässiger das Ergebnis.
Claude wählt aus einem Katalog von Circuit-Typen mit festen Parametern — kein Freitext.

### 3. Test-Driven Development
Jede Komponente wird zuerst als Spec + Tests definiert, dann implementiert.
Tests prüfen exakte Werte: Terminal-IDs, Positionen, Verbindungen, Constraint-Verletzungen.

### 4. Self-Verification
Die Engine enthält einen SVG-Renderer, der .elmt-Grafikprimitive (Linien, Kreise,
Rechtecke, Bögen) und Leiter rendert. Damit kann der Entwickler (Claude Code) das
Ergebnis visuell prüfen — kein Blindflug.

### 5. Echte Symbole
Keine nachgebauten Symbole. Alle Elemente werden über `common://`-Pfade aus der
QElectroTech-Standardsammlung (8.200+ Elemente) referenziert. Die Engine parst die
.elmt-Dateien und kennt exakte Terminal-Positionen.

---

## Voraussetzungen

### QElectroTech Source Code
Der QET-Quellcode liegt lokal vor und wird für folgendes genutzt:
- **Element-Sammlung** (`elements/`): .elmt-Dateien parsen für Terminal-DB
- **Quellcode-Analyse** (`sources/`): Verstehen wie QET intern .qet-Dateien interpretiert
- **Referenz**: Was genau macht QET beim Laden eines Projekts? Wie löst es `common://` auf?

### Sprache
Die Engine wird in **Python** entwickelt (rapid prototyping, XML-Handling, SVG-Erzeugung).
Ein späterer Port nach Rust oder C++ (für Integration in den QET-Fork) ist möglich,
aber nicht Scope dieses Projekts.

---

## Entwicklungsphasen

### Phase 0: Source-Code-Analyse + Tooling

**Ziel**: Vollständiges Verständnis des QET-Dateiformats und ein funktionierender
Self-Verification-Loop.

#### 0.1 — QET Source-Code-Analyse

Analysiere den QET-Quellcode systematisch:

**Dateiformate verstehen:**
- Wie lädt QET eine .qet-Datei? (`sources/qetproject.cpp`, `sources/diagram.cpp`)
- Wie werden Elemente referenziert und aufgelöst? (`common://` → Dateisystem)
- Wie werden Leiter intern gespeichert? (Terminal-Referenzierung: UUID vs. ID?)
- Wie funktioniert das Schriftfeld (Title Block)?
- Wie werden Querverweise (Spule↔Kontakte, link_type master/slave) aufgelöst?

**Element-Format verstehen:**
- Exakte Struktur einer .elmt-Datei
- Alle grafischen Primitive und ihre Attribute
- Terminal-Definition: ID-Vergabe, UUID, Orientierung, Name
- Wie berechnet QET die absolute Position eines Terminals auf dem Folio?
  (Element-Position + Hotspot-Offset + Terminal-Offset + Rotation)

**Verbindungen verstehen:**
- Wie speichert QET einen Conductor? (XML-Struktur)
- Wie referenziert ein Conductor seine Terminals? (element-UUID + terminal-ID?)
- Gibt es Routing-Informationen (Wegpunkte) im XML?

**Ergebnis**: Ein Dokument `docs/qet-internals.md` das alle Erkenntnisse festhält.

#### 0.2 — Element-Parser + Terminal-Datenbank

```python
# Input: Pfad zur Element-Sammlung
# Output: Durchsuchbare DB mit allen Elementen, ihren Terminals, Dimensionen

class ElementDB:
    def scan(self, elements_dir: Path) -> None: ...
    def search(self, query: str) -> list[ElementRecord]: ...
    def get(self, elmt_path: str) -> ElementRecord: ...
    def get_terminals(self, elmt_path: str) -> list[Terminal]: ...
    def get_graphics(self, elmt_path: str) -> list[GraphicPrimitive]: ...
```

**Tests (Phase 0.2):**
```python
def test_parse_contactor_coil():
    """Schützspule hat genau 2 Terminals: A1 (oben) und A2 (unten)"""
    db = ElementDB("elements/")
    info = db.get("10_electric/10_allpole/310_relays_contactors_contacts/01_coils/bobine_contacteur.elmt")
    assert len(info.terminals) == 2
    assert info.terminals[0].name == "A1"
    assert info.terminals[0].orientation == "n"
    assert info.terminals[1].name == "A2"
    assert info.terminals[1].orientation == "s"
    assert info.link_type == "master"

def test_parse_motor_3phase():
    """Drehstrommotor hat 3 Terminals: U1, V1, W1"""
    info = db.get(".../moteur_3ph.elmt")
    assert len(info.terminals) == 3
    terminal_names = {t.name for t in info.terminals}
    assert terminal_names == {"U1", "V1", "W1"}

def test_terminal_absolute_position():
    """Terminal-Position auf dem Folio = Element-Position + Terminal-Offset (rotationskorrigiert)"""
    info = db.get(".../bobine_contacteur.elmt")
    # Element platziert bei (280, 300), Orientation 0
    abs_pos = info.terminal_absolute_position(terminal_name="A1", element_x=280, element_y=300, orientation=0)
    # Muss exakte Werte liefern, die QET auch berechnen würde
    assert isinstance(abs_pos.x, (int, float))
    assert isinstance(abs_pos.y, (int, float))
```

#### 0.3 — SVG-Renderer (Self-Verification)

Rendert ein QET-Folio als SVG:
- .elmt-Grafikprimitive → SVG-Elemente (line, rect, circle, arc, text, polygon)
- Terminals als kleine Kreise/Punkte markieren
- Leiter als Pfade zwischen Terminal-Positionen
- Schriftfeld (vereinfacht)
- Rasterlinien optional

```python
class FolioRenderer:
    def render(self, project: QETProject, folio_index: int) -> str:
        """Rendert ein Folio als SVG-String"""
        ...

    def render_to_file(self, project: QETProject, folio_index: int, path: Path) -> None:
        ...
```

**Tests (Phase 0.3):**
```python
def test_render_empty_folio():
    """Leeres Folio rendert als SVG mit Rahmen und Schriftfeld"""
    svg = renderer.render(project, 0)
    assert svg.startswith("<svg")
    assert "<!-- titleblock -->" in svg

def test_render_element_at_position():
    """Element wird an korrekter Position gerendert"""
    # Prüfe dass SVG-Elemente die richtigen transform-Attribute haben
    ...

def test_render_conductor_between_terminals():
    """Leiter verbindet exakt die Terminal-Positionen"""
    ...
```

#### 0.4 — QET-XML-Writer

Erzeugt valide .qet-Dateien die QElectroTech öffnen kann.

```python
class QETWriter:
    def create_project(self, title: str, author: str, ...) -> QETProject: ...
    def add_folio(self, project: QETProject, title: str) -> Folio: ...
    def place_element(self, folio: Folio, elmt_path: str, x: float, y: float,
                      designation: str, orientation: int = 0) -> PlacedElement: ...
    def connect(self, folio: Folio, elem1: PlacedElement, terminal1: str,
                elem2: PlacedElement, terminal2: str, label: str = "") -> Conductor: ...
    def save(self, project: QETProject, filepath: Path) -> None: ...
```

**Tests (Phase 0.4):**
```python
def test_generated_xml_is_valid():
    """Erzeugte .qet-Datei ist wohlgeformtes XML"""
    project = writer.create_project("Test")
    writer.save(project, "test.qet")
    tree = ET.parse("test.qet")  # Darf keinen ParseError werfen

def test_element_references_common_path():
    """Elemente nutzen common:// statt embed://"""
    # ...
    xml = Path("test.qet").read_text()
    assert "common://" in xml
    assert "embed://" not in xml

def test_conductor_references_correct_terminals():
    """Leiter referenzieren die richtigen Element-UUIDs und Terminal-IDs"""
    # ...
```

---

### Phase 1: Erstes Template — Motorstarter Direktanlauf

**Ziel**: Ein vollständiger, professioneller Schaltplan für einen Drehstrom-Direktstarter,
erzeugt aus 5 Parametern.

#### JSON-Eingabe (was Claude erzeugt):

```json
{
  "schema": "qet-ai/v1",
  "project": {
    "title": "Test Motorstarter",
    "author": "Sebastian",
    "company": "Krampe Werkzeugbau",
    "machine_id": "TEST-01"
  },
  "circuits": [
    {
      "type": "motor_starter_direct",
      "id": "antrieb_1",
      "params": {
        "motor_power_kw": 1.5,
        "motor_voltage": "400V_3ph",
        "motor_current_a": 3.5,
        "protection_type": "thermal_overload",
        "contactor_coil_voltage": "24V_DC",
        "with_control_circuit": true,
        "indicators": ["run", "fault"]
      }
    }
  ]
}
```

#### Was die Engine daraus erzeugt:

**Folio 1 — Hauptstromkreis:**
```
L1────L2────L3
 │     │     │
[F1 — Leitungsschutzschalter 3p, C-Charakteristik]
 │     │     │
[K1 — Schütz Hauptkontakte 3p]
 │     │     │
[F2 — Motorschutzrelais, Einstellbereich inkl. 3.5A]
 │     │     │
 U     V     W
[   M1 — Motor 3~   ]
```

**Folio 2 — Steuerstromkreis:**
```
+24V DC
 │
[S0] Not-Halt (NC, Pilzform)
 │
[F2] Überlast-Hilfskontakt (NC, 95-96)
 │
[S1] Aus-Taster (NC)
 │
├──[S2] Ein-Taster (NO)──┤
│                         │
│    [K1] Selbsthaltung   │
│         (NO, 13-14)     │
├─────────────────────────┤
 │
[K1] Spule (A1-A2)
 │
0V
```

**Tests (Phase 1):**
```python
def test_motor_starter_generates_two_folios():
    result = engine.generate(motor_starter_json)
    assert len(result.folios) == 2

def test_motor_starter_has_protection():
    result = engine.generate(motor_starter_json)
    issues = validator.validate(result)
    assert not any(i["rule"] == "MISSING_PROTECTION" for i in issues)

def test_motor_starter_has_estop():
    result = engine.generate(motor_starter_json)
    estops = [e for e in result.all_elements() if "emergency" in e.elmt_path or "arret" in e.elmt_path]
    assert len(estops) >= 1

def test_motor_starter_contactor_cross_reference():
    """K1 Spule (master) und K1 Selbsthaltekontakt (slave) haben gleiche Bezeichnung"""
    result = engine.generate(motor_starter_json)
    k1_elements = [e for e in result.all_elements() if e.designation == "K1"]
    assert len(k1_elements) == 2  # Spule + Kontakt

def test_motor_starter_all_terminals_connected():
    result = engine.generate(motor_starter_json)
    issues = validator.validate(result)
    open_terminals = [i for i in issues if i["rule"] == "OPEN_TERMINAL"]
    assert len(open_terminals) == 0

def test_motor_starter_no_overlapping_elements():
    result = engine.generate(motor_starter_json)
    issues = validator.validate(result)
    assert not any(i["rule"] == "ELEMENT_OVERLAP" for i in issues)

def test_motor_starter_svg_renders():
    """SVG-Rendering produziert valides SVG mit allen Elementen"""
    result = engine.generate(motor_starter_json)
    svg = renderer.render(result, folio_index=0)
    assert "<svg" in svg
    # Prüfe dass alle BMKs im SVG vorkommen
    for bmk in ["F1", "K1", "F2", "M1"]:
        assert bmk in svg
```

---

### Phase 2: Template-Bibliothek erweitern

Jedes Template folgt dem gleichen Muster: JSON-Schema → Engine → Tests → SVG-Verify.

| Template | Circuit-Type | Parameter |
|----------|-------------|-----------|
| Wendeschützkombination | `motor_starter_reversing` | motor_*, with_mechanical_interlock |
| Stern-Dreieck-Anlauf | `motor_starter_star_delta` | motor_*, transition_time_s |
| Frequenzumrichter-Antrieb | `vfd_drive` | motor_*, vfd_model, control_type |
| Servo-Antrieb | `servo_drive` | drive_model, motor_model, connection (ethercat/pulse) |
| Sicherheitskreis | `safety_circuit` | category (PLa-PLe), estop_count, door_switches, relay_type |
| 24V-Versorgung | `power_supply_24v` | source, output_current_a, type |
| SPS Ein-/Ausgänge | `plc_io` | plc_type, digital_inputs[], digital_outputs[], analog_inputs[] |
| Beleuchtung/Steckdosen | `aux_power` | circuits[] |

---

### Phase 3: Layout-Engine

Automatische Positionierung aller Elemente und Leiter-Routing.

**Layout-Regeln:**
- Hauptstromkreis: vertikaler Energiefluss (oben→unten), ein Abgang pro Spalte
- Steuerstromkreis: vertikaler Signalfluss, Steuerspannung oben, 0V unten
- SPS-Folios: Eingänge links, SPS-Modul Mitte, Ausgänge rechts
- Mindestabstände zwischen Elementen
- Leiter: Manhattan-Routing (nur horizontal + vertikal), Kreuzungen minimieren
- Automatische Folio-Aufteilung bei Platzmangel

---

### Phase 4: Validator / DRC

Vollständige programmatische Prüfung:

| Regel | Quelle | Prüflogik |
|-------|--------|-----------|
| OPEN_TERMINAL | Engine | Terminal ohne Conductor-Referenz |
| DUPLICATE_BMK | EN 81346 | Gleiche Bezeichnung (außer master/slave-Paare) |
| MISSING_PROTECTION | EN 60204-1 §7 | Graph: Pfad Einspeisung→Motor ohne Schutzknoten |
| MISSING_ESTOP | EN 60204-1 §10.7 | Kein Not-Halt-Element bei vorhandenen Motoren |
| MISSING_PE | EN 60204-1 §8 | Kein Schutzleiter-Anschluss |
| ELEMENT_OVERLAP | Layout | Bounding-Box-Kollision |
| OUT_OF_BOUNDS | Layout | Element außerhalb Zeichnungsrahmen |
| ORPHAN_CONDUCTOR | Engine | Leiter ohne Terminal-Anschluss |
| CROSS_REF_MISMATCH | Engine | master/slave-Paar ohne Gegenpart |
| WIRE_GAUGE_MISMATCH | EN 60204-1 | Querschnitt vs. Nennstrom + Verlegeart |

---

### Phase 5: JSON-Schema + Claude-Code-Skill

Finales JSON-Schema mit strikter Validierung. Dazu ein Claude-Code-Skill (SKILL.md),
der Claude Opus exakt erklärt, wie das JSON aufgebaut sein muss.

---

## Erster Schritt: Source-Code-Analyse

### Aufgabe für Claude Code

Bevor irgendein Code geschrieben wird, analysiere den QET-Quellcode:

1. **Finde und lies** die Dateien die für das Laden/Speichern von .qet-Projekten zuständig sind
2. **Finde und lies** die Dateien die .elmt-Elemente parsen
3. **Finde und lies** wie Conductor (Leiter) gespeichert und geladen werden
4. **Finde und lies** wie Terminal-Referenzen aufgelöst werden (UUID vs. numerische ID)
5. **Finde und lies** wie `common://` Pfade aufgelöst werden
6. **Finde und lies** wie die absolute Position eines Terminals berechnet wird
   (Element-Position + Hotspot + Terminal-Offset + Rotation)

**Erstelle** das Dokument `docs/qet-internals.md` mit allen Erkenntnissen.
Zitiere relevante Codezeilen mit Datei und Zeilennummer.

**Danach**: Sammle 10-15 der wichtigsten .elmt-Dateien und dokumentiere ihre
exakte Terminal-Struktur (IDs, Positionen, Orientierungen, Namen) in einer Tabelle.

### Wo im Source Code anfangen

Wahrscheinlich relevante Einstiegspunkte (verifizieren!):
- `sources/qetproject.cpp` / `.h` — Projekt laden/speichern
- `sources/diagram.cpp` / `.h` — Folio/Diagramm
- `sources/element.cpp` / `.h` — Element auf dem Folio
- `sources/conductor.cpp` / `.h` — Leiter
- `sources/terminal.cpp` / `.h` — Terminal
- `sources/elementslocation.cpp` — Pfadauflösung (common://, embed://)
- `sources/qetxml.cpp` — XML Serialisierung/Deserialisierung
- `elements/` — Die Element-Sammlung

---

## Langfristige Vision

Diese Engine ist Phase 1 einer größeren Roadmap:

1. **Engine (dieses Projekt)** — Deterministischer Schaltplan-Generator in Python
2. **QET-AI Fork** — Engine in QET integriert (C++/Qt6), CLI + MCP-Server
3. **Claude-Code-Skill** — Opus erzeugt JSON per Spracheingabe → Engine baut Plan
4. **Erweiterung** — Weitere Templates, Klemmenplan-Generator, Stücklisten, 
   Schaltschrank-Layout, DXF-Export

Das Ziel: Aus einer Spracheingabe wie "Messerschleifmaschine, Spindelmotor 1.5kW,
Vorschub Leadshine Servo EtherCAT, WAGO PFC200, zwei Not-Halt, eine Schutztür"
entsteht in Sekunden ein vollständiger, normkonformer, professioneller Schaltplan.

---

## Projektstruktur (Ziel)

```
qet-ai-engine/
├── README.md
├── docs/
│   ├── qet-internals.md          ← Ergebnis der Source-Code-Analyse
│   ├── json-schema.md            ← Schema-Dokumentation
│   └── templates.md              ← Template-Katalog
├── src/
│   ├── element_db/               ← .elmt Parser + Terminal-Datenbank
│   │   ├── __init__.py
│   │   ├── parser.py
│   │   ├── database.py
│   │   └── models.py
│   ├── templates/                ← Circuit-Templates
│   │   ├── __init__.py
│   │   ├── base.py               ← Basis-Klasse für Templates
│   │   ├── motor_starter.py
│   │   ├── safety_circuit.py
│   │   ├── plc_io.py
│   │   └── ...
│   ├── layout/                   ← Positionierung + Routing
│   │   ├── __init__.py
│   │   ├── placer.py
│   │   └── router.py
│   ├── validator/                ← DRC / Constraint-Checks
│   │   ├── __init__.py
│   │   ├── rules.py
│   │   └── checker.py
│   ├── writer/                   ← .qet XML-Erzeugung
│   │   ├── __init__.py
│   │   └── qet_writer.py
│   ├── renderer/                 ← SVG-Rendering (Self-Verification)
│   │   ├── __init__.py
│   │   └── svg_renderer.py
│   └── engine.py                 ← Haupteinstieg: JSON → .qet
├── tests/
│   ├── test_element_db.py
│   ├── test_templates.py
│   ├── test_layout.py
│   ├── test_validator.py
│   ├── test_writer.py
│   ├── test_renderer.py
│   └── test_engine_e2e.py
├── schemas/
│   └── qet-ai-v1.json           ← JSON-Schema (strict)
└── aliases/
    └── default.json              ← Element-Alias → common://-Pfad Mapping
```

---

## Methodologie

- **Spec → Tests → Implementation** (TDD, strikt)
- **Keine Phase beginnt bevor die vorherige grün ist**
- **Self-Verification**: SVG-Rendering + programmatische Checks nach jedem Schritt
- **Dokumentation**: Jede Erkenntnis aus der Source-Code-Analyse wird festgehalten
- **Inkrementell**: Ein Template nach dem anderen, jedes vollständig getestet
