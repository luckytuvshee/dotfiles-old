#pylint: disable=C0111,R0903

"""Displays the name, IP address(es) and status of each available network interface.

Requires the following python module:
    * netifaces

Parameters:
    * nic.exclude: Comma-separated list of interface prefixes to exclude (defaults to "lo,virbr,docker,vboxnet,veth")
    * nic.states: Comma-separated list of states to show (prefix with "^" to invert - i.e. ^down -> show all devices that are not in state down)
    * nic.format: Format string (defaults to "{intf} {state} {ip} {ssid}")
"""

import netifaces
import subprocess

import bumblebee.util
import bumblebee.input
import bumblebee.output
import bumblebee.engine

class Module(bumblebee.engine.Module):
    def __init__(self, engine, config):
        widgets = []
        super(Module, self).__init__(engine, config, widgets)
        self._exclude = tuple(filter(len, self.parameter("exclude", "lo,virbr,docker,vboxnet,veth").split(",")))

        self._states = {}
        self._states["include"] = []
        self._states["exclude"] = []
        for state in tuple(filter(len, self.parameter("states", "").split(","))):
            if state[0] == "^":
                self._states["exclude"].append(state[1:])
            else:
                self._states["include"].append(state)
        self._format = self.parameter("format","{intf} {state} {ip} {ssid}");
        self._update_widgets(widgets)
        self.iwgetid = bumblebee.util.which("iwgetid")


    def update(self, widgets):
        self._update_widgets(widgets)

    def state(self, widget):
        states = []

        if widget.get("state") == "down":
           states.append("critical")
        elif widget.get("state") != "up":
            states.append("warning")

        intf = widget.get("intf")
        iftype = "wireless" if self._iswlan(intf) else "wired"
        iftype = "tunnel" if self._istunnel(intf) else iftype

        states.append("{}-{}".format(iftype, widget.get("state")))

        return states

    def _iswlan(self, intf):
        # wifi, wlan, wlp, seems to work for me
        if intf.startswith("w"): return True
        return False

    def _istunnel(self, intf):
        return intf.startswith("tun") or intf.startswith("wg")

    def get_addresses(self, intf):
        retval = []
        try:
            for ip in netifaces.ifaddresses(intf).get(netifaces.AF_INET, []):
                if ip.get("addr", "") != "":
                    retval.append(ip.get("addr"))
        except Exception:
            return []
        return retval

    def _update_widgets(self, widgets):
        interfaces = [i for i in netifaces.interfaces() if not i.startswith(self._exclude)]

        for widget in widgets:
            widget.set("visited", False)

        for intf in interfaces:
            addr = []
            state = "down"
            for ip in self.get_addresses(intf):
                addr.append(ip)
                state = "up"

            if len(self._states["exclude"]) > 0 and state in self._states["exclude"]: continue
            if len(self._states["include"]) > 0 and state not in self._states["include"]: continue

            # hide disconnected networks or interfaces that are down.
            if(state == "down"):
                continue

            widget = self.widget(intf)
            if not widget:
                widget = bumblebee.output.Widget(name=intf)
                widgets.append(widget)
            # join/split is used to get rid of multiple whitespaces (in case SSID is not available, for instance
            widget.full_text(" ".join(self._format.format(ip=", ".join(addr),intf=intf,state=state,ssid=self.get_ssid(intf)).split()))
            widget.set("intf", intf)
            widget.set("state", state)
            widget.set("visited", True)

        for widget in widgets:
            if widget.get("visited") is False:
                widgets.remove(widget)

    def get_ssid(self, intf):
        if self._iswlan(intf):
            try:
                return subprocess.check_output([self.iwgetid,"-r",intf]).strip().decode('utf-8')
            except:
                return ""
        return ""

# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4
