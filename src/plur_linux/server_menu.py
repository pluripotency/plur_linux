#! /usr/bin/env python
from plur import session_wrap
from plur import base_node
from plur import base_shell
from plur import log_param_templates
from mini.ansi_colors import blue, red, green
from mini.menu import get_input, choose_num, get_y_n, select_2nd
from mini import misc
from recipes.kvm.kvm_menu import runner as kvm_menu_runner
from recipes.kvm.kvm_menu import lib_kvm_module
from recipes.kvm.kvm_menu import lib_vm_module


def kvm_expand_volume():
    from recipes.kvm import qemu_img

    default_size = 20
    size = int(
        get_input(
            r"\d+",
            f"Disk Size (Default: {default_size}(G)): ",
            "invalid format",
            default_size,
        )
    )
    file_name = get_input(
        r"\w+", "Raw disk file name in /vm_images: ", "invalid format"
    )
    raw_disk_path = f"/vm_images/{file_name}"
    default_lv_path = "/dev/VolGroup/lv_root"
    lv_path = get_input(
        r"\w+",
        f"lv path (Default: {default_lv_path}): ",
        "invalid format",
        default_lv_path,
    )
    kvm = lib_kvm_module.select_kvm()
    log_params = log_param_templates.normal_on_tmp()
    kvm_menu_runner.run_on(
        kvm, qemu_img.expand_guest_raw_ext4(raw_disk_path, size, lv_path), log_params
    )


def configure_network():
    num = choose_num(["vm", "kvm", "Me"], "vm or kvm")
    if num == 0:
        node_module = select_2nd(lib_vm_module.vm_nodes, blue("Please select from vm"))
        node = select_2nd(node_module.create_nodes())
    elif num == 2:
        node = base_node.Me()
    else:
        node_module = select_2nd(
            lib_kvm_module.kvm_module_list, blue("Please select from kvm")
        )
        node = select_2nd(node_module.create_nodes())
    from recipes import setup
    session_wrap.ssh(node)(setup.setup_with_network)()


def post_run():
    num = choose_num(["vm", "kvm"], "vm or kvm")
    if num == 0:
        node_module = select_2nd(
            lib_vm_module.vm_nodes, blue("Please select from vm to Create")
        )
        node = select_2nd(node_module.create_nodes())
    else:
        node_module = select_2nd(
            lib_kvm_module.kvm_module_list, blue("Please select from kvm")
        )
        node = select_2nd(node_module.create_nodes())

    def func(session):
        from recipes import setup
        setup.run_setup_list(session, node)

    session_wrap.ssh(node)(func)()


def docker_menu():
    def func():
        all_nodes = (
            lib_vm_module.vm_nodes + lib_kvm_module.kvm_module_list + [["Me", ""]]
        )
        num = choose_num([n[0] for n in all_nodes], "Select node to deploy")
        from recipes.docker import git_repository

        if num == len(all_nodes) - 1:
            print(red("in Me"))
            session_wrap.bash()(git_repository.deploy)()
        else:
            print(red("in " + all_nodes[num][0]))
            session_wrap.ssh(all_nodes[num][1].create_nodes())(git_repository.deploy)()

    select_2nd([["deploy git_repository", func]], "Start Docker", vertical=True)


def change_password_by_libguestfs():
    from recipes.kvm.cloud_image import cloud_image_ops

    @session_wrap.sudo
    def on_kvm_sudo(session):
        image_dir = "/vm_images"
        base_shell.work_on(session, image_dir)
        base_shell.run(session, "ls")
        image_name = get_input(
            "[a-z][a-z0-9_]{0,30}",
            green("\nimage name(need power off):"),
            "Invalid name",
        )
        image_path = f"/vm_images/{image_name}"
        password = misc.read_json(
            "/mnt/MC/work_space/app_config/credentials/main.json"
        )["pass"]
        if get_y_n(f"password: {password} to {image_path}?"):
            cloud_image_ops.change_cloud_image_password(image_path, password)(session)

    kvm = lib_kvm_module.select_kvm()
    log_params = log_param_templates.normal_on_tmp()
    kvm_menu_runner.run_on(kvm, on_kvm_sudo, log_params)


def kvm_menu():
    select_2nd(
        [
            ["On KVM", kvm_menu_runner.menu_on_kvm],
            ["Create defined guest", kvm_menu_runner.create_defined_guest],
            #["Create defined guest from history", kvm_menu_runner.create_defined_guest_from_history],
            ["Expand Volume", kvm_expand_volume],
            ["Conf Network for defined nodes", configure_network],
            ["Post Run for defined nodes", post_run],
            ["Change password by libguestfs", change_password_by_libguestfs],
        ],
        "KVM Menu",
        vertical=True,
    )


if __name__ == "__main__":
    main_menu_list = [
        ["Ad Hoc Setup", kvm_menu_runner.ad_hoc_setup],
        ["KVM Menu", kvm_menu],
    ]
    while True:
        select_2nd(main_menu_list, green("Please select from Recipes"), vertical=True)
