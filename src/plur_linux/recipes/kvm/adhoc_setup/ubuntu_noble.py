from plur import base_shell
from recipes.kvm.adhoc_setup import generic

class Desktop(generic.SelectMenu):
    def __init__(self):
        selection = {
            'ubuntu-desktop': False,
            'xubuntu-desktop': True,
            'mate-desktop': False,
            'cinamon-desktop': False,
            'lubuntu-desktop': False,
            'xrdp': False,
            'startx': True,
            'xfreerdp': False,

        }
        exclusive_list = [
            [
                'ubuntu-desktop'
                , 'xubuntu-desktop'
                , 'mate-desktop'
                , 'cinamon-desktop'
                , 'lubuntu-desktop'
            ]
        ]
        super().__init__(selection, exclusive_list, 'Desktop')

    def setup(self, session):
        if self.enable:
            from recipes.ubuntu import desktop_noble
            enable_xrdp = self.selection['xrdp']
            if self.selection['ubuntu-desktop']:
                desktop_noble.install_gnome(session, enable_xrdp)
            elif self.selection['xubuntu-desktop']:
                desktop_noble.install_xubuntu(session, enable_xrdp)
            elif self.selection['mate-desktop']:
                desktop_noble.install_mate(session, enable_xrdp)
            elif self.selection['cinamon-desktop']:
                desktop_noble.install_mate(session, enable_xrdp)
            elif self.selection['lubuntu-desktop']:
                desktop_noble.install_lubuntu(session, enable_xrdp)

            if self.selection['startx']:
                base_shell.run(session, 'sudo systemctl set-default graphical.target')
            else:
                base_shell.run(session, 'sudo systemctl set-default multi-user.target')
            if self.selection['xfreerdp']:
                from recipes.rdp import xfreerdp
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
            from recipes.ubuntu import docker_ce
            docker_ce.install(session)

                # [base_shell.run(session, action) for action in [
                #     'groupadd docker',
                #     f'usermod -aG docker {first_not_root_user["username"]}'
                # ]]

            def setup_containers(sess):
                if self.selection['firecracker']:
                    from recipes.ubuntu import firecracker
                    firecracker.install(session)
                from recipes.centos.docker import containers
                if self.selection['portainer']:
                    containers.create_portainer(sess)
                if self.selection['cadvisor']:
                    containers.create_cadvisor(sess)
            setup_containers(session)

class Apps(generic.SelectMenu):
    def __init__(self):
        super().__init__({
            "gns3": False,
            "openvswitch": False,
        },
            exclusive_list=None,
            menu_title='Apps')

    def setup(self, session):
        if self.selection['gns3']:
            from recipes.ubuntu import gns3
            gns3.install(session)
        if self.selection['gns3']:
            from recipes.ubuntu import openvswitch
            openvswitch.install_openvswitch(session)

def get_selection():
    platform = 'ubuntu noble'
    vm = {
        'hostname': 'localhost',
        'platform': platform,
        'org_hostname': 'ubuntu',
        'ssh_options': '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
        'size': 8,
    }
    postrun_list = [
        generic.Initial(platform),
        Desktop(),
        Apps(),
        Docker(),
        generic.Languages(platform),
        generic.BaseApps(platform),
    ]
    return [vm, postrun_list]
