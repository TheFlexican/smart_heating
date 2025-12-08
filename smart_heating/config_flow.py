"""Config flow for Smart Heating integration."""
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


class SmartHeatingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Smart Heating."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step.
        
        This is a simple config flow that doesn't require any user input.
        
        Args:
            user_input: User input data (not used in this basic implementation)
            
        Returns:
            FlowResult: Result of the flow step
        """
        _LOGGER.debug("Config flow started")
        
        # Check if already configured - only abort if there's an active entry
        existing_entries = self._async_current_entries()
        if existing_entries:
            _LOGGER.debug("Found %d existing entries", len(existing_entries))
            # Check if any entry is not being removed
            active_entries = [e for e in existing_entries if e.state not in (
                config_entries.ConfigEntryState.NOT_LOADED,
                config_entries.ConfigEntryState.FAILED_UNLOAD,
            )]
            if active_entries:
                _LOGGER.debug("Smart Heating already configured with active entry")
                return self.async_abort(reason="already_configured")
            else:
                _LOGGER.debug("Found entries but none are active, allowing new setup")
        
        if user_input is not None:
            _LOGGER.debug("Creating config entry")
            # Create the config entry
            return self.async_create_entry(
                title="Smart Heating",
                data={},
            )
        
        # Show the configuration form (empty in this case)
        _LOGGER.debug("Showing config form")
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema({}),
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Get the options flow for this handler.
        
        Args:
            config_entry: Config entry instance
            
        Returns:
            OptionsFlow: Options flow handler
        """
        return SmartHeatingOptionsFlowHandler()


class SmartHeatingOptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Smart Heating."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options.
        
        Args:
            user_input: User input data
            
        Returns:
            FlowResult: Result of the flow step
        """
        if user_input is not None:
            _LOGGER.debug("Updating options: %s", user_input)
            
            # Update the area manager with the OpenTherm gateway selection
            if DOMAIN in self.hass.data:
                for entry_id, data in self.hass.data[DOMAIN].items():
                    if isinstance(data, dict) and "area_manager" in data:
                        area_manager = data["area_manager"]
                        
                        # Set or clear the OpenTherm gateway
                        if user_input.get("opentherm_gateway_id"):
                            area_manager.set_opentherm_gateway(
                                user_input["opentherm_gateway_id"],
                                enabled=user_input.get("opentherm_enabled", True)
                            )
                            _LOGGER.info(
                                "OpenTherm gateway configured: %s (enabled: %s)",
                                user_input["opentherm_gateway_id"],
                                user_input.get("opentherm_enabled", True)
                            )
                        else:
                            area_manager.set_opentherm_gateway(None, enabled=False)
                            _LOGGER.info("OpenTherm gateway disabled")
                        
                        break
            
            return self.async_create_entry(title="", data=user_input)
        
        # Get all climate entities for the dropdown, filtering for OpenTherm-compatible devices
        climate_entities = []
        
        for entity_id in self.hass.states.async_entity_ids("climate"):
            state = self.hass.states.get(entity_id)
            if state:
                # Filter for OpenTherm gateways
                # Check if entity_id or friendly name contains "opentherm" or "otgw"
                entity_lower = entity_id.lower()
                friendly_name = state.attributes.get("friendly_name", entity_id)
                friendly_lower = friendly_name.lower()
                
                # Also check for known OpenTherm integration patterns
                is_opentherm = (
                    "opentherm" in entity_lower or
                    "opentherm" in friendly_lower or
                    "otgw" in entity_lower or
                    "otgw" in friendly_lower or
                    # Check for OpenTherm-specific attributes
                    "control_setpoint" in state.attributes or
                    "ch_water_temp" in state.attributes
                )
                
                if is_opentherm:
                    climate_entities.append((entity_id, f"{friendly_name} ({entity_id})"))
        
        # Sort by friendly name
        climate_entities.sort(key=lambda x: x[1])
        
        # Get current options
        current_gateway = self.config_entry.options.get("opentherm_gateway_id", "")
        current_enabled = self.config_entry.options.get("opentherm_enabled", True)
        
        # Create options with "None" option
        options_dict = {"": "None (Disabled)"}
        options_dict.update(dict(climate_entities))
        
        # Show options form
        _LOGGER.debug("Showing options form with %d climate entities", len(climate_entities))
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema({
                vol.Optional(
                    "opentherm_gateway_id",
                    description={"suggested_value": current_gateway},
                    default=""
                ): vol.In(options_dict),
                vol.Optional(
                    "opentherm_enabled",
                    description={"suggested_value": current_enabled},
                    default=True
                ): bool,
            }),
            description_placeholders={
                "info": "Configure the global OpenTherm gateway that will be used for boiler control across all areas."
            }
        )
