"""Binary sensor platform for Audi Connect integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, BINARY_SENSOR_TYPES

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the binary sensor platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    connection = hass.data[DOMAIN][config_entry.entry_id]["connection"]

    entities = []
    
    for vehicle in coordinator.data or []:
        for sensor_type in BINARY_SENSOR_TYPES:
            entities.append(
                AudiConnectBinarySensor(
                    coordinator,
                    connection,
                    vehicle,
                    sensor_type,
                )
            )

    async_add_entities(entities)


class AudiConnectBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of an Audi Connect binary sensor."""

    def __init__(
        self,
        coordinator,
        connection,
        vehicle,
        sensor_type: str,
    ) -> None:
        """Initialize the binary sensor."""
        super().__init__(coordinator)
        self._connection = connection
        self._vehicle = vehicle
        self._sensor_type = sensor_type
        self._attr_unique_id = f"{vehicle.vin}_{sensor_type}"
        
        sensor_config = BINARY_SENSOR_TYPES[sensor_type]
        self._attr_name = f"{vehicle.title} {sensor_config['name']}"
        self._attr_icon = sensor_config.get("icon")
        
        if sensor_config.get("device_class"):
            self._attr_device_class = getattr(
                BinarySensorDeviceClass, sensor_config["device_class"].upper(), None
            )

    @property
    def device_info(self) -> dict[str, Any]:
        """Return device information."""
        return {
            "identifiers": {(DOMAIN, self._vehicle.vin)},
            "name": self._vehicle.title,
            "manufacturer": "Audi",
            "model": self._vehicle.model,
            "sw_version": self._vehicle.model_year,
        }

    @property
    def is_on(self) -> bool | None:
        """Return true if the binary sensor is on."""
        if not self._vehicle or not self._vehicle.state:
            return None

        vehicle_state = self._vehicle.state
        
        # Map binary sensor types to vehicle state attributes
        if self._sensor_type == "doors_locked":
            return vehicle_state.get("overallLockStatus") == "locked"
        elif self._sensor_type == "windows_closed":
            return not vehicle_state.get("anyWindowOpen", False)
        elif self._sensor_type == "any_door_unlocked":
            return vehicle_state.get("anyDoorUnlocked", False)
        elif self._sensor_type == "any_window_open":
            return vehicle_state.get("anyWindowOpen", False)
        elif self._sensor_type == "trunk_unlocked":
            return vehicle_state.get("trunkUnlocked", False)
        elif self._sensor_type == "hood_open":
            return vehicle_state.get("hoodOpen", False)
        elif self._sensor_type == "is_moving":
            return vehicle_state.get("isMoving", False)
        
        return None

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self._vehicle or not self._vehicle.state:
            return None
            
        attributes = {}
        
        # Add last update time
        if hasattr(self._vehicle, 'last_update_time'):
            attributes["last_update"] = self._vehicle.last_update_time
            
        # Add VIN (last 4 digits only for privacy)
        if self._vehicle.vin:
            attributes["vin"] = f"***{self._vehicle.vin[-4:]}"
            
        return attributes if attributes else None