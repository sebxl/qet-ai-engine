from pathlib import Path

import pytest

from src.element_db.models import ElementRecord, KindInformations, Terminal


@pytest.fixture
def elements_dir() -> Path:
    return Path("C:/Program Files/QElectroTech/elements")


@pytest.fixture
def coil_elmt_path() -> str:
    return "10_electric/10_allpole/310_relays_contactors_contacts/01_coils/bobine3.elmt"


@pytest.fixture
def motor_tri_elmt_path() -> str:
    return "10_electric/10_allpole/391_consumers_actuators/10_engines/moteur_tri.elmt"


@pytest.fixture
def breaker_3f_elmt_path() -> str:
    return "10_electric/10_allpole/200_fuses_protective_gears/12_magneto_thermal_circuit_breakers/dis_mag_term_3f-2.elmt"


@pytest.fixture
def slave_contact_elmt_path() -> str:
    return "10_electric/10_allpole/310_relays_contactors_contacts/02_contacts_cross_referencing/01_auxiliary_contacts/con_simple.elmt"


@pytest.fixture
def terminal_block_elmt_path() -> str:
    return "10_electric/10_allpole/130_terminals_terminal_strips/borne_continuite.elmt"


@pytest.fixture
def coil_element_record():
    """Fake coil ElementRecord for writer tests."""
    return ElementRecord(
        path="10_electric/10_allpole/310_relays_contactors_contacts/01_coils/bobine3.elmt",
        uuid="{793302b1-e96a-f7f8-70bc-dec53eeaab5b}",
        names={"de": "Spule", "en": "Coil"},
        width=40, height=60, hotspot_x=20, hotspot_y=32,
        link_type="master",
        kind_informations=KindInformations(type="coil"),
        terminals=[
            Terminal(uuid="{8d0fa333-2d98-4a75-8a4e-21c81cce7ec3}", name="A1",
                     x=0.0, y=-20.0, orientation="n", type="Generic"),
            Terminal(uuid="{c5376fd7-bdf1-4c10-985a-0d7d5f52c8f9}", name="A2",
                     x=0.0, y=20.0, orientation="s", type="Generic"),
        ],
        graphic_primitives=[],
        informations="",
    )


@pytest.fixture
def slave_element_record():
    """Fake slave contact ElementRecord for writer tests."""
    return ElementRecord(
        path="10_electric/10_allpole/310_relays_contactors_contacts/02_contacts_cross_referencing/01_auxiliary_contacts/con_simple.elmt",
        uuid="{abcdef01-2345-6789-abcd-ef0123456789}",
        names={"de": "Kontakt NO", "en": "Contact NO"},
        width=30, height=60, hotspot_x=20, hotspot_y=30,
        link_type="slave",
        kind_informations=KindInformations(type="simple", state="NO", number=1),
        terminals=[
            Terminal(uuid="{11111111-1111-1111-1111-111111111111}", name="",
                     x=0.0, y=-21.0, orientation="n", type="Generic"),
            Terminal(uuid="{22222222-2222-2222-2222-222222222222}", name="",
                     x=0.0, y=21.0, orientation="s", type="Generic"),
        ],
        graphic_primitives=[],
        informations="",
    )


@pytest.fixture
def fake_element_db(coil_element_record, slave_element_record):
    """Dict-based element DB for writer unit tests."""
    return {
        coil_element_record.path: coil_element_record,
        slave_element_record.path: slave_element_record,
    }


# ── Motor Starter fixtures (QET-4) ───────────────────────────────────


@pytest.fixture
def contactor_3p_elmt_path() -> str:
    return "10_electric/10_allpole/310_relays_contactors_contacts/02_contacts_cross_referencing/02_power_contacts/com_puiss4.elmt"


@pytest.fixture
def thermal_relay_elmt_path() -> str:
    return "10_electric/10_allpole/200_fuses_protective_gears/30_thermal_relays/relais_therm4.elmt"


@pytest.fixture
def breaker_3f_element_record():
    return ElementRecord(
        path="10_electric/10_allpole/200_fuses_protective_gears/12_magneto_thermal_circuit_breakers/dis_mag_term_3f-2.elmt",
        uuid="{fake-breaker-uuid}",
        names={"de": "Leitungsschutzschalter 3p", "en": "Circuit breaker 3p"},
        width=60, height=100, hotspot_x=30, hotspot_y=50,
        link_type="master",
        kind_informations=KindInformations(type="protection"),
        terminals=[
            Terminal(uuid="{b-t1}", name="1", x=-20.0, y=-40.0, orientation="n", type="Generic"),
            Terminal(uuid="{b-t3}", name="3", x=0.0, y=-40.0, orientation="n", type="Generic"),
            Terminal(uuid="{b-t5}", name="5", x=20.0, y=-40.0, orientation="n", type="Generic"),
            Terminal(uuid="{b-t6}", name="6", x=20.0, y=40.0, orientation="s", type="Generic"),
            Terminal(uuid="{b-t4}", name="4", x=0.0, y=40.0, orientation="s", type="Generic"),
            Terminal(uuid="{b-t2}", name="2", x=-20.0, y=40.0, orientation="s", type="Generic"),
        ],
        graphic_primitives=[],
        informations="",
    )


@pytest.fixture
def contactor_3p_element_record():
    return ElementRecord(
        path="10_electric/10_allpole/310_relays_contactors_contacts/02_contacts_cross_referencing/02_power_contacts/com_puiss4.elmt",
        uuid="{fake-contactor-uuid}",
        names={"de": "Leistungskontakt 3p", "en": "Power contact 3p"},
        width=60, height=60, hotspot_x=30, hotspot_y=30,
        link_type="slave",
        kind_informations=KindInformations(type="power", state="NO", number=3),
        terminals=[
            Terminal(uuid="{c-t0}", name="", x=-20.0, y=-20.0, orientation="n", type="Generic"),
            Terminal(uuid="{c-t1}", name="", x=-20.0, y=20.0, orientation="s", type="Generic"),
            Terminal(uuid="{c-t2}", name="", x=0.0, y=-20.0, orientation="n", type="Generic"),
            Terminal(uuid="{c-t3}", name="", x=0.0, y=20.0, orientation="s", type="Generic"),
            Terminal(uuid="{c-t4}", name="", x=20.0, y=-20.0, orientation="n", type="Generic"),
            Terminal(uuid="{c-t5}", name="", x=20.0, y=20.0, orientation="s", type="Generic"),
        ],
        graphic_primitives=[],
        informations="",
    )


@pytest.fixture
def thermal_relay_element_record():
    return ElementRecord(
        path="10_electric/10_allpole/200_fuses_protective_gears/30_thermal_relays/relais_therm4.elmt",
        uuid="{fake-thermal-uuid}",
        names={"de": "Thermisches Überlastrelais", "en": "Thermal overload relay"},
        width=40, height=62, hotspot_x=10, hotspot_y=31,
        link_type="master",
        kind_informations=KindInformations(type="protection"),
        terminals=[
            Terminal(uuid="{th-t0}", name="", x=0.0, y=-21.0, orientation="n", type="Generic"),
            Terminal(uuid="{th-t1}", name="", x=0.0, y=21.0, orientation="s", type="Generic"),
            Terminal(uuid="{th-t2}", name="", x=10.0, y=-21.0, orientation="n", type="Generic"),
            Terminal(uuid="{th-t3}", name="", x=10.0, y=21.0, orientation="s", type="Generic"),
            Terminal(uuid="{th-t4}", name="", x=20.0, y=-21.0, orientation="n", type="Generic"),
            Terminal(uuid="{th-t5}", name="", x=20.0, y=21.0, orientation="s", type="Generic"),
        ],
        graphic_primitives=[],
        informations="",
    )


@pytest.fixture
def motor_tri_element_record():
    return ElementRecord(
        path="10_electric/10_allpole/391_consumers_actuators/10_engines/moteur_tri.elmt",
        uuid="{fake-motor-uuid}",
        names={"de": "Drehstrommotor", "en": "Three-phase motor"},
        width=60, height=50, hotspot_x=30, hotspot_y=35,
        link_type="simple",
        kind_informations=None,
        terminals=[
            Terminal(uuid="{m-w1}", name="W1", x=20.0, y=-30.0, orientation="n", type="Generic"),
            Terminal(uuid="{m-u1}", name="U1", x=-20.0, y=-30.0, orientation="n", type="Generic"),
            Terminal(uuid="{m-pe}", name="PE", x=21.0, y=6.0, orientation="s", type="Generic"),
            Terminal(uuid="{m-v1}", name="V1", x=0.0, y=-30.0, orientation="n", type="Generic"),
        ],
        graphic_primitives=[],
        informations="",
    )


@pytest.fixture
def motor_starter_element_db(breaker_3f_element_record, contactor_3p_element_record,
                              thermal_relay_element_record, motor_tri_element_record):
    return {
        breaker_3f_element_record.path: breaker_3f_element_record,
        contactor_3p_element_record.path: contactor_3p_element_record,
        thermal_relay_element_record.path: thermal_relay_element_record,
        motor_tri_element_record.path: motor_tri_element_record,
    }


@pytest.fixture
def valid_motor_starter_params():
    return {
        "motor_power_kw": 1.5,
        "motor_voltage": "400V_3ph",
        "motor_current_a": 3.5,
        "protection_type": "thermal_overload",
    }


# ── Control Circuit fixtures (QET-5) ─────────────────────────────────


@pytest.fixture
def estop_nc_element_record():
    """Fake ElementRecord for e_stop_1p.elmt (E-Stop NC)."""
    return ElementRecord(
        path=(
            "10_electric/10_allpole/380_signaling_operating"
            "/20_push_buttons/e_stop_1p.elmt"
        ),
        uuid="{9f535be6-89ee-f067-f1d0-4683a1db2a30}",
        names={"de": "Not-Aus", "en": "E-Stop"},
        width=30, height=60, hotspot_x=15, hotspot_y=30,
        link_type="master",
        kind_informations=KindInformations(type="commutator"),
        terminals=[
            # SOUTH FIRST in XML -- idx0=BOTTOM, idx1=TOP (reversed!)
            Terminal(uuid="{es-t0}", name="",
                     x=0.0, y=20.0, orientation="s", type="Generic"),
            Terminal(uuid="{es-t1}", name="",
                     x=0.0, y=-20.0, orientation="n", type="Generic"),
        ],
        graphic_primitives=[],
        informations="",
    )


@pytest.fixture
def overload_aux_nc_element_record():
    """Fake ElementRecord for con_simple_nf.elmt (Overload aux NC)."""
    return ElementRecord(
        path=(
            "10_electric/10_allpole/310_relays_contactors_contacts"
            "/02_contacts_cross_referencing/01_auxiliary_contacts/con_simple_nf.elmt"
        ),
        uuid="{a48a492d-e5e9-8768-2997-a2e4ec843957}",
        names={"de": "Kontakt NC", "en": "Contact NC"},
        width=30, height=60, hotspot_x=20, hotspot_y=30,
        link_type="slave",
        kind_informations=KindInformations(type="simple", state="NC", number=1),
        terminals=[
            Terminal(uuid="{nf-t0}", name="",
                     x=0.0, y=-20.0, orientation="n", type="Generic"),
            Terminal(uuid="{nf-t1}", name="",
                     x=0.0, y=20.0, orientation="s", type="Generic"),
        ],
        graphic_primitives=[],
        informations="",
    )


@pytest.fixture
def stop_button_nc_element_record():
    """Fake ElementRecord for poussoir_nf.elmt (Stop button NC)."""
    return ElementRecord(
        path=(
            "10_electric/10_allpole/380_signaling_operating"
            "/20_push_buttons/poussoir_nf.elmt"
        ),
        uuid="{875793b5-3fcb-4ff8-f9c6-d5a5e3ad53ae}",
        names={"de": "Taster NC", "en": "Push button NC"},
        width=30, height=60, hotspot_x=15, hotspot_y=30,
        link_type="master",
        kind_informations=KindInformations(type="commutator"),
        terminals=[
            Terminal(uuid="{pnf-t0}", name="",
                     x=0.0, y=-21.0, orientation="n", type="Generic"),
            Terminal(uuid="{pnf-t1}", name="",
                     x=0.0, y=21.0, orientation="s", type="Generic"),
        ],
        graphic_primitives=[],
        informations="",
    )


@pytest.fixture
def start_button_no_element_record():
    """Fake ElementRecord for poussoir.elmt (Start button NO)."""
    return ElementRecord(
        path=(
            "10_electric/10_allpole/380_signaling_operating"
            "/20_push_buttons/poussoir.elmt"
        ),
        uuid="{0d256453-ab42-30c1-1d91-b3ec0fb1298c}",
        names={"de": "Taster NO", "en": "Push button NO"},
        width=30, height=60, hotspot_x=15, hotspot_y=30,
        link_type="master",
        kind_informations=KindInformations(type="commutator"),
        terminals=[
            Terminal(uuid="{pno-t0}", name="",
                     x=0.0, y=-21.0, orientation="n", type="Generic"),
            Terminal(uuid="{pno-t1}", name="",
                     x=0.0, y=21.0, orientation="s", type="Generic"),
        ],
        graphic_primitives=[],
        informations="",
    )


@pytest.fixture
def control_circuit_element_db(
    breaker_3f_element_record,
    contactor_3p_element_record,
    thermal_relay_element_record,
    motor_tri_element_record,
    coil_element_record,
    slave_element_record,
    estop_nc_element_record,
    overload_aux_nc_element_record,
    stop_button_nc_element_record,
    start_button_no_element_record,
):
    """Combined element DB with all 10 elements for power + control circuit."""
    records = [
        breaker_3f_element_record,
        contactor_3p_element_record,
        thermal_relay_element_record,
        motor_tri_element_record,
        coil_element_record,
        slave_element_record,
        estop_nc_element_record,
        overload_aux_nc_element_record,
        stop_button_nc_element_record,
        start_button_no_element_record,
    ]
    return {r.path: r for r in records}


@pytest.fixture
def valid_control_circuit_params():
    """Motor starter params with control circuit enabled."""
    return {
        "motor_power_kw": 1.5,
        "motor_voltage": "400V_3ph",
        "motor_current_a": 3.5,
        "protection_type": "thermal_overload",
        "with_control_circuit": True,
        "contactor_coil_voltage": "24V_DC",
    }
