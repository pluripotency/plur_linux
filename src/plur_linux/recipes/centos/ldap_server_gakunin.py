#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)

from plur import base_shell as shell
from plur import session_wrap
from recipes.centos.openldap import ldap_server



def init_gakunin_db(password='password'):
    temp_var = 'DATA_ROOT_PW'

    @session_wrap.sudo
    @ldap_server.temp_slappasswd(temp_var, password, hash_type='{CRYPT}', options='-c \'$6$%%s$\'')
    def register_ldif(session):
        base_dn_base = 'dn.base="gidNumber=0+uidNumber=0,cn=peercred,cn=external,cn=auth"'
        register = [
            'cn=olmgr',
            'o=test_o',
            'dc=ac',
            'c=JP'
        ]

        manager_dn_base = 'dn.base="%s"' % (','.join(register))
        olc_suffix = ','.join(register[1:])
        olc_root_dn = ','.join(register)

        ldif = 'init_gakunin_db.ldif'
        shell.here_doc(session, ldif, [
            'dn: olcDatabase={1}monitor,cn=config',
            'changetype: modify',
            'replace: olcAccess',
            'olcAccess: {0}to * ',
            '  by %s read' % base_dn_base,
            '  by %s read' % manager_dn_base,
            '  by * none',
            '',
            'dn: olcDatabase={2}hdb,cn=config',
            'changetype: modify',
            'replace: olcSuffix',
            'olcSuffix: %s' % olc_suffix,
            '',
            'dn: olcDatabase={2}hdb,cn=config',
            'changetype: modify',
            'replace: olcRootDN',
            'olcRootDN: %s' % olc_root_dn,
            '',
            'dn: olcDatabase={2}hdb,cn=config',
            'changetype: modify',
            'replace: olcRootPW',
            'olcRootPW: $%s' % temp_var,
        ])
        shell.run(session, 'sudo ldapmodify -Y EXTERNAL -H ldapi:/// -f %s' % ldif)

    return register_ldif



