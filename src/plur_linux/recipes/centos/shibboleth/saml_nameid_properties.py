from plur import base_shell as shell


def configure(p):
    def func(session):
        if 'salt' in p:
            salt = p['salt']
        else:
            salt = 'suicamelontomatonasusalt'

        saml_nameid_properties = '$SHIB_HOME/conf/saml-nameid.properties'
        backup_file = saml_nameid_properties + '.org'
        shell.create_backup(session, saml_nameid_properties)
        shell.sed_pipe(session, backup_file, saml_nameid_properties, [
            [
                '^#idp.persistentId.sourceAttribute = changethistosomethingreal$',
                'idp.persistentId.sourceAttribute = uid'
            ],
            [
                '^#idp.persistentId.salt = changethistosomethingrandom$',
                'idp.persistentId.salt = %s' % salt
            ]
        ])
        shell.run(session, 'chown tomcat:tomcat %s' % saml_nameid_properties)
    return func
