from plur import session_wrap
from plur import base_shell
from plur_linux.recipes import firewalld


def install_zabbix_agent():
    @session_wrap.sudo
    def func(session):
        firewalld.configure(ports=['10050/tcp'], add=True)(session)
        repo = 'https://repo.zabbix.com/zabbix/5.0/rhel/7/x86_64/zabbix-release-5.0-1.el7.noarch.rpm'
        actions = [
            f'sudo rpm -Uvh {repo}'
            , 'sudo yum install -y zabbix-agent'
        ]
        [base_shell.run(session, a) for a in actions]
    return func


def configure(zabbix_server_ip, agent_hostname):
    @session_wrap.sudo
    def func(session):
        file_path = '/etc/zabbix/zabbix_agentd.conf'
        replace_list = [
            f's/^Server=127.0.0.1$/Server={zabbix_server_ip}/'
            ,  f's/^ServerActive=127.0.0.1$/ServerActive={zabbix_server_ip}/'
            , f's/^Hostname=Zabbix server$/Hostname={agent_hostname}/'
        ]
        [base_shell.run(session, f"sed -i '{r}' {file_path}") for r in replace_list]

    return func


def setup_agent(zabbix_server_ip, agent_hostname):
    @session_wrap.sudo
    def func(session):
        install_zabbix_agent()(session)
        configure(zabbix_server_ip, agent_hostname)(session)
        base_shell.service_on(session, 'zabbix-agent')
    return func


def configure_server_fw(session):
    firewalld.configure(services=['http', 'https', 'ssh'], ports=['3389/tcp', '10050-10051/tcp'])(session)


