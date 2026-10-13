from plur import base_shell


def setup(session):
    # base_shell.yum_install(session, {'packages': ['java-1.8.0-openjdk', 'java-1.8.0-openjdk-devel']})
    base_shell.yum_install(session, {'packages': ['java-1.8.0-openjdk']})

    jdk_profile_path = '/etc/profile.d/jdk.sh'
    base_shell.here_doc(session, jdk_profile_path, [
        "export JAVA_HOME=/usr/lib/jvm/jre",
        # 'export JAVA_HOME=`dirname $(dirname $(dirname $(readlink $(readlink $(which java)))))`',
        'export PATH=\$JAVA_HOME/bin:\$PATH',
        'export CLASSPATH=.:\$JAVA_HOME/jre/lib:\$JAVA_HOME/lib:\$JAVA_HOME/lib/tools.jar'
    ])
    base_shell.run(session, 'source /etc/profile')

