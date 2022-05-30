from sqlalchemy import Column, Integer, ForeignKey, String, Boolean, Index
from db.models import Base
from db.models.fileversion import Fileversion


class FileRevisionRelation(Base):
    __tablename__ = 'FileRevisionRelation'
    __table_args__ = (
        Index('FileRevisionRelationIdx', 'id', 'revision_hash', 'fileversion_id'),
    )
    id = Column(Integer, autoincrement=True, primary_key=True)
    revision_hash = Column(Integer, ForeignKey('Revisions.hash'))
    fileversion_id = Column(Integer, ForeignKey(Fileversion.id))

    def __init__(self, revision_hash, fileversion_id):
        self.revision_hash = revision_hash
        self.fileversion_id = fileversion_id
