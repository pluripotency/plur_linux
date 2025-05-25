# ! /usr/bin/env python
import os
import sys

sys.path.append(os.pardir)

from plur import base_shell as shell


example_file_list = [
    {
        'name': 'rrdtool',
        'files': [
            {
                'name': 'rrdtool-1.4.8.tgz',
                'option': 'extract_tgz'
            }
        ],
        'src': 'http://repo/virt/pkgs/',
        'dst': '/opt/'
    },
    {
        'name': 'scripts',
        'files': [
            'ovs.sh',
            'ovsinfo.py'
        ],
        'src': 'http://repo/setups/scripts/',
        'dst': '/bin/'
    }
]


def plant(session, file_list):
    for f in file_list:
        if 'files' in f and 'src' in f and 'dst' in f:
            files = f['files']
            src_url = f['src']
            dst = f['dst']
            shell.work_on(session, dst)
            for file_obj in files:
                if isinstance(file_obj, dict):
                    file_name = file_obj['name']
                    shell.wget(session, src_url + file_name)
                    if 'option' in file_obj:
                        if file_obj['option'] == 'extract_tgz':
                            shell.run(session, 'tar xvzf ' + file_name)
                if isinstance(file_obj, str):
                    shell.wget(session, src_url + file_obj)
