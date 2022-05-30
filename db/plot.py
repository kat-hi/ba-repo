import matplotlib.pyplot as plt

# create data
changed_files = ([139590, 72983, 10058, 2356, 1674], [669.94, 254, 17.69, 0.8, 0.58])
revisions = ([15561, 15519, 922, 546, 550], [254, 669.94, 17.69, 0.8, 0.58])
branches = ([82, 16, 120, 12, 21], [254, 669.94, 17.69, 0.8, 0.58])

# plot lines
plt.plot(changed_files[0], changed_files[1], label="changed files")
plt.plot([0, 40000, 80000, 120000], [0, 150, 300, 450], label='linear')
# plt.plot(revisions[1], revisions[0], label="revisions")
# plt.plot(branches[1], branches[0], label="branches")

plt.legend()
plt.show()
