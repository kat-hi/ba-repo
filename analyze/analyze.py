import json
import logging
import os
import time
from datetime import datetime

from analyze.git.analyzer import GitRepoAnalyzer
from analyze.git.iterative_analyzer import IterativeGitrepoAnalyzer
from analyze.svn.svnrepo_analyzer import SvnRepoAnalyzer
from db.api.branches import find_branchname_by_revisionhash
from db.api.utils import find_revisions_of_context
from db.models.branch import Branches
from db.models.file import Files
from db.models.revisionChangedFileEffect import RevisionChangedFileEffect
from db.models.revision import Revisions
from entry import Session


def analyze_history(repository_path, include_deleted_contexts, start_date):
    logging.info("===ANALYSE HISTORY===")
    analyzer = None

    if os.path.isdir(os.path.join(repository_path, ".git")):
        analyzer = GitRepoAnalyzer(repository_path, start_date)
        analyzer.default_branchname = "origin/master"

    elif os.path.isdir(os.path.join(repository_path, ".svn")):
        analyzer = SvnRepoAnalyzer(repository_path, start_date)
        analyzer.default_branchname = "trunk"

    processing_t0 = time.process_time()
    execution_t0 = datetime.strptime(datetime.now().strftime("%d-%m-%y %H:%M:%S"), "%d-%m-%y %H:%M:%S")

    analyzer.update_local_repository()
    analyzer.analyze_branches()
    analyzer.analyze_revisions()
    if include_deleted_contexts:
        analyzer.analyze_revisions_without_context()
    analyzer.analyze_merges()
    if start_date:
        analyzer.create_fileversion_keyframe()
    analyzer.create_fileversions()
    analyzer.analyze_effect_by_files()

    processing_t1 = time.process_time()
    execution_t1 = datetime.strptime(datetime.now().strftime("%d-%m-%y %H:%M:%S"), "%d-%m-%y %H:%M:%S")
    processing_time = round((processing_t1 - processing_t0) / 60, 3)
    execution_time = round((execution_t1 - execution_t0).total_seconds() / 60, 3)

    analyzer.dump_results(processing_time, execution_time)


def iterative_analysis(repository_path, start_date=None):
    logging.info("===ANALYSE NEW HISTORY===")
    analyzer = None

    if os.path.isdir(os.path.join(repository_path, ".git")):
        analyzer = IterativeGitrepoAnalyzer(repository_path)
        analyzer.default_branchname = "origin/master"

    elif os.path.isdir(os.path.join(repository_path, ".svn")):
        analyzer = SvnRepoAnalyzer(repository_path, start_date)
        analyzer.default_branchname = "trunk"

    processing_t0 = time.process_time()
    execution_t0 = datetime.strptime(datetime.now().strftime("%d-%m-%y %H:%M:%S"), "%d-%m-%y %H:%M:%S")

    analyzer.set_iterative(True)
    analyzer.update_local_repository()
    analyzer.analyze_branches()
    analyzer.analyze_revisions()
    analyzer.analyze_merges()
    analyzer.create_fileversions()
    analyzer.analyze_effect_by_files()

    processing_t1 = time.process_time()
    execution_t1 = datetime.strptime(datetime.now().strftime("%d-%m-%y %H:%M:%S"), "%d-%m-%y %H:%M:%S")
    processing_time = round((processing_t1 - processing_t0) / 60, 3)
    execution_time = round((execution_t1 - execution_t0).total_seconds() / 60, 3)

    analyzer.dump_results(processing_time, execution_time, iterative=True)


def get_results():
    results_dict = {"branches": {}, "execution_time": str(), "number_branches": 0, "number_revisions": 0,
                    "success_rate": str()}
    with Session.begin() as session:
        branches = session.query(Branches).all()
        results_dict['number_branches'] = len(branches)
        for branch in branches:
            origin_branch = find_branchname_by_revisionhash(branch.origin_revision)
            results_dict["branches"][branch.name] = {"origin": {}}
            results_dict["branches"][branch.name]["origin"] = {"origin_revision": branch.origin_revision,
                                                               "origin_branch": origin_branch}

            revisions = find_revisions_of_context(branch.id)
            if revisions:
                results_dict['number_revisions'] += len(revisions)
                results_dict["branches"][branch.name] = {"revisions": {}}
                for rev in revisions:
                    rev_dict = {rev: {}}
                    db_rev = session.query(Revisions).filter(Revisions.hash == rev).first()
                    is_merge = db_rev.is_merge == 1
                    rev_dict[rev]["is_merge"] = is_merge
                    rev_dict[rev]["authordate"] = db_rev.authordate

                    # merges
                    if is_merge:
                        results = get_transported_commits(rev)
                        rev_dict[rev]["transported_commits"] = {"first_level": results["directly"],
                                                                "second_and_above": results["all"]}

                    # effects per commit
                    effects = session.query(RevisionChangedFileEffect).join(Revisions,
                                                                            Revisions.hash == RevisionChangedFileEffect.revision_hash).filter(
                        Revisions.hash == rev).all()
                    revision_loc_delta = 0
                    revision_comments_delta = 0
                    for effect in effects:
                        revision_loc_delta += effect.LOC_delta
                        revision_comments_delta += effect.Comments_delta

                    rev_dict[rev]["effects_total"] = {"LOC": revision_loc_delta, "Comments": revision_comments_delta}

                    # effects per file
                    rev_dict[rev]["effects_per_file"] = {}
                    revision_changedfiles = session.query(RevisionChangedFileEffect).filter(
                        RevisionChangedFileEffect.revision_hash == rev).all()
                    for revision_changedfile in revision_changedfiles:
                        filepath = \
                            session.query(Files.relative_filepath).filter(
                                Files.id == revision_changedfile.file_id).first()[
                                0]
                        effects = {"effects": {"LOC": revision_changedfile.LOC_delta,
                                               "Comments": revision_changedfile.Comments_delta}}
                        rev_dict[rev]["effects_per_file"][filepath] = effects

                    results_dict["branches"][branch.name]['revisions'][rev] = rev_dict[rev]

        return results_dict


def get_transported_commits(revision):
    transport_results = {"all": [], "directly": []}
    with Session.begin() as session:
        transported_commits = [commit.hash for commit in
                               session.query(Revisions).filter(Revisions.related_merge_commit == revision).all()]

        for transported_commit in transported_commits:
            commit = session.query(Revisions).filter(Revisions.hash == transported_commit).first()
            if commit.is_merge:
                recursive_results = get_transported_commits(commit.hash)
                for revision in recursive_results["directly"]:
                    transport_results["all"].append(revision)
                for revision in recursive_results["all"]:
                    transport_results["all"].append(revision)
            else:
                transport_results["directly"].append(commit.hash)
    return transport_results


def write_output(repository_path):
    name = repository_path.split('/')[-1]
    logging.info("Write data dump.")
    results = get_results()
    with open(f"../out/results_{name}.json", "w") as outfile:
        json.dump(results, outfile, indent=2, default=str)
