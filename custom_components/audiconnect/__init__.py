"""The Audi Connect integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN
from .coordinator import AudiConnectDataUpdateCoordinator

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.DEVICE_TRACKER,
    Platform.LOCK,
    Platform.NUMBER,
    Platform.SELECT,
    Platform.SENSOR,
    Platform.SWITCH,
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Audi Connect from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    session = async_get_clientsession(hass)

    # Initialize coordinator
    coordinator = AudiConnectDataUpdateCoordinator(hass, entry, session)

    # Fetch initial data
    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception as ex:
        _LOGGER.error("Unable to connect to Audi Connect: %s", ex)
        raise ConfigEntryNotReady from ex

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Set up platforms using the new method (HA 2025 compatible)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    # Register services
    await _async_register_services(hass, coordinator)

    # Add update listener
    entry.async_on_unload(entry.add_update_listener(update_listener))

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    # Remove services
    services_to_remove = [
        "refresh_data", 
        "execute_vehicle_action", 
        "turn_on_action", 
        "turn_off_action"
    ]
    
    for service_name in services_to_remove:
        if hass.services.has_service(DOMAIN, service_name):
            hass.services.async_remove(DOMAIN, service_name)

    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Update listener for options."""
    await hass.config_entries.async_reload(entry.entry_id)


async def _async_register_services(hass: HomeAssistant, coordinator) -> None:
    """Register integration services."""
    
    async def refresh_data(call):
        """Service to refresh vehicle data."""
        vin = call.data.get("vin")
        if vin and hasattr(coordinator, 'connection') and coordinator.connection:
            try:
                await coordinator.connection.refresh_vehicle_data(vin)
                await coordinator.async_request_refresh()
            except Exception as ex:
                _LOGGER.error("Failed to refresh data for VIN %s: %s", vin, ex)

    async def execute_vehicle_action(call):
        """Service to execute vehicle actions."""
        vin = call.data.get("vin")
        action = call.data.get("action")
        if vin and action and hasattr(coordinator, 'connection') and coordinator.connection:
            try:
                await coordinator.connection.execute_vehicle_action(vin, action)
                await coordinator.async_request_refresh()
            except Exception as ex:
                _LOGGER.error("Failed to execute action %s for VIN %s: %s", action, vin, ex)

    async def turn_on_action(call):
        """Service for turn on actions (backward compatibility)."""
        vin = call.data.get("vin")
        action = call.data.get("action")
        if vin and action and hasattr(coordinator, 'connection') and coordinator.connection:
            # Map old action names to new ones for backward compatibility
            action_mapping = {
                "climater": "start_climatisation",
                "charger": "start_charger",
                "preheater": "start_preheater",
                "window_heating": "start_window_heating",
            }
            mapped_action = action_mapping.get(action, f"start_{action}")
            
            try:
                await coordinator.connection.execute_vehicle_action(vin, mapped_action)
                await coordinator.async_request_refresh()
            except Exception as ex:
                _LOGGER.error("Failed to turn on %s for VIN %s: %s", action, vin, ex)

    async def turn_off_action(call):
        """Service for turn off actions (backward compatibility)."""
        vin = call.data.get("vin")
        action = call.data.get("action")
        if vin and action and hasattr(coordinator, 'connection') and coordinator.connection:
            # Map old action names to new ones for backward compatibility
            action_mapping = {
                "climater": "stop_climatisation",
                "charger": "stop_charger",
                "preheater": "stop_preheater",
                "window_heating": "stop_window_heating",
            }
            mapped_action = action_mapping.get(action, f"stop_{action}")
            
            try:
                await coordinator.connection.execute_vehicle_action(vin, mapped_action)
                await coordinator.async_request_refresh()
            except Exception as ex:
                _LOGGER.error("Failed to turn off %s for VIN %s: %s", action, vin, ex)

    # Register services
    hass.services.async_register(DOMAIN, "refresh_data", refresh_data)
    hass.services.async_register(DOMAIN, "execute_vehicle_action", execute_vehicle_action)
    hass.services.async_register(DOMAIN, "turn_on_action", turn_on_action)
    hass.services.async_register(DOMAIN, "turn_off_action", turn_off_action)