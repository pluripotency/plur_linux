#! /usr/bin/env python
import os
import sys
sys.path.append(os.pardir)
from plur import base_shell as shell
from recipes.ops import git


def remove_old_repos(repos):
    def func(session):
        [shell.run(session, 'rm -rf ' + repo['dir']) for repo in repos]
    return func


def clone_repos(repos):
    def func(session):
        for repo in repos:
            shell.work_on(session, '`dirname %s`' % repo['dir'])
            password = repo['passowrd'] if 'pass' in repo else None
            git.clone(session, repo['src'], password)
    return func


def run(repos):
    """
    "prepare_repos": [
        {
            "dir": "~/Projects/myapp/",
            "src": "https://github.com/myapp/myapp"
        }
    ]
    """
    return [
        remove_old_repos(repos),
        clone_repos(repos)
    ]

