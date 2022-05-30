import logging
import time

import pyparsing

from abc import ABC, abstractmethod

from analyze.exe_runner import ExeRunner
from db.models.branch import Branches
from db.models.fileRevisionRelation import FileRevisionRelation
from db.models.revision import Revisions
from db.models.revisionRelation import RevisionRelations
from entry import Session
import json


class RepoAnalyzer(ABC):

    def __init__(self, repository_path, start_date):
        self.iterative = False
        self.repository_path = repository_path
        self.start_date = start_date
        self.branches = dict()
        self.branches_to_analyze = list()
        self.revisions = dict()
        self.default_branchname = str()
        self.date_format = '--date=format:%Y-%m-%d %H:%M:%S %z'
        self.results = {
            "results": {"number_branches_without_origins": 0, "number_ignored_branches": 0, "number_changed_files": 0,
                        "number_file_versions": 0, "number_effects": 0, "errors_effects": 0,
                        "success_rate": float}}
        self.cache = {"db_revisions": list(), 'db_branches': list(), 'db_file_revision_relations': list(),
                      'db_revision_relations': list()}

        self.ignored_files = []

    @abstractmethod
    def analyze_branches(self):
        raise NotImplementedError

    @abstractmethod
    def analyze_merges(self):
        raise NotImplementedError

    @abstractmethod
    def analyze_revisions(self):
        raise NotImplementedError

    @abstractmethod
    def update_local_repository(self):
        raise NotImplementedError

    def set_iterative(self, boolean):
        self.iterative = boolean

    def _parse_logs(self, cmd, logfile):
        try:
            out = ExeRunner.run(cmd, self.repository_path)
            logs = logfile.parseString(out)
            return logs
        except pyparsing.ParseException as e:
            print(f'e: {e}\n')

    def dump_results(self, processing_time, execution_time, iterative=False):
        repo_name = self.repository_path.split('/')[-1]
        self.results['results']['execution_time(min)'] = execution_time
        self.results['results']['processing_time_(min)'] = processing_time
        self.results['results']['start_date'] = self.start_date

        number_effects = self.results['results']["number_effects"]
        number_changed_files = self.results['results']["number_changed_files"]

        if iterative:
            filename = f'../out/reports_iterative_{repo_name}.json'
            self.results['results']['success_rate'] = ''
        else:
            filename = f'../out/reports_{repo_name}.json'
            self.results['results']['success_rate'] = number_effects / number_changed_files * 100

        with open(filename, 'w') as file:
            json.dump(self.results['results'], file)

    def add_all_file_revision_relations(self):
        logging.info('... add all file-revision relations')
        with Session.begin() as session:
            session.bulk_insert_mappings(FileRevisionRelation, self.cache['db_file_revision_relations'])
        self.cache['db_file_revision_relations'].clear()

    def create_revisions_relations(self):
        logging.info('... add all revision relations')
        with Session.begin() as session:
            session.bulk_insert_mappings(RevisionRelations, self.cache['db_revision_relations'])
        self.cache['db_file_revision_relations'].clear()

    def create_all_revisions(self):
        logging.info('... add all revisions')
        with Session.begin() as session:
            if self.cache['db_revisions']:
                session.bulk_insert_mappings(Revisions, self.cache['db_revisions'])
        self.cache['db_revisions'].clear()

    def create_all_artificial_contexts(self):
        logging.info('... add all contexts')
        with Session.begin() as session:
            session.bulk_insert_mappings(Branches, self.cache['db_branches'])
        self.cache['db_branches'].clear()

    def set_affected_branches(self):
        with Session.begin() as session:
            db_revisions = session.query(Revisions).filter(Revisions.affected_branch == None).all()
            for db_rev in db_revisions:
                db_branches = session.query(Branches).filter(db_rev.authordate <= Branches.last_activity).all()
                for branch in db_branches:
                    if db_rev.hash in self.branches[branch.name]['branch_path_to_analyze_desc']:
                        db_rev.affected_branch = branch.id
                        session.add(db_rev)
                        session.flush()
                        session.refresh(db_rev)
                        break
