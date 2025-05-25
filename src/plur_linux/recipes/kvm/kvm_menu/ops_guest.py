from mini.ansi_colors import yellow
from mini.menu import re, choose_num, get_y_n
from plur import base_node
from plur import base_shell
from plur import session_wrap
from recipes.kvm import virsh
from recipes.kvm.kvm_menu import runner, lib


def start_vm(session):
    hostname = lib.select_vmname(session, yellow("Please select vmname to start: "))
    base_shell.run(session, f"sudo virsh start {hostname}")


def shutdown_vm(session):
    hostname = lib.select_vmname(session, yellow("Please select vmname to shutdown: "))
    base_shell.run(session, f"sudo virsh shutdown {hostname}")


def setup_adhoc(session):
    hostname = lib.select_vmname(session, yellow("Please select vmname: "))
    [vm_dict, postrun_list] = runner.select_adhoc(connect_method_list=None, hostname=hostname)
    vm_dict["hostname"] = hostname
    username = vm_dict["username"]
    if re.search("^ubuntu", vm_dict["platform"]):
        vm_dict["waitprompt"] = rf"{username}@(ubuntu|{hostname}):.+\$ "
    else:
        vm_dict["waitprompt"] = rf"\[?{username}@(localhost|{hostname}) .+\]\$ "

    def post_run(session):
        for instance in postrun_list:
            instance.setup(session)
    # post_run = vm_dict['setups']['run_post']

    vm_node = base_node.Node(vm_dict)
    if get_y_n("Do you want to run "):
        (virsh.console(vm_node)(post_run))(session)


def configure_nic(session):
    from nodes import new_node
    hostname = lib.select_vmname(session, yellow("Please select vmname: "))
    vm_dict = new_node.create_single_iface_node_dict(hostname)
    vm_dict["hostname"] = hostname
    username = vm_dict["username"]
    vm_dict["waitprompt"] = rf"\[?{username}@(localhost|{hostname})[ :].+\]?\$ "
    vm_node = base_node.Node(vm_dict)

    def by_user(session):
        capt = base_shell.run(session, "cat /etc/issue")
        if re.search("Ubuntu", capt):
            session.nodes[-1].platform = "ubuntu"
            from recipes.ubuntu import netplan
            netplan.configure(vm_node)(session)
        else:
            from recipes.net import network
            session_wrap.sudo(network.configure(vm_node))(session)

    if get_y_n("Do you want to run "):
        (virsh.console(vm_node)(by_user))(session)


def menu_on_kvm(session):
    menu_list = [
        ["setup AdHoc", setup_adhoc],
        ["Start VM", start_vm],
        ["Shutdown VM", shutdown_vm],
        ["Configure NIC", configure_nic],
        ["Back"],
    ]
    num = choose_num([item[0] for item in menu_list])
    if num != len(menu_list) - 1:
        menu_list[num][1](session)
