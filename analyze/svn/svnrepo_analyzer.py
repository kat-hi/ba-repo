import logging

import pyparsing

from analyze.abstract.repoanalyzer import RepoAnalyzer
from analyze.exe_runner import ExeRunner as exe, ExeRunner
from analyze.svn.grammar import log_entry
from db.models.branch import Branches
from db.models.revision import Revisions


class SvnRepoAnalyzer(RepoAnalyzer):

    def analyze_branches(self):
        self._collect_branches()

    def _collect_branches(self):
        logging.info("Collect branch information")
        cmd = ['svn', 'ls', '^/branches/']
        out = ExeRunner.run(cmd, self.repository_path)
        lines = out.splitlines()

        # default branch
        self.default_branchname = 'trunk'
        self.branches[self.default_branchname] = Branches(self.default_branchname)
        cmd = ['svn', 'log', '--use-merge-history', '--verbose', '--stop-on-copy', '^/' + self.default_branchname]
        self._parse_branch_information(self.default_branchname, cmd)

        ## branches
        for line in lines:
            branchname = line.replace('/', '')
            self.branches[branchname] = Branches(branchname)
            cmd = ['svn', 'log', '--use-merge-history', '--verbose', '--stop-on-copy', '^/branches/' + branchname]
            self._parse_branch_information(branchname, cmd)

    def _parse_svn_logs(self, cmd):
        try:
            out = ExeRunner.run(cmd, self.repository_path)
            # out = '------------------------------------------------------------------------\nr6 | admin | 2022-01-24 14:41:27 +0100 (Mo, 24 Jan 2022) | 1 line\nChanged paths:\n   M /trunk/main.py\n   M /trunk/other.py\n\nupdate merge------------------------------------------------------------------------'
            logs = log_entry.parseString(out)
            return logs
        except pyparsing.ParseException as e:
            print(f'e: {e}')

    def _parse_branch_information(self, branchname, cmd):
        logs = self._parse_svn_logs(cmd)
        for log in logs:
            self.branches[branchname].mainpath_to_origin.append(log.revision)
        self.branches[branchname].origin_revision = 'r' + logs[-1].origin_revision
        origin_branch = logs[-1].origin_branch
        if origin_branch == '':
            self.branches[branchname].origin_branch = branchname
        else:
            self.branches[branchname].origin_branch = logs[-1].origin_branch
        self.branches[branchname].last_activity = logs[0].datetime

    def analyze_merges(self):
        raise NotImplementedError

    def analyze_revisions(self):
        logging.info("Collect hash information")
        for item in self.branches.items():
            branchname = item[0]

            cmd = ['svn', 'log', '--use-merge-history', '--verbose', '--stop-on-copy', '^/']
            if branchname == 'trunk':
                branchpath = '/trunk'
                cmd.append(branchname)
            else:
                branchpath = f'/branches/{branchname}'
                cmd.append(branchpath)

            cmd_mergeinfo = ['svn', 'mergeinfo', f'^{branchpath}', '--show-revs', 'merged']
            out_merges = ExeRunner.run(cmd_mergeinfo, self.repository_path)
            merges = out_merges.splitlines()
            logs = self._parse_svn_logs(cmd)

            for log in logs:
                revision_context = []
                rev = log.revision

                self.revisions[rev] = Revisions(rev)
            # for item in self.branches.items():
            #     branch = item[1]
            #     if rev in branch.mainpath_to_origin:
            #         revision_context = branch.mainpath_to_origin
            # index_current_rev = revision_context.index(rev)
            # if index_current_rev != 0:
            #     self.revisions[rev].successors.add(revision_context[index_current_rev-1])
            # if index_current_rev != len(revision_context)-1:
            #     self.revisions[rev].parents.add(revision_context[index_current_rev+1])
            #     changed_files = log.changed_files
            #     for file in changed_files:
            #         self.revisions[rev].changed_files = {"mode": file.svn_status[0], "filepath": file.filepath[0]}

    def update_local_repository(self):
        logging.info('Run "svn update" to get latest info from remote repository.')
        cmd = ['svn', 'update']
        exe.run(cmd, self.repository_path)


