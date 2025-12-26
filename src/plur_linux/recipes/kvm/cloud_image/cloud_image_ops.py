from plur import base_shell
from plur_linux.recipes.kvm import virt_builder
from plur_linux.recipes.kvm import qemu_img
cloud_image_download_dir = '$HOME/Downloads/vm'
tmp_image_dir = '/tmp'


def curl_if_not_exist(session, local_file_path, url):
    if not base_shell.check_file_exists(session, local_file_path):
        base_shell.run(session, f'curl -O {url}')


def copy_image(session, org_image_file_name, url, dst_image_file_name):
    base_shell.work_on(session, cloud_image_download_dir)
    curl_if_not_exist(session, org_image_file_name, url)
    base_shell.run(session, rf'\cp -f {org_image_file_name} {tmp_image_dir}/{dst_image_file_name}')
    return f'{tmp_image_dir}/{dst_image_file_name}'


def unxz(session, xz_file_path):
    if not base_shell.check_command_exists(session, 'xz'):
        base_shell.yum_install(session, {'packages': ['xz-utils']})
    if base_shell.check_file_exists(session, xz_file_path):
        base_shell.run(session, f'unxz -k {xz_file_path}')


def copy_image_raw_xz(session, org_image_file_name, url, image_name, ext='raw.xz'):
    copied_image_path = copy_image(session, org_image_file_name, url, f'{image_name}.{ext}')
    if ext in ['raw.xz', 'xz']:
        base_shell.work_on(session, tmp_image_dir)
        unxz(session, copied_image_path)
        if ext in ['raw.xz']:
            base_shell.run(session, f'qemu-img convert {tmp_image_dir}/{image_name}.raw -O qcow2 {tmp_image_dir}/{image_name}.qcow2')
    return f'{tmp_image_dir}/{image_name}.qcow2'


def resize_to(image_path, size=None):
    if size is None:
        size = 8
    return qemu_img.resize_to(image_path, size)
