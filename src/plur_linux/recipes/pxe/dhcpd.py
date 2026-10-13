from plur import session_wrap
from plur import base_shell
from plur_linux.recipes import firewalld
from plur_linux.recipes.pxe import dhcpd_conf


def setup(pxe_ip, subnet_params=None, set_fw=True):
    if subnet_params is None:
        subnet_params = dhcpd_conf.get_subnet_params(pxe_ip)

    @session_wrap.sudo
    def func(session):
        if set_fw:
            firewalld.configure(services=['dhcp'], add=True)(session)
        base_shell.run(session, 'dnf install -y dhcp-server')
        conf_path = '/etc/dhcp/dhcpd.conf'
        contents = dhcpd_conf.create_pxe_dhcp_conf_str(pxe_ip, subnet_params)
        base_shell.here_doc(session, conf_path, contents.split('\n'))
        base_shell.run(session, 'systemctl enable --now dhcpd')
    return func

