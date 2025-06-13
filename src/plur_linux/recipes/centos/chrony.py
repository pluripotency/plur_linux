from plur import base_shell
from plur import base_node
from plur_linux.recipes.ops import ops


def tz_asia_tokyo(session):
    ops.set_timezone('Asia/Tokyo')(session)


def enable_chronyd(session):
    if not base_shell.check_command_exists(session, 'chronyc'):
        base_shell.yum_install(session, {'packages': ['chrony']})
    ops.service_on('chronyd')(session)


def sync_force(session):
    base_shell.run(session, 'sudo chronyc -a makestep')
    base_shell.run(session, 'sudo chronyc sources')


def configure(session):
    platform = session.nodes[-1].platform
    if base_node.is_platform_rhel(platform):
        tz_asia_tokyo(session)
        enable_chronyd(session)
        sync_force(session)


