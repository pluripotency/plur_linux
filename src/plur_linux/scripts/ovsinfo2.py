#!/usr/bin/env python3

import sys
import libvirt
from xml.dom import minidom

Conn = libvirt.open("qemu:///system")


def msg_out(msg):
    sys.stdout.write(msg + '\n')


def get_dom_list():
    dom_list = []
    for id in Conn.listDomainsID():
        dom_info = []
        vm = Conn.lookupByID(id)
        vm_xml_desc = minidom.parseString(vm.XMLDesc(0))
        for i, iface in enumerate(vm_xml_desc.getElementsByTagName("interface")):
            iface_type = iface.getAttribute("type")
            bridge = iface.getElementsByTagName("source")[0].getAttribute(iface_type)
            mac = iface.getElementsByTagName("mac")[0].getAttribute("address")
            device = iface.getElementsByTagName("target")[0].getAttribute("dev")
            dev_info = [bridge, mac, device, vm.name()]

            dom_info.append(dev_info)

        dom_list.append(dom_info)
    return dom_list


def show_taps(dom_list):
    fmt = "%-8s %-18s %-6s %-16s"
    for dom_info in dom_list:
        for devInfo in dom_info:
            msg_out(fmt % (devInfo[0], devInfo[1], devInfo[2], devInfo[3]))


if __name__ == "__main__":
    dom_iist = get_dom_list()
    show_taps(dom_iist)
