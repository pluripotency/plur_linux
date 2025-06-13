#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell

from plur_linux.recipes.ops import ops


def install_packages_for_sp(session):
    session.sudo_i()
    url = 'http://download.opensuse.org/repositories/security://shibboleth/CentOS_7/security:shibboleth.repo'
    base_shell.wget(session, url, '-O /etc/yum.repos.d/shibboleth.repos')
    base_shell.yum_install(session, {'packages': [
        'shibboleth.x86_64',
        'httpd',
        'openssl',
        'mod_ssl',
        'php'
    ]})

    ops.disable_selinux(session)
    session.su_exit()


def deploy_test_page(session, server_name):
    sp_secure = '/var/www/html/secure/index.html'
    base_shell.run(session, 'mkdir -p `dirname %s`' % sp_secure)
    base_shell.here_doc(session, sp_secure, [
        '<body>',
        '<h1>Your access seems to be granted successfully</h1>',
        '<p>You can see your session in',
        '<a href="https://%s/Shibboleth.sso/Session">this page</a>' % server_name,
        '</p>',
        '</body>'
    ])


def deploy_gakunin_php(session):
    from mini.misc import read_lines
    # dir path on this script
    cwd = os.path.dirname(__file__)
    php_page_lines = read_lines(f'{cwd}/index.php')

    sp_secure = '/var/www/html/secure/index.php'
    base_shell.run(session, 'mkdir -p `dirname %s`' % sp_secure)
    base_shell.here_doc(session, sp_secure, php_page_lines)
    # [base_shell.run(session, 'cat %s >> %s' % (a, sp_secure)) for a in php_page_lines]


def conf_httpd(server_name, httpd_certs=None):
    def func(session):
        session.sudo_i()

        from plur_linux.recipes.centos.shibboleth import httpd
        httpd.configure_for_sp(server_name, httpd_certs)(session)

        deploy_test_page(session, server_name)
        # deploy_gakunin_php(session)
        base_shell.service_on(session, 'httpd')
        session.su_exit()
    return func


def conf_shibd(server_name, idp_entity_id):
    def func(session):
        session.sudo_i()

        # metadata dir for getting idp metadata
        base_shell.run(session, 'mkdir -p /etc/shibboleth/metadata')
        idp_fqdn = idp_entity_id.split('/')[2]
        base_shell.here_doc(session, '/etc/shibboleth/metadata/get_idp_metadata.sh', [
            '#! /bin/sh',
            'scp root@%s:/opt/shibboleth-idp/metadata/idp-metadata.xml .' % idp_fqdn,
        ])

        # shibboleth2.xml
        shibd_conf = '/etc/shibboleth/shibboleth2.xml'
        base_shell.create_backup(session, shibd_conf)
        base_shell.sed_pipe(session, shibd_conf + '.org', shibd_conf, [
            [
                '    <ApplicationDefaults entityID="https://sp.example.org/shibboleth"',
                '    <ApplicationDefaults entityID="https://%s/shibboleth"' % server_name
            ],
            [
                '            <SSO entityID="https://idp.example.org/idp/shibboleth"',
                '            <SSO entityID="%s"' % idp_entity_id
            ],
            [
                '                 discoveryProtocol="SAMLDS" discoveryURL="https://ds.example.org/DS/WAYF">',
                '>'
            ],
            [
                '        <!-- Example of remotely supplied batch of signed metadata. -->',
                '        <!-- Example of remotely supplied batch of signed metadata. -->' +
                '<MetadataProvider type="XML" validate="true" ' +
                'path="metadata/idp-metadata.xml"></MetadataProvider>'
                # 'file="metadata/idp-metadata.xml"></MetadataProvider>'
                # 'uri="%s" reloadInterval="7200"></MetadataProvider>' % idp_entity_id
            ]
        ])
        base_shell.service_on(session, 'shibd')
        session.su_exit()
    return func


def setup(server_name, httpd_certs=None, idp_entity_id='https://c7idp.r/idp/shibboleth'):
    def func(session):
        from plur_linux.recipes.centos import chrony
        chrony.configure(session)
        [func(session) for func in [
            install_packages_for_sp,
            conf_httpd(server_name, httpd_certs),
            conf_shibd(server_name, idp_entity_id)
        ]]
    return func
