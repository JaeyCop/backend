
from sqlalchemy.orm import Session
from app.models.user_recipe import UserRecipe
from app.schemas.user_recipe import UserRecipeCreate, UserRecipeUpdate

def get_user_recipe(db: Session, user_recipe_id: int):
    return db.query(UserRecipe).filter(UserRecipe.id == user_recipe_id).first()

def get_user_recipes_by_owner(db: Session, owner_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(UserRecipe)
        .filter(UserRecipe.owner_id == owner_id)
        .offset(skip)
        .limit(limit)
        .all()
    )

def create_user_recipe(db: Session, user_recipe: UserRecipeCreate, owner_id: int):
    db_user_recipe = UserRecipe(**user_recipe.dict(), owner_id=owner_id)
    db.add(db_user_recipe)
    db.commit()
    db.refresh(db_user_recipe)
    return db_user_recipe

def update_user_recipe(db: Session, user_recipe_id: int, user_recipe: UserRecipeUpdate):
    db_user_recipe = get_user_recipe(db, user_recipe_id)
    if db_user_recipe:
        update_data = user_recipe.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_user_recipe, key, value)
        db.commit()
        db.refresh(db_user_recipe)
    return db_user_recipe

def delete_user_recipe(db: Session, user_recipe_id: int):
    db_user_recipe = get_user_recipe(db, user_recipe_id)
    if db_user_recipe:
        db.delete(db_user_recipe)
        db.commit()
    return db_user_recipe
