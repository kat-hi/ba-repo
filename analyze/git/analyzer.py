import logging
import os
import re

from sqlalchemy.exc import IntegrityError
from analyze.git.api.cmd import update_repository, get_remote_branches, get_mainpath_to_genesis, get_merge_base, \
    get_ancestry_path, \
    checkout
from analyze.git.grammar import LOGFILE
from analyze.abstract.repoanalyzer import RepoAnalyzer
from analyze.exe_runner import ExeRunner
from analyze.git.utils.datetime import convert_gitdatestr_to_datetime
from analyze.git.utils.file import filepath_is_valid, filepath_exists
from analyze.git.utils.revisions import set_all_tracked_files
from db.api.utils import find_second_parent_by_merge_hash, get_or_create_file_id, \
    file_exists, revision_exists, get_authordate, get_filerevision_relation_before_date, \
    find_changed_fileversions_by_revision, \
    find_metrics_of_fileversion_in_branch_before_date, get_first_parent_hash, find_parent_file_version_metrics
from db.api.branches import find_origin_revision_of_branch_by_any_revision_hash, \
    branch_exists_without_origin, \
    branch_exists, get_branch_path_from_start_date_by_branch_name, find_all_persisted_branchnames, \
    get_branch_path_from_start_date_by_branch_id, find_branch_id_by_branchname, find_branch_origin_revision, \
    find_first_branch_revision_by_start_date, find_all_branchnames_without_origin_revision
from db.models.branch import Branches
from db.models.file import Files
from db.models.fileRevisionRelation import FileRevisionRelation
from db.models.revision import Revisions
from db.models.fileversion import Fileversion
from db.models.revisionChangedFileEffect import RevisionChangedFileEffect
from entry import Session
from parser.metrics_extractor import extract


class GitRepoAnalyzer(RepoAnalyzer):

    def __init__(self, repository_path, start_date, time_delta=None):
        super().__init__(repository_path, start_date, time_delta)

    def analyze_branches(self):
        self._collect_branches()
        logging.info('for each branch: identify first branch-away commit')
        branch_tries = 0
        while branch_exists_without_origin():
            if branch_tries == 5:
                logging.info('max branch try exceeded')
                break
            self._find_branch_origins()
            branch_tries += 1

        number_branches = len(find_all_branchnames_without_origin_revision())
        self.results['results']['number_branches_without_origins'] += number_branches

    def analyze_revisions(self):
        logging.info('===ANALYZE REVISIONS===')

        cmd = ['git', 'log', '--reverse', '--first-parent', '-m', '--all', '--name-status', self.date_format,
               '--pretty=format:hash=%H parents=%P author_email=%ae\n author_date=%ad\n commit_date=%cd']

        if self.start_date:
            startdate = self.start_date.split('T')[0]
            cmd = cmd + [f'--since="{startdate}"']

        revisions = self._parse_logs(cmd, LOGFILE)
        if not revisions:
            print("no revisions")
        self.create_revisions(revisions)
        self.set_affected_branches()

    def create_revisions(self, revisions):
        self._parse_revisions(revisions)
        self.create_all_revisions()
        self.create_revisions_relations()

    def analyze_revisions_without_context(self):
        logging.info('===ANALYZE REVISIONS WITHOUT CONTEXT===')
        with Session.begin() as session:
            merge_hashes = session.query(Revisions.hash).filter(Revisions.is_merge).filter(
                Revisions.affected_branch != None).order_by(Revisions.authordate).all()
            revisions = set()
            context_names = []
            for merge in merge_hashes:
                merge = merge[0]
                cmd = ['git', 'log', merge, '-1', '--format=format:%P']
                parents = ExeRunner.run(cmd, self.repository_path).split(' ')
                for parent in parents:
                    if not revision_exists(parent):
                        other_parent = [p for p in parents if p != parent]
                        common_ancestor = get_merge_base(self.repository_path, parent, other_parent[0])
                        ancestry_path = get_ancestry_path(self.repository_path, common_ancestor, parent)
                        for index, revision in enumerate(ancestry_path):
                            cmd = ['git', 'log', revision, '-m', '-1', '--name-status', self.date_format,
                                   '--pretty=format:hash=%H parents=%P author_email=%ae\n author_date=%ad\n commit_date=%cd']
                            revision = self._parse_logs(cmd, LOGFILE)
                            revisions.add(revision[0])
                            if index == 0:
                                context_name = f'deleted_{merge[:7]}'
                                self._create_artificial_context(session, context_name, merge, ancestry_path,
                                                                revision[0].author_date, common_ancestor)
                                context_names.append(context_name)

        self.create_revisions(revisions)
        self.set_related_merge_commit(context_names)
        self.create_all_artificial_contexts()
        self.set_affected_branches()

    def analyze_merges(self):
        logging.info('===ANALYZE MERGES===')
        # annahme: branch wird nicht mehrmals gemerged (nur ein merge commit wird jeweils zugeordnet)
        with Session.begin() as session:
            if self.start_date:
                merges = session.query(Revisions).filter(Revisions.is_merge) \
                    .filter(Revisions.authordate > self.start_date).all()
            else:
                merges = session.query(Revisions).filter(Revisions.is_merge).all()

            logging.info('... for each merge find transported commits')
            for merge_revision in merges:
                second_parent_hash = find_second_parent_by_merge_hash(merge_revision.hash,
                                                                      merge_revision.affected_branch)
                if second_parent_hash:
                    origin_revision_hash = find_origin_revision_of_branch_by_any_revision_hash(second_parent_hash)
                    if origin_revision_hash:
                        git_path = f'{origin_revision_hash}..{second_parent_hash}'
                        cmd = ['git', 'rev-list', '--ancestry-path', '--first-parent', git_path]
                        ancestry_path_to_branch_origin = ExeRunner.run(cmd, self.repository_path).splitlines()

                        for line in ancestry_path_to_branch_origin:
                            db_revision = session.query(Revisions).filter(Revisions.hash == line).first()
                            if db_revision:
                                db_revision.related_merge_commit = merge_revision.hash

    def _get_all_files_of_revision(self, revision):
        changed_filepathes = list(self.revisions[revision]['changed_files'].keys())
        tracked_files = self.revisions[revision]['tracked_files']
        all_files = changed_filepathes + tracked_files
        return all_files

    def create_fileversion_keyframe(self):
        logging.info('=== CREATE INITIAL FILE VERSIONS ===')
        default_branch_start_revision = find_first_branch_revision_by_start_date(self.default_branchname,
                                                                                 self.start_date)

        set_all_tracked_files(default_branch_start_revision, self.revisions, self.repository_path)
        all_tracked_files = self.revisions[default_branch_start_revision]['tracked_files']
        file_modified_at = self.revisions[default_branch_start_revision]['file_modified_at']

        modifier = 'S'
        file_revision_relations = []
        counter = 0
        num = len(all_tracked_files)
        checkout(self.repository_path, default_branch_start_revision)

        for path in all_tracked_files:
            counter += 1
            if divmod(counter, 50)[1] == 0:
                logging.info(f'done: {counter} of {num}.')

            file_id = get_or_create_file_id(path)
            metrics = {'LOC': 0, 'Comments': 0}
            if path in self.ignored_files:
                print(f'filepath not exist {default_branch_start_revision}: {path}')
            else:
                if filepath_exists(path, self.repository_path):
                    metrics = extract(os.path.join(self.repository_path, path))
                    with Session.begin() as session:
                        if file_modified_at:
                            fileversion = Fileversion(modifier, file_id, file_modified_at, metrics['LOC'],
                                                      metrics['Comments'])
                            session.add(fileversion)
                            session.flush()
                            session.refresh(fileversion)
                            file_revision_relations \
                                .append(FileRevisionRelation(default_branch_start_revision, fileversion.id))

        with Session.begin() as session:
            session.add_all(file_revision_relations)

    def create_fileversions(self):
        logging.info('=== CREATE CHANGED FILEVERSIONS ===')
        for current_branch in self.branches_to_analyze:
            if self.start_date:
                branch_path = get_branch_path_from_start_date_by_branch_name(self.start_date, current_branch)[1:]
            else:
                branch_path = list(reversed(self.branches[current_branch]['branch_path_to_analyze_desc']))

            for revision in branch_path:
                checkout(self.repository_path, revision)
                if revision in self.revisions.keys():
                    changed_files = self.revisions[revision]['changed_files']
                    for path, modifier in changed_files.items():
                        self.results['results']['number_changed_files'] += 1
                        self._create_fileversion(path, revision, modifier)
                else:
                    print(f'key error{revision}')

        self.add_all_file_revision_relations()

    def _collect_branches(self):
        logging.info('===COLLECT BRANCHES===')
        out = get_remote_branches(self.repository_path)
        branches = out.splitlines()

        with Session.begin() as session:
            branches_to_add = []
            for branchname in branches:
                branchname = branchname.lstrip(' ')
                regex = '^.+ -> (.+)$'
                match = re.match(regex, branchname)
                if match:
                    self.default_branchname = match.group(1)
                else:
                    cmd = ['git', 'log', '-1', '--pretty=format:%ci', branchname]
                    datestr = ExeRunner.run(cmd, self.repository_path)

                    branch = {"name": branchname, "last_activity": convert_gitdatestr_to_datetime(datestr),
                              "origin_revision": None}

                    if not branch_exists(branchname):
                        if self.start_date:
                            # if last activity is after start_date, this branch is relevant
                            if datestr > self.start_date:
                                branches_to_add.append(branch)
                                self.branches[branchname] = {'branch_path_to_analyze_desc': [],
                                                             'mainpath_to_origin': []}
                                logging.info(f"Add branch {branchname}.")
                        else:
                            branches_to_add.append(branch)
                            self.branches[branchname] = {'branch_path_to_analyze_desc': [], 'mainpath_to_origin': []}
                            logging.info(f"Add branch {branchname}.")
                        # branch_path_to_analyze_desc: either path to origin, or path to last saved state
                    else:
                        db_branch = session.query(Branches).filter(Branches.name == branchname).first()
                        db_branch.last_activity = branch['last_activity']
                        session.add(db_branch)

            session.bulk_insert_mappings(Branches, branches_to_add)

    def _find_branch_origins(self):
        # special handling of default branch
        with Session.begin() as session:
            branches = []
            default_branch = session.query(Branches).filter(Branches.name == self.default_branchname).first()
            branches.append(default_branch)
            db_branches = session.query(Branches).filter(Branches.name != self.default_branchname).order_by(
                Branches.last_activity).all()  # not desc! old -> new!
            branches = branches + db_branches
            ff_merge_branches = []

            for branch in branches:
                genesis_path = get_mainpath_to_genesis(self.repository_path, branch.name)
                if branch.origin_revision is None:
                    logging.info(f'find branch origin {branch.name}')
                    if branch.name == self.default_branchname:
                        branch.origin_revision = genesis_path[-1]
                        self.branches_to_analyze.append(branch.name)
                        self.branches[branch.name]['branch_path_to_analyze_desc'] = genesis_path
                    else:
                        # find last branch away commit
                        commits_of_others = self._get_commits_of_others(branches, branch.name, ff_merge_branches)
                        commit_in_others = next(filter(lambda commit: commit in commits_of_others, genesis_path), None)
                        if commit_in_others:
                            branch.origin_revision = commit_in_others
                            index_origin = genesis_path.index(commit_in_others)
                            session.flush()
                            session.refresh(branch)
                            if index_origin == 0:  # e.g. in case of ff-merge
                                session.query(Branches).filter(Branches.name == branch.name).delete()
                                logging.info(f'branch {branch.name} is ignored since no path was identified.')
                                self.branches.pop(branch.name)
                                ff_merge_branches.append(branch)
                                self.results['results']['number_ignored_branches'] += 1
                            else:
                                self.branches_to_analyze.append(branch.name)
                                self.branches[branch.name]['branch_path_to_analyze_desc'] = genesis_path[:index_origin]
                        else:
                            logging.info(f'{branch.name} origin is before start date')
                            if branch.name not in self.results['results']['branches_without_origin']:
                                self.results['results']['branches_without_origin'].append(branch.name)

    def _get_commits_of_others(self, branches, branch_name, ff_merge_branches):
        commits_of_others = set()
        other_branches = [b for b in branches if b.name != branch_name if b not in ff_merge_branches]
        for other_branch in other_branches:
            genesis_path_other = get_mainpath_to_genesis(self.repository_path, other_branch.name)
            # if a branch's base_revision already has been identified, cut off mainpath to genesis before update
            if other_branch.origin_revision:
                origin_index = genesis_path_other.index(other_branch.origin_revision)
                commits_of_others.update(genesis_path_other[:origin_index])
            else:
                commits_of_others.update(genesis_path_other)
        return commits_of_others

    def _get_next_branchnames(self, current_branch, branch_path):
        next_branchnames = []
        with Session.begin() as session:
            db_branches = session.query(Branches) \
                .join(Revisions, Branches.origin_revision == Revisions.hash) \
                .filter(Branches.name != current_branch) \
                .order_by(Revisions.authordate).all()

            for db_branch in db_branches:
                if db_branch.origin_revision in branch_path:
                    next_branchnames.append(db_branch.name)
        return next_branchnames

    def set_related_merge_commit(self, branchnames):
        with Session.begin() as session:
            for branchname in branchnames:
                branch = self.branches[branchname]
                for rev_hash in branch['branch_path_to_analyze_desc']:
                    db_rev = session.query(Revisions).filter(Revisions.hash == rev_hash).first()
                    db_rev.related_merge_commit = branch['merge_commit']

    def _create_artificial_context(self, session, context_name, mergehash, ancestry_path, authordate, origin):
        session.begin_nested()
        self.branches[context_name] = {'branch_path_to_analyze_desc': ancestry_path,
                                       'merge_commit': mergehash}

        branch = {"name": context_name, "last_activity": convert_gitdatestr_to_datetime(authordate),
                  "origin_revision": origin}
        self.cache['db_branches'].append(branch)
        logging.info(f'created artificial branch {context_name}')
        session.commit()

    def _parse_revisions(self, revisions):
        logging.info('... parse revisions')
        for revision in revisions:
            if not revision_exists(revision.hash):
                self.revisions[revision.hash] = {'changed_files': {}, 'tracked_files': [], 'deleted_files': {}}
                self._parse_revision(revision)
                self._track_and_create_files(revision)

    def _parse_revision(self, revision):
        rev = {"hash": revision.hash, "authordate": revision.author_date, "is_merge": None,
               "affected_branch": None, "related_merge_commit": None}

        if len(revision.parents) > 1:
            rev['is_merge'] = True
        else:
            rev['is_merge'] = False

        cached_hashes = [rev['hash'] for rev in self.cache['db_revisions']]
        if revision.hash not in cached_hashes:
            self.cache['db_revisions'].append(rev)

        for parent in revision.parents:
            is_first_parent = parent == revision.parents[0]

            revision_relation = {"revision_id": revision.hash, "parent_id": parent,
                                 "is_first_parent": is_first_parent}
            self.cache['db_revision_relations'].append(revision_relation)

    def _create_fileversion(self, path, revision, modifier):
        file_id = get_or_create_file_id(path)
        metrics = {'LOC': 0, 'Comments': 0}
        if not modifier == 'D':
            if path not in self.ignored_files and filepath_exists(path, self.repository_path):
                metrics = extract(os.path.join(self.repository_path, path))
        try:
            with Session.begin() as session:
                # revision_date = session.query(Revisions.authordate).filter_by(hash=revision).first()[0]
                file_modified_at = self.revisions[revision]['file_modified_at']
                fileversion = Fileversion(modifier, file_id, file_modified_at, metrics['LOC'], metrics['Comments'])
                session.add(fileversion)
                session.flush()
                session.refresh(fileversion)

                self._cache_file_revision_relation(revision, file_modified_at, fileversion.id)
                self.results['results']['number_file_versions'] += 1

        except IntegrityError:
            session.rollback()
            print(f'integrity error: {revision}, {path}, {modifier}. File version not created.')

    def _cache_file_revision_relation(self, rev_hash, author_date, file_version_id):
        filerevisionrelation = {"revision_hash": rev_hash, "fileversion_id": file_version_id}
        if not self.start_date:
            self.cache['db_file_revision_relations'].append(filerevisionrelation)
        else:
            if author_date > self.start_date:
                self.cache['db_file_revision_relations'].append(filerevisionrelation)

    def _track_and_create_files(self, revision):
        with Session.begin() as session:
            files = list()
            for current_file in revision.files:
                #  wrong results for 'filedata' if file contains a whitespace
                #  split('    ') would be possible, but there is still a very unlikely case that some file renames
                #  are not splitted correctly.(grammar)
                filedata = [entry.strip() for entry in current_file.split(' ') if entry != '']
                file_modifier = filedata[0]
                relative_filepath = filedata[1]

                modified_at = revision.commit_date

                if 'R' in file_modifier:
                    # Rename == delete + add
                    file_modifier = 'A'
                    relative_filepath = filedata[2]  # new file
                    deleted_file = filedata[1]  # removed file
                    self._track(revision.hash, modifier='D', path=deleted_file, file_modified_at=modified_at)
                elif 'D' in file_modifier:
                    self._track(revision.hash, modifier='D', path=relative_filepath,
                                file_modified_at=modified_at)
                elif 'M' in file_modifier:
                    self._track(revision.hash, modifier=file_modifier, path=relative_filepath,
                                file_modified_at=modified_at)

                if 'A' in file_modifier:
                    valid = self._track(revision.hash, modifier=file_modifier, path=relative_filepath,
                                        file_modified_at=modified_at)
                    if valid:
                        if not file_exists(relative_filepath):
                            files.append({"relative_filepath": relative_filepath})
            try:
                session.bulk_insert_mappings(Files, list(files))
            except IntegrityError:
                session.rollback()
                with Session.begin() as session:
                    for file in files:
                        db_file = session.query(Files.id).filter(
                            Files.relative_filepath == file['relative_filepath']).first()
                        if not db_file:
                            db_effect = Files(file['relative_filepath'])
                            session.add(db_effect)
                        else:
                            print('file already exists')

    def _track(self, rev_hash, modifier, path, file_modified_at):
        if path in self.ignored_files:
            # file is not valid
            return False
        else:
            # check if file is valid
            valid = filepath_is_valid(path)
            if not valid:
                self.ignored_files.append(path)
                return valid

        self.revisions[rev_hash]['changed_files'][path] = modifier
        self.revisions[rev_hash]['file_modified_at'] = file_modified_at
        return valid

    def update_local_repository(self):
        logging.info("Run 'git fetch' to get latest info from remote repository.")
        update_repository(self.repository_path)

    def get_parent_file_version_metrics(self, session, author_date, version_file_id, branch_id):
        filerevisionrelation = get_filerevision_relation_before_date(author_date, version_file_id)
        if filerevisionrelation:
            filerevisionrelation = [relation[0] for relation in filerevisionrelation]

        branch_revisions = get_branch_path_from_start_date_by_branch_id(author_date, branch_id)
        if branch_revisions:
            branch_revisions = [branch[0] for branch in branch_revisions]

        session.begin_nested()
        for branch_revision in branch_revisions:
            if branch_revision in filerevisionrelation:
                file_version_id = session.query(FileRevisionRelation.fileversion_id).filter(
                    FileRevisionRelation.revision_hash == branch_revision).first()[0]
                parent_fileversion_metrics = session.query(Fileversion.LOC, Fileversion.Comments) \
                    .filter(Fileversion.id == file_version_id).first()
                if parent_fileversion_metrics:
                    session.commit()
                    return parent_fileversion_metrics

    def analyze_file_effects_in_context(self, branch_path, current_branch):
        logging.info(f' ... {current_branch}')
        num = len(branch_path)
        count = 0

        branch_id = find_branch_id_by_branchname(current_branch)
        effects = []
        first_branch_revision = branch_path[0]
        for revision in branch_path:
            count += 1
            if divmod(count, 10)[1] == 0:
                logging.info(
                    f'done: {count} of {num}. [success: {self.results["results"]["number_effects"]}, errors: {self.results["results"]["errors_effects"]}]')

            changed_fileversions = find_changed_fileversions_by_revision(revision)
            for version_id, file_id, version_loc, version_comments, version_modification in changed_fileversions:
                effect = {"revision_hash": revision, "branch_id": branch_id, "fileversion_id": version_id,
                          "file_id": file_id, "LOC_delta": None, "Comments_delta": None}

                if version_modification == "A" or version_modification == "S":
                    effect['LOC_delta'] = version_loc
                    effect['Comments_delta'] = version_comments
                    effects.append(effect)
                    self.results['results']["number_effects"] += 1
                else:
                    parent_fileversion_metrics = None
                    author_date = get_authordate(revision)

                    # find parent file version in same branch:
                    parent_fileversion_metrics = find_metrics_of_fileversion_in_branch_before_date(file_id,
                                                                                                   author_date,
                                                                                                   branch_id)
                    # fileversion could be anywhere in its base branches
                    if not parent_fileversion_metrics:
                        parent_fileversion_metrics = self.find_previous_fileversion_in_basebranches(branch_id, file_id,
                                                                                                    author_date)

                    # # fallback: because of rebase, dates are not sorted properly and all parents have to be checked
                    if not parent_fileversion_metrics:
                        parent_fileversion_metrics = self.find_previous_fileversion_by_parents(revision, file_id)

                    if parent_fileversion_metrics:
                        effect['LOC_delta'] = version_loc - parent_fileversion_metrics[0]
                        effect['Comments_delta'] = version_comments - parent_fileversion_metrics[1]
                        effects.append(effect)
                        self.results['results']["number_effects"] += 1
                    else:
                        effect['LOC_delta'] = version_loc
                        effect['Comments_delta'] = version_comments
                        effects.append(effect)
                        if revision == first_branch_revision:
                            self.results['results']["number_effects"] += 1
                        else:
                            self.results['results']['errors_effects'] += 1

        self.create_all_changed_file_effects(effects=effects)

    def find_previous_fileversion_in_basebranches(self, branch_id, file_id, author_date):
        branch_origin_revision = find_branch_origin_revision(branch_id)

        source_branches = self.get_all_source_branches(branch_origin_revision)

        for source_branch in source_branches:
            parent_fileversion_metrics = find_metrics_of_fileversion_in_branch_before_date(
                file_id,
                author_date,
                source_branch[2])
            if parent_fileversion_metrics:
                return parent_fileversion_metrics

    def find_previous_fileversion_by_parents(self, revision, file_id):
        logging.info('----- fallback ----- ')
        current_revision = revision
        parent_fileversion_metrics = None
        while not parent_fileversion_metrics:
            current_revision = get_first_parent_hash(current_revision)
            parent_fileversion_metrics = find_parent_file_version_metrics(file_id, current_revision)
            if not current_revision:
                break
        return parent_fileversion_metrics

    def create_all_changed_file_effects(self, effects):
        try:
            with Session.begin() as session:
                session.bulk_insert_mappings(RevisionChangedFileEffect, effects)
        except IntegrityError:
            logging.error('Integrity error in bulk dump. Trying to insert effects sequentially.')
            session.rollback()
            with Session.begin() as session:
                for effect in effects:
                    db_effect = session.query(RevisionChangedFileEffect.revision_hash).filter(
                        RevisionChangedFileEffect.revision_hash == effect['revision_hash']).filter(
                        RevisionChangedFileEffect.file_id == effect['file_id']).first()
                    if not db_effect:
                        db_effect = RevisionChangedFileEffect(effect['revision_hash'], effect['branch_id'],
                                                              effect['fileversion_id'], effect['file_id'])
                        db_effect.LOC_delta = effect['LOC_delta']
                        db_effect.Comments_delta = effect['Comments_delta']
                        session.add(db_effect)
                    else:
                        print('effect already exists')

    def get_all_source_branches(self, origin_revision):
        source_branches = self._get_source_branches(origin_revision, all_source_branches=[])
        return source_branches

    def _get_source_branches(self, origin_revision, all_source_branches):
        with Session.begin() as session:
            source_branches = session.query(Branches.name, Branches.origin_revision, Branches.id) \
                .join(Revisions, Revisions.affected_branch == Branches.id) \
                .filter(Revisions.hash == origin_revision) \
                .order_by(Revisions.authordate).all()
            all_source_branches += source_branches
            for source_branch in source_branches:
                origin_revision = source_branch[1]
                if not source_branch[0] == self.default_branchname:
                    all_source_branches = self._get_source_branches(origin_revision, all_source_branches)
        return all_source_branches

    def analyze_effect_by_files(self):
        logging.info('===ANALYZE EFFECT BY COMMIT===')
        for current_branch in self.branches_to_analyze:
            if self.start_date:
                path_from_origin = get_branch_path_from_start_date_by_branch_name(self.start_date, current_branch)[1:]
            else:
                path_from_origin = list(reversed(self.branches[current_branch]['branch_path_to_analyze_desc']))

            if path_from_origin:
                self.analyze_file_effects_in_context(path_from_origin, current_branch)

    def get_first_level_transported_commits(self, session, revision, transported_commits):
        session.begin_nested()
        first_level_transported = session.query(Revisions).filter(Revisions.related_merge_commit == revision).all()
        transported_commits += first_level_transported
        return transported_commits
