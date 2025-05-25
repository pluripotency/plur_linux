from plur import base_shell
from plur import session_wrap


def prepare_bunzip2(session):
    if not base_shell.check_command_exists(session, 'bunzip2'):
        base_shell.yum_install(session, {'packages': ['bzip2']})


def download_from_git(file_path):
    def func(session):
        repository = 'curl -LO https://github.com/pluripotency/setup_files/raw/master/'
        base_shell.run(session, repository + file_path)
    return func


@session_wrap.sudo
def download_and_put(session):
    work_dir = '/tmp/'
    dl_filename = 'firefox_latest.tar.bz2'
    url = "https://download.mozilla.org/?product=firefox-latest-ssl&os=linux64&lang=en-US"

    prepare_bunzip2(session)

    base_shell.work_on(session, work_dir)
    if not base_shell.check_file_exists(session, work_dir+dl_filename):
        base_shell.run(session, 'curl -L "%s" -o %s' % (url, dl_filename))
    if not base_shell.check_dir_exists(session, '/usr/local/src/firefox'):
        actions = [
            'FIREFOX_DIR=`tar xvjf %s | head -1 | cut -f1 -d"/"`' % dl_filename,
            'tar xvjf %s' % dl_filename,
            'mv -f $FIREFOX_DIR /usr/local/src/firefox',
            'ln -s /usr/local/src/firefox/firefox /usr/local/bin/firefox'
        ]
        [base_shell.run(session, a) for a in actions]

    download_from_git('firefox/firefox.desktop')(session)
    download_from_git('firefox/firefox.png')(session)
    base_shell.run(session, 'mv -f firefox.png /usr/local/src/firefox/icons/')
