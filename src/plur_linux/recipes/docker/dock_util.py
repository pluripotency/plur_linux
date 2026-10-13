from plur import base_shell
import os


def is_built(session, tag):
    result = session.do(base_shell.check(f'if [ `docker images -q {tag}| wc -l` -gt 0 ];'))
    session.child.expect(session.waitprompt)
    return result


def is_running(session, container_name):
    result = session.do(base_shell.check(f'if [ `docker ps -q -f name=^{container_name}$| wc -l` -gt 0 ];'))
    session.child.expect(session.waitprompt)
    return result


def prepare_file(session, file_path):
    cwd = os.path.dirname(__file__)
    base_shell.heredoc_from_local(f'{cwd}/{file_path}', file_path)(session)


def work_on(container_name):
    def func(session):
        docker_dir = f'~/Docker/{container_name}'
        base_shell.work_on(session, docker_dir)

    return func


