from mini.menu import get_y_n, choose_num, Selection
from mini import misc
from plur import base_node
from plur_linux.recipes.kvm.kvm_menu import lib_vm_module, runner
from plur_linux.nodes import new_node


def create_guest_by_select(session):
    selection = Selection('create_defined_guest')
    selection.set_title('last')
    vm_dict = lib_vm_module.select_vm_history(selection)
    runner.create_vm_dict(vm_dict)(session)


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
