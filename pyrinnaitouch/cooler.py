﻿"""Cooling unit handling"""
import logging

from .util import get_attribute, y_n_to_bool, symbol_to_schedule_period

_LOGGER = logging.getLogger(__name__)

def handle_cooling_mode(j,brivis_status):
    """Parse cooling part of JSON."""
    # pylint: disable=too-many-branches,too-many-statements,too-many-locals

    cfg = get_attribute(j[1].get("CGOM"),"CFG",None)
    if not cfg:
        # Probably an error
        _LOGGER.error("No CFG - Not happy, Jan")

    else:
        if y_n_to_bool(get_attribute(cfg, "ZAIS", None)):
            brivis_status.cooling_status.zones.append("A")
        if y_n_to_bool(get_attribute(cfg, "ZBIS", None)):
            brivis_status.cooling_status.zones.append("B")
        if y_n_to_bool(get_attribute(cfg, "ZCIS", None)):
            brivis_status.cooling_status.zones.append("C")
        if y_n_to_bool(get_attribute(cfg, "ZDIS", None)):
            brivis_status.cooling_status.zones.append("D")

    oop = get_attribute(j[1].get("CGOM"),"OOP",None)
    if not oop:
        # Probably an error
        _LOGGER.error("No OOP - Not happy, Jan")

    else:
        brivis_status.cooling_status.schedule_period = None
        brivis_status.cooling_status.advance_period = None
        brivis_status.cooling_status.advanced = False

        switch = get_attribute(oop,"ST",None)
        if switch == "N":
            _LOGGER.debug("Cooling is ON")
            brivis_status.system_on = True
            brivis_status.cooling_status.cooling_on = True
            brivis_status.cooling_status.set_circulation_fan_on(switch)

            # Cooling is on - get attributes
            fan_speed = get_attribute(oop,"FL",None)
            _LOGGER.debug("Fan Speed is: %s", fan_speed)
            brivis_status.cooling_status.fan_speed = int(fan_speed) # Should catch errors!

            # GSO should be there
            gso = get_attribute(j[1].get("CGOM"),"GSO",None)
            if not gso:
                # Probably an error
                _LOGGER.error("No GSO when cooling on. Not happy, Jan")
            else:
                # Cooling is on - get attributes
                op_mode = get_attribute(gso,"OP",None)
                _LOGGER.debug("Cooling OpMode is: %s", op_mode) # A = Auto, M = Manual
                brivis_status.cooling_status.set_mode(op_mode)

                # Set temp?
                set_temp = get_attribute(gso,"SP",None)
                _LOGGER.debug("Cooling set temp is: %s", set_temp)
                brivis_status.cooling_status.set_temp = int(set_temp)

                brivis_status.cooling_status.set_advanced(get_attribute(gso,"AO",None))

                _LOGGER.debug("Setting custom JSON path for Cooling")
                # gss = get_attribute(j[1].get("HGOM"),"GSS",None)
                gss = get_attribute(j[1].get("CGOM"),"GSS",None)

                if not gss:
                    _LOGGER.error("No GSS here")
                else:
                    period = symbol_to_schedule_period(get_attribute(gss,"AT",None))
                    brivis_status.cooling_status.schedule_period = period
                    period = symbol_to_schedule_period(get_attribute(gss,"AZ",None))
                    brivis_status.cooling_status.advance_period = period

        elif switch == "F":
            # Cooling is off
            _LOGGER.debug("Cooling is OFF")
            brivis_status.system_on = False
            brivis_status.cooling_status.cooling_on = False
            brivis_status.cooling_status.set_circulation_fan_on(switch)

        elif switch == "Z":
            _LOGGER.debug("Circulation Fan is: %s", switch)
            brivis_status.system_on = True
            brivis_status.cooling_status.set_circulation_fan_on(switch)

            fan_speed = get_attribute(oop,"FL",None)
            _LOGGER.debug("Fan Speed is: %s", fan_speed)
            brivis_status.cooling_status.fan_speed = int(fan_speed) # Should catch errors!

        zone_a = zone_b = zone_c = zone_d = None
        zone = get_attribute(j[1].get("CGOM"),"ZAO",None)
        if zone:
            zone_a = get_attribute(zone,"UE",None)
            brivis_status.cooling_status.zone_a_set_temp = get_attribute(zone,"SP", 999)
        zone = get_attribute(j[1].get("CGOM"),"ZBO",None)
        if zone:
            zone_b = get_attribute(zone,"UE",None)
            brivis_status.cooling_status.zone_b_set_temp = get_attribute(zone,"SP", 999)
        zone = get_attribute(j[1].get("CGOM"),"ZCO",None)
        if zone:
            zone_c = get_attribute(zone,"UE",None)
            brivis_status.cooling_status.zone_c_set_temp = get_attribute(zone,"SP", 999)
        zone = get_attribute(j[1].get("CGOM"),"ZDO",None)
        if zone:
            zone_d = get_attribute(zone,"UE",None)
            brivis_status.cooling_status.zone_d_set_temp = get_attribute(zone,"SP", 999)
        brivis_status.cooling_status.set_zones(zone_a,zone_b,zone_c,zone_d)

        zone = get_attribute(j[1].get("CGOM"),"ZAS",None)
        if zone:
            brivis_status.cooling_status.zone_a_auto = y_n_to_bool(get_attribute(zone,"AE",None))
            brivis_status.cooling_status.zone_a_temp = get_attribute(zone,"MT", 999)
        zone = get_attribute(j[1].get("CGOM"),"ZBS",None)
        if zone:
            brivis_status.cooling_status.zone_b_auto = y_n_to_bool(get_attribute(zone,"AE",None))
            brivis_status.cooling_status.zone_b_temp = get_attribute(zone,"MT", 999)
        zone = get_attribute(j[1].get("CGOM"),"ZCS",None)
        if zone:
            brivis_status.cooling_status.zone_c_auto = y_n_to_bool(get_attribute(zone,"AE",None))
            brivis_status.cooling_status.zone_c_temp = get_attribute(zone,"MT", 999)
        zone = get_attribute(j[1].get("CGOM"),"ZDS",None)
        if zone:
            brivis_status.cooling_status.zone_d_auto = y_n_to_bool(get_attribute(zone,"AE",None))
            brivis_status.cooling_status.zone_d_temp = get_attribute(zone,"MT", 999)
        zone = get_attribute(j[1].get("CGOM"),"ZUS",None)
        if zone:
            brivis_status.cooling_status.common_auto = y_n_to_bool(get_attribute(zone,"AE",None))
            brivis_status.cooling_status.temperature = get_attribute(zone,"MT", 999)

class CoolingStatus():
    """Cooling function status"""
    # pylint: disable=too-many-instance-attributes

    cooling_on = False
    fan_speed = 0
    circulation_fan_on = False
    manual_mode = False
    auto_mode = False
    set_temp = 0
    common_auto = False
    temperature = 999
    schedule_period = None
    advance_period = None
    advanced = False

    #zones
    zones = []
    zone_a = False
    zone_a_auto = False
    zone_a_temp = 999
    zone_a_set_temp = 999
    zone_b = False
    zone_b_auto = False
    zone_b_temp = 999
    zone_b_set_temp = 999
    zone_c = False
    zone_c_auto = False
    zone_c_temp = 999
    zone_c_set_temp = 999
    zone_d = False
    zone_d_auto = False
    zone_d_temp = 999
    zone_d_set_temp = 999

    def set_mode(self,mode):
        """Set auto/manual mode."""
        # A = Auto Mode and M = Manual Mode
        if mode == "A":
            self.auto_mode = True
            self.manual_mode = False
        elif mode == "M":
            self.auto_mode = False
            self.manual_mode = True

    def set_zones(self,zone_a,zone_b,zone_c,zone_d):
        """Define zones."""
        # Y = On, N = off
        self.zone_a = y_n_to_bool(zone_a)
        self.zone_b = y_n_to_bool(zone_b)
        self.zone_c = y_n_to_bool(zone_c)
        self.zone_d = y_n_to_bool(zone_d)

    def set_circulation_fan_on(self,status_str):
        """Set circ fan state."""
        # Z = On, N = Off
        if status_str == "Z":
            self.circulation_fan_on = True
        else:
            self.circulation_fan_on = False

    def set_advanced(self,status_str):
        """Set advanced state."""
        # A = Advance, N = None, O = Operation (what is that?)
        if status_str == "A":
            self.advanced = True
        else:
            self.advanced = False
