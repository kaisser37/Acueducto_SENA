from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


# DATABASE_URL = "mysql+pymysql://root:@localhost/acueducto"
DATABASE_URL = "mysql+pymysql://u8ipn0etdx6mbbdj:WBJLHfFZ6B8OMCt0AUET@bodq85raah3zklzgvwrj-mysql.services.clever-cloud.com:3306/bodq85raah3zklzgvwrj"

engine = create_engine(DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_database():
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
