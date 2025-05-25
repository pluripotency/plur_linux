import re
from mini import misc
from plur import session_wrap
from plur import base_shell


def create_seed_meta_data_str(hostname):
    meta_data = f"""
    local-hostname: {hostname}
    """
    return misc.del_indent(meta_data)


def create_seed_meta_data_link_local_str(vm):
    if hasattr(vm, 'vnets'):
        vnet_list = vm.vnets
    else:
        vnet_list = [{'ifname': 'eth0'}]
    meta_data = misc.del_indent(f"""
    local-hostname: {vm.hostname}
    network-interfaces: |
    
    """)
    for vnet in vnet_list:
        ifname = vnet['ifname']
        meta_data += misc.del_indent(f"""
            auto {ifname}
            iface {ifname} inet static
                address 169.254.0.1 
                netmask 255.255.255.0\n
        """)

    return meta_data


def create_seed_meta_data_ifaces_str(hostname, ifaces):
    """
    for cloud-init 23.4.1 reference
    https://cloudinit.readthedocs.io/en/latest/reference/network-config-format-v1.html
    """
    meta_data = misc.del_indent(f"""
    local-hostname: {hostname}
    network-interfaces: |
    
    """)
    for iface in ifaces:
        ifname = iface['con_name'] if 'con_name' in iface else iface['name'] if 'name' in iface else False
        if 'ip' in iface:
            ip = iface['ip']
            if ip and misc.is_ipv4_with_prefix(ip):
                ip_sp = ip.split('/')
                netmask = misc.prefix_to_netmask(ip_sp[1])
                meta_data += misc.del_indent(f"""
                    auto {ifname}
                    iface {ifname} inet static
                    address {ip_sp[0]}
                    netmask {netmask}

                """)
                additional = []
                if 'gateway' in iface:
                    additional += ['gateway ' + iface['gateway']]
                if 'nameservers' in iface:
                    nameservers = iface['nameservers']
                    if isinstance(nameservers, list) and len(nameservers) > 0:
                        ns = ' '.join(nameservers)
                        additional += ['dns-nameservers ' + ns]
                if 'search' in iface:
                    additional += ['dns-search ' + iface['search']]
                if len(additional) > 0:
                    meta_data += '    ' + '\n    '.join(additional)
                # if 'routes' in iface:
                #     routes = iface['routes']
                #     if isinstance(routes, list) and len(routes) > 0:
                #         # one route is "192.168.0.0/24 192.168.1.254"
                #         iface_meta_data += f'    dns-search ' + iface['search']
                #         for route in routes:
                #             route_sp = re.split('(/|\s)', route)
                #             misc.del_indent("""
                #                   - gateway
                #             """)
            elif ip == 'dhcp':
                meta_data += misc.del_indent(f"""
                    auto {ifname}
                    iface {ifname} inet dhcp

                """)
            else:
                meta_data += misc.del_indent(f"""
                    auto {ifname}
                    iface {ifname} inet static
                    address 169.254.0.1 
                    netmask 255.255.255.0

                """)
    return meta_data


def create_seed_user_data_str(username, password):
    """
    https://dev.classmethod.jp/articles/cloud-init-cfg/
    """
    user_data = f"""
    #cloud-config

    user: {username}
    password: {password}"""
    user_data += """
    chpasswd: {expire: False}
    ssh_pwauth: True

    #timezone: Asia/Tokyo
    #locale: ja_JP.UTF-8
    #locale: en_US.UTF-8
    """
    return misc.del_indent(user_data)


def create_seed_user_data_centos_str(username, password, vm):
    """
    https://dev.classmethod.jp/articles/cloud-init-cfg/
    """
    user_data = f"""
    #cloud-config
    
    user: {username}
    password: {password}"""
    user_data += """
    chpasswd: {expire: False}
    ssh_pwauth: True
    
    #timezone: Asia/Tokyo
    #locale: ja_JP.UTF-8
    #locale: en_US.UTF-8
    
    network:
      config: disabled
      
    """
    # for vnet in vm.vnets:
    #     ifname = vnet['ifname']
    #
    #     user_data += f"""
    #     - type: physical
    #       name: {ifname}
    #       subnets:
    #         - type: static
    #           address 169.254.0.1
    #           netmask 255.255.255.0
    #     """

    return misc.del_indent(user_data)


def create_seed_user_data_str_test(password):
    """
    https://dev.classmethod.jp/articles/cloud-init-cfg/
    """
    user_data = f"""
    #cloud-config
    
    users:
      - default
      - name: worker
        groups: users,wheel
        ssh_pwauth: True
    chpasswd:
      list: |
        cloud-user:{password}
        worker:{password}
      expire: False"""
    return misc.del_indent(user_data)


def create_host_seed_iso_sh(vm, xorriso_exists=False):
    hostname = vm.hostname
    username = vm.username
    password = vm.password
    platform = vm.platform
    ifaces = []
    if hasattr(vm, 'ifaces'):
        ifaces = vm.ifaces

    seed_iso_sh_dir = '/tmp/seediso'
    seed_iso_name = f'seed_{misc.sanitize_to_file_name(hostname)}.iso'

    created_seed_iso_path = f'{seed_iso_sh_dir}/{seed_iso_name}'
    user_data = create_seed_user_data_str(username, password)
    if re.search('^ubuntu', platform):
        # ubuntu can not be configured by seediso
        meta_data = create_seed_meta_data_str(hostname)
    elif platform == 'arch':
        # meta_data = create_seed_meta_data_str(hostname)
        meta_data = create_seed_meta_data_ifaces_str(hostname, ifaces)
    else:
        # meta_data = create_seed_meta_data_str(hostname)
        meta_data = create_seed_meta_data_ifaces_str(hostname, ifaces)
        # meta_data = create_seed_meta_data_link_local_str(vm)

    seed_iso_sh_name = 'create_seed_iso.sh'
    seed_iso_sh_path = f'{seed_iso_sh_dir}/{seed_iso_sh_name}'

    misc.prepare_clean_dir(seed_iso_sh_dir)
    misc.open_write(f'{seed_iso_sh_dir}/meta-data', meta_data)
    misc.open_write(f'{seed_iso_sh_dir}/user-data', user_data)

    if xorriso_exists:
        genisoimage_cmd = 'xorriso -as genisoimage'
    else:
        genisoimage_cmd = 'genisoimage'
    misc.open_write(seed_iso_sh_path, misc.del_indent(f"""
    #! /bin/sh
    CURRENT=$(cd $(dirname $0);pwd)
    {genisoimage_cmd} -output {created_seed_iso_path} -volid cidata -joliet -rock $CURRENT/user-data $CURRENT/meta-data

    """))
    return [
        seed_iso_sh_dir,
        seed_iso_sh_name,
        created_seed_iso_path
    ]


def create_host_seed_iso(vm, remote_kvm=None):
    def check_xorriso(session):
        return base_shell.check_command_exists(session, 'xorriso')

    if remote_kvm:
        xorriso_exists = session_wrap.ssh(remote_kvm)(check_xorriso)()
    else:
        xorriso_exists = session_wrap.bash()(check_xorriso)()
    [
        seed_iso_sh_dir,
        seed_iso_sh_name,
        created_seed_iso_path
    ] = create_host_seed_iso_sh(vm, xorriso_exists)

    @session_wrap.bash()
    def run_create_iso_sh_local(session):
        base_shell.work_on(session, seed_iso_sh_dir)
        base_shell.run(session, f'sh {seed_iso_sh_name}')

    @session_wrap.bash()
    def run_create_iso_sh_remote(session):
        from recipes.ops import ssh as ssh_ops
        ssh_ops.one_liner_to_remote_node(remote_kvm, f'sudo rm -rf {seed_iso_sh_dir}')(session)
        dst_path = f'{remote_kvm.username}@{remote_kvm.access_ip}:/tmp'
        ssh_ops.scp_from_local(seed_iso_sh_dir, dst_path, remote_kvm.password)
        session_wrap.ssh(remote_kvm)(lambda session: base_shell.run(session, f'sh {seed_iso_sh_dir}/{seed_iso_sh_name}'))()

    if remote_kvm:
        run_create_iso_sh_remote()
    else:
        run_create_iso_sh_local()

    return created_seed_iso_path

