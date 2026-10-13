from plur import base_shell as shell


def setup_tomcat7(session):
    shell.yum_install(session, {'packages': ['tomcat']})
    shell.service_on(session, 'tomcat')


def configure_opts(session):
    session.sudo_i()
    sysconfig_tomcat = '/etc/sysconfig/tomcat'
    shell.create_backup(session, sysconfig_tomcat)
    shell.run(session, '\cp -f %s %s' % (sysconfig_tomcat+'.org', sysconfig_tomcat))
    shell.run(session, 'echo \'JAVA_OPTS="-server -Xmx1500m -XX:MaxPermSize=256m -XX:+UseG1GC"\' >> %s' % sysconfig_tomcat)
    session.su_exit()


def setup_env(session):
    tomcat_profile = [
        "export CATALINA_HOME=/usr/share/tomcat",
        "export CATALINA_BASE=\$CATALINA_HOME",
        "export PATH=\$CATALINA_HOME/bin:\$PATH"
    ]
    session.sudo_i()
    file_path = '/etc/profile.d/tomcat.sh'
    shell.here_doc(session, file_path, tomcat_profile)
    session.su_exit()
    shell.run(session, 'source /etc/profile')


def setup(session):
    setup_tomcat7(session)
    configure_opts(session)
    setup_env(session)
