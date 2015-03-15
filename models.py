from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship, backref
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Person(Base):
    __tablename__ = "person"

    id = Column(Integer, primary_key=True)
    ballot_name = Column(String)
    locality = Column(String)
    party_id = Column(Integer, ForeignKey("party.id"))
    phone = Column(String)
    mobile = Column(String)
    website = Column(String)
    email = Column(String)

    party = relationship("Party", backref=backref("people"))


class District(Base):
    __tablename__ = "district"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Party(Base):
    __tablename__ = "party"

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)


class Group(Base):
    __tablename__ = "group"

    id = Column(Integer, primary_key=True)

    identifier = Column(String)
    name = Column(String)


class LegislativeAssembly(Base):
    __tablename__ = "legislative_assembly"

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("person.id"), nullable=False)
    district_id = Column(Integer, ForeignKey("district.id"), nullable=False)

    person = relationship("Person")
    district = relationship("District")


class LegislativeCouncil(Base):
    __tablename__ = "legislative_council"

    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey("person.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("group.id"))

    person = relationship("Person")
    group = relationship("Group")

