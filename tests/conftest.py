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
