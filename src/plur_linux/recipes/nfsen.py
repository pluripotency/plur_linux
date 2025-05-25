from plur import base_shell
from plur import session_wrap


# https://wiki.polaire.nl/doku.php?id=nfsen_centos7

@session_wrap.sudo
def install_required(session):
    from recipes.ops import ops
    ops.disable_selinux(session)
    base_shell.run(session, 'yum groupinstall -y development tools')
    base_shell.run(session, 'yum install -y ' + ' '.join([
        'vim',

        'rrdtool',
        'rrdtool-devel',

        'apache',
        'php',
        'perl-MailTools',
        'rrd-tool-perl',
        'perl-Socket6',
        'perl-Sys-Syslog.x86_64',

        'policycoreutils-python',
    ]))

    [base_shell.run(session, a) for a in [
        'echo "date.timezone = Asia/Tokyo" > /etc/php.d/timezone.ini',
        'useradd netflow',
        'usermod -G apache netflow',
    ]]


def download_nfsen(session):
    base_shell.run(session, 'cd $HOME')
    if not base_shell.check_command_exists(session, 'wget'):
        base_shell.yum_y_install(['wget'])(session)
    nfsen = "https://sourceforge.net/projects/nfsen/files/stable/nfsen-1.3.7/nfsen-1.3.7.tar.gz/download"
    nfdump = "https://sourceforge.net/projects/nfdump/files/stable/nfdump-1.6.13/nfdump-1.6.13.tar.gz/download"
    base_shell.run(session, f"wget --no-check-certificate {nfsen}")
    base_shell.run(session, "tar xvzf download")
    base_shell.run(session, f"wget --no-check-certificate {nfdump}")
    base_shell.run(session, "tar xvzf download.1")


def install_nfdump(session):
    base_shell.run(session, 'cd $HOME/nfdump*')
    commands = [
        "./configure --prefix=/opt/nfdump --enable-nfprofile --enable-sflow",
        'autoreconf',
        'make',
        'sudo make install',
    ]
    [base_shell.run(session, a)for a in commands]


def install_nfsen(session):
    base_shell.run(session, 'cd $HOME/nfsen*')
    base_shell.run(session, 'cd etc')
    commands = [
        'cp nfsen-dist.conf nfsen.conf'
    ]
    [base_shell.run(session, a)for a in commands]

@session_wrap.sudo
def conf_firewall(session):
    commands = """
    firewall-cmd --permanent --zone=trusted --add-service=http
    firewall-cmd --permanent --zone=trusted --add-source=1.2.3.1
    firewall-cmd --permanent --zone=trusted --add-port=9995/udp
    firewall-cmd --reload
    firewall-cmd --zone=trusted --list-all
    """


@session_wrap.sudo
def conf_httpd(session):
    base_shell.here_doc(session, "/etc/httpd/conf.d/nfsen.conf", """
<Directory "/opt/nfsen/www">
   AllowOverride None
   Require all granted
</Directory>

Alias /nfsen "/opt/nfsen/www"
""".split('\n')[1:])
    base_shell.service_on(session, 'httpd')


@session_wrap.sudo
def register_service(session):
    commands = """
[Unit]
Description=NfSen Service
After=network.target

[Service]
Type=forking
PIDFile=/opt/nfsen/var/run/nfsend.pid
ExecStart=/opt/nfsen/bin/nfsen start
ExecStop=/opt/nfsen/bin/nfsen stop
Restart=on-abort

[Install]
WantedBy=multi-user.target
""".split('\n')[1:]
    base_shell.here_doc(session, '/etc/systemd/system/nfsen.service', commands)
    base_shell.service_on(session, 'nfsen')


def setup(session):
    install_required(session)
    download_nfsen(session)
    install_nfdump(session)
    install_nfsen(session)
    conf_httpd(session)
    register_service(session)

