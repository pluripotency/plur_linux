from plur import base_shell
from plur import session_wrap
from recipes.ops import ops
from recipes import firewalld
from mini import misc


@session_wrap.sudo
def install_server(session):
    ops.disable_selinux(session)
    # base_shell.run(session, 'setsebool -P nis_enabled on')
    #base_shell.yum_y_install(['centos-release-gluster'])(session)
    #base_shell.yum_y_install(['glusterfs-server'])(session)
    firewalld.configure(services=['glusterfs'], add=True)(session)
    base_shell.service_on(session, 'glusterd')
    base_shell.here_doc(session, '/etc/sysctl.d/fs_inotify.conf', [
        'fs.inotify.max_user_watches=1000000',
    ])
    base_shell.run(session, 'sysctl --system')


def install_client(session):
    # glusterfs-fuse is in @base
    base_shell.yum_install(session, {'packages': ['glusterfs-fuse']})


def mount_and_append_hosts(host_list, mount_point='/mnt/MC', volume_name='gvol0'):
    fstab_entry = f'{host_list[0][1]}:{volume_name} {mount_point} glusterfs'
    fstab_entry += ' defaults,_netdev,backup-volfile-servers=%s 0 0' % (':'.join([entry[1] for entry in host_list[1:]]))

    @session_wrap.sudo
    def func(session):
        ops.idempotent_append_hosts(host_list)(session)
        file_path = '/etc/fstab'
        base_shell.append_line(fstab_entry, file_path)(session)
        base_shell.run(session, 'mount -a')
    return func


def mount_gluster_by_env(env='pt'):
    if env == 'pt':
        config = {
            'mount_point': '/mnt/MC',
            'volume_name': 'gvol0',
            'permit_user': 'worker',
            'host_list': [
                ['10.30.0.41', 'c7gl041', 'c7gl041.r'],
                ['10.30.0.42', 'c7gl042', 'c7gl042.r'],
                ['10.30.0.43', 'c7gl043', 'c7gl043.r'],
            ]
        }
    elif env == 'sc':
        config = {
            'mount_point': '/mnt/MC',
            'volume_name': 'gvol0',
            'permit_user': 'worker',
            'host_list': [
                ['192.168.10.41', 'gl41041', 'gl41041.r'],
                ['192.168.10.42', 'gl41042', 'gl41042.r'],
            ]
        }
    else:
        config = {
            'mount_point': '/mnt/MC',
            'volume_name': 'gvol0',
            'permit_user': 'worker',
            'host_list': [
                ['192.168.10.41', 'gl41041', 'gl41041.r'],
                ['192.168.10.42', 'gl41042', 'gl41042.r'],
                ['192.168.10.43', 'gl41043', 'gl41043.r'],
            ]
        }
    [
        mount_point,
        volume_name,
        permit_user,
        host_list
    ] = misc.extract_config_dict_by_attr_list(config, [
        'mount_point',
        'volume_name',
        'permit_user',
        'host_list',
    ])

    @session_wrap.sudo
    def func(session):
        if not base_shell.check_dir_exists(session, mount_point):
            install_client(session)
            base_shell.run(session, f'sudo mkdir -p {mount_point}')
            base_shell.run(session, f'sudo chown -R {permit_user}. {mount_point}')
            mount_and_append_hosts(host_list, mount_point=mount_point, volume_name=volume_name)(session)
    return func


