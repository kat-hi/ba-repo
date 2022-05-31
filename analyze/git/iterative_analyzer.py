import logging
from datetime import datetime, timedelta

from analyze.git.analyzer import GitRepoAnalyzer
from analyze.git.api.cmd import get_mainpath_to_genesis
from analyze.exe_runner import ExeRunner
from db.api.utils import find_path_to_origin_by_branch
from db.api.branches import find_all_persisted_branchnames, branch_exists_without_origin
from db.models.branch import Branches
from entry import Session


class IterativeGitrepoAnalyzer(GitRepoAnalyzer):
    def __init__(self, repository_path):
        super().__init__(repository_path, start_date=None)
        self.start_date = datetime.today() - timedelta(days=2)

    def analyze_branches(self):
        db_branchnames = find_all_persisted_branchnames()
        self._update_mainpath_to_origin(db_branchnames)
        self._collect_branches()
        branch_tries = 0
        logging.info('for each branch: identify first branch-away commit')
        while branch_exists_without_origin():
            if branch_tries == 5:
                logging.info('max branch try exceeded')
                break
            self._find_new_branch_origins()
            branch_tries += 1

    def analyze_revisions_without_context(self):
        pass

    def _find_new_branch_origins(self):
        with Session.begin() as session:
            db_new_branches = session.query(Branches) \
                .filter(Branches.origin_revision == None) \
                .order_by(Branches.last_activity).all()
            db_all_branches = session.query(Branches).order_by(Branches.last_activity).all()
            ff_merge_branches = []

            for new_branch in db_new_branches:
                logging.info(f'find branch origin {new_branch.name}')
                # concerning these new branches the "branch_path_to_analyze_desc" is identical to the mainpath to genesis
                genesis_path_current_branch = self.branches[new_branch.name]['branch_path_to_analyze_desc']
                if not genesis_path_current_branch:
                    genesis_path_current_branch = get_mainpath_to_genesis(self.repository_path, new_branch.name)
                    self.branches[new_branch.name][
                        'branch_path_to_analyze_desc'] = genesis_path_current_branch  # all commits

                if new_branch.origin_revision is None:
                    commits_of_others = set()
                    other_branches = [b for b in db_all_branches if b.name != new_branch.name if
                                      b.name not in ff_merge_branches]

                    for other_branch in other_branches:
                        # other branches are a mix of branches having a mainpath_to_origin,
                        # and new branches having an empty list or mainpath to genesis
                        other_branch_path_to_origin = self.branches[other_branch.name]["branch_path_to_analyze_desc"]
                        if other_branch_path_to_origin:
                            commits_of_others.update(other_branch_path_to_origin)
                        else:
                            genesis_path_other_branch = get_mainpath_to_genesis(self.repository_path, other_branch.name)
                            self.branches[other_branch.name]["branch_path_to_analyze_desc"] = genesis_path_other_branch
                            commits_of_others.update(genesis_path_other_branch)

                    commit_in_others = next(
                        filter(lambda commit: commit in commits_of_others, genesis_path_current_branch), None)
                    if commit_in_others:
                        new_branch.origin_revision = commit_in_others
                        index_origin = genesis_path_current_branch.index(commit_in_others)
                        if index_origin == 0:  # e.g. in case of ff-merge
                            session.query(Branches).filter(Branches.name == new_branch.name).delete()
                            logging.info(f'branch {new_branch.name} is ignored since no path was identified.')
                            self.branches.pop(new_branch.name)
                            ff_merge_branches.append(new_branch.name)
                            self.results['results']['number_ignored_branches'] += 1
                        else:
                            # cut off mainpath to genesis -> mainpath to origin
                            self.branches[new_branch.name]['branch_path_to_analyze_desc'] = \
                                genesis_path_current_branch[:index_origin]
                    else:
                        print('branch origin not found')
                        self.results['results']['number_branches_without_origins'] += 1

    def _update_mainpath_to_origin(self, branchnames):
        for branchname in branchnames:
            mainpath_to_origin = find_path_to_origin_by_branch(branchname)
            # get all commits between current branch pointer and persisted last revision
            cmd = ['git', 'log', '--first-parent', '--pretty=format:%H', f'{mainpath_to_origin[0]}..{branchname}']
            out = ExeRunner.run(cmd, self.repository_path)
            branch_path_to_analyze_desc = out.splitlines()
            self.branches[branchname] = {'branch_path_to_analyze_desc': []}
            if branch_path_to_analyze_desc:
                branch_path_to_analyze_desc = branch_path_to_analyze_desc
                self.branches[branchname]['mainpath_to_origin'] = branch_path_to_analyze_desc + mainpath_to_origin
                self.branches[branchname]['branch_path_to_analyze_desc'] = branch_path_to_analyze_desc
                self.branches_to_analyze.append(branchname)
            else:
                self.branches[branchname]['mainpath_to_origin'] = mainpath_to_origin
