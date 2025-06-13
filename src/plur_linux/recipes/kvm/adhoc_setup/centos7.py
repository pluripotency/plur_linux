from plur import session_wrap
from plur_linux.recipes.kvm.adhoc_setup import generic


class Docker(generic.SelectMenu):
    def __init__(self):
        super().__init__({
            'enable_api': False,
            'portainer': False,
            'cadvisor': False,
            'kubeadmin': False,
            'minikube': False,
        }, None, 'Docker')

    def setup(self, session):
        if self.enable:
            from plur_linux.recipes.centos.docker import setup_docker
            setup_docker.install_docker_if_not_installed(session)

            if self.selection['enable_api']:
                setup_docker.enable_rest_api(session)

            from plur_linux.recipes.centos.docker import containers
            if self.selection['portainer']:
                containers.create_portainer(session)
            if self.selection['cadvisor']:
                containers.create_cadvisor(session)

            if self.selection['kubeadmin']:
                from plur_linux.recipes.centos.kubernetes import kubeadm
                kubeadm.kubeadm_only()(session)
            if self.selection['minikube']:
                from plur_linux.recipes.centos.kubernetes import minikube
                minikube.setup(session)


class MinDesk(generic.SelectMenu):
    def __init__(self):
        super().__init__({
            'shortcuts': True,
            'xrdp': False,
            'xfreerdp': False,
            'vbox': False,
        }, None, 'Desktop')

    def setup(self, session):
        if self.enable:
            from plur_linux.recipes.centos.desktop import c7
            c7.minimul_to_mindesk(session)
            if self.selection['shortcuts']:
                c7.configure_desktop(session)
            if self.selection['vbox']:
                c7.lib_for_vboxadditions(session)
            if self.selection['xfreerdp']:
                from plur_linux.recipes.rdp import xfreerdp
                xfreerdp.setup(session)
            if self.selection['xrdp']:
                from plur_linux.recipes.centos import xrdp
                xrdp.install(session)


class Apps(generic.SelectMenu):
    def __init__(self):
        super().__init__({
            "nginx": False,
            "cobbler": False,
            "nfsen": False,
            "openldap": False,
            "vpn_ldap": False,
            "rad_ldap": False,
            "rad_mysql": False,
            "v70": False,
            "v80": False,
            "daloRADIUS": False,
            "openvswitch": False,
            "vsftpd": False,
        }, None, 'Apps')

    def setup(self, session):
        if self.selection['rad_ldap']:
            from plur_linux.recipes.centos.freeradius import rad_ldap
            rad_ldap.setup()(session)
        elif self.selection['openldap']:
            from plur_linux.recipes.centos.openldap import ldap_server
            ldap_server.setup()(session)
        elif self.selection['vpn_ldap']:
            from plur_linux.recipes.centos.openldap import vpn as ldap_server_vpn
            ldap_server_vpn.setup()(session)

        if self.selection['daloRADIUS']:
            from plur_linux.recipes.centos.freeradius import rad_mysql
            rad_mysql.setup(True)(session)
        elif self.selection['nginx']:
            from plur_linux.recipes.nginx import repo_install
            repo_install.install(session)
            from plur_linux.recipes.nginx import conf_reverse_proxy
            conf_reverse_proxy.gen_nginx_conf(session)
        elif self.selection['cobbler']:
            from plur_linux.recipes.centos.cobbler import install
            install.install(session)
            install.copy_kickstart(session)
        elif self.selection['rad_mysql']:
            from plur_linux.recipes.centos.freeradius import rad_mysql
            rad_mysql.setup(False)(session)
        elif self.selection['v70']:
            from plur_linux.recipes.docker.freeradius_mariadb import v70
            session_wrap.su('worker')(v70.run)(session)
        elif self.selection['v80']:
            from plur_linux.recipes.docker.freeradius_mariadb import v80
            session_wrap.su('worker')(v80.run)(session)
        if self.selection['openvswitch']:
            from plur_linux.recipes.centos.open_vswitch import install
            install.from_openstack(session)
        if self.selection['vsftpd']:
            from plur_linux.recipes import vsftpd
            vsftpd.vsftpd_server_setup(session)
        if self.selection['nfsen']:
            from plur_linux.recipes import nfsen
            nfsen.setup(session)


def get_selection():
    platform = 'centos7'
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
