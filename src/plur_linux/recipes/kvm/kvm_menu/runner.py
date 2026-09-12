from mini.ansi_colors import red, cyan
from mini.menu import get_input, choose_num, select_2nd, get_y_n, Selection
from plur import base_shell
from plur import base_node
from plur import session_wrap
from plur import log_param_templates
from plur_linux.recipes.kvm import virsh
from plur_linux.recipes.kvm.kvm_menu import lib_kvm_module
from plur_linux.recipes.kvm.kvm_menu import lib_vm_module
from plur_linux.recipes.kvm import spawn
from . import lib


def run_on(kvm, func, log_params=None):
    if log_params is None:
        log_params = log_param_templates.normal_on_tmp()
    if kvm:
        return session_wrap.ssh(kvm, log_params=log_params)(func)()
    else:
        return session_wrap.bash(log_params=log_params)(func)()


def create_vm_dict(vm_dict):
    def func(session):
        vm = base_node.Node(vm_dict)
        if "prepare_vdisk" in vm_dict and "type" in vm_dict['prepare_vdisk']:
            spawn.create_vm_by_virt_install_cloudinit(vm)(session)
    return func


def create_vm_dict_on(kvm, vm_dict):
    run_on(kvm, create_vm_dict(vm_dict), log_params=None)


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

def select_adhoc(connect_method_list, hostname=None):
    from plur_linux.recipes.kvm.adhoc_setup.select_post_run import select_post_run
    from plur_linux.recipes.kvm.adhoc_setup import arch
    from plur_linux.recipes.kvm.adhoc_setup import almalinux10
    from plur_linux.recipes.kvm.adhoc_setup import almalinux9
    from plur_linux.recipes.kvm.adhoc_setup import almalinux8
    from plur_linux.recipes.kvm.adhoc_setup import centos10stream
    from plur_linux.recipes.kvm.adhoc_setup import fedora
    from plur_linux.recipes.kvm.adhoc_setup import ubuntu_jammy
    from plur_linux.recipes.kvm.adhoc_setup import ubuntu_noble
    from plur_linux.recipes.kvm.adhoc_setup import ubuntu_resolute
    from plur_linux.recipes.kvm.adhoc_setup import debian10

    [vm_dict, post_run_list] = select_2nd(
        [
            ["AlmaLinux9", almalinux9.get_selection],
            ["AlmaLinux10", almalinux10.get_selection],
            ["Arch", arch.get_selection],
            ["Ubuntu resolute", ubuntu_resolute.get_selection],
            ["Ubuntu noble", ubuntu_noble.get_selection],
            ["Fedora", fedora.get_selection],
            ["Debian10", debian10.get_selection],
            ["AlmaLinux8", almalinux8.get_selection],
            ["Ubuntu jammy", ubuntu_jammy.get_selection],
            ["CentOS10Stream", centos10stream.get_selection],
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
    elif login_method == 'bash':
        if get_y_n('Do you want to run '):
            vm = base_node.Node(vm_dict)
            session_wrap.bash(vm, log_params=log_param_templates.normal())(post_run)()
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
        if get_y_n('Do you want to run '):
            vm_dict['setups'] = {
                'run_post': post_run
            }
            create_vm_dict_on(kvm, vm_dict)
    elif login_method == 'create vm by copy':
        kvm = lib_kvm_module.select_kvm()
        vm_image_list = list_vm_images_on_kvm(kvm)
        while True:
            num = choose_num(menu_list=vm_image_list, message='Select vm copy from')
            if get_y_n('Do you want to copy from ' + vm_image_list[num]):
                break

        vm_dict['setups'] = {
            'run_post': post_run
        }
        vm_dict['prepare_vdisk'] = {
            'type': 'copy',
            'org_file': vm_image_list[num],
        }
        create_vm_dict_on(kvm, vm_dict)


def list_vm_images_on_kvm(kvm):
    @session_wrap.sudo
    def on_kvm(session):
        capt = base_shell.run(session, f'cd {spawn.vdisk_dir} && ls > /tmp/vm_image_list && cat /tmp/vm_image_list')
        return lib.parse_vm_image_list(capt)

    return run_on(kvm, on_kvm, log_params=log_param_templates.silent())

