from plur_linux.recipes.kvm.adhoc_setup import generic


class Docker(generic.SelectMenu):
    def __init__(self):
        super().__init__({
            'portainer': False,
            'cadvisor': False,
        },
            exclusive_list=None,
            menu_title='Docker')

    def setup(self, session):
        if self.enable:
            from plur_linux.recipes.almalinux8 import docker
            docker.install(session)

            def setup_containers(sess):
                nonlocal self
                from plur_linux.recipes.centos.docker import containers
                if self.selection['portainer']:
                    containers.create_portainer(sess)
                if self.selection['cadvisor']:
                    containers.create_cadvisor(sess)
            setup_containers(session)


class MinDesk(generic.SelectMenu):
    def __init__(self):
        super().__init__({
            'xrdp': False,
            'vbox libs': False,
        },
        exclusive_list=None,
        menu_title='Desktop')

    def setup(self, session):
        if self.enable:
            from plur_linux.recipes.almalinux8 import desktop
            desktop.install_gui(session)
            if self.selection['vbox libs']:
                desktop.install_vbox_additions_libs(session)
            if self.selection['xrdp']:
                desktop.install_xrdp(session)


class Apps(generic.SelectMenu):
    def __init__(self):
        super().__init__({
            "qemu-kvm": False,
            "google-auth": False,
            # "openvswitch": False,
            "vsftpd": False,
            "pxe": False,
            "pxe_uefi": False,
            "keepalived": False,
        },
            exclusive_list=['pxe', 'pxe_uefi'],
            menu_title='Apps')

    def setup(self, session):
        if self.selection['qemu-kvm']:
            from plur_linux.recipes.kvm import virt_builder
            virt_builder.install_kvm(session)
        if self.selection['google-auth']:
            from plur_linux.recipes.almalinux8 import google_authenticator
            google_authenticator.setup(session)
        # if self.selection['openvswitch']:
        #     from plur_linux.recipes.almalinux8 import openvswitch
        #     openvswitch.install(session)
        if self.selection['vsftpd']:
            from plur_linux.recipes import vsftpd
            vsftpd.vsftpd_server_setup(session)
        if self.selection['pxe']:
            from plur_linux.recipes.almalinux8 import pxe
            pxe.setup_pxe(session)
        elif self.selection['pxe_uefi']:
            from plur_linux.recipes.almalinux8 import pxe
            pxe.setup_pxe_uefi(session)
        if self.selection['keepalived']:
            from plur_linux.recipes import keepalived
            keepalived.dict_keepalived['almalinux8']['install'](session)


def get_selection():
    platform = 'almalinux8'
    vm = {
        'hostname': 'localhost',
        'platform': platform,
        'ssh_options': '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
        'size': 10,
    }
    postrun_list = [
        generic.Initial(platform),
        MinDesk(),
        Apps(),
        Docker(),
        generic.Languages(platform),
        generic.BaseApps(platform),
    ]
    return [vm, postrun_list]
