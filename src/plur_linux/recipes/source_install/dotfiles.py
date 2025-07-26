import re
from plur import base_shell

def setup(session, nvim=False):
    packages = []
    if not base_shell.check_command_exists(session, 'git'):
        packages += ['git']
    if not base_shell.check_command_exists(session, 'tmux'):
        packages += ['tmux']
    if not base_shell.check_command_exists(session, 'vim'):
        packages += ['vim']
    if len(packages) > 0:
        platform = session.nodes[-1].platform
        if re.search('^ubuntu', platform):
            from plur_linux.recipes.ubuntu import ops as ubuntu_ops
            ubuntu_ops.sudo_apt_install_y(packages)(session)
        elif re.search('^arch', platform):
            from plur_linux.recipes.dists.arch import ops as arch_ops
            arch_ops.pacman_install(packages)(session)
        else:
            base_shell.run(session, 'sudo yum install -y ' + ' '.join(packages))
    if not base_shell.check_dir_exists(session, '~/.tmux'):
        _ = [base_shell.run(session, a) for a in [
            'cd && mkdir .tmux && cd .tmux',
            'git clone https://github.com/tmux-plugins/tmux-logging.git',
        ]]
    if base_shell.check_dir_exists(session, '~/dotfiles'):
        _ = [base_shell.run(session, a) for a in [
            "cd ~/dotfiles",
            "git pull origin master",
        ]]
    else:
        repo = 'https://github.com/pluripotency/dotfiles.git/'
        _ = [base_shell.run(session, a) for a in [
            'cd',
            f"git clone {repo}",
        ]]
    _ = [base_shell.run(session, a) for a in [
        "cd ~/dotfiles",
        './dotsetup.sh',
    ]]
    if nvim:
        base_shell.run(session, './nvsetup.sh')
