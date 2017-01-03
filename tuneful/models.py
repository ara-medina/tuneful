import os.path

from flask import url_for
from sqlalchemy import Column, Integer, String, Sequence, ForeignKey
from sqlalchemy.orm import relationship

from tuneful import app
from .database import Base, engine



class File(Base):
    __tablename__ = "file"
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    
    song = relationship("Song", uselist=False, backref="file")
    
    def as_dictionary(self):
        file = {
            "id": self.id,
            "name": self.name,
        }
        
class Song(Base):
    __tablename__ = "song"
    
    id = Column(Integer, primary_key=True)
    
    file_id = Column(Integer, ForeignKey="file.id", nullable=False)
    
    def as_dictionary(self):
        song = {
            "id": self.id,
            "file": {
                "id": self.file.id,
                "name": self.file.name
            }
        }
        
        
    # file.song.id 
    # song.file.id
    # song.file.name
    # song.id
    # file.id