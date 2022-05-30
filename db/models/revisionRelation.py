from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, Index
from db.models import Base


class RevisionRelations(Base):
    __tablename__ = 'RevisionRelations'
    __table_args__ = (
        Index('RevisionRelationIdx', 'revision_id', 'parent_id', 'is_first_parent'),
    )
    id = Column(Integer, autoincrement=True, primary_key=True)
    revision_id = Column(String, ForeignKey('Revisions.hash'))
    parent_id = Column(String, ForeignKey('Revisions.hash'))
    is_first_parent = Column(Boolean)

    def __init__(self, revision_hash, parent_hash, is_first_parent):
        self.revision_id = revision_hash
        self.parent_id = parent_hash
        self.is_first_parent = is_first_parent
