from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from db import Photo  # Import your Photo class here

# Replace 'YourDatabaseURL' with the actual database URL
engine = create_engine('instance/database.db')
Session = sessionmaker(bind=engine)
session = Session()

try:
    # Delete all records from the Photo class
    session.query(Photo).delete()
    session.commit()
    print("All data from the Photo class deleted successfully.")
except Exception as e:
    print("An error occurred:", str(e))
    session.rollback()
finally:
    session.close()
