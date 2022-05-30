from sqlalchemy import exists

from analyze.exe_runner import ExeRunner
from analyze.git.utils.file import filepath_is_valid


def set_unchanged_tracked_files(revision_hash, revision_dict, repository_path):
    cmd = ['git', 'ls-tree', '-r', revision_hash, '--name-only']
    revision_tracked_files = ExeRunner.run(cmd, repository_path).splitlines()

    revision_dict[revision_hash]["tracked_files"] = [file for file in revision_tracked_files
                                                     if filepath_is_valid(file)
                                                     and file not in revision_dict[revision_hash][
                                                         'changed_files'].keys()]


def set_all_tracked_files(revision_hash, revision_dict, repository_path):
    cmd = ['git', 'ls-tree', '-r', revision_hash, '--name-only']
    revision_tracked_files = ExeRunner.run(cmd, repository_path).splitlines()

    revision_dict[revision_hash]["tracked_files"] = [file for file in revision_tracked_files
                                                     if filepath_is_valid(file)
                                                     and file not in revision_dict[revision_hash][
                                                         'changed_files'].keys()]
