from app.db.session import Base, engine
from app.models import entities  # noqa: F401

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    print("ResumeIQ schema is ready.")
