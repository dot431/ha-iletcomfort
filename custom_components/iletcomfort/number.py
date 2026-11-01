"""Number entities for the iLetComfort integration."""

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ILetComfortCoordinator
from .entity import atw27_status_body, build_device_info
from .model_profiles import (
    ATW_DHW_SETPOINT_INDEX,
    KJRH120L_DHW_TEMP_MAX,
    KJRH120L_DHW_TEMP_MIN,
    ModelProfile,
    atw27_dhw_limits,
    kjrh120l_has_zone1,
    resolve_profile,
)


def _is_kjrh120l_dual(coordinator: ILetComfortCoordinator) -> bool:
    if resolve_profile(coordinator.sn8) is not ModelProfile.KJRH120L:
        return False
    status = (coordinator.data or {}).get("status")
    return bool(status and kjrh120l_has_zone1(status.raw_body))


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create a DHW control for the validated dual KJRH-120L and 27-byte ATW."""
    coordinator: ILetComfortCoordinator = hass.data[DOMAIN][entry.entry_id]
    if _is_kjrh120l_dual(coordinator):
        async_add_entities([ILetComfortKjrh120lDhwSetpoint(coordinator)])
    elif atw27_status_body(coordinator) is not None:
        async_add_entities([ILetComfortAtwDhwSetpoint(coordinator)])


class ILetComfortAtwDhwSetpoint(CoordinatorEntity[ILetComfortCoordinator], NumberEntity):
    """DHW target on the 27-byte ATW layout, bounded by the unit's own limits."""

    _attr_has_entity_name = True
    _attr_name = "DHW Setpoint"
    _attr_icon = "mdi:water-thermometer"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_step = 1.0
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: ILetComfortCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.appliance_code}_atw_dhw_setpoint"
        self._attr_device_info = build_device_info(coordinator)

    @property
    def available(self) -> bool:
        return super().available and atw27_status_body(self.coordinator) is not None

    @property
    def native_min_value(self) -> float:
        body = atw27_status_body(self.coordinator)
        return float(atw27_dhw_limits(body)[0]) if body else 0.0

    @property
    def native_max_value(self) -> float:
        body = atw27_status_body(self.coordinator)
        return float(atw27_dhw_limits(body)[1]) if body else 0.0

    @property
    def native_value(self) -> float | None:
        body = atw27_status_body(self.coordinator)
        return float(body[ATW_DHW_SETPOINT_INDEX]) if body else None

    async def async_set_native_value(self, value: float) -> None:
        clamped = max(self.native_min_value, min(float(value), self.native_max_value))
        await self.coordinator.async_set_device(dhw_temperature=int(clamped))


class ILetComfortKjrh120lDhwSetpoint(
    CoordinatorEntity[ILetComfortCoordinator], NumberEntity
):
    """DHW target using the hardware-confirmed KJRH-120L field 0x07 write."""

    _attr_has_entity_name = True
    _attr_name = "DHW Setpoint"
    _attr_icon = "mdi:water-thermometer"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = float(KJRH120L_DHW_TEMP_MIN)
    _attr_native_max_value = float(KJRH120L_DHW_TEMP_MAX)
    _attr_native_step = 1.0
    _attr_mode = NumberMode.BOX

    def __init__(self, coordinator: ILetComfortCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.appliance_code}_kjrh120l_dhw_setpoint"
        self._attr_device_info = build_device_info(coordinator)

    @property
    def native_value(self) -> float | None:
        status = (self.coordinator.data or {}).get("status")
        return status.kjrh120l_dhw_setpoint if status else None

    async def async_set_native_value(self, value: float) -> None:
        clamped = max(
            self._attr_native_min_value,
            min(float(value), self._attr_native_max_value),
        )
        await self.coordinator.async_set_device(temperature=int(clamped))
