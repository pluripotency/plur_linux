import os
from plur.base_shell import run, heredoc_from_local, here_doc
from plur import session_wrap
from . import ldap_server


@session_wrap.sudo
def register_radius_schema(session):
    cwd = os.path.dirname(__file__)
    profile = 'radiusprofile.ldif'
    heredoc_from_local(f'{cwd}/{profile}', f'/tmp/{profile}')(session)
    run(session, f'ldapadd -Y EXTERNAL -H ldapi:/// -f /tmp/{profile}')


def add_radius_user(bind_dn, bind_dn_credential, olc_suffix, user, user_ou='People'):
    username = user[0]
    password = user[1]
    vlan_id = user[2]

    @ldap_server.temp_slappasswd(password=password)
    def func(session):
        ldif = f'{username}.ldif'
        contents = [
            f'dn: uid={username},ou={user_ou},{olc_suffix}',
            'objectClass: inetOrgPerson',
            'objectClass: radiusprofile',
        ]
        contents += [
            f'cn: {username}',
            'sn: RADIUS User',
            'userPassword: $TEMP_PW',

            'radiusTunnelType: 13',
            'radiusTunnelMediumType: 6',
            f'radiusTunnelPrivategroupId: {vlan_id}',
        ]
        here_doc(session, ldif, contents, eof='EOF')
        run(session, f'ldapadd -x -D "{bind_dn}" -w {bind_dn_credential} -f {ldif}')
    return func


olc_suffix_example = 'dc=example,dc=org'
radius_ldap_params_example = {
    'organization': 'ABC Organization',
    'bindDN': 'cn=manager,' + olc_suffix_example,
    'bindDNCredential': 'managerpass',
    'olcRootPW': 'managerpass',
    'olcSuffix': olc_suffix_example,
    'enable_ssl': True,
}


def setup(ldap_params=None, user_list=None):
    if ldap_params is None:
        ldap_params = radius_ldap_params_example
    if user_list is None:
        user_list = []
        for i in range(1, 3):
            nstr = ('00' + str(i))[-3:]
            user_list += [
                # username, password, vlan id
                [f'user{nstr}', f'pass{nstr}', i + 100],
            ]

    def func(session):
        ldap_server.setup(ldap_params, user_list)(session)
        register_radius_schema(session)

    return func
