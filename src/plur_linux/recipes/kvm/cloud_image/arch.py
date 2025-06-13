import os
from plur import base_shell
from plur_linux.recipes.kvm.cloud_image import cloud_image_ops


def create_arch(image_name):
    def func(session):
        org_image_file_name = 'Arch-Linux-x86_64-cloudimg.qcow2'
        url = f'https://geo.mirror.pkgbuild.com/images/latest/{org_image_file_name}'
        return cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')
    return func

