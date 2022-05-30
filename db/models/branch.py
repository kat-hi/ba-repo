from sqlalchemy import Column, Integer, String, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from db.models import Base
from db.models.revisionChangedFileEffect import RevisionChangedFileEffect


class Branches(Base):
    __tablename__ = 'Branches'
    id = Column(Integer, autoincrement=True, primary_key=True)
    name = Column(String, unique=True)
    last_activity = Column(String)
    origin_revision = Column(String, ForeignKey('Revisions.hash'))

    child = relationship('Revisions', primaryjoin='Branches.id == Revisions.affected_branch')
    effect_child = relationship('RevisionChangedFileEffect')

    def __init__(self, name):
        self.name = name