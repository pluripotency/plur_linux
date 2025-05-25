#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell as shell

from recipes.ops import ops


def install_packages_for_sp(session):
    session.sudo_i()
    url = 'http://download.opensuse.org/repositories/security://shibboleth/CentOS_7/security:shibboleth.repo'
    shell.wget(session, url, '-O /etc/yum.repos.d/shibboleth.repos')
    shell.yum_install(session, {'packages': [
        'shibboleth.x86_64',
        'httpd',
        'openssl',
        'mod_ssl'
    ]})
    session.su_exit()


def deploy_test_page(session, server_name):
    sp_secure = '/var/www/html/secure/index.html'
    shell.run(session, 'mkdir -p `dirname %s`' % sp_secure)
    shell.here_doc(session, sp_secure, [
        '<body>',
        '<h1>Your access seems to be granted successfully</h1>',
        '<p>You can see your session in',
        '<a href="https://%s/Shibboleth.sso/Session">this page</a>' % server_name,
        '</p>',
        '</body>'
    ])


def conf_httpd(server_name):
    def func(session):
        session.sudo_i()
        httpd_conf = '/etc/httpd/conf/httpd.conf'
        shell.create_backup(session, httpd_conf)
        shell.sed_pipe(session, httpd_conf + '.org', httpd_conf, [
            ['^#ServerName www.example.com:80$', 'ServerName %s:80' % server_name]
        ])
        ssl_conf = '/etc/httpd/conf.d/ssl.conf'
        shell.create_backup(session, ssl_conf)
        shell.sed_pipe(session, ssl_conf + '.org', ssl_conf, [
            ['^#ServerName www.example.com:443$', 'ServerName %s:443' % server_name],
            ['^SSLProtocol all -SSLv2$', 'SSLProtocol all -SSLv2 -SSLv3']
        ])
        deploy_test_page(session, server_name)
        ops.service_on('httpd')(session)
        session.su_exit()
    return func


def conf_shibd(server_name, idp_name):
    def func(session):
        session.sudo_i()
        shibd_conf = '/etc/shibboleth/shibboleth2.xml'
        shell.create_backup(session, shibd_conf)
        shell.sed_pipe(session, shibd_conf + '.org', shibd_conf, [
            [
                '    <ApplicationDefaults entityID="https://sp.example.org/shibboleth"',
                '    <ApplicationDefaults entityID="https://%s/shibboleth"' % server_name
            ],
            [
                '            <SSO entityID="https://idp.example.org/idp/shibboleth"',
                '            <SSO entityID="%s"' % idp_name
            ],
            [
                '                 discoveryProtocol="SAMLDS" discoveryURL="https://ds.example.org/DS/WAYF">',
                '>'
            ],
            [
                '        <!-- Example of remotely supplied batch of signed metadata. -->',
                '        <!-- Example of remotely supplied batch of signed metadata. -->' +
                '<MetadataProvider type="XML" validate="true" ' +
                'uri="%s" reloadInterval="7200"></MetadataProvider>' % idp_name
            ]
        ])
        shell.run(session, 'systemctl restart httpd')
        shell.run(session, 'systemctl restart shibd')
        shell.run(session, 'systemctl enable shibd')
        session.su_exit()
    return func


def setup(server_name='c7sp.r', idp='https://c7idp.r/idp/shibboleth'):
    def func(session):
        [func(session) for func in [
            ops.disable_selinux,
            install_packages_for_sp,
            conf_httpd(server_name),
            conf_shibd(server_name, idp)
        ]]
    return func
