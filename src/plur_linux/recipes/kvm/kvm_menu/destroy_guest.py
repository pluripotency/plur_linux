from mini.menu import *
from recipes.kvm.kvm_menu import lib_vm_module, lib
from recipes.kvm import spawn
from nodes import new_node


def destroy_guest_by_input(session):
    vmname = get_input('[a-zA-Z][a-zA-Z0-9_-]+', yellow('Please input Name to destroy: '))
    vm = new_node.destroy_node(vmname)
    spawn.destroy_with_check(vm)(session)


def destroy_guest_from_virsh_list_all(session):
    vmname = lib.select_vmname(session, yellow('Please input Number of vm to destroy: '))
    vm = new_node.destroy_node(vmname)
    spawn.destroy_with_check(vm)(session)


def destroy_guest_by_select(session):
    node_module = select_2nd(lib_vm_module.vm_nodes, yellow("Please select from vm to Destroy"))
    vm = select_2nd(node_module.destroy_nodes())
    spawn.destroy_with_check(vm)(session)


def menu_on_kvm(session):
    destroy_guest_from_virsh_list_all(session)



