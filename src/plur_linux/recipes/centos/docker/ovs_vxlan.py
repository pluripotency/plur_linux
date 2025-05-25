import plur.base_shell as shell


def allow_segment(trust_seg_list=['172.16.0.0/12']):
    def func(session):
        actions = [
            'firewall-cmd --add-port=4789/udp --add-port=8472/udp',
            'firewall-cmd --permanent --add-port=4789/udp --add-port=8472/udp',
        ]
        actions += [
            f'firewall-cmd --permanent --zone=trusted --add-source={trust_seg}' for trust_seg in trust_seg_list
        ]
        [shell.run(session, 'sudo %s' % a) for a in actions]
    return func


def install_ovs_docker(session):
    session.sudo_i()
    actions = [
        'yum install -y wget',
        'cd /usr/bin',
        'wget https://raw.githubusercontent.com/openvswitch/ovs/master/utilities/ovs-docker',
        'chmod a+rx ovs-docker'
    ]
    [shell.run(session, a) for a in actions]
    session.su_exit()


def run_busybox(name, ip, br='br-vxlan'):
    def func(session):
        actions =[
            f'docker run -itd --network=none --name={name} busybox /bin/sh',
            f'ovs-docker add-port {br} eth0 {name} --ipaddress={ip}',
        ]
        [shell.run(session, f'sudo {a}') for a in actions]
    return func


def create(remote_ip_list, ip=None, br='br-vxlan'):
    def func(session):
        session.sudo_i()
        actions = [f'ovs-vsctl add-br {br}']
        if ip:
            actions += [
                f'ip addr add {ip} dev {br}',
                f'ip link set dev {br} up',
            ]
        # shell.here_doc(session, '/etc/sysconfig/network-scripts/ifcfg-%s' % br_vxlan, [
        #     'DEVICE=%s' % br_vxlan,
        #     'TYPE=Bridge',
        #     'IPADDR=%s' % sw_ip.split('/')[0],
        #     'PREFIX=%s' % sw_ip.split('/')[1],
        #     'ONBOOT=yes',
        #     'BOOTPROTO=none',
        #     'DELAY=0'
        # ])

        actions += [
            f'ovs-vsctl add-port {br} vxlan0 -- set Interface vxlan0 type=vxlan options:remote_ip={remote_ip}' for remote_ip in remote_ip_list
        ]
        [shell.run(session, a) for a in actions]
        session.su_exit()
    return func


def example():
    return lambda session: [
        allow_segment(['172.16.0.0/12']),
        install_ovs_docker,
        create('172.30.0.1/12', ['10.0.2.9']),
        run_busybox('con1', '172.18.0.1/24')
    ]
