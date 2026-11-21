from plur_linux.recipes.kvm.adhoc_setup import generic


class MinDesk(generic.SelectMenu):
    def __init__(self):
        super().__init__({
            'enable rdp': False,
            'vbox libs': False,
        },
            exclusive_list=None,
            menu_title='Desktop')

    def setup(self, session):
        if self.enable:
            from plur_linux.recipes.desktop import redhat
            redhat.dict_desktop['almalinux10']['desktop'](session)
            if self.selection['enable rdp']:
                from plur_linux.recipes.almalinux10 import desktop
                desktop.enable_rdp(session)
            if self.selection['vbox libs']:
                redhat.dict_desktop['almalinux10']['vbox'](session)


class Apps(generic.SelectMenu):
    def __init__(self):
        from plur_linux.recipes.openssl import ca_menu
        super().__init__({
            "docker": False,
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
        if self.selection['docker']:
            from plur_linux.recipes.centos.docker import docker_dnf
            docker_dnf.install(session)
        if self.selection['rad_ldap']:
            from plur_linux.recipes.centos.freeradius import rad_ldap
            rad_ldap.setup()(session)
        elif self.selection['openldap']:
            from plur_linux.recipes.centos.openldap import ldap_server
            ldap_server.setup()(session)
        if self.selection['qemu-kvm']:
            from plur_linux.recipes.kvm import virt_builder
            virt_builder.install_kvm(session)
        if self.selection['openvswitch']:
            from plur_linux.recipes.almalinux10 import openvswitch
            openvswitch.install(session)
        if self.selection['ca']:
            from plur_linux.recipes.openssl import ca_menu
            ca_menu.run_params(**self.extra_params['ca'])(session)

        if self.selection['pxe']:
            from plur_linux.recipes.pxe import pxe
            pxe.setup_pxe('AlmaLinux 10', uefi=False)(session)
        elif self.selection['pxe_uefi']:
            from plur_linux.recipes.pxe import pxe
            pxe.setup_pxe('AlmaLinux 10')(session)


def get_selection():
    platform = 'almalinux10'
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
        generic.Languages(platform),
        generic.BaseApps(platform),
    ]
    return [vm, postrun_list]
