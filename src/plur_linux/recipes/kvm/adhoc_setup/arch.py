from plur import base_shell
from plur_linux.recipes.kvm.adhoc_setup import generic
from plur_linux.recipes.dists.arch import ops


class Desktop(generic.SelectMenu):
    def __init__(self):
        selection = {
            "xfce4": True,
            "i3": False,
            "sway": False,
            "NetworkManager": False,
            "for vbox": False,
        }
        super().__init__(selection, [], 'Desktop')

    def setup(self, session):
        if self.enable:
            distro_list = []
            if self.selection['xfce4']:
                distro_list += ['xfce4']
            if self.selection['sway']:
                distro_list += ['sway']
            if self.selection['i3']:
                distro_list += ['i3']
            ops.install_desktop(distro_list, nm=self.selection['NetworkManager'])(session)
            if self.selection["for vbox"]:
                ops.install_for_vbox_additions(session)

class BaseApps(generic.SelectMenu):
    def __init__(self):
        selection = {
            "neovim": False,
            "vim": True,
            "tmux": True,
            "git": True,
            "dotfiles": False,
            "yay": False,
        }
        exclusive_list = []
        super().__init__(selection, exclusive_list, 'Base Apps')

    def setup(self, session):
        if self.enable:
            packages = []
            nvim = False
            if self.selection['neovim']:
                nvim = True
                if not base_shell.check_command_exists(session, 'zig'):
                    packages += ['zig']
                packages += ['neovim ripgrep fd']
            if self.selection['vim']:
                packages += ['vim']
            if self.selection['tmux']:
                packages += ['tmux']
            if self.selection['git']:
                packages += ['git']
            if self.selection['yay']:
                ops.install_yay(session)
            if self.selection['dotfiles']:
                if not self.selection['git']:
                    if not base_shell.check_command_exists(session, 'git'):
                        packages += ['git']
            if len(packages) > 0:
                ops.pacman_install(packages)(session)

            if self.selection['dotfiles']:
                from plur_linux.recipes.source_install import dotfiles
                dotfiles.setup(session, nvim)


class Languages(generic.SelectMenu):
    def __init__(self):
        from plur_linux.recipes.lang import go
        self.python_version = '3.13'
        self.uv_key = 'python(uv)'
        self.go_version = go.go_install_version
        self.go_key = f'go({self.go_version})'
        self.rust_key = 'rust(latest)'
        self.zig_key = 'zig'

        selection = {
            f"{self.uv_key}": False,
            f"{self.go_key}": False,
            f"{self.rust_key}": False,
            f"{self.zig_key}": False,
        }
        extra_menu = {}
        from plur_linux.recipes.lang import uv
        extra_menu[self.uv_key] = uv.input_uv_params
        super().__init__(selection, [], 'Languages', extra_menu=extra_menu)

    def setup(self, session):
        if self.enable:
            packages = []
            if generic.has_true(self.selection, self.uv_key):
                from plur_linux.recipes.lang import uv
                uv.install_python(**self.extra_params[self.uv_key])(session)
            if self.selection[self.go_key]:
                from plur_linux.recipes.lang import go
                go.install(self.go_version)(session)
            if self.selection[self.rust_key]:
                from plur_linux.recipes.lang import rust
                rust.install(session)
            if self.selection[self.zig_key]:
                packages += ['zig']
            if len(packages) > 0:
                ops.pacman_install(packages)(session)


def get_selection():
    platform = 'arch'
    vm = {
        'hostname': 'localhost',
        'platform': platform,
        'ssh_options': '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
        'size': 10,
    }
    postrun_list = [
        Desktop(),
        Languages(),
        BaseApps(),
    ]
    return [vm, postrun_list]

