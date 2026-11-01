"""Tests for DHW setpoint controls (KJRH-120L dual #5, 27-byte ATW #42)."""

from unittest.mock import AsyncMock, MagicMock

from custom_components.iletcomfort.api import ITSSensors
from custom_components.iletcomfort.entity import atw27_status_body
from custom_components.iletcomfort.model_profiles import (
    ATW_SN8,
    KJRH120L_SN8,
    decode_atw_status,
    decode_kjrh120l_status,
)
from custom_components.iletcomfort.number import (
    ILetComfortAtwDhwSetpoint,
    ILetComfortKjrh120lDhwSetpoint,
    _is_kjrh120l_dual,
)


def _entity() -> ILetComfortKjrh120lDhwSetpoint:
    body = bytearray(20)
    body[0] = 0x01
    body[8] = body[9] = body[10] = 0x01
    body[12] = 19
    body[15] = 51
    coordinator = MagicMock()
    coordinator.appliance_code = "APPL1"
    coordinator.sn8 = KJRH120L_SN8
    coordinator.appliance_meta = {"sn8": KJRH120L_SN8}
    coordinator.data = {
        "status": decode_kjrh120l_status(body),
        "sensors": ITSSensors(),
    }
    coordinator.async_set_device = AsyncMock()
    return ILetComfortKjrh120lDhwSetpoint(coordinator)


async def test_dhw_number_reads_and_writes_confirmed_dhw_setpoint():
    entity = _entity()

    assert entity.native_value == 51.0
    await entity.async_set_native_value(55)

    entity.coordinator.async_set_device.assert_awaited_once_with(temperature=55)


async def test_dhw_number_clamps_to_validated_range():
    entity = _entity()

    await entity.async_set_native_value(99)

    entity.coordinator.async_set_device.assert_awaited_once_with(temperature=60)


def test_pure_dhw_kjrh_does_not_create_separate_number():
    entity = _entity()
    body = bytearray(entity.coordinator.data["status"].raw_body)
    body[8] = body[9] = 0
    entity.coordinator.data["status"] = decode_kjrh120l_status(body)

    assert not _is_kjrh120l_dual(entity.coordinator)


NORDIS_STATUS = bytes.fromhex(
    "01 0d 17 a0 03 03 23 1e 3c 30 37 19 19 05 37 19 19 05 3c 22 3c 14 32 00 40 05 00"
)


def _atw_entity(body: bytes = NORDIS_STATUS) -> ILetComfortAtwDhwSetpoint:
    coordinator = MagicMock()
    coordinator.appliance_code = "APPL1"
    coordinator.sn8 = ATW_SN8
    coordinator.data = {"status": decode_atw_status(body), "sensors": ITSSensors()}
    coordinator.async_set_device = AsyncMock()
    return ILetComfortAtwDhwSetpoint(coordinator)


async def test_atw27_dhw_number_uses_unit_limits_and_dhw_write():
    entity = _atw_entity()

    assert entity.native_value == 60.0
    assert (entity.native_min_value, entity.native_max_value) == (20.0, 60.0)
    await entity.async_set_native_value(70)

    entity.coordinator.async_set_device.assert_awaited_once_with(dhw_temperature=60)


def test_atw_dhw_number_not_created_for_25_byte_layout():
    entity = _atw_entity(bytes.fromhex(
        "01 0c 07 68 03 03 1e 28 32 28 37 19 19 05 41 23 19 05 3c 22 3c 14 2d 00 80"
    ))

    assert atw27_status_body(entity.coordinator) is None
