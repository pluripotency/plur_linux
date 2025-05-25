from recipes.kvm.adhoc_setup import generic


class Docker(generic.SelectMenu):
    def __init__(self):
        super().__init__({
            "kubeadm": False,
            'portainer': False,
            'cadvisor': False,
        },
            exclusive_list=None,
            menu_title='Docker')

    def setup(self, session):
        if self.enable:
            from recipes.almalinux9 import docker
            docker.install(session)

            from recipes.centos.docker import containers
            if self.selection['portainer']:
                containers.create_portainer(session)
            if self.selection['cadvisor']:
                containers.create_cadvisor(session)
            if self.selection['kubeadm']:
                from recipes.kubernetes import kubeadm
                kubeadm.setup_kubeadm(session)


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
            from recipes.almalinux9 import desktop
            desktop.install_gui(session)
            if self.selection['vbox libs']:
                desktop.install_vbox_additions_libs(session)
            if self.selection['xrdp']:
                desktop.install_xrdp(session)


class Apps(generic.SelectMenu):
    def __init__(self):
        from recipes.openssl import ca_menu
        super().__init__({
            "openvswitch": False,
            "pxe": False,
            "pxe_uefi": False,
            "ca": False,
            "qemu-kvm": False,
            "openldap": False,
            # "vpn_ldap": False,
            "rad_ldap": False,
            # "rad_mysql": False,
        },
            exclusive_list=['pxe', 'pxe_uefi'],
            menu_title='Apps',
            extra_menu={'ca': ca_menu.input_params})

    def setup(self, session):
        if self.selection['rad_ldap']:
            from recipes.centos.freeradius import rad_ldap
            rad_ldap.setup()(session)
        elif self.selection['openldap']:
            from recipes.centos.openldap import ldap_server
            ldap_server.setup()(session)
        if self.selection['qemu-kvm']:
            from recipes.kvm import virt_builder
            virt_builder.install_kvm(session)
        if self.selection['openvswitch']:
            from recipes.almalinux9 import openvswitch
            openvswitch.install(session)
        if self.selection['ca']:
            from recipes.openssl import ca_menu
            ca_menu.run_params(**self.extra_params['ca'])(session)

        if self.selection['pxe']:
            from recipes.almalinux9 import pxe
            pxe.setup_pxe(session)
        elif self.selection['pxe_uefi']:
            from recipes.almalinux9 import pxe
            pxe.setup_pxe_uefi(session)


def get_selection():
    platform = 'almalinux9'
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
