#! /usr/bin/env python
import sys
import os
sys.path.append(os.pardir)
from plur import base_shell as shell
from plur import output_methods
from plur import session_wrap


def setup_env(shib_home):
    def func(session):
        profile = [
            "export SHIB_HOME=%s" % shib_home
        ]
        if shib_home is not '/opt/shibboleth-idp':
            profile += [
                'export JAVA_OPTS="-Didp.home=%s"' % shib_home
            ]
            web_xml = shib_home + '/webapp/WEB-INF/web.xml'
            shell.create_backup(session, web_xml)
            shell.sed_pipe(session, web_xml + '.org', web_xml, [
                '^    <display-name>Shibboleth Identity Provider</display-name>$',
                '    <display-name>Shibboleth Identity Provider</display-name>\\n' +
                '    <context-param>\\n' +
                '        <param-name>idp.home</param-name>\\n' +
                '        <param-value>%s</param-value>\\n' % shib_home +
                '    </context-param>'
            ])

        session.sudo_i()
        file_path = '/etc/profile.d/shib.sh'
        shell.here_doc(session, file_path, profile)
        session.su_exit()
        shell.run(session, 'source /etc/profile')
    return func


def conf_page(server_params):
    def func(session):
        shib_home = server_params['shib_home']
        target_file = shib_home + '/messages/error-messages.properties'
        lines = []
        if 'footer' in server_params:
            footer = server_params['footer']
            lines += [
                [
                    '^idp\.footer = Insert your footer text here.$',
                    'idp.footer = %s' % footer
                ],
                [
                    '^root\.footer = Insert your footer text here.$',
                    'root.footer = %s' % footer
                ]
            ]
        if 'logo' in server_params:
            logo = server_params['logo']
            if shell.check_file_exists(session, logo):
                logo_file_name = logo.split('/')[-1]
                shell.run(session, '\cp -f %s %s/edit-webapp/images/' % (logo, shib_home))
                lines += [
                    [
                        '^idp\.logo = /images/dummylogo.png$',
                        'idp.logo = /images/%s' % logo_file_name
                    ]
                ]
        shell.create_backup(session, target_file)
        shell.sed_pipe(session, target_file + '.org', target_file, lines)
        session.do(shell.create_sequence(shib_home + '/bin/build.sh', [
            ['Installation Directory: \[.+\]', output_methods.send_line, shib_home, ''],
            [session.waitprompt, output_methods.success, '', '']
        ]))
        shell.run(session, 'chown tomcat. %s/war/idp.war' % shib_home)

    return func


def change_login_shell(username, login_shell):
    return lambda session: shell.run(session, 'sudo chsh -s %s %s' % (login_shell, username))


def install_idp(server_params):
    shib_home = server_params['shib_home']
    server_name = server_params['server_name']
    search = '.'.join(server_name.split('.')[1:])
    back_channel_password = server_params['back_channel_password']
    cookie_encryption_password = server_params['cookie_encryption_password']

    version = '3.2.1'
    shibboleth_idp = 'shibboleth-identity-provider-%s' % version

    download_dir = '~/Downloads'
    url = 'http://shibboleth.net/downloads/identity-provider/%s/%s.tar.gz' % (version, shibboleth_idp)

    def extract_idp(session):
        shell.work_on(session, download_dir)
        if not shell.check_file_exists(session, download_dir + '/%s.tar.gz' % shibboleth_idp):
            shell.run(session, 'wget -4 %s' % url)
        shell.run(session, 'tar xvzf %s.tar.gz' % shibboleth_idp)

    def prepare_shib_home(session):
        shell.run(session, 'sudo rm -rf $SHIB_HOME')
        shell.run(session, 'sudo mkdir $SHIB_HOME')

        session_user = session.nodes[-1].username
        shell.run(session, 'sudo chown %s. $SHIB_HOME' % session_user)

    def build(session):
        def send_password(password):
            return lambda session: session.child.sendline(password)

        work_dir = '%s/%s' % (download_dir, shibboleth_idp)
        shell.work_on(session, work_dir)
        session.do(shell.create_sequence('./bin/install.sh', [
            ['Source \(Distribution\) Directory: \[.+\]', output_methods.send_line, '', ''],
            ['Installation Directory: \[.+\]', output_methods.send_line, shib_home, ''],
            ['Hostname: \[.*\]', output_methods.send_line, server_name, ''],
            ['SAML EntityID: \[.+\]', output_methods.send_line, '', ''],
            ['Attribute Scope: \[.+\]', output_methods.send_line, search, ''],
            ['Backchannel PKCS12 Password: ', output_methods.wait([['Re-enter password: ', output_methods.new_send_pass(back_channel_password)]], shell.new_send_pass(back_channel_password)), '', ''],
            ['Cookie Encryption Key Password: ', output_methods.wait([['Re-enter password: ', output_methods.new_send_pass(cookie_encryption_password)]], shell.new_send_pass(cookie_encryption_password)), '', ''],
            ['BUILD SUCCESSFUL', output_methods.wait([[session.nodes[-1].waitprompt, output_methods.success_f(True)]]), '', '']
        ]))
        shell.run(session, 'sudo chown -R tomcat:tomcat $SHIB_HOME')
        # actions = [
        #     'sudo chown -R tomcat:tomcat /opt/shibboleth-idp/logs',
        #     'sudo chgrp -R tomcat /opt/shibboleth-idp/conf',
        #     'sudo chmod -R g+r /opt/shibboleth-idp/conf',
        #     'sudo chgrp tomcat /opt/shibboleth-idp/metadata',
        #     'sudo chmod g+w /opt/shibboleth-idp/metadata',
        #     'sudo chmod +t /opt/shibboleth-idp/metadata'
        # ]
        # [shell.run(session, a) for a in actions]

    def func(session):
        setup_env(shib_home)(session)
        extract_idp(session)
        prepare_shib_home(session)
        build(session)

    return func


def restart_idp(session):
    shell.run(session, 'sudo service tomcat stop')
    shell.run(session, 'sudo service httpd restart')
    shell.run(session, 'sudo service tomcat start')


def test(sp_server_name, user):
    # check localhost/idp/status from browser or wget
    def func(session):
        session.sudo_i()
        shell.run(session, 'wget -O - http://localhost/idp/status')
        shell.run(session, 'wget -O - http://localhost/idp/status')
        shell.run(session, '$SHIB_HOME/bin/aacli.sh -r https://%s/shibboleth -n %s' % (sp_server_name, user))
        session.su_exit()
    return func


ldap_params_example = {
    'ldapURL': 'ldap://localhost:389',
    'useStartTLS': 'false',
    'subtreeSearch': 'true',

    'organization': 'ABC Organization',
    'bindDN': 'cn=Manager,dc=c7idp,dc=r',
    'bindDNCredential': 'managerpass',
    'olcRootPW': 'managerpass',
}

server_params_example = {
    'shib_home': '/opt/shibboleth-idp',
    'server_name': 'idp.c7idp.r',
    'back_channel_password': 'password',
    'cookie_encryption_password': 'password',
    'salt': 'suicamelontomatonasusalt',
    'syslog_ip': '192.168.182.8'
}


def setup(server_params, ldap_params, sp_server_name=None, httpd_certs=None):
    shib_home = server_params['shib_home']

    @session_wrap.sudo
    def install_packages_for_idp(session):
        shell.yum_install(session, {'packages': [
            'firewalld',
            'httpd',
            'openssl',
            'mod_ssl',
            'wget'
        ]})
        from plur_linux.recipes import firewalld
        firewalld.configure(services=['ssh', 'https'])(session)
        from plur_linux.recipes.centos.jdk import openjdk8
        openjdk8.setup(session)

        # from plur_linux.recipes.centos.tomcat import tomcat7
        # tomcat7.setup(session)
        # oracle_jdk8.setup({'jce': True})(session)
        # from plur_linux.recipes.centos.tomcat import tomcat8
        # tomcat8.setup(session)
        # from plur_linux.recipes.centos.tomcat import tomcat85
        # tomcat85.setup(session)

        from plur_linux.recipes.centos.tomcat import tomcat9
        tomcat9.setup(session)

    @session_wrap.sudo
    def configure_packages(session):
        from plur_linux.recipes.centos.shibboleth import httpd as conf_httpd
        from plur_linux.recipes.centos.shibboleth import tomcat as conf_tomcat
        from plur_linux.recipes.centos.shibboleth import syslog as conf_syslog

        [func(session) for func in [
            conf_httpd.configure(server_params['server_name'], httpd_certs),
            conf_tomcat.configure(shib_home),
            conf_tomcat.configure_log4j,
            conf_syslog.configure(server_params)
        ]]

    @session_wrap.sudo
    def configure_idp(session):
        from plur_linux.recipes.centos.shibboleth import jakarta
        from plur_linux.recipes.centos.shibboleth import saml_nameid_properties
        from plur_linux.recipes.centos.shibboleth import logback
        from plur_linux.recipes.centos.shibboleth import idp_properties
        from plur_linux.recipes.centos.shibboleth import ldap_properties

        [func(session) for func in [
            jakarta.link(shib_home),
            conf_page(server_params),

            idp_properties.configure(server_params),
            saml_nameid_properties.configure(server_params),
            ldap_properties.configure(ldap_params),
            logback.configure(server_params),
        ]]

    @session_wrap.sudo
    def configure_for_sp(session):
        from plur_linux.recipes.centos.shibboleth import metadata_provider
        from plur_linux.recipes.centos.shibboleth import attribute_resolver
        from plur_linux.recipes.centos.shibboleth import attribute_filter
        [func(session) for func in [
            metadata_provider.configure(sp_server_name, shib_home),
            attribute_resolver.configure(sp_server_name),
            attribute_filter.configure(sp_server_name)
        ]]

    def run(session):
        from plur_linux.recipes.centos import chrony
        chrony.configure(session)
        install_packages_for_idp(session)
        configure_packages(session)
        install_idp(server_params)(session)
        configure_idp(session)

        if sp_server_name is not None:
            configure_for_sp(session)

        restart_idp(session)
    return run
