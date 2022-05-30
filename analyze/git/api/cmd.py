from analyze.exe_runner import ExeRunner


def checkout(repository_path, object):
    cmd = ['git', 'checkout', object]
    ExeRunner.run(cmd, repository_path)


def update_repository(repository_path):
    cmd = ['git', 'fetch']
    ExeRunner.run(cmd, repository_path)

    cmd = ['git', 'pull']
    ExeRunner.run(cmd, repository_path)


def get_remote_branches(repository_path):
    cmd = ['git', 'branch', '-r']
    out = ExeRunner.run(cmd, repository_path)
    return out


def get_mainpath_to_genesis(repository_path, branchname):
    cmd = ['git', 'log', '--first-parent', '--pretty=format:%H', branchname]
    out = ExeRunner.run(cmd, repository_path).splitlines()
    return out


def get_ancestry_path(repository_path, common_ancestor, revision_hash):
    commits = f'{common_ancestor}..{revision_hash}'
    cmd = ['git', 'rev-list', '--ancestry-path', commits]
    ancestry_path = ExeRunner.run(cmd, repository_path).splitlines()
    return ancestry_path


def get_merge_base(repository_path, base_branch_parent, merge_branch_parent):
    cmd = ['git', 'merge-base', base_branch_parent, merge_branch_parent]  # [0] base branch, [1] merge branch
    merge_base = ExeRunner.run(cmd, repository_path).strip()
    return merge_base


def log_pretty(repository_path, format, object):
    cmd = ['git', 'log', format, object]
    out = ExeRunner.run(cmd, repository_path)
    return out
