import sys
from mini import misc, ansi_colors
from plur_linux.recipes.kvm.cloud_image import cloud_image_ops

ex_a10_dict = {
    'platform': 'almalinux10',
    'version': '10',
    'arch': 'x86_64_v2',
    'repo_url': 'https://repo.almalinux.org',
    'tmpl_image_filename': 'AlmaLinux-{version}-GenericCloud-latest.{arch}.qcow2',
    'tmpl_download_url': '{repo_url}/almalinux/{version}/x86_64/images/{image_filename}',
}

def extract_image_conf(image):
    """
    >>> extract_image_conf(ex_a10_dict)
    ('AlmaLinux-10-GenericCloud-latest.x86_64_v2.qcow2', 'https://repo.almalinux.org/almalinux/10/x86_64/images/AlmaLinux-10-GenericCloud-latest.x86_64_v2.qcow2')
    """
    key_dict = {}
    tmpl_dict = {}
    for key in image:
        if key.startswith('tmpl_'):
            tmpl_dict[key] = image[key]
        else:
            key_dict[key] = image[key]
    bound_dict = {}
    for key in ['image_filename', 'download_url']:
        if 'tmpl_' + key in tmpl_dict:
            value = tmpl_dict[f'tmpl_{key}'].format(**key_dict)
            key_dict[key] = value
            bound_dict[key] = value
    image_filename = bound_dict['image_filename']
    download_url = bound_dict['download_url']
    return image_filename, download_url

def read_platform_image(platform):
    cloudimage_list = misc.read_toml(misc.resolve_project_path('config/cloudimage.toml'))['images']
    found_image = misc.find(cloudimage_list, lambda x: x['platform'] == platform)
    if found_image:
        return found_image
    print(ansi_colors.red(f'bad platform: {platform}'))
    sys.exit(1)

def create_image(image_name, platform='almalinux10'):
    def func(session):
        image_filename, download_url = extract_image_conf(read_platform_image(platform))
        return cloud_image_ops.copy_image(session, image_filename, download_url, f'{image_name}.qcow2')
    return func


