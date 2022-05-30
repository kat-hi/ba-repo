# ******************************************************************************
# * seerene(tm) - A framework for analyzing and visualizing complex software systems.
# * Copyright (C) 2005 - 2020 for all source codes:
# * seerene(tm) GmbH, Potsdam, Germany
# ******************************************************************************
import unittest
import os
import json
import re
import pexpect
from pexpect.popen_spawn import PopenSpawn
from tests.consts import TESTDIR, TOOLPATH, ROOTPATH, TESTREPO_NAME


class TestBranchOrigin(unittest.TestCase):
    class _spawn(PopenSpawn):
        # PopenSpawn does not implement close(), but it is used by SpawnBase.__exit__().
        # Further it does not close stdin + stdout of the subprocess resulting in ResourceWarning: unclosed file.
        def close(self):
            self.proc.kill()
            self.proc.stdin.close()
            self.proc.stdout.close()

    def _expect(self, child, pattern, **kwargs):
        return self.expect(child, pattern, **kwargs)

    @staticmethod
    def expect(process, pattern, **kwargs):
        """
        Allows to set expectations not only on the spawned process but also beyond that.
        """
        try:
            return process.expect(pattern, **kwargs)
        except (pexpect.ExceptionPexpect, pexpect.EOF) as e:
            raise Exception(
                'Expectation on process failed:\n'
                f'- pattern="{pattern}"\n'
                f'- exception="{repr(e)}"\n'
                f'- before="{process.before}"'
            )

    def run_analyze_command(self, repos_json_filepath):
        command = f'{TOOLPATH} analyze --repodir {repos_json_filepath}'

        os.chdir(ROOTPATH)
        with self._spawn(command, timeout=60) as child:
            self._expect(child, pexpect.EOF)
            ret_code = child.wait()
            before = child.before.decode('utf-8')
            self.assertEqual(ret_code, 0)
            return before

    def test_branch_origins(self):
        expected_history_json = os.path.join(TESTDIR, 'testdata', 'testrepo.json')
        with open(expected_history_json, 'r') as file:
            expected_history = json.load(file)

        self.run_analyze_command(repos_json_filepath=os.path.join(TESTDIR, 'testrepo', TESTREPO_NAME))
        result_history_json = self._get_repos_json()
        result_history_json_filepath = os.path.join(ROOTPATH, result_history_json)

        with open(result_history_json_filepath, 'r') as file:
            result_history = json.load(file)

        expected_branches = expected_history['branches']
        result_branches = result_history['branches']

        branches_currently_expected_to_fail = ['origin/branch7', 'origin/branch10', 'origin/branch11',
                                               'origin/branch12', 'origin/branch13']

        for branch in result_branches:
            branchname = branch['branch_name']
            print(branchname)
            expected_branch = [b for b in expected_branches if b['branch_name'] == branchname][0]
            print(expected_branch)
            with self.subTest(f"Test {branchname} mainpath to origin"):
                if branchname not in branches_currently_expected_to_fail:
                    self.assertEqual(expected_branch['origin_commit'], branch['mainpath_to_origin'][-1])
                else:
                    self.assertFalse(expected_branch['origin_commit'] == branch['mainpath_to_origin'][-1])

    def _get_repos_json(self):
        regex = 'repo_[\w\W]*.json'
        r = re.compile(regex)

        files = os.listdir(ROOTPATH)
        for file in files:
            if r.search(file):
                return file
