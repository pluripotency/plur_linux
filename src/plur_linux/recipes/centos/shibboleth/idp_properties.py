from plur import base_shell


def configure(p):
    def func(session):
        if 'server_name' in p:
            server_name = p['server_name']
        else:
            server_name = session.nodes[-1].fqdn

        idp_properties = '$SHIB_HOME/conf/idp.properties'
        base_shell.create_backup(session, idp_properties)
        base_shell.sed_pipe(session, "%s.org" % idp_properties, idp_properties, [
            [
                '^idp.entityID= https://%s/idp/shibboleth$' % server_name,
                'idp.entityID= https://%s/idp/shibboleth\\nidp.entityID.metadataFile =' % server_name
            ]
        ])
        base_shell.run(session, 'chown tomcat:tomcat %s' % idp_properties)
    return func

