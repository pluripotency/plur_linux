from plur_linux.nodes.util import *
from plur_linux.recipes.kvm.adhoc_setup import run_account, generic


class MinDesk(generic.SelectMenu):
    def __init__(self):
        selection = {
            'ubuntu-desktop': False,
            'xubuntu-desktop': True,
            'lubuntu-desktop': False,
            'i3-desktop': False,
            'no-install-recommends': True,
            'ja-support': True,
            'xrdp': False,
            'xfreerdp': False,

        }
        exclusive_list = [
            [
                'ubuntu-desktop'
                , 'xubuntu-desktop'
                , 'lubuntu-desktop'
                , 'i3-desktop'
            ]
        ]
        super().__init__(selection, exclusive_list, 'Desktop')

    def setup(self, session):
        if self.enable:
            from plur_linux.recipes.ubuntu import desktop
            no_recommends = self.selection['no-install-recommends']
            ja_support = self.selection['ja-support']
            if self.selection['ubuntu-desktop']:
                desktop.install_desktop(session, no_recommends, ja_support)
            elif self.selection['xubuntu-desktop']:
                desktop.install_xubuntu(session, no_recommends, ja_support)
            elif self.selection['lubuntu-desktop']:
                desktop.install_lubuntu(session, no_recommends, ja_support)
            elif self.selection['i3-desktop']:
                desktop.install_i3(session, ja_support)

            if self.selection['xrdp']:
                desktop.setup_xrdp(session)
                base_shell.run(session, 'sudo systemctl set-default multi-user.target')
            else:
                base_shell.run(session, 'sudo systemctl set-default graphical.target')
            if self.selection['xfreerdp']:
                from plur_linux.recipes.rdp import xfreerdp
                xfreerdp.setup(session)


class Docker(generic.SelectMenu):
    def __init__(self):
        selection = {
            'firecracker': False,
            'portainer': False,
            'cadvisor': False,
        }
        super().__init__(selection, None, 'Docker')

    def setup(self, session):
        if self.enable:
            from plur_linux.recipes.ubuntu import docker_ce
            docker_ce.install(session)

                # [base_shell.run(session, action) for action in [
                #     'groupadd docker',
                #     f'usermod -aG docker {first_not_root_user["username"]}'
                # ]]

            def setup_containers(sess):
                if self.selection['firecracker']:
                    from plur_linux.recipes.ubuntu import firecracker
                    firecracker.install(session)
                from plur_linux.recipes.centos.docker import containers
                if self.selection['portainer']:
                    containers.create_portainer(sess)
                if self.selection['cadvisor']:
                    containers.create_cadvisor(sess)
            setup_containers(session)


class Apps(generic.SelectMenu):
    def __init__(self):
        super().__init__({
            "firefox no snap": False,
            "gns3": False,
            "openvswitch": False,
            "pxe_uefi": False,
        },
            exclusive_list=None,
            menu_title='Apps')

    def setup(self, session):
        if self.selection['firefox no snap']:
            from plur_linux.recipes.ubuntu import firefox_not_snap
            firefox_not_snap.setup(session)
        if self.selection['gns3']:
            from plur_linux.recipes.ubuntu import gns3
            gns3.install(session)
        if self.selection['openvswitch']:
            from plur_linux.recipes.ubuntu import openvswitch
            openvswitch.install_openvswitch(session)
        from plur_linux.recipes.ubuntu import pxe_jammy
        if self.selection['pxe_uefi']:
            pxe_jammy.setup_pxe(session)


def get_selection():
    platform = 'ubuntu jammy'
    vm = {
        'hostname': 'localhost',
        'platform': platform,
        'org_hostname': 'ubuntu',
        'ssh_options': '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
        'size': 8,
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


