from plur_linux.recipes.kvm.cloud_image import cloud_image_ops


def create_centos_stream(version='10'):
    def receive_func(image_name):
        def func(session):
            org_image_file_name = f'CentOS-Stream-GenericCloud-{version}-latest.x86_64.qcow2'
            url = f'https://cloud.centos.org/centos/{version}-stream/x86_64/images/{org_image_file_name}'
            return cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')
        return func
    return receive_func


def create_almalinux(version='10'):
    def receive_func(image_name):
        def func(session):
            # repo_org = 'http://ftp.riken.jp/Linux'
            repo_org = 'https://repo.almalinux.org'
            arch = 'x86_64_v2'
            if version != '10':
                arch = 'x86_64'
            org_image_file_name = f'AlmaLinux-{version}-GenericCloud-latest.{arch}.qcow2'
            url = f'{repo_org}/almalinux/{version}/cloud/{arch}/images/{org_image_file_name}'
            return cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')
        return func
    return receive_func


def create_fedora(major='43', miner='1.6'):
    def receive_func(image_name):
        def func(session):
            repo_org = 'http://ftp.riken.jp/Linux'
            org_image_file_name = f'Fedora-Cloud-Base-Generic-{major}-{miner}.x86_64.qcow2'
            url = f'{repo_org}/fedora/releases/{major}/Cloud/x86_64/images/{org_image_file_name}'
            return cloud_image_ops.copy_image(session, org_image_file_name, url, f'{image_name}.qcow2')

        return func
    return receive_func
