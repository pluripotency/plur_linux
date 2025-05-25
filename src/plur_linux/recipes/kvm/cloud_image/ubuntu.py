from plur import session_wrap
from recipes.kvm.cloud_image import cloud_image_ops


def create(
        image_name,
        password='password',
        size=8,
        dev_code='jammy'):
    @session_wrap.su('worker')
    def func(session):
        org_image_file_name = f'{dev_code}-server-cloudimg-amd64.img'
        url = f'http://cloud-images.ubuntu.com/{dev_code}/current/{org_image_file_name}'
        created_path = cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')
        cloud_image_ops.resize_to(created_path, size)(session)
        return created_path
    return func


def create_ubuntu_cloudinit(dev_code='jammy'):
    def receive_func(image_name):
        def func(session):
            org_image_file_name = f'{dev_code}-server-cloudimg-amd64.img'
            url = f'http://cloud-images.ubuntu.com/{dev_code}/current/{org_image_file_name}'
            return cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')
        return func
    return receive_func


def create_debian_cloudinit(version='10'):
    def receive_func(image_name):
        def func(session):
            org_image_file_name = f'debian-{version}-openstack-amd64.qcow2'
            url = f'https://cdimage.debian.org/cdimage/openstack/current-{version}/{org_image_file_name}'
            return cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')
        return func
    return receive_func


