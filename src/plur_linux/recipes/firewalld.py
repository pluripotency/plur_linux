from plur import base_shell
from plur import session_wrap


def install_if_not_exists(session):
    if not base_shell.check_command_exists(session, 'firewall-cmd'):
        base_shell.yum_install(session, {'packages': [
            'firewalld'
        ]})
    base_shell.service_on(session, 'firewalld')


def add_rich_rule(protocol):
    @session_wrap.sudo
    def func(session):
        base_shell.run(session, f'firewall-cmd --add-rich-rule=\'rule protocol value="{protocol}" accept\' --permanent')
        base_shell.run(session, f'firewall-cmd --reload')
    return func


def configure(services=['ssh'], ports=None, masquerade=False, zone='public', add=False):
    @session_wrap.sudo
    def func(session):
        install_if_not_exists(session)

        if add is False:
            # disable all services
            [base_shell.run(session, a) for a in [
                # '  services: ' is 12 chars, 13- chars are enabled services
                "TEMP=`firewall-cmd --list-all --zone='%s'| grep '  services:' | cut -c 13-`" % zone,
                'for word in $TEMP; do firewall-cmd --remove-service=$word; done',
                'for word in $TEMP; do firewall-cmd --remove-service=$word --permanent; done',
                'TEMP='
            ]]
            # disable all ports
            [base_shell.run(session, a) for a in [
                # '  ports: ' is 9 chars, 10- chars are enabled services
                "TEMP=`firewall-cmd --list-all --zone='%s'| grep '  ports:' | cut -c 10-`" % zone,
                'for word in $TEMP; do firewall-cmd --remove-port=$word; done',
                'for word in $TEMP; do firewall-cmd --remove-port=$word --permanent; done',
                'TEMP='
            ]]
        # add services
        if services is not None:
            cmd = 'firewall-cmd --add-service={0} --zone="%s"' % zone
            cmds = cmd + ' && ' + cmd + ' --permanent'
            [base_shell.run(session, cmds.format(s)) for s in services]
        # add ports
        if ports is not None:
            cmd = 'firewall-cmd --add-port={0} --zone="%s"' % zone
            cmds = cmd + ' && ' + cmd + ' --permanent'
            [base_shell.run(session, cmds.format(s)) for s in ports]
        if masquerade:
            base_shell.run(session, 'firewall-cmd --permanent --add-masquerade --zone="%s"' % zone)
        base_shell.run(session, 'firewall-cmd --reload')
    return func


def register_service(name, short_desc, desc, tcp_ports=[], udp_ports=[], zone='public'):
    @session_wrap.sudo
    def func(session):
        ports = ['  <port port="%s" protocol="tcp"/>' % p for p in tcp_ports]
        ports += ['  <port port="%s" protocol="udp"/>' % p for p in udp_ports]
        base_shell.here_doc(session, '/usr/lib/firewalld/services/%s.xml' % name, [
            '<?xml version="1.0" encoding="utf-8"?>',
            '<service>',
            '  <short>%s</short>' % short_desc,
            '  <description>%s</description>' % desc,
            '\n'.join(ports),
            '</service>'
        ])
        actions = [
            'systemctl restart firewalld',
            'firewall-cmd --add-service=%s --zone=%s' % (name, zone),
            'firewall-cmd --add-service=%s --zone=%s --permanent' % (name, zone),
            ]
        [base_shell.run(session, a) for a in actions]
    return func


