"""Support for Danfoss Ally"""
import base64
import json
import requests
import logging

from homeassistant.core import HomeAssistant
from homeassistant.components.climate import ClimateEntity
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.components.climate.const import (
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_OFF,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import TEMP_CELSIUS, TEMP_FAHRENHEIT

_LOGGER = logging.getLogger(__name__)

DOMAIN = "danfoss_ally"
BASE_API = "https://api.danfoss.com/ally"
OAUTH2_TOKEN = "https://api.danfoss.com/oauth2/token"
ACCESS_TOKEN = ""


def generate_base64_token(key: str, secret: str) -> str:
    _LOGGER.info("DANFOSS ALLY generate_base64_token")
    """ Generates a base64 token needed to retrive the access token from danfoss """
    key_secret = key + ":" + secret
    key_secret_bytes = key_secret.encode("ascii")
    base64_bytes = base64.b64encode(key_secret_bytes)
    base64_token = base64_bytes.decode("ascii")

    return base64_token


def get_access_token(base64_token: str) -> str:
    _LOGGER.info("DANFOSS ALLY get_access_token")
    """ Returns our access token """
    requestUrl = OAUTH2_TOKEN
    requestBata = {"grant_type": "client_credentials"}
    requestHeaders = {
        "Authorization": "Basic " + base64_token,
        "content-type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }
    requestBody = {}

    request = requests.post(
        requestUrl, headers=requestHeaders, json=requestBody, data=requestBata
    )
    response = json.loads(request.content)

    return response["access_token"]


def get_devices():
    _LOGGER.info("DANFOSS ALLY get_devices")
    """ Returns a list of devices the user has """
    requestUrl = BASE_API + "/devices"
    requestHeaders = {
        "Authorization": "Bearer " + ACCESS_TOKEN,
        "Accept": "application/json",
    }

    request = requests.get(requestUrl, headers=requestHeaders)
    response = json.loads(request.content)

    return response["result"]


def get_device_data(device_id):
    _LOGGER.info("DANFOSS ALLY get_device_data")
    """ Returns all data on a single device """
    requestUrl = BASE_API + "/devices/" + device_id
    requestHeaders = {
        "Authorization": "Bearer " + ACCESS_TOKEN,
        "Accept": "application/json",
    }

    request = requests.get(requestUrl, headers=requestHeaders)
    response = json.loads(request.content)

    return response["result"]


def get_device_status(device_id):
    """ Return status properties only on a device """
    requestUrl = BASE_API + "/devices/" + device_id + "/status"
    requestHeaders = {
        "Authorization": "Bearer " + ACCESS_TOKEN,
        "Accept": "application/json",
    }

    request = requests.get(requestUrl, headers=requestHeaders)
    response = json.loads(request.content)

    return response["result"]


def set_device_temp(device_id, temp) -> bool:
    """ Updates set_temp on a termostant (temp: 220=22degrees | 225=22.5degrees) """
    requestUrl = BASE_API + "/devices/" + device_id + "/commands"
    requestHeaders = {
        "Authorization": "Bearer " + ACCESS_TOKEN,
        "Accept": "application/json",
    }
    requestBody = {"commands": [{"code": "temp_set", "value": temp}]}

    request = requests.post(requestUrl, headers=requestHeaders, json=requestBody)
    response = json.loads(request.content)

    return response["result"]


def get_status_value(statuses, code: str) -> str or int:
    for status in statuses:
        if status["code"] == code:
            return status["value"]

    return False


def generate_entities():
    """ Create all termostat entities """
    devices = get_devices()
    entities = []

    for device in devices:
        entity = create_climate_entity(device)
        is_termostat = get_status_value(device["status"], "switch")

        if entity and is_termostat:
            entities.append(entity)

    return entities


def create_climate_entity(device):
    """ Create a Danfoss Ally climate entity """
    current_temperature = get_status_value(device["status"], "temp_current")
    device_id = device["id"]
    hvac_mode = HVAC_MODE_HEAT if device["online"] else HVAC_MODE_OFF
    max_temp = get_status_value(device["status"], "upper_temp")
    min_temp = get_status_value(device["status"], "lower_temp")
    name = device["name"]
    target_temperature = get_status_value(device["status"], "temp_set")

    entity = AllyTermostat(
        current_temperature,
        device_id,
        hvac_mode,
        max_temp,
        min_temp,
        name,
        target_temperature,
    )

    return entity


async def async_setup(hass: HomeAssistant, config, async_add_entities):
    _LOGGER.info("DANFOSS ALLY async_setup")
    global ACCESS_TOKEN

    if DOMAIN not in config:
        return True

    if not ACCESS_TOKEN:
        app_key = config["danfoss_ally"]["key"]
        app_secret = config["danfoss_ally"]["secret"]
        base64_token = generate_base64_token(app_key, app_secret)
        _LOGGER.info("DANFOSS ALLY ask for token")
        ACCESS_TOKEN = await hass.async_add_executor_job(get_access_token, base64_token)

    return True


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
):
    _LOGGER.info("DANFOSS ALLY async_setup_entry")
    """Set up the Danfoss Ally climate platform."""

    """ ally = hass.data[DOMAIN][entry.entry_id]["data"] """
    entities = await hass.async_add_executor_job(generate_entities)

    if entities:
        async_add_entities(entities, True)

    return True


class AllyTermostat(ClimateEntity):
    """ https://developers.home-assistant.io/docs/core/entity/climate """

    def __init__(
        self,
        current_temperature,
        device_id,
        hvac_mode,
        max_temp,
        min_temp,
        name,
        target_temperature,
    ):
        self._current_temperature = current_temperature
        self._heat_step = 0.5
        self._hvac_action = CURRENT_HVAC_OFF
        self._hvac_mode = hvac_mode
        self._max_temp = max_temp
        self._min_temp = min_temp
        self._name = name
        self._supported_features = SUPPORT_TARGET_TEMPERATURE
        self._supported_hvac_modes = [HVAC_MODE_OFF, HVAC_MODE_HEAT]
        self._target_temperature = target_temperature
        self._temperature_unit = TEMP_CELSIUS
        self._unique_id = f"ally_{device_id}"

    @property
    def current_temperature(self):
        return self._current_temperature

    @property
    def target_temperature_step(self):
        return self._heat_step

    @property
    def hvac_action(self):
        return self._hvac_action

    @property
    def hvac_mode(self):
        return self._hvac_mode

    @property
    def max_temp(self):
        return self._max_temp

    @property
    def min_temp(self):
        return self._min_temp

    @property
    def name(self):
        return self._name

    @property
    def supported_features(self):
        return self._supported_features

    @property
    def target_temperature(self):
        return self._target_temperature

    @property
    def unique_id(self):
        return self._unique_id
