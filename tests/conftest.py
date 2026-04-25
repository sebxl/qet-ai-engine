from pathlib import Path

import pytest


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
