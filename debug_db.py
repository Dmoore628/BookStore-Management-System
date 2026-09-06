from domain_services.database import Base
from domain_services.entities import User
print(f"Base: {Base}")
print(f"Base id: {id(Base)}")
print(f"Base metadata id: {id(Base.metadata)}")
print(f"User.__bases__[0] id: {id(User.__bases__[0])}")
print(f"User.__bases__[0] metadata id: {id(User.__bases__[0].metadata)}")

