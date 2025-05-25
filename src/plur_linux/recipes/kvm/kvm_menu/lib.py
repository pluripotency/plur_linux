from plur import base_shell
from mini.menu import *
import re


ex_virsh_list_all_egrep_19 = """
 3     gl41042        running
 12    vpn97          running
 17    resp_w1        running
 19    resp_k1        running
 47    labdock064     running
 84    r21ldap152     running
 97    r21kacreg144   running
 98    r21syslog_s1   running
 99    a8dev          running
 101   win11          running
 112   r21ka158       running
 -     esxi67         shut off
 -     esxpxe67       shut off
 -     win10          shut off
"""


def parse_virsh_list_all_to_list(capture):
    """
    >>> parse_virsh_list_all_to_list(ex_virsh_list_all_egrep_19)
    [['a8dev', 'running'], ['esxi67', 'shut off'], ['esxpxe67', 'shut off'], ['gl41042', 'running'], ['labdock064', 'running'], ['r21ka158', 'running'], ['r21kacreg144', 'running'], ['r21ldap152', 'running'], ['r21syslog_s1', 'running'], ['resp_k1', 'running'], ['resp_w1', 'running'], ['vpn97', 'running'], ['win10', 'shut off'], ['win11', 'running']]
    """
    vm_state_list = []
    for line in capture.splitlines():
        sp = re.split(r'\s+', line)
        if len(sp) > 3:
            vm_state_list.append([sp[2], ' '.join(sp[3:])])
    return sorted(vm_state_list, key=lambda mem: mem[0])


def format_vm_item(num, vm_item, with_color=True):
    if with_color:
        if re.search('^run', vm_item[1]):
            return f'{str(num + 1).rjust(2)} {green(vm_item[0])}'.ljust(30)
        else:
            return f'{str(num + 1).rjust(2)} {red(vm_item[0])}'.ljust(30)
    else:
        return f'{str(num + 1).rjust(2)} {vm_item[0]}'.ljust(19)


def print_parsed_virsh_list_all(vm_state_list, with_color=True):
    """
    >>> print_parsed_virsh_list_all(parse_virsh_list_all_to_list(ex_virsh_list_all_egrep_19), with_color=False)
     1 a8dev            2 esxi67           3 esxpxe67         4 gl41042          5 labdock064
     6 r21ka158         7 r21kacreg144     8 r21ldap152       9 r21syslog_s1    10 resp_k1
    11 resp_w1         12 vpn97           13 win10           14 win11
    """
    print_str = ''
    for num, item in enumerate(vm_state_list):
        print_str += format_vm_item(num, item, with_color)
        if (num+1) % 5 == 0:
            print_str += '\n'
    print(print_str)


def get_vm_state_list(session):
    capture = base_shell.run(session, 'sudo virsh list --all | egrep "^ [1-9-]" | cat')
    vm_state_list = parse_virsh_list_all_to_list(capture)
    return vm_state_list


def list_kvm_guests(session):
    session.logger.output_log.pause_output()
    vm_state_list = get_vm_state_list(session)
    session.logger.output_log.continue_output()
    print_parsed_virsh_list_all(vm_state_list)
    return vm_state_list


def select_vmname(session, message):
    vm_state_list = list_kvm_guests(session)
    num_str = get_input(r'\d+', message)
    vmname = vm_state_list[int(num_str)-1][0]
    return vmname






