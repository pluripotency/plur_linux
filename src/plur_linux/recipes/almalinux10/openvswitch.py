from plur import base_shell


def install(session):
    extras_url = 'https://ftp.iij.ad.jp/pub/linux/almalinux/10/extras/x86_64/os/Packages'
    pkgs = ' '.join([f'{extras_url}/{pkg}' for pkg in [
        'centos-release-nfv-common-1-5.el10.noarch.rpm',
        'centos-release-nfv-openvswitch-1-5.el10.noarch.rpm',
    ]])
    _ = [base_shell.run(session, a) for a in [
        f'sudo dnf install -y {pkgs}',
        'sudo dnf install -y openvswitch3.5 NetworkManager-ovs',
        'sudo systemctl enable --now openvswitch',
    ]]
