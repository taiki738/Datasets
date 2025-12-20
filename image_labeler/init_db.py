# init_db.py
from app import app, db, _populate_images_from_manifest

print("Starting database initialization...")

with app.app_context():
    print("Creating all database tables...")
    db.create_all()
    print("Database tables created.")
    
    print("Populating images from manifest...")
    _populate_images_from_manifest()
    print("Image population complete.")

print("Database initialization finished.")
