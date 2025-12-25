import os
import socket
import qrcode
from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import datetime

project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
app = Flask(__name__, instance_path=os.path.join(project_root, 'instance'))

# Configure the database
database_url = os.environ.get('DATABASE_URL', f'sqlite:///{os.path.join(app.instance_path, "survey.db")}')
app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['R2_BASE_URL'] = 'https://pub-8a092c33fb2543a78b50eceac30fa75d.r2.dev'
db = SQLAlchemy(app)

# Define Database Models
class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    labels = db.relationship('Label', backref='participant', lazy=True)
    # Add nullable fields for demographics
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        return f'<Participant {self.id}>'

class Image(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(120), nullable=False)
    gender = db.Column(db.String(10), nullable=False) # 'male' or 'female'
    url = db.Column(db.String(255), nullable=True) # New field to store the full R2 URL
    labels = db.relationship('Label', backref='image', lazy=True)

    # Add a unique constraint for the combination of filename and gender
    __table_args__ = (db.UniqueConstraint('filename', 'gender', name='_filename_gender_uc'),)

    def __repr__(self):
        return f'<Image {self.filename}>'

class Label(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    participant_id = db.Column(db.Integer, db.ForeignKey('participant.id'), nullable=False)
    image_id = db.Column(db.Integer, db.ForeignKey('image.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # e.g., 1 to 5 for a subjective rating
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Label {self.id} | P:{self.participant_id} I:{self.image_id} R:{self.rating}>'

# The path to the survey images directory (DATASET_PATH is no longer needed as images are from R2)

def _populate_images_from_manifest():
    """
    Reads image filenames from manifest.txt, constructs R2 URLs, and populates
    the Image table in the database.
    """
    manifest_path = os.path.join(os.path.dirname(__file__), 'manifest.txt')
    r2_base_url = app.config['R2_BASE_URL']

    if not os.path.exists(manifest_path):
        print(f"Manifest file not found at {manifest_path}. Image table will not be populated.")
        return

    with app.app_context():
        with open(manifest_path, 'r') as f:
            for line in f:
                relative_path = line.strip()
                if not relative_path:
                    continue

                # The new path is like: male/20-29/asian/14335.png
                # The gender is the first part. The full path is unique.
                parts = relative_path.split('/')
                if len(parts) < 2:
                    print(f"Skipping malformed path in manifest: {relative_path}")
                    continue
                
                gender = parts[0]
                # Use the full relative path as the "filename" to ensure uniqueness
                filename = relative_path
                
                if not any(filename.endswith(ext) for ext in ['.jpg', '.jpeg', '.png']):
                    continue # Only consider image files

                full_r2_url = f"{r2_base_url}/{filename}"

                # Check if image already exists in DB based on the unique full path
                existing_image = Image.query.filter_by(filename=filename, gender=gender).first()
                if not existing_image:
                    new_image = Image(filename=filename, gender=gender, url=full_r2_url)
                    db.session.add(new_image)
                elif existing_image.url != full_r2_url: # Update URL if it changed
                    existing_image.url = full_r2_url
        db.session.commit()
    print("Image table populated/updated from manifest file.")

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/start_survey_session', methods=['POST'])
def start_survey_session():
    """
    Starts a new survey session by creating a new participant and returning a random
    sample of 20 images (10 male, 10 female) to label.
    """
    # Create a new participant
    participant = Participant()
    db.session.add(participant)
    db.session.commit()

    # Get 10 random male images
    male_images = Image.query.filter_by(gender='male').order_by(func.random()).limit(10).all()

    # Get 10 random female images
    female_images = Image.query.filter_by(gender='female').order_by(func.random()).limit(10).all()

    # Combine the lists, male first
    images = male_images + female_images
    
    image_data = [{
        'id': img.id,
        'filename': img.filename,
        'gender': img.gender,
        'url': img.url # Include the URL in the response
    } for img in images]

    return jsonify({
        'participant_id': participant.id,
        'images': image_data
    })

@app.route('/api/submit_survey_label', methods=['POST'])
def submit_survey_label():
    """
    Submits a label for an image by a participant.
    """
    data = request.json
    participant_id = data.get('participant_id')
    image_id = data.get('image_id')
    rating = data.get('rating')

    if not all([participant_id, image_id, rating is not None]):
        return jsonify({'error': 'Missing data'}), 400

    # Validate participant and image
    participant = Participant.query.get(participant_id)
    image = Image.query.get(image_id)

    if not participant:
        return jsonify({'error': 'Participant not found'}), 404
    if not image:
        return jsonify({'error': 'Image not found'}), 404
    
    # Create and save the label
    label = Label(participant_id=participant_id, image_id=image_id, rating=rating)
    db.session.add(label)
    db.session.commit()

    return jsonify({'success': True})

@app.route('/api/submit_demographics', methods=['POST'])
def submit_demographics():
    """
    Submits demographic data for a participant.
    """
    data = request.json
    participant_id = data.get('participant_id')
    age = data.get('age')
    gender = data.get('gender')

    if not participant_id:
        return jsonify({'error': 'Missing participant_id'}), 400

    participant = Participant.query.get(participant_id)
    if not participant:
        return jsonify({'error': 'Participant not found'}), 404
    
    # Update participant with provided data (it's okay if they are None/null)
    if age is not None:
        try:
            participant.age = int(age)
        except (ValueError, TypeError):
            return jsonify({'error': 'Invalid age format'}), 400
            
    participant.gender = gender
    
    db.session.commit()

    return jsonify({'success': True})

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # Call the new image population function
        _populate_images_from_manifest()

    host = '0.0.0.0'
    port = 5001

    ip = ''
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # connect to a public DNS server to get the local IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()

        url = f"http://{ip}:{port}"
        print(f"\nAccess the application at: {url}")
        print("Or scan the QR code below with your phone:")
        
        qr = qrcode.QRCode()
        qr.add_data(url)
        qr.make(fit=True)
        qr.print_tty()
        print("\n")

    except Exception as e:
        print(f"Could not determine local IP address to generate QR code: {e}")
        print(f"Starting server on http://localhost:{port} and http://{host}:{port}")

    app.run(host=host, debug=True, port=port)
