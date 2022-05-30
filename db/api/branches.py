import logging

import sqlalchemy as sql
from sqlalchemy import exists, desc

from db.models.branch import Branches
from db.models.revision import Revisions
from entry import Session


def find_branchname_by_revisionhash(revision_hash):
    with Session.begin() as session:
        result = session.query(Branches.name).join(Revisions, Revisions.affected_branch == Branches.id).filter(
            Revisions.hash == revision_hash).first()
        if not result:
            return None
        else:
            return result[0]


def find_all_branchnames_without_origin_revision():
    with Session.begin() as session:
        branches = session.query(Branches.name).filter(Branches.origin_revision == None).all()
        return [b[0] for b in branches]


def find_origin_revision_of_branch_by_any_revision_hash(second_parent_hash):
    with Session.begin() as session:
        result = session.query(Branches.origin_revision) \
            .join(Revisions, Revisions.affected_branch == Branches.id).filter(
            Revisions.hash == second_parent_hash).first()
    if result:
        return result[0]
    else:
        return None


def find_branch_origin_revision(branch_id):
    with Session.begin() as session:
        result = session.query(Branches.origin_revision).filter(Branches.id == branch_id).first()
        if result:
            return result[0]


def find_branch_id_by_branchname(branchname):
    with Session.begin() as session:
        return session.query(Branches.id).filter(Branches.name == branchname).first()[0]


def find_branch_id_by_revisionhash(revision_hash):
    with Session.begin() as session:
        return session.query(Branches.id).join(Revisions, Revisions.affected_branch == Branches.id).filter(
            Revisions.hash == revision_hash).first()[0]


def find_all_persisted_branchnames():
    with Session.begin() as session:
        branches = session.query(Branches.name).all()
        return [branch[0] for branch in branches]


def find_branch_by_name(branchname):
    with Session.begin() as session:
        return session.query(Branches).filter_by(name=branchname).first()


def get_first_date_from_branch(branch_name):
    with Session.begin() as session:
        return session.query(Revisions.authordate) \
            .join(Branches, Branches.id == Revisions.affected_branch) \
            .filter(Branches.name == branch_name)\
            .order_by(Revisions.authordate).first()


def get_all_branchnames_ordered_by_activity(desc):
    with Session.begin() as session:
        if desc:
            return session.query(Branches.name).order_by(sql.desc(Branches.last_activity)).all()
        else:
            return session.query(Branches.name).order_by(Branches.last_activity).all()


def branch_exists_without_origin():
    with Session.begin() as session:
        return session.query(exists().where(Branches.origin_revision == None)).scalar()


def find_first_branch_revision_by_start_date(branch, start_date):
    with Session.begin() as session:
        return session.query(Revisions.hash) \
            .join(Branches, Branches.id == Revisions.affected_branch) \
            .filter(Branches.name == branch) \
            .filter(Revisions.authordate > start_date) \
            .order_by(Revisions.authordate).first()[0]


def branch_exists(branchname):
    with Session.begin() as session:
        return session.query(exists().where(Branches.name == branchname)).scalar()


def get_branch_path_from_start_date_by_branch_id(start_date, branch_id):
    if start_date:
        with Session.begin() as session:
            return session.query(Revisions.hash) \
                .join(Branches, Branches.id == Revisions.affected_branch) \
                .filter(Branches.id == branch_id) \
                .filter(Revisions.authordate < start_date) \
                .order_by(desc(Revisions.authordate)).all()
    else:
        with Session.begin() as session:
            return session.query(Revisions.hash) \
                .join(Branches, Branches.id == Revisions.affected_branch) \
                .filter(Branches.id == branch_id) \
                .order_by(desc(Revisions.authordate)).all()


def revision_of_branch_exists(branch_name):
    with Session.begin() as session:
        if session.query(Revisions.hash)\
                .join(Branches, Branches.id == Revisions.affected_branch)\
                .filter(Branches.name == branch_name)\
                .first():
            return True
        else:
            return False


def get_branch_path_from_start_date_by_branch_name(start_date, branch_name):
    if start_date:
        with Session.begin() as session:
            branch_path_from_start_date = session.query(Revisions.hash) \
                .join(Branches, Branches.id == Revisions.affected_branch) \
                .filter(Branches.name == branch_name) \
                .filter(Revisions.authordate > start_date) \
                .order_by(Revisions.authordate).all()
            if branch_path_from_start_date:
                branch_path_from_start_date = [rev[0] for rev in branch_path_from_start_date]
        return branch_path_from_start_date
    else:
        with Session.begin() as session:
            branch_path_from_start_date = session.query(Revisions.hash) \
                .join(Branches, Branches.id == Revisions.affected_branch) \
                .filter(Branches.name == branch_name) \
                .order_by(Revisions.authordate).all()
            if branch_path_from_start_date:
                branch_path_from_start_date = [rev[0] for rev in branch_path_from_start_date]
        return branch_path_from_start_date
