from plur import base_shell as shell

syslog_destination = r"""    <!-- syslog destination  -->
    <appender name="IDP_SYSLOG_AUDIT" class="ch.qos.logback.classic.net.SyslogAppender">
        <syslogHost>${idp.fticks.loghost:-localhost}</syslogHost>
        <port>${idp.fticks.logport:-514}</port>
        <facility>local0</facility>
        <suffixPattern>[%thread] %logger %msg</suffixPattern>
    </appender>
    <appender name="IDP_SYSLOG_PROCESS" class="ch.qos.logback.classic.net.SyslogAppender">
        <syslogHost>${idp.fticks.loghost:-localhost}</syslogHost>
        <port>${idp.fticks.logport:-514}</port>
        <facility>local1</facility>
        <suffixPattern>[%thread] %logger %msg</suffixPattern>
    </appender>

    <logger name="Shibboleth-Audit" level="ALL">""".replace('\n', '\\n')


def configure(p):
    def func(session):
        if 'syslog_ip' in p:
            syslog_ip = p['syslog_ip']
        else:
            syslog_ip = 'localhost'
        logback = '$SHIB_HOME/conf/logback.xml'
        backup_file = logback + '.org'
        shell.create_backup(session, logback)
        shell.sed_pipe(session, backup_file, logback, [
            [
                '^    <variable name="idp.fticks.loghost" value="localhost" />$',
                '    <variable name="idp.fticks.loghost" value="%s" />' % syslog_ip
            ],
            [
                '^    <logger name="Shibboleth-Audit" level="ALL">',
                syslog_destination
            ],
            [
                '^        <appender-ref ref="${idp.audit.appender:-IDP_AUDIT}"/>$',
                '        <appender-ref ref="${idp.audit.appender:-IDP_AUDIT}"/>\\n' +
                '        <appender-ref ref="IDP_SYSLOG_AUDIT"/>'
            ],
            [
                '^        <appender-ref ref="${idp.warn.appender:-IDP_WARN}" />$',
                '        <appender-ref ref="${idp.warn.appender:-IDP_WARN}" />\\n' +
                '        <appender-ref ref="IDP_SYSLOG_PROCESS" />'
            ]
        ])
        shell.run(session, 'chown tomcat:tomcat %s' % logback)
    return func

