"""Tests for the 27-byte ATW DHW power switch (#42)."""

from unittest.mock import AsyncMock, MagicMock

from custom_components.iletcomfort.api import ITSSensors
from custom_components.iletcomfort.model_profiles import ATW_SN8, decode_atw_status
from custom_components.iletcomfort.switch import ILetComfortAtwDhwSwitch

NORDIS_STATUS = bytes.fromhex(
    "01 0d 17 a0 03 03 23 1e 3c 30 37 19 19 05 37 19 19 05 3c 22 3c 14 32 00 40 05 00"
)


def _entity(body: bytes = NORDIS_STATUS) -> ILetComfortAtwDhwSwitch:
    coordinator = MagicMock()
    coordinator.appliance_code = "APPL1"
    coordinator.sn8 = ATW_SN8
    coordinator.data = {"status": decode_atw_status(body), "sensors": ITSSensors()}
    coordinator.async_set_device = AsyncMock()
    return ILetComfortAtwDhwSwitch(coordinator)


async def test_dhw_switch_reads_power_bit_and_writes_dhw_power():
    entity = _entity()

    assert entity.is_on is True
    await entity.async_turn_off()

    entity.coordinator.async_set_device.assert_awaited_once_with(dhw_power=False)


def test_dhw_switch_off_when_power_bit_clear():
    body = bytearray(NORDIS_STATUS)
    body[1] = 0x09

    assert _entity(bytes(body)).is_on is False
