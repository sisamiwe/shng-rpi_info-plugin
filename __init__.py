#!/usr/bin/env python3
# vim: set encoding=utf-8 tabstop=4 softtabstop=4 shiftwidth=4 expandtab
#########################################################################
#  Copyright 2020-      <AUTHOR>                                  <EMAIL>
#########################################################################
#  This file is part of SmartHomeNG.
#  https://www.smarthomeNG.de
#  https://knx-user-forum.de/forum/supportforen/smarthome-py
#
#  Sample plugin for new plugins to run with SmartHomeNG version 1.8 and
#  upwards.
#
#  SmartHomeNG is free software: you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation, either version 3 of the License, or
#  (at your option) any later version.
#
#  SmartHomeNG is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with SmartHomeNG. If not, see <http://www.gnu.org/licenses/>.
#
#########################################################################

from lib.model.smartplugin import SmartPlugin
from lib.item import Items

from .webif import WebInterface

import subprocess
from datetime import timedelta


class RPi_Info(SmartPlugin):
    """
    Main class of the Plugin. Does all plugin specific stuff and provides the update functions for the items
    """

    PLUGIN_VERSION = '1.0.A'

    def __init__(self, sh):
        """
        Initalizes the plugin.

        If you need the sh object at all, use the method self.get_sh() to get it. There should be almost no need for
        a reference to the sh object any more.

        """

        # Call init code of parent class (SmartPlugin)
        super().__init__()

        self.alive = False

        try:
            self.webif_pagelength = self.get_parameter_value('webif_pagelength')
            self.poll_cycle = self.get_parameter_value('poll_cycle')
        except KeyError as e:
            self.logger.critical("Plugin '{}': Inconsistent plugin (invalid metadata definition: {} not defined)".format(self.get_shortname(), e))
            self._init_complete = False
            return

        # Initialization code goes here

        # On initialization error use:
        #   self._init_complete = False
        #   return

        self.init_webinterface(WebInterface)
        return

    def run(self):
        """
        Run method for the plugin
        """
        self.logger.debug("Run method called")
        # setup scheduler for device poll loop   (disable the following line, if you don't need to poll the device. Rember to comment the self_cycle statement in __init__ as well)
        self.scheduler_add('poll_device', self.poll_device, cycle=self.poll_cycle)

        self.alive = True

    def stop(self):
        """
        Stop method for the plugin
        """
        self.logger.debug("Stop method called")
        self.scheduler_remove('poll_device')
        self.alive = False

    def parse_item(self, item):
        """
        Default plugin parse_item method. Is called when the plugin is initialized.
        The plugin can, corresponding to its attribute keywords, decide what to do with
        the item in future, like adding it to an internal array for future reference
        :param item:    The item to process.
        :return:        If the plugin needs to be informed of an items change you should return a call back function
                        like the function update_item down below. An example when this is needed is the knx plugin
                        where parse_item returns the update_item function when the attribute knx_send is found.
                        This means that when the items value is about to be updated, the call back function is called
                        with the item, caller, source and dest as arguments and in case of the knx plugin the value
                        can be sent to the knx with a knx write function within the knx plugin.
        """
        if self.has_iattr(item.conf, 'rpiinfo_func'):
            self.logger.debug(f"parse item: {item}")
            self._itemlist.append(item)

        elif self.has_iattr(item.conf, 'rpiinfo_sys'):
            return self.update_item

    def parse_logic(self, logic):
        """
        Default plugin parse_logic method
        """
        if 'xxx' in logic.conf:
            # self.function(logic['name'])
            pass

    def update_item(self, item, caller=None, source=None, dest=None):
        """
        Item has been updated

        This method is called, if the value of an item has been updated by SmartHomeNG.
        It should write the changed value out to the device (hardware/interface) that
        is managed by this plugin.

        :param item: item to be updated towards the plugin
        :param caller: if given it represents the callers name
        :param source: if given it represents the source
        :param dest: if given it represents the dest
        """
        if self.alive and caller != self.get_shortname():
            # code to execute if the plugin is not stopped
            # and only, if the item has not been changed by this this plugin:
            self.logger.info(f"Update item: {item.property.path}, item has been changed outside this plugin")

            if self.has_iattr(item.conf, 'foo_itemtag'):
                self.logger.debug(f"update_item was called with item {item.property.path} from caller {caller}, source {source} and dest {dest}")
            pass

    def poll_device(self):
        """
        Polls for updates of the device

        This method is only needed, if the device (hardware/interface) does not propagate
        changes on it's own, but has to be polled to get the actual status.
        It is called by the scheduler which is set within run() method.
        """
        # # get the value from the device
        # device_value = ...
        #
        # # find the item(s) to update:
        # for item in self.sh.find_items('...'):
        #
        #     # update the item by calling item(value, caller, source=None, dest=None)
        #     # - value and caller must be specified, source and dest are optional
        #     #
        #     # The simple case:
        #     item(device_value, self.get_shortname())
        #     # if the plugin is a gateway plugin which may receive updates from several external sources,
        #     # the source should be included when updating the the value:
        #     item(device_value, self.get_shortname(), source=device_source_id)
        pass

    @staticmethod
    def _call(cmd, arg):
        process = subprocess.Popen([cmd, arg], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        return stdout.decode('utf-8').strip()

    def uptime2(self):
        with open("/proc/uptime", "r") as f:
            upt, __, __ = f.read().partition(' ')
        return int(float(upt))

    def uptime(self):
        with open('/proc/uptime', 'r') as f:
            uptime_seconds = float(f.readline().split()[0])
            return int(uptime_seconds)

    def uptime_string(self):
        time_str = str(timedelta(seconds=self.uptime()))
        return time_str

    def temp(self):
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            tmp = int(float(f.read().strip()) / 100) / 10
        return tmp

    def frequency(self):
        __, __, frq = self._call('vcgencmd', 'measure_clock arm').strip().partition('=')
        return int(int(frq) / 1000000)

    def _flags(self):
        __, __, thr = self._call('vcgencmd', 'get_throttled').strip().partition('=')
        return int(thr, 16)

    def under_voltage(self, flags):
        return bool(flags >> 0 & 1)

    def frequency_capped(self, flags):
        return bool(flags >> 1 & 1)

    def throttled(self, flags):
        return bool(flags >> 2 & 1)

    def temp_limit(self, flags):
        return bool(flags >> 3 & 1)

    def under_voltage_last_reboot(self, flags):
        return bool(flags >> 16 & 1)

    def throttled_last_reboot(self, flags):
        return bool(flags >> 17 & 1)

    def frequency_capped_last_reboot(self, flags):
        return bool(flags >> 18 & 1)

    def temp_limit_last_reboot(self, flags):
        return bool(flags >> 19 & 1)


throttled = {
    0: 'Under-voltage!',
    1: 'ARM frequency capped!',
    2: 'Currently throttled!',
    3: 'Soft temperature limit active',
    16: 'Under-voltage has occurred since last reboot.',
    17: 'Throttling has occurred since last reboot.',
    18: 'ARM frequency capped has occurred since last reboot.',
    19: 'Soft temperature limit has occurred'
}
