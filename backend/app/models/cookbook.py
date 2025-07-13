
from sqlalchemy import Column, Integer, String, ForeignKey, Table
from sqlalchemy.orm import relationship
from app.db.session import Base

cookbook_recipe_association = Table(
    "cookbook_recipe",
    Base.metadata,
    Column("cookbook_id", Integer, ForeignKey("cookbooks.id")),
    Column("recipe_id", Integer, ForeignKey("recipes.id")),
)

class Cookbook(Base):
    __tablename__ = "cookbooks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="cookbooks")
    recipes = relationship(
        "Recipe",
        secondary=cookbook_recipe_association,
        back_populates="cookbooks",
    )
