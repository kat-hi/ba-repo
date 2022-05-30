from sqlalchemy import Column, Integer, ForeignKey, String, UniqueConstraint, Index
from sqlalchemy.orm import relationship

from db.models import Base
from db.models.file import Files


class Fileversion(Base):
    __tablename__ = 'Fileversion'
    __table_args__ = (
        Index('FileversionIdx', 'id', 'file_id'),
    )
    id = Column(Integer, autoincrement=True, primary_key=True)
    file_modified_at = Column(String)  # commit date
    file_id = Column(Integer, ForeignKey(Files.id))
    modification = Column(String)
    LOC = Column(Integer)
    Comments = Column(Integer)

    effect_child = relationship('RevisionChangedFileEffect')
    fileversion_id_child = relationship('FileRevisionRelation')

    def __init__(self, modification_code, file_id, file_modified_at, LOC, Comments):
        self.modification = modification_code
        self.file_id = file_id
        self.file_modified_at = file_modified_at
        self.LOC = LOC
        self.Comments = Comments