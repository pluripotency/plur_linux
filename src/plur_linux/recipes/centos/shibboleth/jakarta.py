from plur import base_shell as shell
from plur import output_methods


def link(shib_home):
    def func(session):
        shell.yum_install(session, {'packages': ['jakarta-taglibs-standard']})
        jakarta_taglibs = [
            'jakarta-taglibs-core.jar',
            'jakarta-taglibs-standard.jar'
        ]
        s_dir = '/usr/share/java/'
        d_dir = '$SHIB_HOME/edit-webapp/WEB-INF/lib/'
        [shell.run(session, a) for a in ['ln -s %s %s' % (s_dir+j, d_dir+j) for j in jakarta_taglibs]]

        session.do(shell.create_sequence('$SHIB_HOME/bin/build.sh', [
            ['Installation Directory: \[.+\]', output_methods.send_line, shib_home, ''],
            [session.waitprompt, output_methods.success, '', '']
        ]))
    return func
