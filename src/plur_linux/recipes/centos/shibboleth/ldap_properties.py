from plur import base_shell as shell


def configure(p):
    def func(session):
        ldap_properties = '$SHIB_HOME/conf/ldap.properties'
        backup_file = ldap_properties + '.org'
        shell.create_backup(session, ldap_properties)
        shell.sed_pipe(session, backup_file, ldap_properties, [
            [
                'idp.authn.LDAP.ldapURL                          = ldap://localhost:10389',
                'idp.authn.LDAP.ldapURL                          = %s' % p['ldapURL']
            ],
            [
                '#idp.authn.LDAP.useStartTLS                     = true',
                'idp.authn.LDAP.useStartTLS                      = %s' % p['useStartTLS']
            ],
            [
                'idp.authn.LDAP.baseDN                           = ou=people,dc=example,dc=org',
                'idp.authn.LDAP.baseDN                           = %s' % p['baseDN']
            ],
            [
                '#idp.authn.LDAP.subtreeSearch                   = false',
                'idp.authn.LDAP.subtreeSearch                    = %s' % p['subtreeSearch']
            ],
            ## bindDN for search uid is not required
            [
                'idp.authn.LDAP.bindDN                           = uid=myservice,ou=system',
                '#idp.authn.LDAP.bindDN                           = uid=myservice,ou=system'
            ],
            [
                'idp.authn.LDAP.bindDNCredential                 = myServicePassword',
                '#idp.authn.LDAP.bindDNCredential                 = myServicePassword'
            ]
            # [
            #     'idp.authn.LDAP.bindDN                           = uid=myservice,ou=system',
            #     'idp.authn.LDAP.bindDN                           = %s' % p['bindDN']
            # ],
            # [
            #     'idp.authn.LDAP.bindDNCredential                 = myServicePassword',
            #     'idp.authn.LDAP.bindDNCredential                 = %s' % p['bindDNCredential']
            # ]
        ])
        shell.run(session, 'chown tomcat:tomcat %s' % ldap_properties)
    return func

