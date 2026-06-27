from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    """
    SQLAlchemy DeclarativeBase class for 2.0 style database models.
    All models must inherit from this class to participate in schema metadata.
    """
    pass
