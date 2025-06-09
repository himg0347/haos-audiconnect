"""Device tracker platform for Audi Connect integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the device tracker platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    connection = hass.data[DOMAIN][config_entry.entry_id]["connection"]

    entities = []
    
    for vehicle in coordinator.data or []:
        entities.append(
            AudiConnectDeviceTracker(
                coordinator,
                connection,
                vehicle,
            )
        )

    async_add_entities(entities)


class AudiConnectDeviceTracker(CoordinatorEntity, TrackerEntity):
    """Representation of an Audi Connect device tracker."""

    def __init__(
        self,
        coordinator,
        connection,
        vehicle,
    ) -> None:
        """Initialize the device tracker."""
        super().__init__(coordinator)
        self._connection = connection
        self._vehicle = vehicle
        self._attr_unique_id = f"{vehicle.vin}_tracker"
        self._attr_name = f"{vehicle.title} Location"
        self._attr_icon = "mdi:car"

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
    def latitude(self) -> float | None:
        """Return latitude value of the device."""
        if not self._vehicle or not self._vehicle.state:
            return None
        
        position = self._vehicle.state.get("position")
        if position and "lat" in position:
            try:
                return float(position["lat"])
            except (ValueError, TypeError):
                return None
        return None

    @property
    def longitude(self) -> float | None:
        """Return longitude value of the device."""
        if not self._vehicle or not self._vehicle.state:
            return None
        
        position = self._vehicle.state.get("position")
        if position and "lng" in position:
            try:
                return float(position["lng"])
            except (ValueError, TypeError):
                return None
        return None

    @property
    def location_accuracy(self) -> int:
        """Return the location accuracy of the device."""
        return 100  # Meters

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self._vehicle or not self._vehicle.state:
            return None
            
        attributes = {}
        vehicle_state = self._vehicle.state
        
        # Add parking information if available
        if "parkingPosition" in vehicle_state:
            parking_pos = vehicle_state["parkingPosition"]
            if parking_pos:
                attributes["parking_time"] = parking_pos.get("parkingTime")
                
        # Add movement status
        attributes["is_moving"] = vehicle_state.get("isMoving", False)
        
        # Add last update time
        if hasattr(self._vehicle, 'last_update_time'):
            attributes["last_update"] = self._vehicle.last_update_time
            
        # Add VIN (last 4 digits only for privacy)
        if self._vehicle.vin:
            attributes["vin"] = f"***{self._vehicle.vin[-4:]}"
            
        return attributes if attributes else None

    @property
    def source_type(self) -> str:
        """Return the source type of the device."""
        return "gps"