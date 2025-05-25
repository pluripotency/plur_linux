#!/usr/bin/python
#
# reginfo.py  : Register All Guests to Nicira if br-int is uesed
# 2012/03/16  First version by Tokyo Electron Device Ltd.
#
#

import sys
import libvirt
import os
import commands
from xml.dom import minidom

Conn = libvirt.open("qemu:///system")
Nbr = "br-int"


def msg_out(msg):
    sys.stdout.write(msg + '\n')


def get_dom_list(br="all"):
    dom_lst = []
    for id in Conn.listDomainsID():
        dom_info = []
        vm = Conn.lookupByID(id)
        vm_xml_desc = minidom.parseString(vm.XMLDesc(0))
        for i, iface in enumerate(vm_xml_desc.getElementsByTagName("interface")):
            iface_type = iface.getAttribute("type")
            if iface_type == "bridge":
                bridge = iface.getElementsByTagName("source")[0].getAttribute("bridge")
                mac = iface.getElementsByTagName("mac")[0].getAttribute("address")
                device = iface.getElementsByTagName("target")[0].getAttribute("dev")
                if bridge == Nbr:
                    dev_info = [vm.name(), vm.name() + "_" + mac[9:], device, mac, bridge]
                else:
                    dev_info = [vm.name(), "", device, mac, bridge]

                if br == "all":
                    dom_info.append(dev_info)
                else:
                    if bridge == br:
                        dom_info.append(dev_info)
        dom_lst.append(dom_info)
    return dom_lst


def show_taps(dom_list, simple=False):
    fmt = "%-16s %-22s %-6s %-18s %-8s"
    if not simple:
        msg_out(fmt % ("Domain", "Reg Name", "Tap", "MAC Address", "Bridge"))
    for dom_info in dom_list:
        if not simple:
            msg_out("-" * 78)
        for dev_info in dom_info:
            msg_out(fmt % (dev_info[0], dev_info[1], dev_info[2], dev_info[3], dev_info[4]))
            if dev_info[5] != "":
                msg_out(dev_info[5])


def get_registered(dev_info):
    tap = dev_info[2]
    cmd = "ovs-vsctl get Interface " + tap + " external-ids"
    return commands.getoutput(cmd)


def register_taps(dev_info):
    tap = dev_info[2]
    name = dev_info[1]
    mac = dev_info[3]

    cmd = "ovs-vsctl set Interface " + tap + " external-ids:iface-id=" + name \
          + " -- set interface " + tap + " external-ids:attached-mac=" + mac \
          + " -- set Interface " + tap + " external-ids:iface-status=active"

    commands.getoutput(cmd)


def get_args():
    if len(sys.argv) != 3:
        if len(sys.argv) == 1:
            br_name = "all"
            info_reg = "info"
            return [br_name, info_reg]
        else:
            msg_out("Usage: %s <all|br name> <info|reg>" % sys.argv[0])
            msg_out("If you specify <br name> like br-int, you only see br-int info")
            msg_out("<info> shows current infomations")
            msg_out("<reg> registers taps to NVP and shows current informations")
            exit(0)
    else:
        br_name = sys.argv[1]
        info_reg = sys.argv[2]
        if (info_reg != "info") and (info_reg != "reg"):
            msg_out("Wrong argument. <info|reg>")

        return [br_name, info_reg]


if __name__ == "__main__":
    [br_name, info_reg] = get_args()

    domList = get_dom_list(br_name)
    for domInfo in domList:
        for devInfo in domInfo:
            if devInfo[4] == Nbr:
                result = get_registered(devInfo)
                if result == '{attached-mac="' + devInfo[3] + \
                        '", iface-id="' + devInfo[1] + \
                        '", iface-status=active}':
                    devInfo.append("")
                elif result == '{}':
                    if info_reg == "reg":
                        register_taps(devInfo)
                        devInfo[0] = "*" + devInfo[0]
                    else:
                        devInfo[1] = "not registered"
                    devInfo.append("")
                else:
                    devInfo[1] = "duplicate info"
                    devInfo.append(result)
            else:
                devInfo.append("")

    show_taps(domList)
