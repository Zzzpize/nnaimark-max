from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, index=True)
    max_user_id = Column(String, unique=True, index=True)
    roadmaps = relationship("Roadmap", back_populates="owner")

class Roadmap(Base):
    __tablename__ = 'roadmaps'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    owner_id = Column(Integer, ForeignKey('users.id'))
    owner = relationship("User", back_populates="roadmaps")
    steps = relationship(
        "RoadmapStep",
        primaryjoin="and_(Roadmap.id==RoadmapStep.roadmap_id, RoadmapStep.parent_id==None)",
        back_populates="roadmap",
        cascade="all, delete-orphan"
    )

class RoadmapStep(Base):
    __tablename__ = 'roadmap_steps'
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(String, default="green")
    is_done = Column(Boolean, default=False)
    
    roadmap_id = Column(Integer, ForeignKey('roadmaps.id'))
    roadmap = relationship("Roadmap", back_populates="steps")

    parent_id = Column(Integer, ForeignKey('roadmap_steps.id'))
    children = relationship(
        "RoadmapStep",
        backref=backref('parent', remote_side=[id]),
        cascade="all, delete-orphan"
    )