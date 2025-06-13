import re
from mini.ansi_colors import light_blue, light_green
from mini.menu import get_input, get_y_n, choose_num
from plur import base_shell


def has_true(obj, key):
    if key in obj and obj[key] == True:
        return True
    return False


def display_current(instance, title):
    if instance.enable:
        title_str = light_green(title + '(Yes,')
    else:
        title_str = title + '(No, '
    title_str += ' '.join(
        [(light_green(key) if instance.selection[key] is True else light_blue(key)) for key in list(instance.selection)])
    title_str += ')'
    return title_str


def check_key(_dict, key):
    if key in _dict and _dict[key]:
        return True
    return False


class SelectMenu:
    def __init__(self, selection, exclusive_list=None, menu_title=None, select_title=None, extra_menu=None):
        self.enable = False
        self.selection = selection
        self.exclusive_list = exclusive_list
        self.menu_title = menu_title
        if select_title:
            self.select_title = select_title
        else:
            self.select_title = 'Setup ' + self.menu_title
        self.extra_menu = extra_menu
        self.extra_params = {}

    def menu_entry(self):
        return [
            display_current(self, self.menu_title)
            , lambda : self.select_menu(self.select_title, self.exclusive_list)
        ]

    def run_extra_menu(self, key):
        if isinstance(self.extra_menu, dict) and key in self.extra_menu and callable(self.extra_menu[key]):
            self.extra_params[key] = self.extra_menu[key](self)

    def select_menu(self, title=None, exclusive_list=False, vertical=True):
        self.enable = get_y_n(title, self.enable)
        if self.enable:
            while True:
                key_list = list(self.selection)
                menu_list = [light_green(a) if self.selection[a] is True else light_blue(a) for a in key_list] + ['back']
                selected_index = choose_num(menu_list, vertical=vertical)
                if selected_index == len(menu_list)-1:
                    break

                selected = key_list[selected_index]
                value = self.selection[selected]
                self.selection[selected] = not value
                if not value:
                    self.run_extra_menu(selected)
                for exclusive_entry in exclusive_list if isinstance(exclusive_list, list) else []:
                    if selected in exclusive_entry if isinstance(exclusive_entry, list) else []:
                        for item in exclusive_entry:
                            if selected != item:
                                self.selection[item] = False


class BaseApps(SelectMenu):
    def __init__(self, platform):
        self.platform = platform
        self.nvim_key = 'nvim'
        self.nvim_version = 'latest'
        if re.search('^ubuntu', platform):
            selection = {
                "vim": True,
                "tmux": True,
                "git": True,
                "dotfiles": True,
            }
            exclusive_list = []
        elif platform == 'centos7':
            selection = {
                "vim": True,
                "vim(src)": False,
                "tmux": True,
                "git": False,
                "git(ius)": True,
                "dotfiles": False,
            }
            exclusive_list = [
                ["vim(src)", "vim"],
                ["git(ius)", "git"],
            ]
        else:
            selection = {
                "vim": True,
                "tmux": True,
                "git": True,
                "dotfiles": False,
            }
            exclusive_list = []

        selection[self.nvim_key] = False
        extra_menu = {}
        from plur_linux.recipes import nvim
        extra_menu[self.nvim_key] = nvim.input_nvim_params
        super().__init__(selection, exclusive_list, 'Base Apps', extra_menu=extra_menu)

    def setup(self, session):
        if self.enable:
            platform = self.platform
            packages = []
            dot_nvim = False
            if self.selection[self.nvim_key]:
                dot_nvim = True
                from plur_linux.recipes import nvim
                nvim.install_appimage(**self.extra_params[self.nvim_key])(session)
            if self.selection['vim']:
                packages += ['vim']
            elif 'vim(src)' in self.selection and self.selection['vim(src)']:
                from plur_linux.recipes.source_install import vim
                vim.install(session)
            if self.selection['tmux']:
                packages += ['tmux']
            if self.selection['git']:
                packages += ['git']
            else:
                from plur_linux.recipes import git
                if 'git(ius)' in self.selection and self.selection['git(ius)']:
                    git.dict_git['centos7']['ius'](session)
                elif 'gi(src)' in self.selection and self.selection['git(src)']:
                    git.dict_git['centos7']['source'](session)

            if len(packages) > 0:
                if re.search('^ubuntu', platform):
                    from plur_linux.recipes.ubuntu import ops as ubuntu_ops
                    ubuntu_ops.sudo_apt_install_y(packages)
                else:
                    base_shell.yum_y_install(packages)(session)

            if self.selection['dotfiles']:
                from plur_linux.recipes.source_install import dotfiles
                dotfiles.setup(session, dot_nvim)


class Initial(SelectMenu):
    def __init__(self, platform):
        if platform in ['centos7']:
            selection = {
                "mkswap(1GB)": False,
                "legacy_devname": False,
                "ttyS0": False,
                "disable_ipv6": True,
                "tz Asia/Tokyo": True,
                "keymap jp106": True,
                "disable_selinux": True,
                "permissive_selinux": False,
                "enforce_selinux": False,
            }
        elif re.search('^almalinux', platform):
            selection = {
                "mkswap(1GB)": False,
                "legacy_devname": False,
                "ttyS0": False,
                "disable_ipv6": True,
                "tz Asia/Tokyo": True,
                "keymap jp106": True,
                "remove cockpit": False,
                "disable_selinux": False,
                "permissive_selinux": False,
                "enforce_selinux": False,
            }
        elif re.search('^ubuntu', platform):
            selection = {
                "mkswap(1GB)": True,
                "legacy_devname": True,
                "ttyS0": False,
                "disable_ipv6": True,
                "tz Asia/Tokyo": True,
                "keymap jp106": True,
            }
        else:
            selection = {
                "mkswap(1GB)": False,
                "legacy_devname": False,
                "ttyS0": False,
                "disable_ipv6": True,
                "tz Asia/Tokyo": True,
                "keymap jp106": True,
            }
        exclusive_list = [
            ["disable_selinux", "permissive_selinux", "enforce_selinux",],
        ]
        super().__init__(selection, exclusive_list, 'Initial')
        self.platform = platform
        self.enable = True

    def setup(self, session):
        if self.enable:
            from plur_linux.recipes.ops import ops
            if has_true(self.selection, 'disable_selinux'):
                ops.disable_selinux(session)
            elif has_true(self.selection, 'permissive_selinux'):
                ops.permissive_selinux(session)
            elif has_true(self.selection, 'enforce_selinux'):
                ops.enforce_selinux(session)

            if has_true(self.selection, 'mkswap(1GB)'):
                ops.mkswap(1)(session)
            if has_true(self.selection, 'disable_ipv6'):
                ops.disable_ipv6(session)
            if has_true(self.selection, 'tz Asia/Tokyo'):
                ops.set_timezone()(session)
            if has_true(self.selection, 'keymap jp106'):
                ops.set_keymap('jp106')(session)
            if has_true(self.selection, 'remove cockpit'):
                ops.remove_cockpit(session)

            if has_true(self.selection, 'legacy_devname') or has_true(self.selection, 'ttyS0'):
                from plur_linux.recipes.ops import fs
                from plur_linux.recipes.ops import grub
                grub_path = '/etc/default/grub'
                backed_up_grub_path = fs.backup(grub_path)(session)
                if re.search('^ubuntu', self.platform):
                    grub.configure_ubuntu(
                        backed_up_grub_path,
                        console=self.selection['ttyS0'],
                        devname=self.selection['legacy_devname']
                    )(session)
                else:
                    grub.configure(
                        backed_up_grub_path,
                        console=self.selection['ttyS0'],
                        devname=self.selection['legacy_devname']
                    )(session)


class Languages(SelectMenu):
    def __init__(self, platform):
        from plur_linux.recipes.lang import go
        self.python_version = '3.13'
        self.python_venv = 'v3'
        self.uv_key = f'python(uv)'
        self.pyenv_key = f'python(pyenv)'
        self.python3_key = f'python3(pkg)'

        self.go_version = go.go_install_version
        self.go_key = f'go({self.go_version})'

        self.rust_key = 'rust(latest)'

        self.node_version = 'v22'
        self.nodesource_version = f'{self.node_version}.x'
        self.nodebrew_key = f'node(nodebrew)'
        self.nodesource_key = f'node(nodesource)'

        selection = {
            f"{self.uv_key}": False,
            f"{self.pyenv_key}": False,
            f"{self.python3_key}": False,
            f"{self.nodebrew_key}": False,
            f"{self.nodesource_key}": False,
            f"{self.go_key}": False,
            f"{self.rust_key}": False,
        }
        exclusive_list = [
            [self.nodebrew_key, self.nodesource_key],
            [self.uv_key, self.pyenv_key, self.python3_key],
        ]
        extra_menu = {}
        from plur_linux.recipes.lang import uv
        extra_menu[self.uv_key] = uv.input_uv_params
        from plur_linux.recipes.lang import pyenv
        extra_menu[self.pyenv_key] = pyenv.input_pyenv_params
        from plur_linux.recipes.lang.nodejs import nodebrew
        extra_menu[self.nodebrew_key] = nodebrew.input_node_params

        super().__init__(selection, exclusive_list, 'Languages', extra_menu=extra_menu)

    def setup(self, session):
        if self.enable:
            if has_true(self.selection, self.go_key):
                from plur_linux.recipes.lang import go
                go.install(self.go_version)(session)
            if has_true(self.selection, self.rust_key):
                from plur_linux.recipes.lang import rust
                rust.install(session)
            if has_true(self.selection, self.uv_key):
                from plur_linux.recipes.lang import uv
                uv.install_python(**self.extra_params[self.uv_key])(session)
            elif has_true(self.selection, self.pyenv_key):
                from plur_linux.recipes.lang import pyenv
                pyenv.install(**self.extra_params[self.pyenv_key])(session)
            elif has_true(self.selection, self.python3_key):
                from plur_linux.recipes.lang import python3 as python_setup
                python_setup.install_python3(self.python_venv)(session)
            if has_true(self.selection, self.nodebrew_key):
                from plur_linux.recipes.lang.nodejs import nodebrew
                nodebrew.install(**self.extra_params[self.nodebrew_key])(session)
            elif has_true(self.selection, self.nodesource_key):
                from plur_linux.recipes.lang.nodejs import nodesource
                nodesource.setup(self.nodesource_version)(session)
