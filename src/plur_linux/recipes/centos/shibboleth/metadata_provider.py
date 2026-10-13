from plur import base_shell as shell


def configure(sp_server_name, shib_home):
    # example sp = 'c7sp.r'
    metadata_file_name = sp_server_name + '.xml'
    metadata_url = 'https://' + sp_server_name + '/Shibboleth.sso/Metadata'

    def func(session):
        metadata_dir = shib_home + '/metadata/'
        metadata_path = metadata_dir + metadata_file_name
        download_cmd = ' '.join([
            'wget',
            '-4',
            '--no-check-certificate',
            '-O %s' % metadata_file_name,
            metadata_url
        ])
        shell.work_on(session, metadata_dir)
        shell.run(session, download_cmd)
        shell.run(session, 'chown tomcat:tomcat %s' % metadata_file_name)

        metadata_conf = shib_home + '/conf/metadata-providers.xml'
        backup_file = metadata_conf + '.org'
        shell.create_backup(session, metadata_conf)
        shell.sed_pipe(session, backup_file, metadata_conf, [
            [
                '    <MetadataProvider id="LocalMetadata"  xsi:type="FilesystemMetadataProvider" metadataFile="PATH_TO_YOUR_METADATA"/>',
                '    -->\\n' +
                '    <MetadataProvider id="LocalMetadata"  xsi:type="FilesystemMetadataProvider" metadataFile="%s"/>\\n    <!--' % metadata_path
            ]
        ])
        shell.run(session, 'chown tomcat:tomcat %s' % metadata_conf)

    return func

