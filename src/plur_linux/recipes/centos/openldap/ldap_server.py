import re
import functools
from plur import base_shell
from plur import session_wrap
"""
about custom ldif
https://www.cisco.com/c/ja_jp/support/docs/ip/lightweight-directory-access-protocol-ldap/116096-configure-anyconnect-openldap-00.html
"""


def conf_syslog(session):
    from recipes.syslog import rsyslog
    template_name = 'slapd_local4'
    logging_path = '/var/log/local4/slapd.log'
    rule_list = [
        f'$template {template_name}, "{logging_path}"',
        f'if $syslogfacility-text=="local4" then -?{template_name}',
        f'& ~ # for {template_name}',
    ]
    rsyslog.setup(rule_list)(session)
    from recipes.syslog import logrotate
    rotate_name = template_name
    logrotate.add_standard_logrotate(rotate_name, [
        logging_path
    ])(session)


def install_packages(session):
    if session.platform == 'almalinux9':
        base_shell.run(session, 'sudo dnf install -y epel-release')
    base_shell.run(session, 'sudo yum install -y ' +  ' '.join([
        'openldap-servers',
        'openldap-clients',
    ]))


@session_wrap.sudo
def init_db_config(session):
    if session.platform == 'almalinux9':
        pass
    else:
        [base_shell.run(session, a) for a in [
            '\cp -f /usr/share/openldap-servers/DB_CONFIG.example /var/lib/ldap/DB_CONFIG',
            'chown ldap:ldap /var/lib/ldap/DB_CONFIG'
        ]]
    base_shell.service_on(session, 'slapd')


def inject_password(password='password', temp_var='TEMP_PASS', hash_type='{SSHA}'):
    return lambda session: base_shell.run(session, f'{temp_var}=`slappasswd -h {hash_type} -s {password}`')


def unload_password(temp_var='TEMP_pass'):
    return lambda session: base_shell.run(session, f'{temp_var}=')


def temp_slappasswd(password='password', temp_var='TEMP_PW', hash_type='{SSHA}', options=''):
    def slap_passwd_session(func):
        @functools.wraps(func)
        def on_slappasswd(session):
            base_shell.run(session, '%s=`slappasswd -h %s -s %s %s`' % (temp_var, hash_type, password, options))
            func(session)
            base_shell.run(session, '%s=' % temp_var)
        return on_slappasswd
    return slap_passwd_session


def change_root_password(olc_root_pass):
    @session_wrap.sudo
    @temp_slappasswd(olc_root_pass, 'ROOTPW')
    def func(session):
        operate_olcRootPW = 'add: olcRootPW'
        conf_file_path = '/etc/openldap/slapd.d/cn\=config/olcDatabase\=\{0\}config.ldif'
        if base_shell.check_line_exists_in_file(session, conf_file_path, 'olcRootPW'):
            operate_olcRootPW = 'replace: olcRootPW'
        olc_root_pw_ldif_name = 'olc_root_pw.ldif'
        olc_root_pw_ldif_content = """
dn: olcDatabase={0}config,cn=config
changetype: modify
%s
olcRootPW: ${ROOTPW}
    """ % operate_olcRootPW
        base_shell.here_doc(session, olc_root_pw_ldif_name, olc_root_pw_ldif_content.split('\n')[1:], eof='EOF')
        base_shell.run(session, 'ldapadd -Y EXTERNAL -H ldapi:/// -f %s' % olc_root_pw_ldif_name)

        """
        output should be:

        SASL/EXTERNAL authentication started
        SASL username: gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth
        SASL SSF: 0
        modifying entry "olcDatabase={0}config,cn=config"
        """
        """
        error case:
        
        SASL/EXTERNAL authentication started
        SASL username: gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth
        SASL SSF: 0
        modifying entry "olcDatabase={0}config,cn=config"
        ldap_modify: Inappropriate matching (18)
                additional info: modify/add: olcRootPW: no equality matching rule
        """
    return func


@session_wrap.sudo
def register_basic_schema(session):
    [base_shell.run(session, a) for a in [
        'ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/cosine.ldif',
        'ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/nis.ldif',
        'ldapadd -Y EXTERNAL -H ldapi:/// -f /etc/openldap/schema/inetorgperson.ldif'
    ]]


def init_db(bind_dn, olc_suffix, bind_dn_credential):
    base_dn_base = 'gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth'
    @session_wrap.sudo
    @temp_slappasswd(bind_dn_credential, 'MGRPW')
    def register_ldif(session):
        db = 'hdb'
        if session.platform == 'almalinux9':
            db = 'mdb'
        ldif = 'init_domain.ldif'
        base_shell.here_doc(session, ldif, [
            'dn: olcDatabase={1}monitor,cn=config',
            'changetype: modify',
            'replace: olcAccess',
            'olcAccess: {0}to * ',
            '  by dn.base="%s" read' % base_dn_base,
            '  by dn.base="%s" read' % bind_dn,
            '  by * none',
            '',
            'dn: olcDatabase={2}%s,cn=config' % db,
            'changetype: modify',
            'replace: olcSuffix',
            'olcSuffix: %s' % olc_suffix,
            '',
            'dn: olcDatabase={2}%s,cn=config' % db,
            'changetype: modify',
            'replace: olcRootDN',
            'olcRootDN: %s' % bind_dn,
            '',
            'dn: olcDatabase={2}%s,cn=config' % db,
            'changetype: modify',
            'replace: olcRootPW',
            'olcRootPW: ${MGRPW}'
            '',
            '',
            # olcAccess
            'dn: olcDatabase={2}%s,cn=config' % db,
            'changetype: modify',
            'add: olcAccess',
            # 'olcAccess: {0}to *',
            # '  by %s write' % base_dn_base,
            # '  by %s write' % manager_dn_base,
            # '  by * none'

            'olcAccess: {0}to attrs=userPassword,shadowLastChange ',
            '  by dn="%s" write by anonymous auth by self write by * none' % bind_dn,
            'olcAccess: {1}to dn.base="" by * read',
            'olcAccess: {2}to * by dn="%s" write by * read' % bind_dn
        ], eof='EOF')
        base_shell.run(session, 'ldapmodify -Y EXTERNAL -H ldapi:/// -f %s' % ldif)

    return register_ldif


def check_db(root_password):
    def func(session):
        db = 'hdb'
        if session.platform == 'almalinux9':
            db = 'mdb'
        command = "ldapsearch -x -b 'olcDatabase={2}%s,cn=config' -D cn=config -w %s" % (db, root_password)
        return base_shell.run(session, command)
    return func


def init_base_domain(organization, bind_dn, olc_suffix, password):
    dc_list = []
    for item in olc_suffix.split(','):
        if re.search('^dc=', item):
            dc_list.append(item.split('=')[1])

    @session_wrap.sudo
    def register_ldif(session):
        ldif = 'base_domain.ldif'
        contents = [
            f'dn: {olc_suffix}',
            'objectClass: top',
            'objectClass: dcObject',
            'objectclass: organization',
            f'o: {organization}',
            f'dc: {dc_list[0]}',
            '',
            'dn: %s' % bind_dn,
            'objectClass: organizationalRole',
            'cn: Manager',
            'description: Directory Manager',
        ]
        for ou in ['People', 'Group']:
            contents += [
                '',
                f'dn: ou={ou},{olc_suffix}',
                'objectClass: organizationalUnit',
                f'ou: {ou}'
            ]

        base_shell.here_doc(session, ldif, contents, eof='EOF')
        base_shell.run(session, 'ldapadd -x -D "%s" -w %s -f %s' % (bind_dn, password, ldif))
    return register_ldif


def add_simple_user(bind_dn, bind_dn_credential, olc_suffix, user, user_ou='People'):
    username = user[0]
    password = user[1]

    @temp_slappasswd(password=password)
    def func(session):
        ldif = f'{username}.ldif'
        contents = [
            f'dn: uid={username},ou={user_ou},{olc_suffix}',
            'objectClass: inetOrgPerson',
        ]
        contents += [
            f'cn: {username}',
            'sn: Linux',
            'userPassword: $TEMP_PW',
        ]
        base_shell.here_doc(session, ldif, contents, eof='EOF')
        base_shell.run(session, f'ldapadd -x -D "{bind_dn}" -w {bind_dn_credential} -f {ldif}')
    return func


def add_simple_users(bind_dn, bind_dn_credential, olc_suffix, user_list):
    func_list = [add_simple_user(bind_dn, bind_dn_credential, olc_suffix, user) for user in user_list]
    return lambda session: [func(session) for func in func_list]


def add_user(bind_dn, bind_dn_credential, olc_suffix, user, user_ou='People', group_ou='Group'):
    username = user[0]
    password = user[1]
    uid_number = user[2]
    gid_number = user[3]

    @temp_slappasswd(password=password)
    def func(session):
        dn_in_people = f'uid={username},ou={user_ou},{olc_suffix}'
        dn_in_group = f'cn={username},ou={group_ou},{olc_suffix}'
        ldif = '%s.ldif' % username

        user_contents = [
            f'dn: {dn_in_people}',
            'objectClass: inetOrgPerson',
            'objectClass: posixAccount',
            'objectClass: shadowAccount',
            f'cn: {username}',
            'sn: Linux',
            f'mail: {username}@test.local',
            'userPassword: $TEMP_PW',
            'loginShell: /bin/bash',
            f'uidNumber: {uid_number}',
            f'gidNumber: {gid_number}',
            f'homeDirectory: /home/{username}',
        ]
        group_contents = [
            '',
            f'dn: {dn_in_group}',
            'objectClass: posixGroup',
            f'cn: {username}',
            f'gidNumber: {gid_number}',
            f'memberUid: {username}'
        ]
        contents = user_contents + group_contents
        base_shell.here_doc(session, ldif, contents, eof='EOF')
        base_shell.run(session, f'ldapadd -x -D "{bind_dn}" -w {bind_dn_credential} -f {ldif}')
    return func


def add_users(bind_dn, bind_dn_credential, olc_suffix, user_list):
    func_list = [add_user(bind_dn, bind_dn_credential, olc_suffix, user) for user in user_list]
    return lambda session: [func(session) for func in func_list]


def check_users(olc_suffix, user_list, enable_ssl, user_ou='People'):
    """
    example:
    ldapsearch -x -D "uid=user001,ou=People,dc=example,dc=org" -b "dc=example,dc=org" "uid=user001" -w pass001
    """
    actions = []
    for user in user_list:
        username = user[0]
        password = user[1]
        bind_dn_by_user = f'-D "uid={username},ou={user_ou},{olc_suffix}"'
        searchbase = f'-b "{olc_suffix}"'
        action = f'ldapsearch -x {bind_dn_by_user} {searchbase} "uid={username}" -w {password}'
        if enable_ssl:
            action += ' -H ldaps:///'
        actions += [action]

    def func(session):
        [base_shell.run(session, a) for a in actions]
    return func


def delete_user():
    """
    ldapdelete -x -D "cn=manager,dc=example,dc=org" -w managerpass "uid=user001,ou=People,dc=example,dc=org"
    """
    pass


olc_suffix_example = 'dc=example,dc=org'
ldap_params_example = {
    'organization': 'ABC Organization',
    'bindDN': 'cn=manager,' + olc_suffix_example,
    'bindDNCredential': 'managerpass',
    'olcRootPW': 'managerpass',
    'olcSuffix': olc_suffix_example,
    'enable_ssl': True,
}
user_list_example = []
for i in range(1, 3):
    nstr = ('00' + str(i))[-3:]
    user_list_example += [
        [f'user{nstr}', f'pass{nstr}', f'2{nstr}', f'2{nstr}', i + 100],
    ]
simple_user_list_example = []
for i in range(3, 5):
    nstr = ('00' + str(i))[-3:]
    simple_user_list_example += [
        [f'user{nstr}', f'pass{nstr}'],
    ]


def setup(ldap_params=None, cert_params=None, user_list=None, enable_syslog=True):
    if ldap_params is None:
        ldap_params = ldap_params_example

    for key in [
        'organization',
        'bindDN',
        'bindDNCredential',
        'olcRootPW',
    ]:
        if key not in ldap_params:
            print(f"{key} is needed")
            exit(1)

    simple_user_list = None
    if user_list is None:
        user_list = user_list_example
        simple_user_list = simple_user_list_example

    def func(session):
        organization = ldap_params['organization']
        bind_dn = ldap_params['bindDN']
        bind_dn_credential = ldap_params['bindDNCredential']
        olc_root_pass = ldap_params['olcRootPW']
        olc_suffix = ldap_params['olcSuffix'] if 'olcSuffix' in ldap_params else ','.join(bind_dn.split(',')[1:])
        enable_ssl = ldap_params['enable_ssl'] if 'enable_ssl' in ldap_params else False

        if enable_syslog:
            action_list = [
                conf_syslog,
            ]
        else:
            action_list = []
        action_list += [
            install_packages,
            init_db_config,
            change_root_password(olc_root_pass),
            register_basic_schema,
            init_db(bind_dn, olc_suffix, bind_dn_credential),
            check_db(olc_root_pass),
            init_base_domain(organization, bind_dn, olc_suffix, bind_dn_credential),
        ]

        if enable_ssl:
            from . import ldaps
            action_list += [ldaps.setup(cert_params)]

        if isinstance(user_list, list) and len(user_list) > 0:
            action_list += [
                add_users(bind_dn, bind_dn_credential, olc_suffix, user_list),
                check_users(olc_suffix, user_list, enable_ssl)
            ]
        if isinstance(simple_user_list, list) and len(simple_user_list) > 0:
            action_list += [
                add_simple_users(bind_dn, bind_dn_credential, olc_suffix, simple_user_list),
                check_users(olc_suffix, simple_user_list, enable_ssl)
            ]

        _ = [f(session) for f in action_list]
    return func
