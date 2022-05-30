# ******************************************************************************
# * seerene(tm) - A framework for analyzing and visualizing complex software systems.
# * Copyright (C) 2005 - 2021 for all source codes:
# * seerene(tm) GmbH, Potsdam, Germany
# ******************************************************************************
import subprocess as s
import time


def fetch():
    s.run([f"git fetch"], shell=True)


def pull():
    s.run([f"git pull"], shell=True)


def checkout(branchname):
    s.run([f"git checkout {branchname}"], shell=True)
    fetch()
    pull()


def checkout_new_branch(branchname):
    s.run([f"git checkout -b {branchname}"], shell=True)


def change_worktree(filename, content, mode='a'):
    with open(filename, mode) as file:
        file.write(content)


def stage_change(filenames, branchname):
    for filename in filenames:
        s.run([f"git add {filename}"], shell=True)
        time.sleep(1)
    s.run([f"git commit -m {branchname}"], shell=True)
    time.sleep(1)


def push_changes(branchname, setup_origin=False):
    if setup_origin:
        s.run([f"git push -u origin {branchname}"], shell=True)
    else:
        s.run([f"git push"], shell=True)


def merge(sourcebranch, targetbranch, check_out=False):
    if check_out:
        checkout(sourcebranch)
    s.run([f"git merge {targetbranch} --commit --no-edit"], shell=True)
    push_changes(sourcebranch, setup_origin=False)


def change_branch_remote(branchname, filenames, number_commits=2, setup_origin=False):
    print("change branch remote")
    for i in range(number_commits):
        for filename in filenames:
            change_worktree(filename=filename, content=f'foo{i}\n#bar\n', mode='a')

        stage_change(filenames=filenames, branchname=branchname)
    push_changes(branchname, setup_origin=setup_origin)
