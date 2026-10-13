from plur import base_shell as shell


download_dir = '$HOME/Downloads/'
download_with_accept_license_agreement = ' '.join([
    'wget',
    '-4',
    '--header',
    '"Cookie: oraclelicense=accept-securebackup-cookie"'
])


def remove_openjdk(session):
    shell.run(session, 'sudo yum remove -y *openjdk*')


def setup_jdk8_rpm(version='8u131-b11'):
    def func(session):
        shell.work_on(session, download_dir)

        v = version.split('-')[0]
        rpm = 'jdk-%s-linux-x64.rpm' % v
        if not shell.check_file_exists(session, rpm):
            dl_command = ' '.join([
                download_with_accept_license_agreement,
                'http://download.oracle.com/otn-pub/java/jdk/%s/%s' % (version, rpm)
            ])
            shell.run(session, dl_command)

        if not shell.check_command_exists(session, 'java -version'):
            shell.run(session, 'sudo yum localinstall -y %s' % rpm)

        jdk_path = '/usr/java/jdk1.8.0_' + (v.split('u')[1])
        return jdk_path
    return func


def enable_jce_policy(jdk_path):
    def func(session):
        shell.work_on(session, download_dir)

        jce_policy = 'jce_policy-8'
        extracted_dir = download_dir + 'UnlimitedJCEPolicyJDK8'
        if not shell.check_file_exists(session, download_dir + '/%s.zip' % jce_policy):
            dl_command = ' '.join([
                download_with_accept_license_agreement,
                'http://download.oracle.com/otn-pub/java/jce/8/%s.zip' % jce_policy
            ])
            shell.run(session, dl_command)
        shell.run(session, 'unzip -o %s.zip' % jce_policy)

        copy_files = [
            'local_policy.jar',
            'US_export_policy.jar'
        ]
        jdk_security_dir = jdk_path + '/jre/lib/security/'
        if not shell.check_file_exists(session, jdk_security_dir + copy_files[0] + '.org'):
            for fname in copy_files:
                f = jdk_security_dir + fname
                shell.run(session, 'sudo mv %s %s && sudo cp %s %s' % (f, f + '.org', extracted_dir + '/' + fname, f))
    return func


def setup_env(jdk_path):
    def func(session):
        session.sudo_i()
        jdk_profile_path = '/etc/profile.d/jdk.sh'
        shell.here_doc(session, jdk_profile_path, [
            'export JAVA_HOME={jdk_path}/jre'.format(jdk_path=jdk_path),
            'export PATH=\$PATH:\$JAVA_HOME/bin',
        ])
        session.su_exit()
        shell.run(session, 'source /etc/profile')
    return func


def setup(flag):
    def func(session):
        shell.yum_install(session, {'packages': [
            'wget',
            'zip',
            'unzip'
        ]})
        jdk_path = [f(session) for f in [
            remove_openjdk,
            setup_jdk8_rpm()
        ]][1]
        setup_env(jdk_path)(session)
        if 'jce' in flag:
            enable_jce_policy(jdk_path)(session)
    return func
