from plur import base_shell


def init(dir_path, packages):
    def func(session):
        base_shell.work_on(session, dir_path)
        install_scripts = []
        if isinstance(packages, dict):
            if 'global' in packages:
                install_scripts += ['npm i -g ' + ' '.join(packages['global'])]
            if 'devel' in packages:
                install_scripts += ['npm i -D ' + ' '.join(packages['devel'])]
            if 'local' in packages:
                install_scripts += ['npm i -S ' + ' '.join(packages['local'])]
        [base_shell.run(session, a) for a in [
            'npm init -y'
        ] + install_scripts]

    return func



