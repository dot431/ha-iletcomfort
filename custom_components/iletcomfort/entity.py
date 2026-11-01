"""Shared entity helpers for the iLetComfort integration."""

from __future__ import annotations

from homeassistant.helpers.device_registry import DeviceInfo

from .const import DOMAIN
from .coordinator import ILetComfortCoordinator
from .model_profiles import ModelProfile, is_27_byte_atw_status, resolve_profile


def build_device_info(coordinator: ILetComfortCoordinator) -> DeviceInfo:
    """Build the DeviceInfo that groups every entity under one HA Device.

    Keyed on the stable appliance code so all platforms attach to the same
    device. ``sw_version`` is taken from the outdoor-unit firmware when the
    coordinator already has sensor data (it does by the time platforms are set
    up, since the first refresh runs during ``async_setup_entry``).
    """
    sensors = (coordinator.data or {}).get("sensors")
    sw_version = getattr(sensors, "odu_version", "") or None
    return DeviceInfo(
        identifiers={(DOMAIN, coordinator.appliance_code)},
        name=coordinator.entry.title,
        manufacturer="iLetComfort",
        model=coordinator.sn8,
        sw_version=sw_version,
    )


def atw27_status_body(coordinator: ILetComfortCoordinator) -> bytes | None:
    """Return the raw status body when the device reports the 27-byte ATW layout."""
    if resolve_profile(coordinator.sn8) is not ModelProfile.ATW:
        return None
    status = (coordinator.data or {}).get("status")
    if status is None or not is_27_byte_atw_status(status.raw_body):
        return None
    return status.raw_body
