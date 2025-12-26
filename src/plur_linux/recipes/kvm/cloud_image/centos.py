from plur import session_wrap
from plur_linux.recipes.kvm.cloud_image import cloud_image_ops


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


def create_fedora(major='42', miner='1.1'):
    def receive_func(image_name):
        def func(session):
            org_image_file_name = f'Fedora-Cloud-Base-Generic-{major}-{miner}.x86_64.qcow2'
            url = f'http://ftp.riken.jp/Linux/fedora/releases/{major}/Cloud/x86_64/images/{org_image_file_name}'
            return cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')

        return func
    return receive_func
