"""Switch platform for Audi Connect integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN,
    ACTION_START_CLIMATISATION,
    ACTION_STOP_CLIMATISATION,
    ACTION_START_CHARGER,
    ACTION_STOP_CHARGER,
    ACTION_START_WINDOW_HEATING,
    ACTION_STOP_WINDOW_HEATING,
)

_LOGGER = logging.getLogger(__name__)

SWITCH_TYPES = {
    "climatisation": {
        "name": "Climatisation",
        "icon": "mdi:air-conditioner",
        "start_action": ACTION_START_CLIMATISATION,
        "stop_action": ACTION_STOP_CLIMATISATION,
        "state_key": "climatisationState",
        "on_state": "on",
    },
    "charger": {
        "name": "Charger",
        "icon": "mdi:ev-station",
        "start_action": ACTION_START_CHARGER,
        "stop_action": ACTION_STOP_CHARGER,
        "state_key": "chargingState",
        "on_state": "charging",
    },
    "window_heating": {
        "name": "Window Heating",
        "icon": "mdi:car-defrost-rear",
        "start_action": ACTION_START_WINDOW_HEATING,
        "stop_action": ACTION_STOP_WINDOW_HEATING,
        "state_key": "windowHeatingState",
        "on_state": "on",
    },
}


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the switch platform."""
    coordinator = hass.data[DOMAIN][config_entry.entry_id]["coordinator"]
    connection = hass.data[DOMAIN][config_entry.entry_id]["connection"]

    entities = []
    
    for vehicle in coordinator.data or []:
        for switch_type in SWITCH_TYPES:
            entities.append(
                AudiConnectSwitch(
                    coordinator,
                    connection,
                    vehicle,
                    switch_type,
                )
            )

    async_add_entities(entities)


class AudiConnectSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of an Audi Connect switch."""

    def __init__(
        self,
        coordinator,
        connection,
        vehicle,
        switch_type: str,
    ) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._connection = connection
        self._vehicle = vehicle
        self._switch_type = switch_type
        self._attr_unique_id = f"{vehicle.vin}_{switch_type}"
        
        switch_config = SWITCH_TYPES[switch_type]
        self._attr_name = f"{vehicle.title} {switch_config['name']}"
        self._attr_icon = switch_config.get("icon")
        self._start_action = switch_config["start_action"]
        self._stop_action = switch_config["stop_action"]
        self._state_key = switch_config["state_key"]
        self._on_state = switch_config["on_state"]

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
        """Return true if the switch is on."""
        if not self._vehicle or not self._vehicle.state:
            return None
        
        state_value = self._vehicle.state.get(self._state_key)
        if state_value is None:
            return None
            
        return str(state_value).lower() == self._on_state

    @property
    def available(self) -> bool:
        """Return if entity is available."""
        return (
            super().available
            and self._vehicle is not None
            and self._vehicle.state is not None
        )

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on."""
        try:
            await self._connection.execute_vehicle_action(
                self._vehicle.vin, self._start_action
            )
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error(
                "Failed to turn on %s for vehicle %s: %s",
                self._switch_type,
                self._vehicle.vin,
                ex
            )
            raise HomeAssistantError(
                f"Failed to turn on {self._switch_type}: {ex}"
            ) from ex

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off."""
        try:
            await self._connection.execute_vehicle_action(
                self._vehicle.vin, self._stop_action
            )
            await self.coordinator.async_request_refresh()
        except Exception as ex:
            _LOGGER.error(
                "Failed to turn off %s for vehicle %s: %s",
                self._switch_type,
                self._vehicle.vin,
                ex
            )
            raise HomeAssistantError(
                f"Failed to turn off {self._switch_type}: {ex}"
            ) from ex

    @property
    def extra_state_attributes(self) -> dict[str, Any] | None:
        """Return additional state attributes."""
        if not self._vehicle or not self._vehicle.state:
            return None
            
        attributes = {}
        vehicle_state = self._vehicle.state
        
        # Add switch-specific attributes
        if self._switch_type == "climatisation":
            temp = vehicle_state.get("targetTemperature")
            if temp:
                attributes["target_temperature"] = temp
                
        elif self._switch_type == "charger":
            remaining_time = vehicle_state.get("chargingRemainingTime")
            if remaining_time:
                attributes["charging_remaining_time"] = remaining_time
            
            charging_rate = vehicle_state.get("chargingRate")
            if charging_rate:
                attributes["charging_rate"] = charging_rate
        
        # Add last update time
        if hasattr(self._vehicle, 'last_update_time'):
            attributes["last_update"] = self._vehicle.last_update_time
            
        # Add VIN (last 4 digits only for privacy)
        if self._vehicle.vin:
            attributes["vin"] = f"***{self._vehicle.vin[-4:]}"
            
        return attributes if attributes else None