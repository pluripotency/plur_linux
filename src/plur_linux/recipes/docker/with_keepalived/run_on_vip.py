from mini import misc
from plur import base_shell


def run_on_vip_str(repo_list, vip, base_dir=None):
    file_path = '$HOME/run_on_vip.sh'
    rlist = [f'"{repo}"' for repo in repo_list]
    base_dir_str = 'BASE_DIR=$(cd $(dirname $0);pwd)'
    if base_dir:
        base_dir_str = f'BASE_DIR={base_dir}'
    contents = misc.del_indent(f"""
    #! /bin/sh
    {base_dir_str}
    declare -a REPO_LIST=({' '.join(rlist)})

    /usr/sbin/ip -4 -br a | grep -q {vip}

    """)
    contents += misc.del_indent("""
    
    if [ $? -gt 0 ]; then
        for REPO in ${REPO_LIST[@]};do
            cd $BASE_DIR/$REPO
            sh stop.sh
        done
    else
        for REPO in ${REPO_LIST[@]};do
            cd $BASE_DIR/$REPO
            sh start.sh
        done
    fi
    
    """)
    return file_path, contents


def arm_cron_str():
    file_path = '$HOME/arm_cron.sh'
    run_file_path = '$HOME/run_on_vip.sh'
    contents = misc.del_indent(f"""
    #! /bin/bash
    echo "*/5 * * * * sh {run_file_path} 2>&1" >  mycron
    crontab mycron
    rm mycron
    """)
    return file_path, contents


def arm_cron(repo_list, vip, base_dir=None):
    def func(session):
        file_path, contents = run_on_vip_str(repo_list, vip, base_dir)
        base_shell.here_doc(session, file_path, contents.split('\n'))
        file_path, contents = arm_cron_str()
        base_shell.here_doc(session, file_path, contents.split('\n'))
        base_shell.run(session, f'bash {file_path}')
    return func
