from mini.menu import get_y_n, choose_num, Selection
from plur import base_node
from plur_linux.recipes.kvm import spawn
from plur_linux.recipes.kvm.kvm_menu import lib, lib_vm_module, runner


def create_guest_by_select(session):
    selection = Selection('create_defined_guest')
    selection.set_title('last')
    vm_dict = lib_vm_module.select_vm_history(selection)
    default_restart = spawn.should_restart_before_setup(base_node.Node(vm_dict))
    restart_before_setup = lib.select_restart_before_setup(default=default_restart)
    vm_dict['restart_before_setup'] = restart_before_setup
    runner.create_vm_dict(vm_dict, restart_before_setup=restart_before_setup)(session)


def create_adhoc(session):
    connect_method_list = [
        'create vm'
    ]
    [vm_dict, postrun_list] = runner.select_adhoc(connect_method_list)
    def post_run(session):
        for instance in postrun_list:
            instance.setup(session)
    vm_dict['setups'] = {
        'run_post': post_run
    }
    if get_y_n('Do you want to run '):
        runner.create_vm_dict(vm_dict)(session)


def menu_on_kvm(session):
    menu_list = [
        ['create by select defined', create_guest_by_select]
        , ['create AdHoc', create_adhoc]
    ]
    num = choose_num([item[0] for item in menu_list], append_exit=True)
    menu_list[num][1](session)
