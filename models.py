
from database import Base

from sqlalchemy import Column, Integer, String


class UserDB(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key = True)
    password =  Column(String)
    email = Column(String, unique = True, index = True)
    
class NoteDB(Base):
    __tablename__ = "notes"
    id = Column(Integer, primary_key = True)
    text = Column(String)
    user_id = Column(Integer)



class ProductforsaleDB(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key = True)
    title = Column(String)
    price = Column(Integer)
    user_id = Column(Integer)


class OrderDB(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key = True)
    product_id = Column(Integer)
    user_id = Column(Integer)