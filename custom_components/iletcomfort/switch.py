"""Switch entities for the iLetComfort integration."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN
from .coordinator import ILetComfortCoordinator
from .entity import atw27_status_body, build_device_info
from .model_profiles import atw27_dhw_power


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    coordinator: ILetComfortCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities: list[SwitchEntity] = [ILetComfortBoostSwitch(coordinator)]
    if atw27_status_body(coordinator) is not None:
        entities.append(ILetComfortAtwDhwSwitch(coordinator))
    async_add_entities(entities)


class ILetComfortAtwDhwSwitch(CoordinatorEntity[ILetComfortCoordinator], SwitchEntity):
    """DHW power on the 27-byte ATW layout."""

    _attr_has_entity_name = True
    _attr_name = "DHW"
    _attr_icon = "mdi:water-boiler"

    def __init__(self, coordinator: ILetComfortCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.appliance_code}_atw_dhw_power"
        self._attr_device_info = build_device_info(coordinator)

    @property
    def available(self) -> bool:
        return super().available and atw27_status_body(self.coordinator) is not None

    @property
    def is_on(self) -> bool | None:
        body = atw27_status_body(self.coordinator)
        return atw27_dhw_power(body) if body else None

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_device(dhw_power=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_device(dhw_power=False)


class ILetComfortBoostSwitch(CoordinatorEntity[ILetComfortCoordinator], SwitchEntity):
    """Switch entity for boost mode."""

    _attr_has_entity_name = True
    _attr_name = "Boost"
    _attr_icon = "mdi:rocket-launch"

    def __init__(self, coordinator: ILetComfortCoordinator) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.appliance_code}_boost"
        self._attr_device_info = build_device_info(coordinator)

    @property
    def is_on(self) -> bool:
        if self.coordinator.data is None:
            return False
        sensors = self.coordinator.data.get("sensors")
        if sensors is None:
            return False
        return sensors.ctrl_flag == 2

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_device(boost=True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.async_set_device(boost=False)
