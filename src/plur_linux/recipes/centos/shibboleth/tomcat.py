from plur import base_shell as shell


def configure_log4j(session):
    log4j_dir = '/home/worker/Downloads/for_log4j/'
    if shell.check_dir_exists(session, log4j_dir):
        tomcat_dir = '/usr/share/tomcat/'
        log4j = log4j_dir + 'apache-log4j-1.2.17/log4j-1.2.17.jar'
        juli = log4j_dir + 'tomcat-juli.jar'
        juli_adapters = log4j_dir + 'tomcat-juli-adapters.jar'
        log4j_properties = log4j_dir + 'log4j.properties'
        shell.work_on(session, log4j_dir)
        if not shell.check_dir_exists(session, log4j_dir + 'apache-log4j-1.2.17/'):
            shell.run(session, 'tar xvzf log4j-1.2.17.tar.gz')
        shell.work_on(session, tomcat_dir)
        [shell.run(session, a) for a in [
            'unlink lib/log4j.jar',
            '\\cp -f %s lib/log4j.jar' % log4j,
            '\\cp -f %s lib/' % juli_adapters,
            '\\cp -f %s lib/' % log4j_properties,
            '\\cp -f %s bin/' % juli,
            '\\rm -f conf/log4j.properties',
            '\\rm -f conf/logging.properties',
        ]]


def configure(shib_home):
    def func(session):
        webapps = '$CATALINA_BASE/webapps/*'
        shell.run(session, 'rm -rf %s' % webapps)

        # server_info = '$CATALINA_BASE/lib/org/apache/catalina/util/ServerInfo.properties'
        # server_info_content = 'Apache Tomcat/8.0.x'
        # shell.run(session, 'mkdir -p `dirname %s`' % server_info)
        # shell.run(session, 'echo "%s" > %s' % (server_info_content, server_info))

        server_xml = '$CATALINA_BASE/conf/server.xml'
        shell.create_backup(session, server_xml)
        shell.sed_pipe(session, server_xml + '.org', server_xml, [
            # [
            #     '^<Server port="8005" shutdown="SHUTDOWN">$',
            #     '<Server port="-1" shutdown="SHUTDOWN">'
            # ],
            [
                '^    <Connector port="8009" protocol="AJP/1.3" redirectPort="8443" />$',
                '    <Connector port="8009" protocol="AJP/1.3" redirectPort="8443"\\n' +
                '        enableLookups="false" tomcatAuthentication="false"\\n' +
                '        address="127.0.0.1" maxPostSize="100000"/>'
            ],
            [
                '^    <Connector port="8080" protocol="HTTP/1.1"$',
                '<!--    <Connector port="8080" protocol="HTTP/1.1"'
            ],
            [
                "^    <!-- A \"Connector\" using the shared thread pool-->$",
                '-->    <!-- A "Connector" using the shared thread pool-->'
            ]
        ])

        idp_xml = [
            '<Context docBase="%s/war/idp.war"' % shib_home,
            '   privileged="true"',
            '   antiResourceLocking="false"',
            '   swallowOutput="true" />'
        ]

        idp_xml_file = '$CATALINA_BASE/conf/Catalina/localhost/idp.xml'
        shell.here_doc(session, idp_xml_file, idp_xml)
        shell.run(session, 'chown tomcat:tomcat %s' % idp_xml_file)
    return func
