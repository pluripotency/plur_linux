import os
import sys
import re
import copy
from mini import misc
from mini.ansi_colors import red, blue, yellow
from plur import base_shell
from plur import session_wrap
from plur_linux.recipes.kvm import virsh
from plur_linux.recipes.kvm import qemu_img
from plur_linux.recipes.net import network
from plur_linux.recipes.ops import ssh as ssh_ops, ops
from plur_linux.recipes import setup
from plur_linux.recipes.kvm import cloudinit_ops
from plur_linux.recipes.kvm.cloud_image import (
    cloud_image_ops,
    centos as cloud_image_centos,
    ubuntu as cloud_image_ubuntu,
    arch as cloud_image_arch,
)
xml_dir = "/etc/libvirt/qemu"
vdisk_dir = "/vm_images"
diskformat = "qcow2"

def prepare_additional_vdisk(session, vm):
    hostname = vm.hostname
    vdisk_list = []
    for disk in vm.additional_vdisks:
        # disk = {
        #     'format': 'raw',
        #     'size': '10G',
        #     'dev_name': 'vdb'
        # }
        add_diskformat = disk["format"]
        size = disk["size"]
        dev_name = disk["dev_name"]
        if "disk_dir" in disk:
            add_disk_dir = disk["disk_dir"]
        else:
            add_disk_dir = vdisk_dir
        if dev_name == "vda":
            vdisk_path = f"{add_disk_dir}/{hostname}.{add_diskformat}"
        else:
            vdisk_path = f"{add_disk_dir}/{hostname}_{dev_name}.{add_diskformat}"
        if (
            "use_existing" in disk
            and disk["use_existing"]
            and base_shell.check_file_exists(session, vdisk_path)
        ):
            pass
        else:
            qemu_img.create(session, vdisk_path, size, add_diskformat)
        vdisk_list += [
            {
                "vdisk_path": vdisk_path,
                "add_diskformat": add_diskformat,
                "dev_name": dev_name,
            }
        ]
    return vdisk_list

def attach_additional_vdisk(session, vm, offline=False):
    if hasattr(vm, "additional_vdisks"):
        vdisk_list = prepare_additional_vdisk(session, vm)
        for vdisk in vdisk_list:
            vdisk_path = vdisk["vdisk_path"]
            add_diskformat = vdisk["add_diskformat"]
            dev_name = vdisk["dev_name"]
            virsh.attach_vdisk(
                session,
                vm.hostname,
                vdisk_path,
                add_diskformat,
                dev_name,
                offline=offline,
            )

def attach_vdisk(session, vm, offline=True):
    if hasattr(vm, "hostname"):
        hostname = vm.hostname

        vdisk_path = f"{vdisk_dir}/{hostname}.{diskformat}"
        virsh.attach_vdisk(
            session, hostname, vdisk_path, diskformat, "vda", offline=offline
        )

        attach_additional_vdisk(session, vm, offline=offline)
        if hasattr(vm, "cdrom"):
            virsh.attach_cdrom(session, hostname, vm.cdrom, offline=offline)
            update_disk_action = (
                f"virsh update-disk {hostname} {vm.cdrom} hdb --type cdrom"
            )
            if offline:
                update_disk_action += " --config"
            base_shell.run(session, update_disk_action)

def prepare_backing_or_copy_vdisk(session, vm):
    hostname = vm.hostname
    vdisk_org_path = vm.prepare_vdisk["org_path"]
    vdisk_type = vm.prepare_vdisk["type"]

    vdisk_path = f"{vdisk_dir}/{vm.hostname}.{diskformat}"
    if not base_shell.check_file_exists(session, vdisk_org_path):
        print(red(f"not found virtual disk: {vdisk_org_path}"))
        exit(1)

    created_image_path = f"{vdisk_dir}/{hostname}.qcow2"
    if vdisk_type == "backing":
        qemu_img.backing(session, vdisk_org_path, vdisk_path)
    elif vdisk_type == "copy":
        base_shell.run(session, f"sudo cp -f {vdisk_org_path} {vdisk_path}")
    else:
        print(red(f"unknown vdisk_type: {vdisk_type}"))
        exit(1)

    if "size" in vm.prepare_vdisk and isinstance(vm.prepare_vdisk["size"], int):
        size = vm.prepare_vdisk["size"]
        cloud_image_ops.resize_to(vdisk_path, size)(session)
    return created_image_path

def prepare_cloudinit_vdisk(session, vm):
    hostname = vm.hostname
    platform = vm.platform
    if hasattr(vm, "prepare_vdisk") and "type" in vm.prepare_vdisk:
        vdisk_type = vm.prepare_vdisk["type"]
        if vdisk_type == "cloud_image":
            cloud_image_func = None
            if platform == "almalinux9":
                cloud_image_func = cloud_image_centos.create_almalinux("9")
            elif platform == "almalinux8":
                cloud_image_func = cloud_image_centos.create_almalinux("8")
            elif platform == "arch":
                cloud_image_func = cloud_image_arch.create_arch
            elif platform == "almalinux10":
                cloud_image_func = cloud_image_centos.create_almalinux10
            elif platform == "centos8stream":
                cloud_image_func = cloud_image_centos.create_centos_stream("8")
            elif platform == "centos9stream":
                cloud_image_func = cloud_image_centos.create_centos_stream("9")
            elif platform == "fedora":
                cloud_image_func = cloud_image_centos.create_fedora()
            elif re.search("questing", vm.platform):
                cloud_image_func = cloud_image_ubuntu.create_ubuntu_cloudinit("questing")
            elif re.search("noble", vm.platform):
                cloud_image_func = cloud_image_ubuntu.create_ubuntu_cloudinit("noble")
            elif re.search("ubuntu", vm.platform):
                cloud_image_func = cloud_image_ubuntu.create_ubuntu_cloudinit("jammy")
            elif re.search("debian", vm.platform):
                cloud_image_func = cloud_image_ubuntu.create_debian_cloudinit("10")
            else:
                print(red("err in prepare_vdisk3: unknown os platform"))
                sys.exit(1)
            created_image_path = cloud_image_func(hostname)(session)
            if "size" in vm.prepare_vdisk and isinstance(vm.prepare_vdisk["size"], int):
                size = vm.prepare_vdisk["size"]
                cloud_image_ops.resize_to(created_image_path, size)(session)
        else:
            created_image_path = prepare_backing_or_copy_vdisk(session, vm)
        return created_image_path
    print(red("vm must have prepare_vdisk and type"))
    sys.exit(1)

def create_vnet_xml(session, xml_dir, vnet):
    """
    vnet: {
        'mac':
        'type':
        'bridge' or 'net_source':
    }
    """
    mac = vnet["mac"]
    filename = f"{xml_dir}/networks/" + vnet["mac"].replace(":", "") + ".xml"
    if "type" in vnet:
        net_type = vnet["type"]
    else:
        net_type = "default"

    net_source = vnet["net_source"]
    if net_type == "openvswitch":
        contents = [
            "<interface type='bridge'>",
            f"<mac address='{mac}'/>",
            f"<source bridge='{net_source}'/>",
            "<virtualport type='openvswitch'/>",
            "<model type='virtio'/>",
            "</interface>",
        ]
    elif net_type == "bridge":
        contents = [
            "<interface type='bridge'>",
            f"<mac address='{mac}'/>",
            f"<source bridge='{net_source}'/>",
            "<model type='virtio'/>",
            "</interface>",
        ]
    elif net_type == "macvtap":
        contents = [
            "<interface type='direct'>",
            f"<mac address='{mac}'/>",
            f"<source dev='{net_source}' mode='bridge'/>",
            "<model type='virtio'/>",
            "</interface>",
        ]
    elif net_type == "direct":
        contents = [
            "<interface type='direct'>",
            f"<mac address='{mac}'/>",
            f"<source dev='{net_source}' mode='vepa'/>",
            "<model type='virtio'/>",
            "</interface>",
        ]
    else:
        contents = [
            "<interface type='network'>",
            f"<mac address='{mac}'/>",
            f"<source network='{net_source}'/>",
            "<model type='virtio'/>",
            "</interface>",
        ]
    base_shell.here_doc(session, filename, contents)
    return filename

def start_domain_by_virt_install(vm, iso_full_path):
    def func(session):
        from plur_linux.recipes.kvm import virt_install_str

        hostname = vm.hostname
        vcpu = vm.vcpu
        vmem = vm.vmem
        vnets = []
        if hasattr(vm, "vnets"):
            vnets = vm.vnets
        option_list = ["--boot hd"]
        for vnet in vnets:
            option_list += [virt_install_str.create_vnet_opt_str(vnet)]

        disk_full_path = f"{vdisk_dir}/{hostname}.qcow2"
        option_list += [f"--disk {disk_full_path},cache=none --cdrom={iso_full_path}"]
        if hasattr(vm, "additional_vdisks"):
            vdisk_list = prepare_additional_vdisk(session, vm)
            for vdisk in vdisk_list:
                vdisk_path = vdisk["vdisk_path"]
                option_list += [f"--disk {vdisk_path},cache=none"]

        base_shell.run(
            session,
            virt_install_str.virt_install_str(
                hostname, option_list, os_variant="almalinux8", cpu=vcpu, mem=vmem
            ),
        )
    return func

def restart_domain(vm, created_seed_iso_path):
    hostname = vm.hostname
    @virsh.console(vm)
    def on_console(session):
        base_shell.run(session, "")

    def on_kvm(session):
        on_console(session)
        virsh.shutdown_from_kvm(session, hostname)
        base_shell.run(session, f"virsh change-media {hostname} --path sda --eject")
        base_shell.run(session, f"sudo rm -f {created_seed_iso_path}")
        base_shell.run(session, f'sudo virsh start {hostname}')
    return on_kvm

def find_user_password(vm, username="worker"):
    user_password = None
    if hasattr(vm, "offline_setups") and "users" in vm.offline_setups:
        user_list = vm.offline_setups["users"]
        for user in user_list:
            if user["username"] == username:
                user_password = user["password"]
    if user_password:
        return user_password
    print(red("userpassword not found in vm"))
    sys.exit(1)

def create_ubuntu_org_vm(vm):
    org_vm = copy.deepcopy(vm)
    org_vm.waitprompt = rf"\[?{vm.username}@({vm.org_hostname}|{vm.hostname}).+[$#] "
    org_vm.password = find_user_password(vm, username=vm.username)
    return org_vm

def find_root_password(vm):
    root_password = None
    if hasattr(vm, "offline_setups"):
        if "users" in vm.offline_setups:
            user_list = vm.offline_setups["users"]
            for user in user_list:
                if user["username"] == "root":
                    root_password = user["password"]
    root_password = (
        vm.root_password
        if hasattr(vm, "root_password")
        else vm.org_password
        if hasattr(vm, "org_password")
        else root_password
    )
    if root_password:
        return root_password
    print(red("either root_password or org_password or env root password is needed."))
    sys.exit(1)

def create_org_vm(vm):
    org_vm = copy.deepcopy(vm)
    org_username = vm.org_username if hasattr(vm, "org_username") else "root"
    if hasattr(vm, "org_hostname"):
        org_vm.waitprompt = rf"\[?{org_username}@({vm.org_hostname}|{vm.hostname}).+[$#] "
        org_vm.username = org_username
        org_vm.password = find_root_password(vm)
        return org_vm
    print(red("org_hostname is needed"))
    sys.exit(1)

def on_spawn_console(vm):
    if re.search("^ubuntu", vm.platform):
        org_vm = create_ubuntu_org_vm(vm)
    else:
        org_vm = create_org_vm(vm)

    @virsh.console(org_vm)
    def offline_setups(session):
        # hostname setting is needed for non-cloudinit
        ops.set_hostname(vm.hostname)(session)
        if re.search("^ubuntu", org_vm.platform):
            from plur_linux.recipes.ubuntu import netplan
            from plur_linux.recipes.ubuntu import ops as ubuntu_ops
            ubuntu_ops.disable_ipv6(session)
            netplan.configure(vm)(session)
        elif org_vm.platform == 'arch':
            from plur_linux.recipes.dists.arch import ops as arch_ops
            arch_ops.configure_network(vm.ifaces)(session)
        else:
            network.configure(vm)(session)
        if hasattr(vm, "prepare_vdisk"):
            if vm.platform in ["almalinux8"]:
                qemu_img.expand_fs(session, "/dev/vda", 2)
            else:
                qemu_img.expand_fs(session, "/dev/vda", 1)
        if hasattr(vm, "offline_setups"):
            print(red("in offline setups"))
            setup.offline_setup(session, vm)
            print(red("out offline setups"))

    @virsh.console(vm)
    def setups(session):
        print(red("in setups"))
        if hasattr(vm, "setups"):
            setup.run_setup_list(session, vm)
        print(red("out setups"))
        on_vm_post(vm)(session)
        if re.search("^ubuntu", vm.platform):
            base_shell.run(session, "reset")
        base_shell.run(session, "ip -4 a")

    @session_wrap.sudo
    def func(session):
        success_console_run = offline_setups(session)
        if not success_console_run:
            print(red("console run failed on offline setups"))
            sys.exit(1)

        session.child.delaybeforesend = 1
        success_console_run = setups(session)
        if not success_console_run:
            print(red("console run failed on setups"))
            sys.exit(1)
        session.child.delaybeforesend = 0
    return func


def on_create_console_with_cloudinit(vm):
    @session_wrap.sudo
    def offline_setups(session):
        # hostname and first nic are configured by seediso
        if re.search("^ubuntu", vm.platform):
            from plur_linux.recipes.ubuntu import netplan
            netplan.configure(vm)(session)
        elif vm.platform == 'arch':
            from plur_linux.recipes.dists.arch import ops as arch_ops
            arch_ops.configure_network(vm.ifaces)(session)
        else:
            network.configure(vm)(session)
        if hasattr(vm, "prepare_vdisk"):
            if "partition" in vm.prepare_vdisk:
                [dev, num] = vm.prepare_vdisk["partition"]
            else:
                dev = "/dev/vda"
                num = 1
            qemu_img.expand_fs(session, dev, num)
        if hasattr(vm, "offline_setups"):
            print(red("in offline setups"))
            setup.offline_setup(session, vm)
            print(red("out offline setups"))

    def setups(session):
        print(red("in setups"))
        if hasattr(vm, "setups"):
            setup.run_setup_list(session, vm)
        print(red("out setups"))

    @virsh.console(vm)
    def func(session):
        offline_setups(session)
        setups(session)
        on_vm_post(vm, cloudinit=True)(session)
        base_shell.run(session, "ip -4 a")

    return func

def on_kvm_post(vm):
    def func(session):
        if hasattr(vm, "imagefy"):
            virsh.shutdown_from_kvm(session, vm.hostname)
            if vm.imagefy is not True and "compress_to" in vm.imagefy:
                compress_to = vm.imagefy["compress_to"]
                vdisk_path = f"{vdisk_dir}/{vm.hostname}.qcow2"
                dst_img = compress_to

                actions = [
                    f"mkdir -p `dirname {compress_to}`",
                    f"qemu-img convert -c {vdisk_path} -O qcow2 {dst_img}"
                ]
                base_shell.run(session, " && ".join(actions))
                if "keep" in vm.imagefy and vm.imagefy["keep"]:
                    pass
                else:
                    destroy(vm)(session)
        elif hasattr(vm, "reboot") or hasattr(vm, "do_reboot"):
            virsh.reboot_from_kvm(session, vm.hostname)

    return func

def on_vm_post(vm, cloudinit=False):
    def remove_cloudinit(session):
        if re.search("^ubuntu", vm.platform):
            # > /dev/null is needed in virsh console for term size problem
            base_shell.run(session, "sudo apt remove -y cloud-init > /dev/null 2>&1 ")
        elif vm.platform == "arch":
            pass
        else:
            base_shell.run(session, "sudo dnf remove -y cloud-init")

    def func(session):
        if hasattr(vm, "imagefy"):
            if re.search("^ubuntu", vm.platform):
                _ = [base_shell.run(session, a) for a in [
                    "sudo hostnamectl set-hostname ubuntu", "sudo apt clean"
                ]]
            else:
                _ = [base_shell.run(session, a) for a in [
                    "sudo hostnamectl set-hostname localhost",
                    "sudo dnf clean all",
                    # "sudo systemctl disable NetworkManager-wait-online",
                ]]
                if base_shell.check_command_exists(session, "cloud-init"):
                    base_shell.run(session, "sudo cloud-init clean --logs")
            if (
                cloudinit
                and "rm_cloud-init" in vm.imagefy
                and vm.imagefy["rm_cloud-init"]
            ):
                remove_cloudinit(session)
        else:
            # if base_node.is_platform_rhel(vm.platform):
            #     base_shell.run(session, "sudo systemctl enable --now NetworkManager-wait-online")

            if cloudinit:
                remove_cloudinit(session)

    return func

def check_vdisk_exists(session, hostname):
    vdisk_path = f"{vdisk_dir}/{hostname}.{diskformat}"
    if base_shell.check_file_exists(session, vdisk_path):
        print("\n".join([
            "",
            red(f"{hostname} disk image exists."),
            yellow("I don't overwrite it to avoid accident."),
            yellow("Please delete the file manually and run again."),
        ]))
        sys.exit(1)
    else:
        print(blue(f"{hostname} disk image doesn't exist. "))

def check_already_defined(session, hostname):
    xml_path = f"{xml_dir}/{hostname}.xml"
    if base_shell.check_file_exists(session, xml_path):
        print("\n".join([
            "",
            red(f"{xml_path} is defined"),
            yellow("I don't overwrite it to avoid accident."),
            yellow("Please delete the file manually and run again."),
        ]))
    else:
        print(blue(f"{xml_path} is not defined."))

def on_kvm_pre_check_files(session, vm):
    hostname = vm.hostname
    check_vdisk_exists(session, hostname)
    check_already_defined(session, hostname)

def check_is_local_kvm(session):
    tmp_local_file = "/tmp/is_local_kvm_" + misc.create_timestamp_str()
    misc.open_write(tmp_local_file, "test")
    result = False
    if base_shell.check_file_exists(session, tmp_local_file):
        result = True
    misc.delete_file_path(tmp_local_file)
    return result

def on_kvm_prepare_cloudinit_seed_iso(vm):
    def func(session):
        is_local_kvm = check_is_local_kvm(session)
        if is_local_kvm:
            created_seed_iso_path = cloudinit_ops.create_host_seed_iso(vm)
        else:
            remote_kvm = session.nodes[-1]
            created_seed_iso_path = cloudinit_ops.create_host_seed_iso(vm, remote_kvm)
        return created_seed_iso_path

    return func

def create_vm_by_virt_install_cloudinit(vm):
    def _inner_on_kvm_sudo(created_image_path, created_seed_iso_path):
        @session_wrap.sudo
        def receive_inner_on_kvm_sudo(session):
            base_shell.work_on(session, vdisk_dir)
            base_shell.run(session, f"mv -f {created_image_path} {vdisk_dir}")

            start_domain_by_virt_install(vm, created_seed_iso_path)(session)
            restart_domain(vm, created_seed_iso_path)(session)

            on_create_console_with_cloudinit(vm)(session)

            on_kvm_post(vm)(session)
        return receive_inner_on_kvm_sudo

    def func(session):
        created_seed_iso_path = on_kvm_prepare_cloudinit_seed_iso(vm)(session)
        created_image_path = prepare_cloudinit_vdisk(session, vm)
        _inner_on_kvm_sudo(created_image_path, created_seed_iso_path)(session)
    return func

def destroy(vm):
    @session_wrap.sudo
    def func(session):
        hostname = vm.hostname
        vdisk_path = f"{vdisk_dir}/{hostname}.{diskformat}"
        base_shell.run(session, f"virsh destroy {hostname}")
        capt = base_shell.run(session, f"virsh dumpxml {hostname} | grep nvram | cat")
        if re.search(rf".+nvram/{hostname}_VARS.+", capt):
            base_shell.run(
                session, f"virsh undefine {hostname} --nvram && rm -f {vdisk_path}"
            )
        else:
            base_shell.run(session, f"virsh undefine {hostname} && rm -f {vdisk_path}")

    return func

def destroy_with_check(vm):
    answer = input(red(f'If you want to destroy {vm.hostname}, type "YES": '))
    if answer == "YES":
        return destroy(vm)
    print(yellow("Canceled."))
    return False
