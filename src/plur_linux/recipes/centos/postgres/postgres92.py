from plur import base_shell


def install(session):
    base_shell.yum_install(session, {'packages': [
        'postgresql-server'
    ]})
