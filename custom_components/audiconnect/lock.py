"""Lock platform for Audi Connect integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.lock import LockEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, ACTION_LOCK, ACTION_UNLOCK

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the lock platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    connection = hass.data[DOMAIN][config_entry.entry_id]["connection"]

    entities = []
    
    for vehicle in coordinator.data or []:
        entities.append(
            AudiConnectLock(
                coordinator,
                connection,
                vehicle,
            )
        )

    async_add_entities(entities)


class AudiConnectLock(CoordinatorEntity, LockEntity):
    """Representation of an Audi Connect lock."""

    def __init__(
        self,
        coordinator,
        connection,
        vehicle,
    ) -> None:
        """Initialize the lock."""
        super().__init__(coordinator)
        self._connection = connection
        self._vehicle = vehicle
        self._attr_unique_id = f"{vehicle.vin}_lock"
        self._attr_name = f"{vehicle.title} Lock"
        self._attr_icon = "mdi:car-door-lock"

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
    def is_locked(self) -> bool | None:
        """Return true if the lock is locked."""
        if not self._vehicle or not self._vehicle.state:
            return None
        
        lock_status = self._vehicle.state.get("overallLockStatus")
        return lock_status == "locked" if lock_status else None

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self._vehicle is not None
            and self._vehicle.state is not None
        )

    async def async_lock(self, **kwargs: Any) -> None:
        """Lock the vehicle."""
        try:
            await self._connection.execute_vehicle_action(self._vehicle.vin, ACTION_LOCK)
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error("Failed to lock vehicle %s: %s", self._vehicle.vin, ex)
            raise HomeAssistantError(f"Failed to lock vehicle: {ex}") from ex

    async def async_unlock(self, **kwargs: Any) -> None:
        """Unlock the vehicle."""
        try:
            await self._connection.execute_vehicle_action(self._vehicle.vin, ACTION_UNLOCK)
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error("Failed to unlock vehicle %s: %s", self._vehicle.vin, ex)
            raise HomeAssistantError(f"Failed to unlock vehicle: {ex}") from ex

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self._vehicle or not self._vehicle.state:
            return None
            
        attributes = {}
        vehicle_state = self._vehicle.state
        
        # Add detailed door status
        for door in ["leftFront", "rightFront", "leftRear", "rightRear"]:
            door_status = vehicle_state.get(f"{door}DoorLocked")
            if door_status is not None:
                attributes[f"{door.lower()}_door_locked"] = door_status
        
        # Add trunk status
        trunk_status = vehicle_state.get("trunkLocked")
        if trunk_status is not None:
            attributes["trunk_locked"] = trunk_status
        
        # Add last update time
        if hasattr(self._vehicle, 'last_update_time'):
            attributes["last_update"] = self._vehicle.last_update_time
            
        # Add VIN (last 4 digits only for privacy)
        if self._vehicle.vin:
            attributes["vin"] = f"***{self._vehicle.vin[-4:]}"
            
        return attributes if attributes else None