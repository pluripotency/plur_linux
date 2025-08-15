from mini import misc
from plur import base_shell

def install_zig_appimage(session, version):
    work_dir = '/tmp/zig'
    base_shell.work_on(session, work_dir)
    zig_app_name = f'zig-x86_64-linux-{version}'
    file_name = f'{zig_app_name}.tar.xz'
    url = f'https://ziglang.org/download/{version}/{file_name}'
    if not base_shell.check_dir_exists(session, f'{work_dir}/{zig_app_name}'):
        base_shell.run(session, f'curl -LO {url}')
        base_shell.run(session, f'unxz {file_name}')
        base_shell.run(session, f'tar xvf {zig_app_name}.tar')
    base_shell.run(session, f'cd {zig_app_name}')
    base_shell.run(session, 'sudo cp -f zig /usr/local/bin')

def install_zig(version):
    def func(session):
        install_zig_appimage(session, version)
    return func

def input_zig_params(self):
    from mini.menu import get_input
    self.zig_version = get_input(expression=r'^0(\.\d{1,2}){2}$', message='zig ver[0.14.1, etc.]' + f'({self.zig_version}): ', default_value=self.zig_version)
    return {
        'version': self.zig_version,
    }
