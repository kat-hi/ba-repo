from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String

from db.models import Base


class Files(Base):
    __tablename__ = 'Files'
    id = Column(Integer, autoincrement=True, primary_key=True)
    relative_filepath = Column(String, unique=True)

    changedFiles = relationship('Fileversion')
    effect_child = relationship('RevisionChangedFileEffect')

    def __init__(self, relative_filepath):
        self.relative_filepath = relative_filepath