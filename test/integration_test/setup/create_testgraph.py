import os

from consts import TESTDIR, TESTREPO_NAME, TESTREPO_URL
from integration_test.setup.git_commands import change_branch_remote, push_changes, merge, checkout, checkout_new_branch
import subprocess as s

testrepopath = os.path.join(TESTDIR)
os.chdir(testrepopath)
s.run([f"git clone {TESTREPO_URL}"], shell=True)
os.chdir(os.path.join(testrepopath, TESTREPO_NAME))

# main
change_branch_remote(branchname='master', filenames=['readme.txt', 'setup.sh'], number_commits=2)

# branch1
checkout_new_branch(branchname='branch1')
change_branch_remote(branchname='branch1', filenames=['filename1.txt', 'filename1a.txt'], number_commits=2,
                     setup_origin=True)

# main
checkout('master')
change_branch_remote(branchname='master', filenames=['readme.txt', 'setup.sh'], number_commits=1)
merge(sourcebranch='master', targetbranch='branch1')
change_branch_remote(branchname='master', filenames=['readme.txt', 'setup.sh'], number_commits=1)

##################################################################
# Branch2, Branch3
# mainbranch and subbranch
# *--*----*----*--*-----*------*
#      \     /   \            /
#       *-*-*    b2-*-*---*--*
#                    \   /
#                    b3-*
##################################################################

# branch2
checkout_new_branch('branch2')
change_branch_remote(branchname='branch2', filenames=['filename2.txt', 'filename2a.txt'], number_commits=2,
                     setup_origin=True)

# branch3
checkout_new_branch('branch3')
change_branch_remote('branch3', filenames=['filename3.txt', 'filename3a.txt'], number_commits=2, setup_origin=True)

# main
checkout('master')
change_branch_remote(branchname='master', filenames=['readme.txt', 'setup.sh'], number_commits=1)

# branch2
checkout('branch2')
change_branch_remote(branchname='branch2', filenames=['filename2.txt', 'filename2a.txt'], number_commits=1)

push_changes('branch2')
change_branch_remote(branchname='branch2', filenames=['filename2.txt', 'filename2a.txt'], number_commits=1)

# main
merge(sourcebranch='master', targetbranch='branch2', check_out=True)

change_branch_remote(branchname='master', filenames=['readme.txt', 'setup.sh'], number_commits=1)

#####
checkout_new_branch('branch4')
change_branch_remote(branchname='branch4', filenames=['filename4.txt', 'filename2.txt'], number_commits=2,
                     setup_origin=True)

checkout('master')

checkout_new_branch('branch5')
change_branch_remote(branchname='branch5', filenames=['filename5.txt', 'filename1.txt'], number_commits=2,
                     setup_origin=True)

checkout_new_branch('branch6')
change_branch_remote(branchname='branch6', filenames=['filename6.txt', 'filename1a.txt'], number_commits=2,
                     setup_origin=True)

checkout('branch4')
checkout_new_branch('branch7')
change_branch_remote(branchname='branch7', filenames=['filename7.txt', 'filename2a.txt'], number_commits=2,
                     setup_origin=True)

checkout_new_branch('branch8')
change_branch_remote(branchname='branch8', filenames=['filename8.txt', 'filename8a.txt'], number_commits=2,
                     setup_origin=True)

checkout('branch5')
change_branch_remote(branchname='branch5', filenames=['filename5.txt', 'filename11.txt'], number_commits=2)

checkout('master')
change_branch_remote(branchname='master', filenames=['setup.sh', 'readme.txt'], number_commits=1)
merge(sourcebranch='master', targetbranch='branch6')

checkout('branch7')
change_branch_remote(branchname='branch7', filenames=['filename7.txt', 'filename2a.txt'], number_commits=1)
merge(sourcebranch='branch7', targetbranch='branch8')

checkout('branch4')
change_branch_remote(branchname='branch4', filenames=['filename4.txt', 'filename2.txt'], number_commits=2)

checkout('branch7')
change_branch_remote(branchname='branch7', filenames=['filename7.txt', 'filename2a.txt'], number_commits=1)

merge(sourcebranch='branch4', targetbranch='branch7', check_out=True)

change_branch_remote(branchname='branch4', filenames=['filename4.txt', 'filename2.txt'], number_commits=1)

merge(sourcebranch='master', targetbranch='branch4', check_out=True)

checkout_new_branch('branch9')
change_branch_remote(branchname='branch9', filenames=['filename9.txt', 'filename1.txt'], number_commits=2,
                     setup_origin=True)

checkout('master')
checkout_new_branch('branch10')
change_branch_remote(branchname='branch10', filenames=['filename10.txt', 'filename10a.txt'], number_commits=2,
                     setup_origin=True)

checkout_new_branch('branch11')
change_branch_remote(branchname='branch11', filenames=['filename11.txt', 'filename4.txt'], number_commits=2,
                     setup_origin=True)

merge(sourcebranch='master', targetbranch='branch9', check_out=True)

checkout('branch10')
change_branch_remote(branchname='branch10', filenames=['filename10.txt', 'filename2.txt'], number_commits=1)

merge(sourcebranch='branch10', targetbranch='branch11', check_out=True)

merge(sourcebranch='master', targetbranch='branch10', check_out=True)
