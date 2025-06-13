from plur import base_shell
from plur_linux.recipes.kvm.adhoc_setup import generic
from plur_linux.recipes.dists.arch import ops


class Desktop(generic.SelectMenu):
    def __init__(self):
        selection = {
            "xfce4": True,
            "i3": False,
            "NetworkManager": True,
            "lightdm": False,
        }
        exclusive_list = [
            "xfce4",
            "i3",
        ]
        super().__init__(selection, exclusive_list, 'Desktop')

    def setup(self, session):
        if self.enable:
            packages = [
                'noto-fonts-cjk'
                , 'fcitx5-im'
                , 'fcitx5-mozc'
                , 'firefox'
            ]
            # to start, startxfce4
            if self.selection['xfce4']:
                packages += ['xfce4']
            elif self.selection['i3']:
                # https://blog.livewing.net/install-arch-linux-2021
                # Win+Enter   > terminal
                # Win+D       > dmenu
                # Win+Shift+Q > close window
                # Win+Shift+E > logout
                packages += [
                    'i3',
                    'alacritty',
                    'dmenu',
                ]
            packages += [
                'xorg'
                , 'xorg-server'
            ]
            if self.selection['lightdm']:
                packages += [
                    'lightdm'
                    , 'lightdm-gtk-greeter'
                ]
            if self.selection['NetworkManager']:
                packages += [
                    'networkmanager'
                ]
            session.set_timeout(30*60)
            ops.pacman_install(packages)(session)
            session.set_timeout()
            base_shell.run(session, 'sudo localectl set-x11-keymap jp')
            if self.selection['NetworkManager']:
                base_shell.run(session, 'sudo systemctl enable --now NetworkManager')
            if self.selection['lightdm']:
                base_shell.run(session, 'sudo systemctl enable --now lightdm')


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
            if self.selection['neovim']:
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
                dotfiles.setup(session)


class Languages(generic.SelectMenu):
    def __init__(self):
        from plur_linux.recipes.lang import go
        self.go_version = go.go_install_version
        self.go_key = f'go({self.go_version})'
        self.rust_key = 'rust(latest)'
        self.zig_key = 'zig'

        selection = {
            f"{self.go_key}": False,
            f"{self.rust_key}": False,
            f"{self.zig_key}": False,
        }
        super().__init__(selection, [], 'Languages')

    def setup(self, session):
        if self.enable:
            packages = []
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

