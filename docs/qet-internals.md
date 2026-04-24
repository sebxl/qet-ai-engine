# QElectroTech Internals -- Source-Code-Analyse

Dieses Dokument fasst die Erkenntnisse aus der systematischen Analyse des
QElectroTech-Quellcodes zusammen. Ziel: Vollstaendiges Verstaendnis des
.qet-Dateiformats und der .elmt-Elementdateien, um eine deterministische
Engine zu bauen, die valide .qet-Projektdateien erzeugt.

Quellcode-Basis: `qelectrotech-source-mirror/`

---

## 1. Projekt-Dateiformat (.qet)

### 1.1 XML-Grundstruktur

Eine .qet-Datei ist ein XML-Dokument mit folgendem Aufbau:

```xml
<project title="Projekttitel" version="0.90">

    <properties>
        <property show="1" name="saveddate">17/04/2021</property>
        <property show="1" name="saveddate-eu">17-04-2021</property>
        <property show="1" name="saveddate-us">2021-04-17</property>
        <property show="1" name="savedtime">14:30</property>
        <property show="1" name="savedfilename">projekt.qet</property>
        <property show="1" name="savedfilepath">/pfad/zu/projekt.qet</property>
    </properties>

    <newdiagrams>
        <border cols="17" colsize="60" rows="8" rowsize="80"
                displaycols="true" displayrows="true"/>
        <inset displayAt="bottom" title="" author="" folio="%id/%total"
               date="" filename="" plant="" locmach="" indexrev="" version=""/>
        <conductors type="multi" condsize="1" num="" formula=""
                    displaytext="1" text_color="#000000" numsize="9"
                    onetextperfolio="0" ... />
        <report label="%f-%l%c"/>
        <xrefs>
            <xref type="coil" master_label="%f-%l%c" slave_label="(%f-%l%c)" .../>
            <xref type="protection" .../>
            <xref type="commutator" .../>
        </xrefs>
        <conductors_autonums current_autonum="" freeze_new_conductors="false"/>
        <folio_autonums/>
        <element_autonums current_autonum="" freeze_new_elements="false"/>
    </newdiagrams>

    <titleblocktemplates>
        <!-- Optional: eingebettete Schriftfeld-Vorlagen -->
    </titleblocktemplates>

    <diagram ... order="1">
        <!-- Folio 1 -->
    </diagram>

    <diagram ... order="2">
        <!-- Folio 2 -->
    </diagram>

    <terminal_strips>
        <!-- Optional: Klemmleisten-Definitionen -->
    </terminal_strips>

    <collection>
        <!-- Eingebettete Elemente (embed://) -->
    </collection>

</project>
```

**Quellcode-Referenz:**
- `sources/qetproject.h` (Zeilen 18-302) -- QETProject-Klasse
- `sources/qetproject.cpp` (1640+ Zeilen) -- Implementierung
- `toXml()`: Zeile 918-998 -- Serialisierung
- `readProjectXml()`: Zeile 1344 -- Haupt-Dispatcher beim Laden

### 1.2 Lade-Reihenfolge

`QETProject::readProjectXml()` (Zeile 1344) ruft nacheinander auf:

1. `readProjectPropertiesXml()` (Zeile 1416) -- `<properties>`
2. `readDefaultPropertiesXml()` (Zeile 1419) -- `<newdiagrams>`
3. `m_titleblocks_collection.fromXml()` (Zeile 1422) -- `<titleblocktemplates>`
4. `readElementsCollectionXml()` (Zeile 1425) -- `<collection>`
5. `readDiagramsXml()` (Zeile 1428) -- `<diagram>`-Elemente
6. `readTerminalStripXml()` (Zeile 1431) -- `<terminal_strips>`
7. `refresh()` (Zeile 1434) -- Aktualisierung

### 1.3 Speicher-Reihenfolge

`QETProject::toXml()` (Zeile 918) erzeugt:

1. Root-Element `<project>` mit `title` und `version`
2. `<titleblocktemplates>` (Zeile 934-940)
3. `<properties>` via `writeProjectPropertiesXml()` (Zeile 944-946)
4. `<newdiagrams>` via `writeDefaultPropertiesXml()` (Zeile 949-951)
5. Jedes `<diagram>` via `diagram->toXml()` (Zeile 957-970)
6. `<terminal_strips>` (Zeile 973-979)
7. `<collection>` Root-Element (Zeile 983)

### 1.4 Version

Das `version`-Attribut auf `<project>` und `<diagram>` muss gesetzt werden.
Aktuelle Version: `"0.90"` (oder `"0.100.0"` fuer neuere Elemente).
Wird via `QetVersion::toXmlAttribute()` geschrieben (Zeile 923).

---

## 2. Diagramm / Folio

### 2.1 XML-Struktur

```xml
<diagram
    title="Folio-Titel"
    author="Autor"
    version="0.90"
    order="1"
    date="20210417"
    filename="projekt.qet"
    folio="%id/%total"
    auto_page_num=""
    plant=""
    locmach=""
    indexrev=""
    height="660"
    rows="8" rowsize="80"
    cols="17" colsize="60"
    displayrows="true" displaycols="true"
    displayAt="bottom"
    freezeNewElement="false"
    freezeNewConductor="false"
    >

    <defaultconductor type="multi" condsize="1" num="" formula=""
        displaytext="1" text_color="#000000" numsize="9" ... />

    <elements>
        <element ... />
        <element ... />
    </elements>

    <conductors>
        <conductor ... />
    </conductors>

    <inputs>
        <!-- Unabhaengige Textfelder -->
    </inputs>

    <images>
        <!-- Eingebettete Bilder -->
    </images>

    <shapes>
        <!-- Grafische Formen (Rechtecke, Linien, etc.) -->
    </shapes>

    <tables>
        <!-- Tabellen -->
    </tables>

</diagram>
```

**Quellcode-Referenz:**
- `sources/diagram.h` (Zeilen 18-425)
- `sources/diagram.cpp` -- `toXml()` Zeilen 771-1037, `fromXml()` Zeilen 1102-1254

### 2.2 Koordinatensystem

| Eigenschaft | Wert | Einheit |
|-------------|------|---------|
| Ursprung | Oben-links (0, 0) | Pixel |
| X-Achse | Links nach rechts | Pixel |
| Y-Achse | Oben nach unten | Pixel |
| Raster X/Y | 10 x 10 | Pixel |
| Feines Raster | 1 x 1 | Pixel |
| Standard-Spalten | 17 Spalten x 60 px = 1020 px | Pixel |
| Standard-Zeilen | 8 Zeilen x 80 px = 640 px | Pixel |
| Rand (margin) | 5.0 | Pixel |
| Spalten-Header-Hoehe | 20.0 | Pixel |
| Zeilen-Header-Breite | 20.0 | Pixel |

**Quellcode-Referenz:**
- Grid-Konstanten: `diagram.h` Zeilen 85-97
- Border-Defaults: `sources/borderproperties.cpp` Zeilen 35-45

### 2.3 Schriftfeld (Title Block)

Das Schriftfeld wird ueber `<inset>`-Attribute in `<newdiagrams>` definiert
und ueber die Diagramm-Attribute gesetzt.

**Felder:**
- `title` -- Titel des Folios
- `author` -- Autor
- `date` -- Datum (Format: YYYYMMDD oder DD/MM/YYYY)
- `filename` -- Dateiname
- `folio` -- Folio-Format (z.B. `"%id/%total"`)
- `plant` -- Anlage
- `locmach` -- Ort/Maschine
- `indexrev` -- Revisionsindex
- `version` -- Version
- `auto_page_num` -- Automatische Seitennummerierung
- `displayAt` -- Position: `"bottom"` oder `"right"`

**Quellcode-Referenz:**
- `sources/titleblockproperties.h` Zeilen 24-74
- `sources/titleblockproperties.cpp` Zeilen 77-133
- `sources/bordertitleblock.cpp` Zeilen 212-281

---

## 3. Elemente auf dem Folio

### 3.1 Element-Platzierung (XML)

```xml
<element
    type="common://10_electric/10_allpole/310_.../bobine3.elmt"
    uuid="{52d4b9e8-05c3-49a2-8455-a42ff651200a}"
    x="280"
    y="300"
    z="10"
    orientation="0"
    prefix="K"
    freezeLabel="false"
    >

    <terminals>
        <terminal x="0" y="-20" orientation="0" id="0"
                  uuid="{8d0fa333-2d98-4a75-8a4e-21c81cce7ec3}"/>
        <terminal x="0" y="20"  orientation="2" id="1"
                  uuid="{c5376fd7-bdf1-4c10-985a-0d7d5f52c8f9}"/>
    </terminals>

    <inputs/>

    <elementInformations>
        <elementInformation show="1" name="label">K1</elementInformation>
        <elementInformation show="1" name="description">Schuetz</elementInformation>
    </elementInformations>

    <dynamic_texts>
        <dynamic_elmt_text
            x="25" y="-9.17" z="6"
            rotation="0"
            uuid="{3ef105d2-...}"
            Halignment="AlignLeft" Valignment="AlignTop"
            font="Liberation Sans,9,-1,5,50,0,0,0,0,0,Regular"
            text_width="-1"
            frame="false"
            keep_visual_rotation="false"
            text_from="ElementInfo">
            <text>K1</text>
            <info_name>label</info_name>
        </dynamic_elmt_text>
    </dynamic_texts>

    <texts_groups/>

    <links_uuids>
        <!-- Fuer master/slave-Verknuepfungen -->
        <link_uuid uuid="{uuid-des-verknuepften-elements}"/>
    </links_uuids>

</element>
```

### 3.2 Element-Attribute

| Attribut | Typ | Beschreibung |
|----------|-----|--------------|
| `type` | String | Element-Pfad (`common://...`, `embed://...`) |
| `uuid` | UUID | Eindeutige Instanz-ID `{XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX}` |
| `x` | qreal | X-Position auf dem Folio (Pixel) |
| `y` | qreal | Y-Position auf dem Folio (Pixel) |
| `z` | qreal | Z-Ordnung (Tiefensortierung) |
| `orientation` | int | 0=0deg, 1=90deg, 2=180deg, 3=270deg |
| `prefix` | String | Bezeichnungs-Praefix (z.B. "K", "F", "M") |
| `freezeLabel` | bool | Label eingefroren (keine Auto-Nummerierung) |

**Quellcode-Referenz:**
- `sources/qetgraphicsitem/element.cpp` Zeilen 858-1000 (`toXml()`)
- Orientation-Berechnung: `element.h` Zeilen 264-273:
  `orientation() = QET::correctAngle(rotation()) / 90`

---

## 4. Element-Dateiformat (.elmt)

### 4.1 XML-Grundstruktur

```xml
<definition
    type="element"
    version="0.100.0"
    width="40"
    height="60"
    hotspot_x="20"
    hotspot_y="32"
    link_type="master"
    >

    <uuid uuid="{793302b1-e96a-f7f8-70bc-dec53eeaab5b}"/>

    <names>
        <name lang="de">Spule</name>
        <name lang="en">Coil</name>
        <name lang="fr">Bobine</name>
    </names>

    <kindInformations>
        <kindInformation name="type">coil</kindInformation>
    </kindInformations>

    <elementInformations>
        <elementInformation name="label">_</elementInformation>
    </elementInformations>

    <informations>Author: The QElectroTech team</informations>

    <description>
        <!-- Grafik-Primitive -->
        <rect x="-14" y="-8" width="28" height="16" rx="0" ry="0"
              style="line-style:normal;line-weight:normal;filling:none;color:black"
              antialias="false"/>
        <line x1="0" y1="-20" x2="0" y2="-8" end1="none" end2="none"
              length1="1.5" length2="1.5"
              style="line-style:normal;line-weight:normal;filling:none;color:black"
              antialias="false"/>

        <!-- Terminals (Anschlusspunkte) -->
        <terminal uuid="{8d0fa333-...}" name="A1" x="0" y="-20"
                  orientation="n" type="Generic"/>
        <terminal uuid="{c5376fd7-...}" name="A2" x="0" y="20"
                  orientation="s" type="Generic"/>

        <!-- Dynamische Texte -->
        <dynamic_text x="25" y="-9.17" z="6" text_width="-1"
                      text_from="ElementInfo" uuid="{3ef105d2-...}"
                      font="Liberation Sans,9,...">
            <text></text>
            <info_name>label</info_name>
        </dynamic_text>
    </description>
</definition>
```

**Quellcode-Referenz:**
- Element-Laden: `sources/qetgraphicsitem/element.cpp` Zeilen 384-643 (`buildFromXml()`)
- ElementData: `sources/properties/elementdata.h` Zeilen 31-167
- TerminalData: `sources/properties/terminaldata.h` Zeilen 18-120

### 4.2 Definition-Attribute

| Attribut | Typ | Beschreibung |
|----------|-----|--------------|
| `type` | String | Muss `"element"` sein |
| `version` | String | Format-Version (z.B. `"0.100.0"`) |
| `width` | int | Breite in Pixel |
| `height` | int | Hoehe in Pixel |
| `hotspot_x` | int | Hotspot X-Koordinate |
| `hotspot_y` | int | Hotspot Y-Koordinate |
| `link_type` | String | Verknuepfungstyp (siehe 4.3) |

### 4.3 link_type-Werte

| link_type | Enum-Wert | Zweck |
|-----------|-----------|-------|
| `"simple"` | 1 | Unabhaengiges Element (Standard) |
| `"next_report"` | 2 | Naechste Seite Fortsetzung |
| `"previous_report"` | 4 | Vorherige Seite Fortsetzung |
| `"master"` | 8 | Master-Element (Spule, Schuetz) |
| `"slave"` | 16 | Slave-Element (Kontakt, gesteuert durch Master) |
| `"terminal"` | 32 | Klemmen-Element |
| `"thumbnail"` | 64 | Thumbnail-Darstellung |

**Quellcode-Referenz:** `sources/properties/elementdata.cpp` Zeilen 309-391

### 4.4 kindInformations

**Fuer Master-Elemente:**
```xml
<kindInformations>
    <kindInformation name="type">coil</kindInformation>        <!-- oder: protection, commutator -->
    <kindInformation name="max_slaves">10</kindInformation>     <!-- optional -->
</kindInformations>
```

**Fuer Slave-Elemente:**
```xml
<kindInformations>
    <kindInformation name="type">simple</kindInformation>       <!-- simple, power, delayOn, delayOff, delayOnOff -->
    <kindInformation name="state">NO</kindInformation>          <!-- NO, NC, SW, Other -->
    <kindInformation name="number">1</kindInformation>
</kindInformations>
```

**Fuer Terminal-Elemente:**
```xml
<kindInformations>
    <kindInformation name="type">generic</kindInformation>      <!-- Generic, Fuse, Sectional, Diode, Ground -->
    <kindInformation name="function">generic</kindInformation>  <!-- Generic, Phase, Neutral -->
</kindInformations>
```

**Quellcode-Referenz:** `sources/properties/elementdata.cpp` Zeilen 66-133

### 4.5 Grafik-Primitive

Alle Primitive stehen innerhalb von `<description>` und unterstuetzen ein
`style`-Attribut im CSS-aehnlichen Format:

```
style="line-style:normal;line-weight:normal;filling:none;color:black"
```

**Style-Eigenschaften:**

| Eigenschaft | Werte |
|-------------|-------|
| `line-style` | `normal`, `dashed`, `dotted`, `dashdotted` |
| `line-weight` | `none`, `thin`, `normal`, `hight`, `eleve` |
| `filling` | `none`, `white`, `black`, `red`, `green`, `blue`, `gray`, `yellow`, `cyan`, `magenta`, `orange`, `purple`, ... |
| `color` | Gleiche Farbwerte wie `filling` |
| `antialias` | `true`, `false` |

**Quellcode-Referenz:** `sources/editor/graphicspart/customelementgraphicpart.cpp` Zeilen 517-700+

#### LINE
```xml
<line x1="0" y1="-20" x2="0" y2="-8"
      end1="none" end2="none"
      length1="1.5" length2="1.5"
      style="..." antialias="false"/>
```
- `end1/end2`: `none`, `circle`, `triangle`, `simple_arrow`, `double_arrow`
- Ref: `sources/editor/graphicspart/partline.cpp` Zeilen 137-148

#### RECT
```xml
<rect x="-14" y="-8" width="28" height="16"
      rx="0" ry="0"
      style="..." antialias="false"/>
```
- `rx/ry`: Abrundungsradien
- Ref: `sources/editor/graphicspart/partrectangle.cpp` Zeilen 110-122

#### ELLIPSE / CIRCLE
```xml
<ellipse x="-15" y="-15" width="30" height="30"
         style="..." antialias="true"/>

<circle x="-15" y="-15" diameter="30"
        style="..." antialias="true"/>
```
- Ref: `sources/editor/graphicspart/partellipse.cpp` Zeilen 114-130

#### ARC
```xml
<arc x="-14.5" y="-15.5" width="32" height="32"
     start="300" angle="80"
     style="..." antialias="true"/>
```
- `start`: Startwinkel in Grad
- `angle`: Bogenwinkel in Grad
- Intern als 16tel-Grad gespeichert (x16)
- Ref: `sources/editor/graphicspart/partarc.cpp` Zeilen 126-135

#### POLYGON
```xml
<polygon x1="-20" y1="-30" x2="-20" y2="-20" x3="-11" y3="-11"
         closed="false"
         style="..." antialias="false"/>
```
- Punkte: `x1,y1`, `x2,y2`, `x3,y3`, ... `xN,yN` (sequenziell)
- `closed`: `true` (geschlossen) oder `false` (offen, Polylinie)
- Ref: `sources/editor/graphicspart/partpolygon.cpp` Zeilen 85-108

#### TEXT (statisch)
```xml
<text text="M" x="-6" y="0" rotation="0"
      font="Liberation Sans,11,-1,5,50,0,0,0,0,0,Regular"
      color="#000000"/>
```
- Ref: `sources/editor/graphicspart/parttext.cpp` Zeilen 113-136

#### DYNAMIC_TEXT
```xml
<dynamic_text x="25" y="-9.17" z="6"
              text_width="-1"
              Halignment="AlignLeft" Valignment="AlignTop"
              frame="false" rotation="0"
              keep_visual_rotation="false"
              text_from="ElementInfo"
              uuid="{...}"
              font="Liberation Sans,9,...">
    <text>K1</text>
    <info_name>label</info_name>
</dynamic_text>
```
- `text_from`: `ElementInfo`, `UserText`, `CustomInfo`
- Ref: `sources/editor/graphicspart/partdynamictextfield.cpp` Zeilen 200-270

---

## 5. Terminals (Anschlusspunkte)

### 5.1 Terminal-Definition in .elmt

```xml
<terminal
    uuid="{8d0fa333-2d98-4a75-8a4e-21c81cce7ec3}"
    name="A1"
    x="0"
    y="-20"
    orientation="n"
    type="Generic"
/>
```

| Attribut | Typ | Beschreibung |
|----------|-----|--------------|
| `uuid` | UUID | Eindeutige Terminal-ID (modern) |
| `name` | String | Terminal-Bezeichnung (z.B. "A1", "U1", "1") |
| `x` | qreal | X-Position relativ zum Element-Koordinatensystem |
| `y` | qreal | Y-Position relativ zum Element-Koordinatensystem |
| `orientation` | String | Richtung: `"n"` (North), `"s"` (South), `"e"` (East), `"w"` (West) |
| `type` | String | `"Generic"`, `"Inner"`, `"Outer"` |

**Quellcode-Referenz:**
- `sources/properties/terminaldata.h` Zeilen 36-119
- `sources/properties/terminaldata.cpp` Zeilen 125-161 (`fromXml()`)

### 5.2 Orientierungswerte

| String (.elmt) | Int (diagram) | Richtung | Grad |
|-----------------|---------------|----------|------|
| `"n"` / `"North"` | 0 | Oben | 0deg |
| `"e"` / `"East"` | 1 | Rechts | 90deg |
| `"s"` / `"South"` | 2 | Unten | 180deg |
| `"w"` / `"West"` | 3 | Links | 270deg |

**Hinweis:** In .elmt-Dateien werden die Kurzformen `n`, `s`, `e`, `w` verwendet.
Im Diagramm-XML werden numerische Werte (0-3) gespeichert.

### 5.3 Identifikation: UUID vs. numerische ID

QET unterstuetzt zwei Systeme parallel:

**Modern (ab ~v0.7):** UUID-basiert
```xml
<conductor terminal1="{uuid}" terminal2="{uuid}"
           element1="{element-uuid}" element2="{element-uuid}" ... />
```

**Legacy:** Numerische ID (Index innerhalb des Elements)
```xml
<conductor terminal1="0" terminal2="10" ... />
```

Beim Speichern werden beide Formate geschrieben fuer Abwaertskompatibilitaet.

**Quellcode-Referenz:**
- `sources/diagram.cpp` Zeilen 1166-1221 (`findTerminal()`)
- `sources/qetgraphicsitem/conductor.cpp` Zeilen 1050-1080

### 5.4 KRITISCH: Absolute Terminal-Position auf dem Folio

Die Position eines Terminals auf dem Folio wird durch Qt's
Graphics-Transformations-System berechnet:

```
Terminal_Absolut = Element.mapToScene(Terminal.m_pos)
```

**Detaillierte Formel:**

1. **Element-Position** auf dem Folio: `element.pos()` = `(x, y)` aus dem XML
2. **Element-Rotation**: `orientation * 90deg` (via `setRotation()`)
3. **Element-Hotspot**: Definiert den Ursprung des Elements. Die BoundingRect ist:
   `QRectF(-hotspot_x, -hotspot_y, width, height)`
4. **Terminal-Position**: `TerminalData.m_pos` = `(x, y)` relativ zum Element-Koordinatensystem

Die Transformation wird von Qt automatisch durchgefuehrt:
```cpp
// terminal.cpp, Zeile 722-725
QPointF Terminal::dockConductor() const {
    return(mapToScene(d->m_pos));
}
```

**Manuelle Berechnung (fuer unsere Engine):**

Fuer Rotation `r` (0, 90, 180, 270 Grad):
```
cos_r, sin_r = cos(r), sin(r)

terminal_scene_x = element_x + (terminal_x * cos_r - terminal_y * sin_r)
terminal_scene_y = element_y + (terminal_x * sin_r + terminal_y * cos_r)
```

Wobei `element_x` und `element_y` direkt die `x`/`y`-Attribute aus dem
Diagramm-XML sind (Element-Hotspot ist bereits im Koordinatensystem
beruecksichtigt -- die Position bezieht sich auf den Hotspot-Punkt).

**Quellcode-Referenz:**
- `sources/qetgraphicsitem/terminal.cpp` Zeilen 722-725 (`dockConductor()`)
- `sources/qetgraphicsitem/element.cpp` Zeile 760 (`setPos()`) und Zeile 772 (`setRotation()`)

### 5.5 Conductor Dock Point

Der tatsaechliche Andock-Punkt fuer Leiter ist um `Terminal::terminalSize`
(4.0 Pixel) in Richtung der Terminal-Orientierung verschoben:

```cpp
// terminal.cpp, Zeilen 49-55
dock_elmt_ = d->m_pos;
switch(d->m_orientation) {
    case Qet::North: dock_elmt_ += QPointF(0, Terminal::terminalSize);  break;  // +4 nach unten
    case Qet::East:  dock_elmt_ += QPointF(-Terminal::terminalSize, 0); break;  // -4 nach links
    case Qet::West:  dock_elmt_ += QPointF(Terminal::terminalSize, 0);  break;  // +4 nach rechts
    case Qet::South: dock_elmt_ += QPointF(0, -Terminal::terminalSize); break;  // -4 nach oben
}
```

**Hinweis:** `dock_elmt_` ist der Punkt innerhalb des Elements, an dem der
Leiter andockt. `m_pos` ist der Punkt am Rand des Elements (wo das Terminal-
Stueck endet). Der Leiter verbindet sich an `m_pos`, nicht an `dock_elmt_`.
Die `dockConductor()`-Methode gibt `mapToScene(m_pos)` zurueck.

### 5.6 Rotation und Terminal-Orientierung

Bei Element-Rotation aendert sich die effektive Terminal-Orientierung:

```cpp
// terminal.cpp, Zeilen 103-120
Qet::Orientation Terminal::orientation() const {
    if (Element *elt = parentItem()) {
        int ori_cur = elt->orientation();  // 0, 1, 2, 3
        if (ori_cur == 0) return d->m_orientation;
        else {
            int angle = ori_cur + d->m_orientation;
            while (angle >= 4) angle -= 4;
            return (Qet::Orientation)angle;
        }
    }
    return d->m_orientation;
}
```

**Beispiel:** Terminal mit `orientation="n"` (0) + Element `orientation=1` (90deg)
= effektive Orientierung `"e"` (1 = East).

---

## 6. Leiter (Conductors)

### 6.1 XML-Struktur

```xml
<conductor
    terminal1="{terminal-uuid-1}"
    terminal2="{terminal-uuid-2}"
    element1="{element-uuid-1}"
    element1_label="K1"
    element1_name="Spule"
    terminalname1="A1"
    element2="{element-uuid-2}"
    element2_label="S1"
    element2_name="Taster"
    terminalname2=""
    x="0" y="0"
    type="multi"
    condsize="1"
    num=""
    formula=""
    displaytext="1"
    text_color="#000000"
    numsize="9"
    color="#000000"
    color2="#000000"
    bicolor="false"
    dash-size="1"
    freezeLabel="false"
    horizrotatetext="0"
    vertirotatetext="0"
    horizontal-alignment="AlignBottom"
    vertical-alignment="AlignRight"
    onetextperfolio="0"
    cable=""
    bus=""
    function=""
    conductor_color=""
    conductor_section=""
    tension_protocol=""
    >

    <!-- Routing-Segmente (nur wenn manuell bearbeitet) -->
    <segment orientation="vertical" length="-14"/>
    <segment orientation="horizontal" length="70"/>
    <segment orientation="vertical" length="76"/>

    <sequentialNumbers/>
</conductor>
```

### 6.2 Endpunkt-Referenzierung

**Modern (UUID):**
- `terminal1` / `terminal2` -- Terminal-UUID
- `element1` / `element2` -- Element-UUID
- `terminalname1` / `terminalname2` -- Terminal-Name
- `element1_label` / `element2_label` -- Element-Label

**Legacy (Integer-Index):**
- `terminal1="0"` / `terminal2="10"` -- Numerischer Terminal-Index

Beide Formate koennen gemischt auftreten.

**Quellcode-Referenz:**
- `sources/qetgraphicsitem/conductor.cpp` Zeilen 603-634 (`valideXml()`)
- Zeilen 1040-1112 (`toXml()`)

### 6.3 Routing-Segmente

Segmente werden nur gespeichert wenn `modified_path == true` (manuell bearbeitet).
Sonst wird der Pfad automatisch generiert.

```xml
<segment orientation="vertical" length="-14"/>
<segment orientation="horizontal" length="100"/>
```

- `orientation`: `"horizontal"` oder `"vertical"`
- `length`: Laenge in Pixel (negativ = Gegenrichtung)

**Intern:** Doubly-Linked-List von `ConductorSegment`-Objekten.

**Quellcode-Referenz:**
- `sources/conductorsegment.h` Zeilen 18-71
- `sources/qetgraphicsitem/conductor.cpp` Zeilen 1085-1096 (Serialisierung)
- Zeilen 1121-1191 (`pathFromXml()` -- Laden)

### 6.4 Leiter-Eigenschaften

| Attribut | Beschreibung |
|----------|--------------|
| `type` | `"multi"` (Mehradrig) oder `"single"` (Einpolig-Schema) |
| `condsize` | Linienstaerke (1 = Standard) |
| `num` | Leiter-Nummer/Label |
| `formula` | Auto-Nummerierungs-Formel |
| `displaytext` | `"1"` = Label anzeigen, `"0"` = verstecken |
| `color` | Leiterfarbe (Hex, z.B. `"#000000"`) |
| `conductor_section` | Querschnitt (z.B. `"1.5mm2"`) |
| `cable` | Kabel-Bezeichnung |
| `function` | Funktion |
| `tension_protocol` | Spannungsprotokoll |

---

## 7. Element-Pfad-System

### 7.1 Protokolle

| Protokoll | Beschreibung | Dateisystem |
|-----------|--------------|-------------|
| `common://` | Standard-Elemente (mit QET ausgeliefert) | `{app_dir}/elements/` |
| `custom://` | Benutzer-Elemente | `{AppDataLocation}/elements/` |
| `company://` | Firmen-Elemente | `{AppDataLocation}/elements-company/` |
| `embed://` | Im Projekt eingebettet | In `<collection>` der .qet-Datei |

### 7.2 Pfad-Aufloesung

Die Klasse `ElementsLocation` (Zeilen 35-114 in
`sources/ElementsCollection/elementslocation.h`) verwaltet die Pfad-Aufloesung.

**`setPath()` Logik** (`elementslocation.cpp` Zeilen 235-364):

1. Wenn `m_project` gesetzt: automatisch `embed://` voranstellen
2. Multi-Projekt-Format: `project<N>+embed://pfad` -- Regex-Match
3. Protokoll-Erkennung: `common://`, `custom://`, `company://` abschneiden
   und Dateisystem-Pfad konstruieren via `QETApp::commonElementsDirN() + "/" + pfad`
4. Absolute Dateisystem-Pfade: Erkennung welche Collection, Umwandlung in Protokoll

**Quellcode-Referenz:**
- `sources/ElementsCollection/elementslocation.cpp` Zeilen 235-364
- `sources/qetapp.cpp` Zeilen 539-705 (Verzeichnis-Aufloesung)

### 7.3 Eingebettete Elemente (`embed://`)

Eingebettete Elemente werden in der `<collection>` des Projekts gespeichert:

```xml
<collection>
    <category name="import">
        <names>
            <name lang="en">Imported elements</name>
        </names>
        <category name="subdir">
            <names>...</names>
            <element name="element.elmt">
                <definition type="element" ...>
                    <!-- Komplette Element-Definition -->
                </definition>
            </element>
        </category>
    </category>
</collection>
```

Der Pfad `embed://import/subdir/element.elmt` entspricht der hierarchischen
Verschachtelung der `<category>`/`<element>`-Tags.

### 7.4 Empfehlung fuer die Engine

Fuer unsere Engine verwenden wir `common://`-Pfade, da wir die
Standard-Elemente referenzieren und nicht einbetten wollen. Der Vorteil:
- Kleinere .qet-Dateien
- Konsistenz mit der installierten QET-Version
- Keine Duplikate

**Wichtig:** Die `<collection>`-Sektion muss trotzdem vorhanden sein (kann leer sein):
```xml
<collection/>
```

---

## 8. Querverweise (Cross-References / Master-Slave)

### 8.1 Konzept

Ein **Master-Element** (z.B. Schuetzspule K1) kann mit mehreren
**Slave-Elementen** (z.B. K1-Kontakten) verknuepft werden. QET zeigt
dann automatisch Querverweise an.

### 8.2 Verknuepfung im XML

Im Master-Element:
```xml
<element type="..." uuid="{master-uuid}" ...>
    <links_uuids>
        <link_uuid uuid="{slave-1-uuid}"/>
        <link_uuid uuid="{slave-2-uuid}"/>
    </links_uuids>
</element>
```

Im Slave-Element:
```xml
<element type="..." uuid="{slave-1-uuid}" ...>
    <links_uuids>
        <link_uuid uuid="{master-uuid}"/>
    </links_uuids>
</element>
```

### 8.3 Querverweis-Anzeige

Konfiguriert in `<newdiagrams>`:
```xml
<xrefs>
    <xref type="coil" master_label="%f-%l%c" slave_label="(%f-%l%c)" .../>
    <xref type="protection" .../>
    <xref type="commutator" .../>
</xrefs>
```

Die Platzhalter:
- `%f` -- Folio-Nummer
- `%l` -- Zeile (Row-Buchstabe)
- `%c` -- Spalte (Column-Nummer)

---

## 9. Minimale valide .qet-Datei

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project title="Minimal" version="0.90">
    <properties/>
    <newdiagrams>
        <border cols="17" colsize="60" rows="8" rowsize="80"
                displaycols="true" displayrows="true"/>
        <inset displayAt="bottom" title="" author="" folio="%id/%total"
               date="" filename="" plant="" locmach="" indexrev="" version=""/>
        <conductors type="multi" condsize="1" num="" formula=""
                    displaytext="1" text_color="#000000" numsize="9"
                    dash-size="1" color2="#000000" horizrotatetext="0"
                    vertirotatetext="0" horizontal-alignment="AlignBottom"
                    vertical-alignment="AlignRight" onetextperfolio="0"
                    bicolor="false" conductor_color="" cable="" bus=""
                    function="" conductor_section="" tension_protocol=""/>
        <report label="%f-%l%c"/>
        <xrefs>
            <xref type="coil" master_label="%f-%l%c" slave_label="(%f-%l%c)"/>
            <xref type="protection" master_label="%f-%l%c" slave_label="(%f-%l%c)"/>
            <xref type="commutator" master_label="%f-%l%c" slave_label="(%f-%l%c)"/>
        </xrefs>
        <conductors_autonums current_autonum="" freeze_new_conductors="false"/>
        <folio_autonums/>
        <element_autonums current_autonum="" freeze_new_elements="false"/>
    </newdiagrams>
    <diagram title="Folio 1" author="" version="0.90" order="1"
             date="" folio="%id/%total" rows="8" rowsize="80"
             cols="17" colsize="60" displayrows="true" displaycols="true"
             displayAt="bottom" height="660"
             freezeNewElement="false" freezeNewConductor="false">
        <defaultconductor type="multi" condsize="1" num="" formula=""
                          displaytext="1" text_color="#000000" numsize="9"
                          dash-size="1" color2="#000000" horizrotatetext="0"
                          vertirotatetext="0"
                          horizontal-alignment="AlignBottom"
                          vertical-alignment="AlignRight"
                          onetextperfolio="0" bicolor="false"/>
        <elements/>
        <conductors/>
        <inputs/>
    </diagram>
    <collection/>
</project>
```

---

## 10. Terminal-Struktur wichtiger Elemente

### 10.1 Schuetzspule (Contactor Coil) -- Master

**Pfad:** `10_electric/10_allpole/310_relays_contactors_contacts/01_coils/bobine3.elmt`
**link_type:** `master` | **kindInfo type:** `coil`
**Dimensionen:** 40x60, Hotspot: (20, 32)

| Terminal | Name | X | Y | Orientierung |
|----------|------|---|---|--------------|
| 1 | A1 | 0 | -20 | north |
| 2 | A2 | 0 | 20 | south |

### 10.2 Drehstrommotor (3-Phase Motor)

**Pfad:** `10_electric/10_allpole/391_consumers_actuators/10_engines/moteur_tri.elmt`
**link_type:** `simple`
**Dimensionen:** 60x60, Hotspot: (29, 38)

| Terminal | Name | X | Y | Orientierung |
|----------|------|---|---|--------------|
| 1 | U1 | -20 | -30 | north |
| 2 | V1 | 0 | -30 | north |
| 3 | W1 | 20 | -30 | north |
| 4 | PE | 21 | 6 | north |

### 10.3 Motorschutzschalter 3p (Magneto-Thermal Circuit Breaker) -- Master

**Pfad:** `10_electric/10_allpole/200_fuses_protective_gears/12_magneto_thermal_circuit_breakers/dis_mag_term_3f-2.elmt`
**link_type:** `master` | **kindInfo type:** `protection`
**Dimensionen:** 100x100, Hotspot: (66, 50)

| Terminal | Name | X | Y | Orientierung |
|----------|------|---|---|--------------|
| 1 | 1 (L1) | -20 | -40 | north |
| 2 | 3 (L2) | 0 | -40 | north |
| 3 | 5 (L3) | 20 | -40 | north |
| 4 | 2 (T1) | -20 | 40 | south |
| 5 | 4 (T2) | 0 | 40 | south |
| 6 | 6 (T3) | 20 | 40 | south |

### 10.4 Thermisches Ueberlastrelais 3p (Thermal Relay) -- Master

**Pfad:** `10_electric/10_allpole/200_fuses_protective_gears/30_thermal_relays/relais_therm4.elmt`
**link_type:** `master` | **kindInfo type:** `protection`
**Dimensionen:** 40x60, Hotspot: (10, 30)

| Terminal | Name | X | Y | Orientierung |
|----------|------|---|---|--------------|
| 1 | -- | 0 | -21 | north |
| 2 | -- | 0 | 21 | south |
| 3 | -- | 10 | -21 | north |
| 4 | -- | 10 | 21 | south |
| 5 | -- | 20 | -21 | north |
| 6 | -- | 20 | 21 | south |

### 10.5 Kontakt NO (Schliesser / Thermal Relay Contact)

**Pfad:** `10_electric/10_allpole/310_relays_contactors_contacts/03_contacts/contact_relais.elmt`
**link_type:** `simple`
**Dimensionen:** 30x60, Hotspot: (20, 30)

| Terminal | Name | X | Y | Orientierung |
|----------|------|---|---|--------------|
| 1 | -- | 0 | -21 | north |
| 2 | -- | 0 | 21 | south |

### 10.6 Kontakt NC (Oeffner / Thermal Relay Contact NC)

**Pfad:** `10_electric/10_allpole/310_relays_contactors_contacts/03_contacts/contact_relais_nf.elmt`
**link_type:** `simple`
**Dimensionen:** 30x60, Hotspot: (17, 30)

| Terminal | Name | X | Y | Orientierung |
|----------|------|---|---|--------------|
| 1 | -- | 0 | -21 | north |
| 2 | -- | 0 | 21 | south |

### 10.7 Not-Halt Taster (Emergency Stop NO) -- Master

**Pfad:** `10_electric/10_allpole/380_signaling_operating/20_push_buttons/arret-urgence_no.elmt`
**link_type:** `master` | **kindInfo type:** `commutator`
**Dimensionen:** 30x60, Hotspot: (21, 30)

| Terminal | Name | X | Y | Orientierung |
|----------|------|---|---|--------------|
| 1 | -- | 0 | -20 | north |
| 2 | -- | 0 | 20 | south |

### 10.8 Drucktaster beleuchtet (Push Button NO) -- Master

**Pfad:** `10_electric/10_allpole/380_signaling_operating/20_push_buttons/contact_012.elmt`
**link_type:** `master` | **kindInfo type:** `commutator`
**Dimensionen:** 40x60, Hotspot: (19, 30)

| Terminal | Name | X | Y | Orientierung |
|----------|------|---|---|--------------|
| 1 | -- | 10 | -20 | north |
| 2 | -- | 10 | 20 | south |

### 10.9 Sicherung 1p (Fuse)

**Pfad:** `10_electric/10_allpole/200_fuses_protective_gears/10_fuses/pojistka1p.elmt`
**link_type:** `simple`
**Dimensionen:** 20x60, Hotspot: (11, 32)

| Terminal | Name | X | Y | Orientierung |
|----------|------|---|---|--------------|
| 1 | 1 | 0 | -20 | north |
| 2 | 2 | 0 | 20 | south |

### 10.10 Sicherungstrenner 1p (Switchfuse) -- Master

**Pfad:** `10_electric/11_singlepole/200_fuses_protective_gears/10_fuses/sec_fus1.elmt`
**link_type:** `master` | **kindInfo type:** `protection`
**Dimensionen:** 20x60, Hotspot: (10, 30)

| Terminal | Name | X | Y | Orientierung |
|----------|------|---|---|--------------|
| 1 | -- | 0 | -21 | north |
| 2 | -- | 0 | 21 | south |

### 10.11 Klemme (Terminal Block)

**Pfad:** `10_electric/10_allpole/130_terminals_terminal_strips/borne_continuite.elmt`
**link_type:** `terminal`
**Dimensionen:** 20x40, Hotspot: (10, 20)

| Terminal | Name | X | Y | Orientierung |
|----------|------|---|---|--------------|
| 1 | -- | 0 | -10 | north |
| 2 | -- | 0 | 10 | south |

### 10.12 Meldeleuchte (Pilot Light / Indicator)

**Pfad:** `10_electric/10_allpole/380_signaling_operating/11_optical_signaling/lampe2.elmt`
**link_type:** `simple`
**Dimensionen:** 30x60, Hotspot: (15, 30)

| Terminal | Name | X | Y | Orientierung |
|----------|------|---|---|--------------|
| 1 | A1 | 0 | -20 | north |
| 2 | A2 | 0 | 20 | south |

---

## 11. Wichtige Muster und Erkenntnisse

### 11.1 Terminal-Abstaende

Die meisten Steuerkreis-Elemente (Spulen, Kontakte, Taster) haben:
- **2 Terminals** vertikal angeordnet (north oben, south unten)
- **Abstand**: 40 oder 42 Pixel (y=-20 bis y=20 oder y=-21 bis y=21)
- **X-Position**: Meist x=0 (zentriert)

3-phasige Elemente (Motorschutz, Ueberlast) haben:
- **6 Terminals** (3 oben, 3 unten)
- **Horizontaler Abstand**: 20 Pixel (x=-20, 0, 20) oder 10 Pixel (x=0, 10, 20)

### 11.2 Element-Platzierung fuer vertikalen Energiefluss

Fuer typische Schaltplaene mit vertikalem Energiefluss (oben nach unten):
- Elemente mit `orientation=0` (Standard) haben Terminals oben (north) und unten (south)
- Leiter verbinden south-Terminal eines Elements mit north-Terminal des naechsten
- Horizontale Verbindungen: Elemente nebeneinander, gleiche Y-Position

### 11.3 UUID-Erzeugung

Alle UUIDs muessen im Format `{xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx}` sein.
In der Engine: UUID v4 generieren mit geschweiften Klammern.

### 11.4 Folio-Hoehe

Die `height`-Eigenschaft des Diagramms:
```
height = (rows * rowsize) + column_header_height
       = (8 * 80) + 20
       = 660
```

Standard: `height="660"` fuer 8 Zeilen a 80px + 20px Header.
