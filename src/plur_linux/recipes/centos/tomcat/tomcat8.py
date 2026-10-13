from plur import base_shell as shell


def setup_tomcat8(java_home='/usr/java/', version='v8.0.53'):
    def func(session):
        download_dir = '$HOME/Downloads/'
        shell.work_on(session, download_dir)

        package_name = 'apache-tomcat-%s' % (version[1:])
        tgz = package_name + '.tar.gz'
        org_tomcat_path = '/opt/%s' % package_name
        tomcat_path = java_home + 'tomcat'
        if not shell.check_file_exists(session, tgz):
            # url = 'http://ftp.riken.jp/net/apache/tomcat/tomcat-8/%s/bin/%s' % (version, tgz)
            url = 'http://archive.apache.org/dist/tomcat/tomcat-8/%s/bin/%s' % (version, tgz)
            download = ' '.join([
                'wget',
                '-4',
                url
            ])
            shell.run(session, download)
        if not shell.check_dir_exists(session, tomcat_path):
            if not shell.check_dir_exists(session, java_home):
                shell.create_dir(session, java_home, sudo=True)
            actions = [
                'sudo useradd -s /sbin/nologin tomcat',
                'tar xvzf ' + tgz,
                'sudo mv ' + download_dir + package_name + ' /opt/',
                'sudo ln -s %s %s' % (org_tomcat_path, tomcat_path),
                'sudo chown -R tomcat:tomcat %s' % org_tomcat_path
            ]
            [shell.run(session, a) for a in actions]
        return tomcat_path
    return func


def setup_env(tomcat_path):
    tomcat_profile = """export CATALINA_HOME={tomcat_path}
export CATALINA_BASE={tomcat_path}
export PATH=\$PATH:\$CATALINA_HOME/bin""".format(tomcat_path=tomcat_path)

    def func(session):
        session.sudo_i()
        file_path = '/etc/profile.d/tomcat.sh'
        shell.here_doc(session, file_path, tomcat_profile.split('\n'))
        session.su_exit()
        shell.run(session, 'source /etc/profile')
    return func


def register_centos7_service(tomcat_path):
    tomcat_service = """[Unit]
Description=Apache Tomcat 8
After=network.target

[Service]
User=tomcat
Group=tomcat
Type=oneshot
PIDFile={tomcat_path}/tomcat.pid
RemainAfterExit=yes

ExecStart={tomcat_path}/bin/startup.sh
ExecStop={tomcat_path}/bin/shutdown.sh
ExecReStart={tomcat_path}/bin/shutdown.sh;{tomcat_path}/bin/startup.sh

[Install]
WantedBy=multi-user.target""".format(tomcat_path=tomcat_path, )

    def func(session):
        session.sudo_i()
        file_path = '/etc/systemd/system/tomcat.service'
        shell.here_doc(session, file_path, tomcat_service.split('\n'))
        actions = [
            'chmod 755 ' + file_path,
            'systemctl enable tomcat',
            'systemctl start tomcat',
        ]
        [shell.run(session, a) for a in actions]
        session.su_exit()
    return func


def setup(session):
    tomcat_path = setup_tomcat8()(session)
    setup_env(tomcat_path)(session)
    register_centos7_service(tomcat_path)(session)
