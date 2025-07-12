from app.db.session import engine, Base
from app.models.recipe import Recipe


def create_tables():
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    create_tables()
