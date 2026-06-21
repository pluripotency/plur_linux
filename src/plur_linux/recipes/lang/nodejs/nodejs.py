import sys
from mini.ansi_colors import red
from mini.menu import choose_num
from . import nodebrew
from . import nvm

def input_node_params(self):
    node_installer_list = [
        ['nodebrew', nodebrew.input_node_params],
        ['nvm', nvm.input_node_params]
    ]
    menu_list = [item[0] for item in node_installer_list]
    num = choose_num(menu_list, message='Choose node installer: ')
    self.node_installer = menu_list[num]
    selected = node_installer_list[num][1]
    return selected(self)

def install(self):
    if not hasattr(self, 'node_installer') or not hasattr(self, 'node_version'):
        print(red('err in nodejs: self must have node_installer and node_version'))
        sys.exit(1)
    node_installer = self.node_installer
    node_version = self.node_version

    def func(session):
        if node_installer == 'nodebrew':
            nodebrew.install(node_version)(session)
        elif node_installer == 'nvm':
            nvm.install(node_version)(session)
    return func

