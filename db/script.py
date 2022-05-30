import json

import numpy as np
import matplotlib.pyplot as plt


def cm_to_inch(value):
    return value / 2.54


def convert_branchnames_to_picture_labels(branchnames_reduced):
    new_branchnames = []
    for branchname in branchnames_reduced:
        if "branch" in branchname:
            number = branchname.split('branch')[-1]
            if len(number) == 2:
                new_branchnames.append(f'b_{number}')
            else:
                new_branchnames.append(f'b_0{number}')
        else:
            new_branchnames.append(f'b_00')
    return new_branchnames


with open('../out/results.json', 'r') as file:
    data = json.load(file)

data_branches = data['branches'].keys()
branches_dict = {}  # branch_id (index) - branch name mapping
revisions_dict = {}  # revision_id (index) - time mapping

branch_name_series = []  # lables y-axis
loc_series = []  # z-axis

for branch_index, branch in enumerate(data_branches):
    if 'revisions' in data['branches'][branch].keys():
        revisions = list(data['branches'][branch]['revisions'].keys())
        branches_dict[branch] = branch_index

        for revision in revisions:
            branch_name_series.append(branch)
            loc_series.append(data['branches'][branch]['revisions'][revision]['effects_total']['LOC'])
            revisions_dict[len(revisions_dict)] = revision

revision_hashes_ids_series = np.array(list(revisions_dict.keys()))  # x-axis
revision_hash_series = list(revisions_dict.values())  # x-axis lables
branch_id_series = np.array([branches_dict[branchname] for branchname in branch_name_series])  # y-axis

# setup the figure and axes
fig = plt.figure()
fig.set_size_inches(25, 20)
ax = fig.add_subplot(121, projection='3d')

ax.set_title('revision effects on lines of code in different contexts')
ax.set_xlabel('revisions', fontsize=9, labelpad=50)
# ax.yaxis.set_rotate_label(False)
ax.set_ylabel('branches', fontsize=9, labelpad=-1)
ax.zaxis.set_rotate_label(False)
ax.set_zlabel('changed LoC', fontsize=9, labelpad=2, rotation=-90)
ax.tick_params(axis='y', pad=-1)
ax.tick_params(axis='x', pad=-1)
ax.tick_params(axis='z', pad=3, labelsize=7)
ax.set_box_aspect((6, 3, 1))
plt.xticks(fontsize=7, rotation=90)
plt.yticks(fontsize=7)

# set rgba
rgba = []
for index, loc in enumerate(loc_series):
    rev = revision_hash_series[index]
    branch = branch_name_series[index]

    is_merge = data['branches'][branch]['revisions'][rev]['is_merge']
    if is_merge:
        rgba.append((0.0, 0.0, 1.0, 0.3))
    elif loc == 2:
        rgba.append((0.0, 1.0, 0.0, 1.0))
    elif loc != 2:
        rgba.append((1.0, 0.0, 0.0, 1.0))

dx = [0.5] * len(revision_hashes_ids_series)
dy = [0.6] * len(revision_hashes_ids_series)
z = np.zeros(len(revision_hashes_ids_series))

ax.bar3d(revision_hashes_ids_series, branch_id_series, z, dx, dy, loc_series, color=rgba, shade=True)
branchids_reduced = list(branches_dict.values())
branchnames_reduced = list(branches_dict.keys())

revision_hash_reduced = list(dict.fromkeys(revision_hash_series))
revision_hash_reduced = [rev[:7] for rev in revision_hash_reduced]

revision_time_ids_reduced = list(dict.fromkeys(revision_hashes_ids_series))

new_branchnames = convert_branchnames_to_picture_labels(branchnames_reduced)
plt.yticks(branchids_reduced, new_branchnames)
plt.xticks(revision_time_ids_reduced, revision_hash_reduced)
# manager = plt.get_current_fig_manager()
# manager.full_screen_toggle()
plt.savefig('myfigure.png', dpi=300)

plt.show()
