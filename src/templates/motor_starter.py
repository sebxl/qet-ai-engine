"""Motor Starter template (QET-4 / QET-5).

Generates a 3-phase motor starter:
  Folio 1 -- Hauptstromkreis (power circuit):
    F1 -- Circuit breaker 3p
    K1 -- Contactor 3p (power contacts)
    F2 -- Thermal overload relay
    M1 -- Three-phase motor

  Folio 2 -- Steuerstromkreis (control circuit, optional):
    S0  -- E-Stop NC
    F2  -- Overload aux NC (slave)
    S1  -- Stop button NC
    S2  -- Start button NO   (parallel branch)
    K1  -- Self-hold NO      (parallel branch)
    K1  -- Coil A1-A2        (master)
"""

from __future__ import annotations

from src.writer import QETWriter
from src.writer.models import (
    Conductor,
    Folio,
    PlacedElement,
    QETProject,
)

from .base import BaseTemplate

# ── Element paths ─────────────────────────────────────────────────────

ELEMENT_PATHS = {
    "breaker_3f": (
        "10_electric/10_allpole/200_fuses_protective_gears"
        "/12_magneto_thermal_circuit_breakers/dis_mag_term_3f-2.elmt"
    ),
    "contactor_3p": (
        "10_electric/10_allpole/310_relays_contactors_contacts"
        "/02_contacts_cross_referencing/02_power_contacts/com_puiss4.elmt"
    ),
    "thermal_relay": (
        "10_electric/10_allpole/200_fuses_protective_gears"
        "/30_thermal_relays/relais_therm4.elmt"
    ),
    "motor_tri": (
        "10_electric/10_allpole/391_consumers_actuators"
        "/10_engines/moteur_tri.elmt"
    ),
}

CONTROL_ELEMENT_PATHS = {
    "estop_nc": (
        "10_electric/10_allpole/380_signaling_operating"
        "/20_push_buttons/e_stop_1p.elmt"
    ),
    "overload_aux_nc": (
        "10_electric/10_allpole/310_relays_contactors_contacts"
        "/02_contacts_cross_referencing/01_auxiliary_contacts/con_simple_nf.elmt"
    ),
    "stop_button_nc": (
        "10_electric/10_allpole/380_signaling_operating"
        "/20_push_buttons/poussoir_nf.elmt"
    ),
    "start_button_no": (
        "10_electric/10_allpole/380_signaling_operating"
        "/20_push_buttons/poussoir.elmt"
    ),
    "self_hold_no": (
        "10_electric/10_allpole/310_relays_contactors_contacts"
        "/02_contacts_cross_referencing/01_auxiliary_contacts/con_simple.elmt"
    ),
    "coil": (
        "10_electric/10_allpole/310_relays_contactors_contacts"
        "/01_coils/bobine3.elmt"
    ),
}

REQUIRED_PARAMS = ("motor_power_kw", "motor_voltage", "motor_current_a", "protection_type")


class MotorStarterTemplate(BaseTemplate):
    """Generates a 3-phase motor starter Hauptstromkreis."""

    def __init__(self, writer: QETWriter) -> None:
        self._writer = writer

    # ── Public API ────────────────────────────────────────────────────

    def generate(self, params: dict) -> QETProject:
        """Generate the motor starter project from parameters."""
        self._validate_params(params)

        project = self._writer.create_project(
            title=f"Motorstarter {params['motor_power_kw']}kW",
            author="QET-AI Engine",
        )
        folio = self._writer.add_folio(project, "Hauptstromkreis")

        power_elements = self._place_elements(folio, params)
        self._connect_phases(folio, power_elements)

        if params.get("with_control_circuit"):
            folio2 = self._writer.add_folio(project, "Steuerstromkreis")
            ctrl_elements = self._place_control_elements(folio2)
            self._connect_control_circuit(folio2, ctrl_elements)
            self._link_cross_references(power_elements, ctrl_elements)

        return project

    # ── Internal ──────────────────────────────────────────────────────

    def _validate_params(self, params: dict) -> None:
        missing = [k for k in REQUIRED_PARAMS if k not in params]
        if missing:
            raise ValueError(f"Missing required parameters: {', '.join(missing)}")

        if params.get("with_control_circuit") and "contactor_coil_voltage" not in params:
            raise ValueError("Missing required parameter: contactor_coil_voltage")

    def _place_elements(
        self, folio: Folio, params: dict
    ) -> dict[str, PlacedElement]:
        f1 = self._writer.place_element(
            folio, ELEMENT_PATHS["breaker_3f"], x=300, y=150,
            designation="F1",
        )
        k1 = self._writer.place_element(
            folio, ELEMENT_PATHS["contactor_3p"], x=300, y=250,
            designation="K1",
        )
        # Thermal relay at x=280 so its x=0 terminal aligns with x=-20 of others at x=300
        f2 = self._writer.place_element(
            folio, ELEMENT_PATHS["thermal_relay"], x=280, y=330,
            designation="F2",
        )
        m1 = self._writer.place_element(
            folio, ELEMENT_PATHS["motor_tri"], x=300, y=420,
            designation="M1",
        )
        return {"F1": f1, "K1": k1, "F2": f2, "M1": m1}

    def _place_control_elements(
        self, folio: Folio,
    ) -> dict[str, PlacedElement]:
        s0 = self._writer.place_element(
            folio, CONTROL_ELEMENT_PATHS["estop_nc"], x=300, y=150,
            designation="S0",
        )
        f2_aux = self._writer.place_element(
            folio, CONTROL_ELEMENT_PATHS["overload_aux_nc"], x=300, y=230,
            designation="F2",
        )
        s1 = self._writer.place_element(
            folio, CONTROL_ELEMENT_PATHS["stop_button_nc"], x=300, y=310,
            designation="S1",
        )
        s2 = self._writer.place_element(
            folio, CONTROL_ELEMENT_PATHS["start_button_no"], x=300, y=390,
            designation="S2",
        )
        k1_self = self._writer.place_element(
            folio, CONTROL_ELEMENT_PATHS["self_hold_no"], x=380, y=390,
            designation="K1",
        )
        k1_coil = self._writer.place_element(
            folio, CONTROL_ELEMENT_PATHS["coil"], x=300, y=470,
            designation="K1",
        )
        return {
            "S0": s0, "F2_aux": f2_aux, "S1": s1,
            "S2": s2, "K1_self": k1_self, "K1_coil": k1_coil,
        }

    def _connect_control_circuit(
        self,
        folio: Folio,
        ctrl: dict[str, PlacedElement],
    ) -> None:
        s0 = ctrl["S0"]
        f2_aux = ctrl["F2_aux"]
        s1 = ctrl["S1"]
        s2 = ctrl["S2"]
        k1_self = ctrl["K1_self"]
        k1_coil = ctrl["K1_coil"]

        # 1: S0 idx0 (bottom) -> F2_aux idx0 (top)
        _connect_by_index(folio, s0, 0, f2_aux, 0)
        # 2: F2_aux idx1 (bottom) -> S1 idx0 (top)
        _connect_by_index(folio, f2_aux, 1, s1, 0)
        # 3: S1 idx1 (bottom) -> S2 idx0 (top)
        _connect_by_index(folio, s1, 1, s2, 0)
        # 4: S1 idx1 (bottom) -> K1_self idx0 (top)
        _connect_by_index(folio, s1, 1, k1_self, 0)
        # 5: S2 idx1 (bottom) -> K1_coil A1 (named)
        _connect_by_index_and_name(folio, s2, 1, k1_coil, "A1")
        # 6: K1_self idx1 (bottom) -> K1_coil A1 (named)
        _connect_by_index_and_name(folio, k1_self, 1, k1_coil, "A1")

    def _link_cross_references(
        self,
        power_elements: dict[str, PlacedElement],
        ctrl_elements: dict[str, PlacedElement],
    ) -> None:
        k1_coil = ctrl_elements["K1_coil"]
        k1_self = ctrl_elements["K1_self"]
        k1_power = power_elements["K1"]

        # K1_coil (master) <-> K1_self (slave)
        self._writer.link_master_slave(k1_coil, k1_self)
        # K1_coil (master) <-> K1_power (slave)
        self._writer.link_master_slave(k1_coil, k1_power)

    def _connect_phases(
        self, folio: Folio, elements: dict[str, PlacedElement]
    ) -> None:
        f1 = elements["F1"]
        k1 = elements["K1"]
        f2 = elements["F2"]
        m1 = elements["M1"]

        # F1 (breaker) bottom -> K1 (contactor) top
        # F1 has named terminals: "2"=L1 bottom, "4"=L2 bottom, "6"=L3 bottom
        # K1 unnamed: idx0=L1 top, idx2=L2 top, idx4=L3 top
        _connect_by_name_and_index(folio, f1, "2", k1, 0)
        _connect_by_name_and_index(folio, f1, "4", k1, 2)
        _connect_by_name_and_index(folio, f1, "6", k1, 4)

        # K1 (contactor) bottom -> F2 (thermal relay) top
        # K1 unnamed: idx1=L1 bottom, idx3=L2 bottom, idx5=L3 bottom
        # F2 unnamed: idx0=L1 top, idx2=L2 top, idx4=L3 top
        _connect_by_index(folio, k1, 1, f2, 0)
        _connect_by_index(folio, k1, 3, f2, 2)
        _connect_by_index(folio, k1, 5, f2, 4)

        # F2 (thermal relay) bottom -> M1 (motor) top
        # F2 unnamed: idx1=L1 bottom, idx3=L2 bottom, idx5=L3 bottom
        # M1 named: "U1"=L1, "V1"=L2, "W1"=L3
        _connect_by_index_and_name(folio, f2, 1, m1, "U1")
        _connect_by_index_and_name(folio, f2, 3, m1, "V1")
        _connect_by_index_and_name(folio, f2, 5, m1, "W1")


# ── Module-level helpers ──────────────────────────────────────────────


def _connect_by_index(
    folio: Folio,
    elem1: PlacedElement,
    idx1: int,
    elem2: PlacedElement,
    idx2: int,
    label: str = "",
) -> Conductor:
    """Create a conductor between two elements using terminal list indices."""
    t1 = elem1.terminals[idx1]
    t2 = elem2.terminals[idx2]
    conductor = Conductor(
        terminal1_uuid=t1.uuid,
        terminal2_uuid=t2.uuid,
        element1_uuid=elem1.uuid,
        element2_uuid=elem2.uuid,
        terminal1_id=t1.id,
        terminal2_id=t2.id,
        terminal1_name=t1.name,
        terminal2_name=t2.name,
        element1_label=elem1.designation,
        element2_label=elem2.designation,
        label=label,
        terminal1_elmt_uuid=t1.elmt_uuid,
        terminal2_elmt_uuid=t2.elmt_uuid,
    )
    folio.conductors.append(conductor)
    return conductor


def _connect_by_name_and_index(
    folio: Folio,
    elem1: PlacedElement,
    name1: str,
    elem2: PlacedElement,
    idx2: int,
    label: str = "",
) -> Conductor:
    """Connect elem1 by terminal name to elem2 by terminal index."""
    t1 = _find_terminal_by_name(elem1, name1)
    t2 = elem2.terminals[idx2]
    conductor = Conductor(
        terminal1_uuid=t1.uuid,
        terminal2_uuid=t2.uuid,
        element1_uuid=elem1.uuid,
        element2_uuid=elem2.uuid,
        terminal1_id=t1.id,
        terminal2_id=t2.id,
        terminal1_name=t1.name,
        terminal2_name=t2.name,
        element1_label=elem1.designation,
        element2_label=elem2.designation,
        label=label,
        terminal1_elmt_uuid=t1.elmt_uuid,
        terminal2_elmt_uuid=t2.elmt_uuid,
    )
    folio.conductors.append(conductor)
    return conductor


def _connect_by_index_and_name(
    folio: Folio,
    elem1: PlacedElement,
    idx1: int,
    elem2: PlacedElement,
    name2: str,
    label: str = "",
) -> Conductor:
    """Connect elem1 by terminal index to elem2 by terminal name."""
    t1 = elem1.terminals[idx1]
    t2 = _find_terminal_by_name(elem2, name2)
    conductor = Conductor(
        terminal1_uuid=t1.uuid,
        terminal2_uuid=t2.uuid,
        element1_uuid=elem1.uuid,
        element2_uuid=elem2.uuid,
        terminal1_id=t1.id,
        terminal2_id=t2.id,
        terminal1_name=t1.name,
        terminal2_name=t2.name,
        element1_label=elem1.designation,
        element2_label=elem2.designation,
        label=label,
        terminal1_elmt_uuid=t1.elmt_uuid,
        terminal2_elmt_uuid=t2.elmt_uuid,
    )
    folio.conductors.append(conductor)
    return conductor


def _find_terminal_by_name(element: PlacedElement, name: str):
    """Find a terminal on a placed element by name."""
    for t in element.terminals:
        if t.name == name:
            return t
    raise ValueError(
        f"Terminal '{name}' not found on element '{element.designation}'. "
        f"Available: {[t.name for t in element.terminals]}"
    )
