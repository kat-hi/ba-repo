from sqlalchemy import desc, exists, func
from db.models.branch import Branches
from db.models.file import Files
from db.models.fileRevisionRelation import FileRevisionRelation
from db.models.fileversion import Fileversion
from db.models.revision import Revisions
from db.models.revisionRelation import RevisionRelations
from entry import Session


def get_or_create_file_id(relative_filepath):
    with Session.begin() as session:
        file_id = session.query(Files.id).filter_by(relative_filepath=relative_filepath).first()
        if not file_id:
            db_file = Files(relative_filepath)
            session.add(db_file)
            session.flush()
            session.refresh(db_file)
            file_id = db_file.id
        else:
            file_id = file_id[0]
        return file_id


def find_parent_file_version_metrics(file_id, first_parent):
    with Session.begin() as session:
        parent_file_version = session.query(Fileversion.LOC, Fileversion.Comments) \
            .join(Files, Files.id == Fileversion.file_id) \
            .filter(Files.id == file_id) \
            .join(FileRevisionRelation, FileRevisionRelation.fileversion_id == Fileversion.id) \
            .join(Revisions, Revisions.hash == FileRevisionRelation.revision_hash) \
            .filter(Revisions.hash == first_parent).first()
        if parent_file_version:
            return parent_file_version


def get_first_parent_hash(revision):
    with Session.begin() as session:
        first_parent = session.query(RevisionRelations.parent_id) \
            .filter(RevisionRelations.revision_id == revision) \
            .filter(RevisionRelations.is_first_parent == True) \
            .first()
        if first_parent:
            return first_parent[0]


def get_filerevision_relation_before_date(author_date, file_id):
    with Session.begin() as session:
        return session.query(FileRevisionRelation.revision_hash) \
            .join(Fileversion, Fileversion.id == FileRevisionRelation.fileversion_id) \
            .filter(Fileversion.content_modified_at < author_date) \
            .join(Files, Fileversion.file_id == Files.id) \
            .filter(Fileversion.file_id == file_id) \
            .join(Revisions, Revisions.hash == FileRevisionRelation.revision_hash) \
            .filter(Revisions.authordate < author_date).order_by(desc(Revisions.authordate)).all()


def find_parent_hashes_by_revision(revision):
    with Session.begin() as session:
        parents = session.query(RevisionRelations.parent_id).filter(RevisionRelations.revision_id == revision).all()
        return [parent[0] for parent in parents]


def find_all_revisions_by_branch_id(branch_id, order_desc=True):
    with Session.begin() as session:
        if order_desc:
            db_revisions = session.query(Revisions.hash).filter(Revisions.affected_branch == branch_id).order_by(
                desc(Revisions.authordate)).all()
        else:
            db_revisions = session.query(Revisions.hash).filter(Revisions.affected_branch == branch_id).order_by(
                Revisions.authordate).all()
        revisions = [revision[0] for revision in db_revisions]
        return revisions


def find_all_revisions_by_branch_name(branchname):
    with Session.begin() as session:
        db_revisions = session.query(Revisions.hash).join(Branches, Revisions.affected_branch == Branches.id).filter(
            Branches.name == branchname).filter(Revisions.affected_branch == Branches.id).order_by(
            desc(Revisions.authordate)).all()
        revisions = [revision[0] for revision in db_revisions]
        return revisions


def find_path_to_origin_by_branch(branchname):
    with Session.begin() as session:
        branch_id = session.query(Branches.id).filter(Branches.name == branchname).first()[0]
        mainpath = session.query(Revisions.hash) \
            .filter(Revisions.affected_branch == branch_id) \
            .order_by(desc(Revisions.authordate)) \
            .all()

        return [hash[0] for hash in mainpath]


def find_recent_file_revision_relation(session, relative_path, revision_date):
    session.begin_nested()
    filerevision_relation_parent = \
        session.query(FileRevisionRelation.revision_hash) \
            .join(Fileversion, FileRevisionRelation.fileversion_id == Fileversion.id) \
            .join(Files, Files.id == Fileversion.file_id) \
            .filter(Files.relative_filepath == relative_path) \
            .filter(Fileversion.content_modified_at < revision_date) \
            .order_by(desc(Fileversion.content_modified_at)).first()
    session.commit()
    if filerevision_relation_parent:
        return filerevision_relation_parent[0]


def find_second_parent_by_merge_hash(revision_hash, affected_branch_id):
    with Session.begin() as session:
        parents = session.query(RevisionRelations.parent_id).filter(
            RevisionRelations.revision_id == revision_hash).all()
        for parent_hash in parents:
            parent_revision = session.query(Revisions).filter(Revisions.hash == parent_hash[0]).first()
            if parent_revision:
                if not parent_revision.affected_branch == affected_branch_id:
                    return parent_hash[0]
            else:
                # parents cannot be found sometimes if deleted branches are not included
                print(f'parent not found: {revision_hash}')

def is_merge_commit(revision):
    with Session.begin() as session:
        return session.query(Revisions.is_merge).filter(Revisions.hash == revision).first()


def file_exists(relative_filepath):
    with Session.begin() as session:
        return session.query(exists().where(Files.relative_filepath == relative_filepath)).scalar()


def revision_exists(revision):
    with Session.begin() as session:
        return session.query(exists().where(Revisions.hash == revision)).scalar()


def parent_fileversion_exists(revision_hash, fileid):
    with Session.begin() as session:
        return session.query(Fileversion.id).join(FileRevisionRelation) \
            .filter(FileRevisionRelation.revision_hash == revision_hash) \
            .filter(Fileversion.file_id == fileid).first()


def find_fileversion_id_by_revision(revision_hash, fileid):
    with Session.begin() as session:
        return session.query(Fileversion.id).join(FileRevisionRelation) \
            .filter(FileRevisionRelation.revision_hash == revision_hash) \
            .filter(Fileversion.file_id == fileid).first()


def find_changed_fileversions_by_revision(revision):
    with Session.begin() as session:
        return session.query(Fileversion.id, Fileversion.file_id, Fileversion.LOC,
                             Fileversion.Comments, Fileversion.modification) \
            .join(Files, Files.id == Fileversion.file_id) \
            .join(FileRevisionRelation, FileRevisionRelation.fileversion_id == Fileversion.id) \
            .filter(FileRevisionRelation.revision_hash == revision).all()


def get_authordate(revision_hash):
    with Session.begin() as session:
        return session.query(Revisions.authordate).filter(Revisions.hash == revision_hash).first()[0]


def find_revisions_of_context(context_id):
    with Session.begin() as session:
        result = session.query(Revisions.hash).filter(Revisions.affected_branch == context_id).order_by(
            desc(Revisions.authordate)).all()
        if result:
            return [r[0] for r in result]


def find_metrics_of_fileversion_in_branch_before_date(file_id, date, branch_id):
    with Session.begin() as session:
        return session.query(Fileversion.LOC, Fileversion.Comments) \
            .join(Files, Fileversion.file_id == Files.id) \
            .filter(Files.id == file_id) \
            .join(FileRevisionRelation, FileRevisionRelation.fileversion_id == Fileversion.id) \
            .join(Revisions, Revisions.hash == FileRevisionRelation.revision_hash) \
            .filter(Revisions.authordate < date) \
            .join(Branches, Revisions.affected_branch == Branches.id) \
            .filter(Branches.id == branch_id) \
            .order_by(desc(Revisions.authordate)).first()


def find_fileversion_metrics(fileversion_id):
    with Session.begin() as session:
        return session.query(Fileversion.LOC, Fileversion.Comments) \
            .filter(Fileversion.id == fileversion_id).first()
