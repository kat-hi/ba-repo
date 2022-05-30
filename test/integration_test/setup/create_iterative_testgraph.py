import os

from consts import TESTDIR, TESTREPO_NAME
from integration_test.setup.git_commands import change_branch_remote, merge, checkout, checkout_new_branch

testrepopath = os.path.join(TESTDIR)

os.chdir(os.path.join(testrepopath, TESTREPO_NAME))

checkout('branch3')
change_branch_remote('branch3', filenames=['filename3.txt', 'filename3a.txt'], number_commits=2)

checkout('branch5')
change_branch_remote('branch5', filenames=['filename5.txt', 'filename5a.txt'], number_commits=3)

checkout('master')

checkout_new_branch('branch12')
change_branch_remote(branchname='branch12', filenames=['filename12.txt', 'filename1.txt'], number_commits=2,
                     setup_origin=True)

merge('master', 'branch5', check_out=True)
checkout_new_branch('branch13')
change_branch_remote(branchname='branch13', filenames=['filename13.txt', 'filename2.txt'], number_commits=2,
                     setup_origin=True)

merge('master', 'branch12', check_out=True)






