import re
from plur import base_shell
from plur import session_wrap
from plur_linux.recipes import repos

def alias_appimage(install_path):
    def func(session):
        _ = [base_shell.run(session, a) for a in [
            "sed -i '/alias nvim=/d' ~/.bashrc"
            , "sed -i '/alias vim=/d' ~/.bashrc"
            , f"echo \"alias nvim='{install_path}'\" >> ~/.bashrc"
            , "echo \"#alias vim='nvim'\" >> ~/.bashrc"
        ]]
    return func

def add_additional(session):
    if base_shell.check_command_exists(session, 'npm'):
        base_shell.run(session, 'npm i -g neovim')
    if base_shell.check_command_exists(session, '$HOME/.virtualenv/v3/bin/pip'):
        base_shell.run(session, '$HOME/.virtualenv/v3/bin/pip install pynvim neovim')
    elif base_shell.check_command_exists(session, 'uv'):
        base_shell.run(session, 'v3')
        base_shell.run(session, 'uv pip install pynvim neovim')
        base_shell.run(session, 'deactivate')

def install_platform_dependancy(session):
    platform = session.nodes[-1].platform
    if platform in ['almalinux9', 'centos9stream', 'fedora']:
        base_shell.run(session, 'sudo dnf install -y epel-release')
        base_shell.run(session, 'sudo dnf install -y fuse fuse-libs xclip ripgrep fd-find unzip wget gcc')
    elif platform in ['almalinux8', 'centos8stream']:
        base_shell.run(session, 'sudo dnf install -y epel-release')
        base_shell.run(session, 'sudo dnf install -y fuse tar ripgrep fd-find unzip wget gcc')
        # base_shell.run(session, 'sudo dnf install -y fuse tar')
    elif re.search('^ubuntu', platform):
        from plur_linux.recipes.ubuntu import ops
        ops.sudo_apt_install_y(['libfuse2 unzip xz-utils fd-find ripgrep gcc'])(session)
    elif platform in ['centos7']:
        repos.install_with_repo(['fuse-sshfs'], 'centos7', 'epel')(session)

def install_appimage(version='latest', arch="linux-x86_64"):
    def func(session):
        install_platform_dependancy(session)
        if version == 'latest':
            ver = 'latest/download'
        else:
            ver = f'download/{version}'
        dir_path = "/usr/local/bin"
        appimage = f"nvim-{arch}.appimage"
        install_path = f'{dir_path}/{appimage}'
        base_shell.work_on(session, '$HOME/Downloads')
        _ = [base_shell.run(session, a) for a in [
            f"curl -LO https://github.com/neovim/neovim/releases/{ver}/{appimage}"
            , f"chmod u+x {appimage}"
            , f"sudo mv {appimage} {dir_path}/"
        ]]
        add_additional(session)
        alias_appimage(install_path)(session)
    return func

def input_nvim_params(self):
    from mini.menu import get_input
    self.nvim_version = get_input(expression=r'^(latest|v\d(\.\d{1,2}){1,2})$', message='nvim ver[v0.10.4, latest, etc.]', default_value=self.nvim_version) 
    return {
        'version': self.nvim_version,
        'arch': 'linux-x86_64',
    }
