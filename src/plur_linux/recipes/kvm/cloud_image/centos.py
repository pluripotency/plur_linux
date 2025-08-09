from plur import session_wrap
from plur_linux.recipes.kvm.cloud_image import cloud_image_ops


def create7(image_name,
            password,
            size=None):
    @session_wrap.su('worker')
    def func(session):
        major = '7'
        minor = '2111'
        compress_format = 'qcow2c'
        org_image_file_name = f'CentOS-{major}-x86_64-GenericCloud-{minor}.{compress_format}'
        url = f'https://cloud.centos.org/centos/{major}/images/{org_image_file_name}'
        created_image_path = cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')
        cloud_image_ops.disable_cloud_init_centos7(created_image_path)(session)
        cloud_image_ops.resize_to(created_image_path, size)(session)
        cloud_image_ops.change_cloud_image_password(created_image_path, password)(session)
        return created_image_path

    return func


def create_centos7_cloudinit(image_name):
    def func(session):
        major = '7'
        minor = '2111'
        compress_format = 'qcow2c'
        org_image_file_name = f'CentOS-{major}-x86_64-GenericCloud-{minor}.{compress_format}'
        url = f'https://cloud.centos.org/centos/{major}/images/{org_image_file_name}'
        return cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')
    return func


def create_centos_stream(version='8'):
    def receive_func(image_name):
        def func(session):
            org_image_file_name = f'CentOS-Stream-GenericCloud-{version}-latest.x86_64.qcow2'
            url = f'https://cloud.centos.org/centos/{version}-stream/x86_64/images/{org_image_file_name}'
            return cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')
        return func
    return receive_func


def create_almalinux10(image_name):
    def func(session):
        version = '10'
        org_image_file_name = "AlmaLinux-10-GenericCloud-latest.x86_64_v2.qcow2"
        url = f'http://ftp.riken.jp/Linux/almalinux/{version}/cloud/x86_64/images/{org_image_file_name}'
        return cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')
    return func


def create_almalinux(version='8'):
    def receive_func(image_name):
        def func(session):
            org_image_file_name = f'AlmaLinux-{version}-GenericCloud-latest.x86_64.qcow2'
            url = f'http://ftp.riken.jp/Linux/almalinux/{version}/cloud/x86_64/images/{org_image_file_name}'
            return cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')
        return func
    return receive_func


def create_fedora(major='41', miner='1.4'):
    def receive_func(image_name):
        def func(session):
            org_image_file_name = f'Fedora-Cloud-Base-Generic-{major}-{miner}.x86_64.qcow2'
            url = f'http://ftp.riken.jp/Linux/fedora/releases/{major}/Cloud/x86_64/images/{org_image_file_name}'
            return cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')

        return func
    return receive_func
