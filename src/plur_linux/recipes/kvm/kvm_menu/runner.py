from plur import base_shell
from plur import base_node
from plur import session_wrap
from plur import log_param_templates
from plur_linux.recipes.kvm import virsh
from plur_linux.recipes.kvm.kvm_menu import lib_kvm_module
from plur_linux.recipes.kvm.kvm_menu import lib_vm_module
from mini.ansi_colors import red, cyan
from mini.menu import re, get_input, choose_num, select_2nd, get_y_n, Selection
from mini import misc
from plur_linux.recipes.kvm import spawn
from . import lib


def run_on(kvm, func, log_params=None):
    if log_params is None:
        log_params = log_param_templates.normal_on_tmp()
    if kvm:
        session_wrap.ssh(kvm, log_params=log_params)(func)()
    else:
        session_wrap.bash(log_params=log_params)(func)()


def create_vm_dict(vm_dict, by_libguestfs=False):
    def func(session):
        kvm_platform = session.nodes[-1].platform
        vm = base_node.Node(vm_dict)
        if "prepare_vdisk" in vm_dict and "type" in vm_dict['prepare_vdisk']:
            vdisk_type = vm_dict['prepare_vdisk']["type"]
            if vdisk_type == "cloud_image":
                if by_libguestfs:
                    hostname = vm_dict['hostname']
                    username = vm_dict['username']
                    platform = vm_dict['platform']
                    if re.search("^ubuntu", platform):
                        vm.waitprompt = rf"{username}@(ubuntu|{hostname}):.+\$ "
                    else:
                        vm.waitprompt = rf"\[?{username}@(localhost|{hostname}) .+\]\$ "
                    spawn.create_vm_by_libguestfs(vm)(session)
                else:
                    if kvm_platform == "centos7":
                        spawn.create_vm_by_cloudinit(vm)(session)
                    else:
                        spawn.create_vm_by_virt_install_cloudinit(vm)(session)
            elif vdisk_type == "copy":
                if "cloudinit" in vm_dict['prepare_vdisk'] and "cloudinit" in vm_dict['prepare_vdisk']:
                    if kvm_platform == "centos7":
                        spawn.create_vm_by_cloudinit(vm)(session)
                    else:
                        spawn.create_vm_by_virt_install_cloudinit(vm)(session)
                else:
                    spawn.create_vm_by_copy_vdisk(vm)(session)
            else:
                spawn.create_vm_by_copy_vdisk(vm)(session)

    return func


def create_vm_dict_on(kvm, vm_dict, by_libguestfs=False):
    run_on(kvm, create_vm_dict(vm_dict, by_libguestfs), log_params=None)


def interact(session):
    base_shell.run(session, "stty -echo")

    def inner(session):
        action = get_input("")
        if action == "exit":
            base_shell.run(session, "stty -echo")
            return
        base_shell.run(session, action)
        return inner(session)

    return inner(session)


def menu_on_kvm():
    from plur_linux.recipes.kvm.kvm_menu import ops_guest, create_guest, destroy_guest, snapshot

    selection = Selection("create_defined_guest")
    selection.set_title("last")

    def inner(session):
        while True:
            print(cyan("\nCurrent VM Entries"))
            lib.list_kvm_guests(session)
            menu_list = [
                ["interact", interact],
                ["Ops", ops_guest.menu_on_kvm],
                ["Create", create_guest.menu_on_kvm],
                [red("Destroy"), destroy_guest.menu_on_kvm],
                ["Snapshot", snapshot.menu_on_kvm],
                ["Back"],
            ]
            num = choose_num([item[0] for item in menu_list])
            if num == len(menu_list) - 1:
                break
            else:
                menu_list[num][1](session)

    kvm = lib_kvm_module.select_kvm()
    return run_on(kvm, inner)


def create_defined_guest():
    selection = Selection("create_defined_guest")
    selection.set_title("last")

    vm_dict = lib_vm_module.select_vm_history(selection)
    kvm = lib_kvm_module.select_kvm_history(selection)

    selection.save()

    create_vm_dict_on(kvm, vm_dict)


# def create_defined_guest_from_history():
#     selection = Selection("history")
#     selection.load("last")
#     kvm_module = misc.find(
#         selection.selected_list, lambda index, obj: obj["key"] == "kvm_module"
#     )
#     vm_module = misc.find(
#         selection.selected_list, lambda index, obj: obj["key"] == "vm_module"
#     )
#     kvm = lib_kvm_module.extract_kvm(kvm_module)
#     vm = lib_vm_module.extract_vm(vm_module)
#     if get_y_n("Do you want to create_defined_guest"):
#         create_vm_on(kvm, vm)


def select_adhoc(connect_method_list, hostname=None):
    from plur_linux.recipes.kvm.adhoc_setup.select_post_run import select_post_run
    from plur_linux.recipes.kvm.adhoc_setup import arch
    from plur_linux.recipes.kvm.adhoc_setup import almalinux9
    from plur_linux.recipes.kvm.adhoc_setup import almalinux8
    from plur_linux.recipes.kvm.adhoc_setup import centos8stream
    from plur_linux.recipes.kvm.adhoc_setup import centos7
    from plur_linux.recipes.kvm.adhoc_setup import fedora
    from plur_linux.recipes.kvm.adhoc_setup import ubuntu_jammy
    from plur_linux.recipes.kvm.adhoc_setup import ubuntu_noble
    from plur_linux.recipes.kvm.adhoc_setup import debian10

    [vm_dict, post_run_list] = select_2nd(
        [
            ["AlmaLinux9", almalinux9.get_selection],
            ["AlmaLinux8", almalinux8.get_selection],
            ["Fedora", fedora.get_selection],
            ["Arch", arch.get_selection],
            ["Ubuntu jammy", ubuntu_jammy.get_selection],
            ["Ubuntu noble", ubuntu_noble.get_selection],
            ["Debian10", debian10.get_selection],
            ["CentOS8Stream", centos8stream.get_selection],
            ["CentOS7", centos7.get_selection],
        ],
        "Ad Hoc Setup: select OS",
    )
    vm_dict = select_post_run(vm_dict, post_run_list, connect_method_list, hostname)
    return [vm_dict, post_run_list]


def ad_hoc_setup():
    [vm_dict, post_run_list] = select_adhoc(None)
    def post_run(session):
        for instance in post_run_list:
            instance.setup(session)
    login_method = vm_dict['login_method']
    if login_method == 'ssh':
        if get_y_n('Do you want to run '):
            vm = base_node.Node(vm_dict)
            session_wrap.ssh(vm, log_params=log_param_templates.normal())(post_run)()
    elif login_method == 'virsh console':
        kvm = lib_kvm_module.select_kvm()
        if get_y_n('Do you want to run '):
            vm = base_node.Node(vm_dict)
            if kvm:
                session_wrap.ssh(kvm, log_params=log_param_templates.normal())(virsh.console(vm)(post_run))()
            else:
                session_wrap.bash(log_params=log_param_templates.normal())(virsh.console(vm)(post_run))()
    elif login_method == 'create vm':
        kvm = lib_kvm_module.select_kvm()
        num = choose_num([
            'cloudinit',
            'libguestfs',
        ], message='select create method')
        if num == 0:
            by_libguestfs = False
        else:
            by_libguestfs = True
        if get_y_n('Do you want to run '):
            vm_dict['setups'] = {
                'run_post': post_run
            }
            create_vm_dict_on(kvm, vm_dict, by_libguestfs=by_libguestfs)


# def destroy_guest(by_input=False):
#     def func():
#         if by_input:
#             hostname = get_input('\\w+', message='input hostname: ')
#             vm = new_node.destroy_node(hostname)
#         else:
#             node_module = select_2nd(lib_vm_module.vm_nodes, red("Please select from vm to Destroy"))
#             vm = select_2nd(node_module.destroy_nodes())
#         kvm = lib_kvm_module.select_kvm()
#         log_params = log_param_templates.append()
#         if kvm:
#             session_wrap.ssh(kvm, log_params=log_params)(spawn.destroy_with_check(vm))()
#         else:
#             session_wrap.bash(log_params=log_params)(spawn.destroy_with_check(vm))()
#
#     return func
