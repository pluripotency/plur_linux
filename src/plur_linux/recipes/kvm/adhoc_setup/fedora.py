from recipes.kvm.adhoc_setup import generic


class MinDesk(generic.SelectMenu):
    def __init__(self):
        super().__init__({
            'xrdp': False,
        },
            exclusive_list=None,
            menu_title='Desktop')

    def setup(self, session):
        if self.enable:
            if self.selection['xrdp']:
                from recipes.desktop import fedora
                fedora.install_xwindow(session)
                if self.selection['xrdp']:
                    fedora.install_xrdp(session)


def get_selection():
    platform = 'fedora'
    vm = {
        'hostname': 'localhost',
        'platform': platform,
        'ssh_options': '-o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null',
        'size': 8,
    }
    postrun_list = [
        generic.Initial(platform),
        MinDesk(),
        generic.Languages(platform),
        generic.BaseApps(platform),
    ]
    return [vm, postrun_list]


