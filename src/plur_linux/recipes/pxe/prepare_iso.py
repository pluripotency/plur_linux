from mini import misc
from plur import session_wrap
from plur import base_shell


def prepare_iso(iso_name, iso_url, www_iso_dir):
    local_dir = '/home/worker/Downloads'
    iso_path = f'{local_dir}/{iso_name}'

    @session_wrap.sudo
    def mount_iso(session):
        fstab_line = f'{iso_path} {www_iso_dir} iso9660 loop,ro,auto,nofail 0 0'
        base_shell.idempotent_append(session, '/etc/fstab', fstab_line, fstab_line)
        base_shell.run(session, f"mkdir -p {www_iso_dir} && mount {www_iso_dir}")

    def as_worker(session):
        base_shell.work_on(session, local_dir)
        if not base_shell.check_file_exists(session, iso_path):
            base_shell.run(session, f'curl -O {iso_url}')
        mount_iso(session)

    return as_worker


def prepare_a8_iso(session):
    iso_name = 'AlmaLinux-8-latest-x86_64-minimal.iso'
    iso_url = f'http://ftp.riken.jp/Linux/almalinux/8/isos/x86_64/{iso_name}'
    dist_dir = 'almalinux8'
    www_iso_dir = f'/var/pxe/{dist_dir}'
    prepare_iso(iso_name, iso_url, www_iso_dir)(session)
    return dist_dir, www_iso_dir


def prepare_a9_iso(session):
    iso_name = 'AlmaLinux-9-latest-x86_64-minimal.iso'
    iso_url = f'http://ftp.riken.jp/Linux/almalinux/9/isos/x86_64/{iso_name}'
    dist_dir = 'almalinux9'
    www_iso_dir = f'/var/pxe/{dist_dir}'
    prepare_iso(iso_name, iso_url, www_iso_dir)(session)
    return dist_dir, www_iso_dir


def prepare_jammy_iso(session):
    iso_url = 'https://ftp.riken.jp/Linux/ubuntu-releases/22.04/ubuntu-22.04.4-live-server-amd64.iso'
    sp = iso_url.split('/')
    iso_name = sp[-1]
    dist_dir = 'jammy'
    www_iso_dir = f'/var/www/iso/{dist_dir}'
    prepare_iso(iso_name, iso_url, www_iso_dir)(session)
    return dist_dir, www_iso_dir


def prepare_a8_iso_old(username, access_ip, password):
    @session_wrap.bash()
    def scp_iso(session):
        iso_name = 'AlmaLinux-8-latest-x86_64-minimal.iso'
        local_dir = '/home/worker/Downloads'
        local_iso_path = f'{local_dir}/{iso_name}'
        dst_dir = f'/home/{username}'
        base_shell.work_on(session, local_dir)
        if not base_shell.check_file_exists(session, local_iso_path):
            url = f'http://ftp.riken.jp/Linux/almalinux/8/isos/x86_64/{iso_name}'
            base_shell.run(session, f'curl -O {url}')

        from recipes.ops import ssh
        ssh.scp(session, iso_name, f'{username}@{access_ip}:{dst_dir}', password)
        iso_path = f'{dst_dir}/{iso_name}'
        return iso_path

    iso_path = scp_iso()
    dist_dir = 'almalinux8'

    @session_wrap.sudo
    def func(session):
        fstab_line = f'{iso_path} /var/pxe/{dist_dir} iso9660 loop,ro,auto,nofail 0 0'
        base_shell.idempotent_append(session, '/etc/fstab', fstab_line, fstab_line)
        [base_shell.run(session, a) for a in misc.del_indent_lines(f"""
        mkdir -p /var/pxe/{dist_dir}
        mount /var/pxe/{dist_dir}
        """)]
        return dist_dir

    return func


