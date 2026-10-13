from plur import session_wrap
from plur import base_shell

def prepare_dist_iso(dist_dir):
    if dist_dir == "almalinux10":
        iso_name = 'AlmaLinux-10-latest-x86_64_v2-minimal.iso'
        iso_url = f'http://ftp.riken.jp/Linux/almalinux/10/isos/x86_64_v2/{iso_name}'
    elif dist_dir == "almalinux9":
        iso_name = 'AlmaLinux-9-latest-x86_64-minimal.iso'
        iso_url = f'http://ftp.riken.jp/Linux/almalinux/9/isos/x86_64/{iso_name}'
    elif dist_dir == "almalinux8":
        iso_name = 'AlmaLinux-8-latest-x86_64-minimal.iso'
        iso_url = f'http://ftp.riken.jp/Linux/almalinux/8/isos/x86_64/{iso_name}'
    else:
        iso_name = 'AlmaLinux-10-latest-x86_64_v2-minimal.iso'
        iso_url = f'http://ftp.riken.jp/Linux/almalinux/10/isos/x86_64_v2/{iso_name}'

    www_iso_dir = f'/var/www/html/{dist_dir}'
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
        return www_iso_dir

    return as_worker
