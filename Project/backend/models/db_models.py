from sqlalchemy import Column, String, Float, Integer, Text
from database import Base

class Assessment(Base):
    __tablename__ = 'assessments'
    id = Column(String, primary_key=True)
    timestamp = Column(String)
    name = Column(String)
    location = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    roof_type = Column(String)
    roof_area = Column(Float)
    soil_type = Column(String)
    groundwater_depth = Column(Float)
    num_people = Column(Integer)
    open_space_area = Column(Float)
    annual_runoff_volume = Column(Float)
    annual_recharge_potential = Column(Float)
    recommended_structure = Column(String)
    estimated_cost = Column(Float)
    payback_period = Column(Float)
    full_response_json = Column(Text)
