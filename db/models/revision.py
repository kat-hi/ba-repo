from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Index
from db.models import Base
from db.models.fileRevisionRelation import FileRevisionRelation
from db.models.revisionRelation import RevisionRelations


class Revisions(Base):
    __tablename__ = 'Revisions'
    __table_args__ = (
        Index('RevisionIdx', 'hash', 'affected_branch'),
    )
    hash = Column(String, primary_key=True, index=True, unique=True)
    authordate = Column(String)
    is_merge = Column(Boolean)
    affected_branch = Column(Integer, ForeignKey('Branches.id'))
    related_merge_commit = Column(String, ForeignKey('Revisions.hash'))

    file_revision_child = relationship(FileRevisionRelation)
    effect_child = relationship('RevisionChangedFileEffect')
    branch_child = relationship('Branches', primaryjoin='Revisions.hash == Branches.origin_revision')
    relation_child = relationship(RevisionRelations, primaryjoin='Revisions.hash == RevisionRelations.revision_id')
    relation_child2 = relationship(RevisionRelations, primaryjoin='Revisions.hash == RevisionRelations.parent_id')

    def __init__(self, revision_hash):
        self.hash = revision_hash
