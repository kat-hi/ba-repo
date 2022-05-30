from sqlalchemy import Column, Integer, ForeignKey, String, UniqueConstraint

from db.models import Base
from db.models.file import Files
from db.models.revision import Revisions


class RevisionChangedFileEffect(Base):
    __tablename__ = 'Revision_ChangedFile_Effect'
    __table_args__ = (
        UniqueConstraint('file_id', 'revision_hash', name='unique file effect'),
    )
    id = Column(Integer, autoincrement=True, primary_key=True)
    branch_id = Column(Integer, ForeignKey('Branches.id'))
    revision_hash = Column(String, ForeignKey(Revisions.hash))
    fileversion_id = Column(Integer, ForeignKey('Fileversion.id'))
    file_id = Column(Integer, ForeignKey(Files.id))
    LOC_delta = Column(Integer)
    Comments_delta = Column(Integer)

    def __init__(self, revision_hash, branch_id, fileversion_id, file_id):
        self.revision_hash = revision_hash
        self.file_id = file_id
        self.fileversion_id = fileversion_id
        self.branch_id = branch_id
