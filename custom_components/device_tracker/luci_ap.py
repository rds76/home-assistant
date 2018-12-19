"""
Support for OpenWRT (luci) routers.

For more details about this platform, please refer to the documentation at
https://home-assistant.io/components/device_tracker.luci/

Moded by rds76 to scan wifi AP for current assoc list
"""
import json
import logging
import re
from collections import namedtuple

import requests
import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.exceptions import HomeAssistantError
from homeassistant.components.device_tracker import (
    DOMAIN, PLATFORM_SCHEMA, DeviceScanner)
from homeassistant.const import (
    CONF_HOST, CONF_USERNAME, CONF_PASSWORD, CONF_SSL)

_LOGGER = logging.getLogger(__name__)

DEFAULT_SSL = False
CONF_INTERFACES = 'interfaces'
DEFAULT_INTERFACE = 'wlan0-1'

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend({
    vol.Required(CONF_HOST): cv.string,
    vol.Required(CONF_USERNAME): cv.string,
    vol.Required(CONF_PASSWORD): cv.string,
    vol.Optional(CONF_INTERFACES, default=[DEFAULT_INTERFACE]): vol.All(cv.ensure_list, [cv.string]),
    vol.Optional(CONF_SSL, default=DEFAULT_SSL): cv.boolean
    
})


class InvalidLuciTokenError(HomeAssistantError):
    """When an invalid token is detected."""

    pass


def get_scanner(hass, config):
    """Validate the configuration and return a Luci scanner."""
    scanner = LuciApDeviceScanner(config[DOMAIN])

    return scanner if scanner.success_init else None


Device = namedtuple('Device', ['mac', 'signal', 'inactive', 'interface', 'host'])


class LuciApDeviceScanner(DeviceScanner):
    """This class queries a wireless router running OpenWrt firmware."""

    def __init__(self, config):
        """Initialize the scanner."""
        self.host = config[CONF_HOST]
        protocol = 'http' if not config[CONF_SSL] else 'https'
        self.origin = '{}://{}'.format(protocol, self.host)
        self.username = config[CONF_USERNAME]
        self.password = config[CONF_PASSWORD]
        self.interfaces = config[CONF_INTERFACES]

        self.parse_api_pattern = re.compile(r"(?P<param>\w*) = (?P<value>.*);")

        self.last_results = {}
        self.refresh_token()
        self.mac2name = None
        self.success_init = self.token is not None

    def refresh_token(self):
        """Get a new token."""
        self.token = _get_token(self.origin, self.username, self.password)

    def scan_devices(self):
        """Scan for new devices and return a list with found device IDs."""
        self._update_info()
        return [device.mac for device in self.last_results]

    def get_device_name(self, device):
        """Return the name of the given device or None if we don't know."""
        # AP mode/no dhcp here - do not waste time here
        return
        if self.mac2name is None:
            url = '{}/cgi-bin/luci/rpc/uci'.format(self.origin)
            result = _req_json_rpc(
                url, 'get_all', 'dhcp', params={'auth': self.token})
            if result:
                hosts = [x for x in result.values()
                         if x['.type'] == 'host' and
                         'mac' in x and 'name' in x]
                mac2name_list = [
                    (x['mac'].upper(), x['name']) for x in hosts]
                self.mac2name = dict(mac2name_list)
            else:
                # Error, handled in the _req_json_rpc
                return
        return self.mac2name.get(device.upper(), None)

    def get_extra_attributes(self, device):
        """Return the IP of the given device."""
        filter_att = next((
            {
                'signal': result.signal,
                'inactive_ms': result.inactive,
                'interface': result.interface,
                'host': result.host
            } for result in self.last_results
            if result.mac == device), None)
        return filter_att

    def _update_info(self):
        """Ensure the information from the Luci router is up to date.

        Returns boolean if scanning successful.
        """
        if not self.success_init:
            return False

        self.last_results = []
        for index, interface in enumerate(self.interfaces):
           _LOGGER.info("Checking Wifi assoclist for host {0}@{1}#{2}".format(self.host, interface, index) )

           url = '{}/cgi-bin/luci/rpc/sys'.format(self.origin)

           try:
               result = _req_json_rpc(
                   url, 'wifi.getiwinfo', interface, params={'auth': self.token})
           except InvalidLuciTokenError:
               _LOGGER.info("Refreshing token")
               self.refresh_token()
               return False

           # no result and we are in the end of interfacs then return False
           if result:
               result = result['assoclist'];
               #_LOGGER.debug(result)
               for device_entry in result:
                   # _LOGGER.debug("MAC: " + device_entry)

                    self.last_results.append(Device( device_entry,
                                                     result[device_entry]['signal'],
                                                     result[device_entry]['inactive'],
                                                     interface,
                                                     self.host))

           elif ((index + 1) == len(self.interfaces)) and (len(self.last_results) == 0):
              return False
           
        _LOGGER.debug("MAC list for {0}: {1} ".format(self.host, str(self.last_results)))
        return True


def _req_json_rpc(url, method, *args, **kwargs):
    """Perform one JSON RPC operation."""
    data = json.dumps({'method': method, 'params': args})

    try:
        res = requests.post(url, data=data, timeout=5, **kwargs)
    except requests.exceptions.Timeout:
        _LOGGER.exception("Connection to the router timed out")
        return
    if res.status_code == 200:
        try:
            result = res.json()
        except ValueError:
            # If json decoder could not parse the response
            _LOGGER.exception("Failed to parse response from luci")
            return
        try:
            #_LOGGER.debug(result)
            return result['result']
        except KeyError:
            _LOGGER.exception("No result in response from luci")
            return
    elif res.status_code == 401:
        # Authentication error
        _LOGGER.exception(
            "Failed to authenticate, check your username and password")
        return
    elif res.status_code == 403:
        _LOGGER.error("Luci responded with a 403 Invalid token")
        raise InvalidLuciTokenError

    else:
        _LOGGER.error("Invalid response from luci: %s", res)


def _get_token(origin, username, password):
    """Get authentication token for the given configuration."""
    url = '{}/cgi-bin/luci/rpc/auth'.format(origin)
    return _req_json_rpc(url, 'login', username, password)
