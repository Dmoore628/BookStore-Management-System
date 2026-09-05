from bookstore.database import Base
from bookstore.models.entities import User
print(f"Base: {Base}")
print(f"Base id: {id(Base)}")
print(f"Base metadata id: {id(Base.metadata)}")
print(f"User.__bases__[0] id: {id(User.__bases__[0])}")
print(f"User.__bases__[0] metadata id: {id(User.__bases__[0].metadata)}")
