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
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///survey.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
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
    filename = db.Column(db.String(120), unique=True, nullable=False)
    gender = db.Column(db.String(10), nullable=False) # 'male' or 'female'
    labels = db.relationship('Label', backref='image', lazy=True)

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

# The path to the filtered_dataset directory
DATASET_PATH = '/home/tm/img-science/github/Datasets/UTK-FACE/filtered_dataset'

def _populate_images_from_filesystem():
    """
    Scans the DATASET_PATH for images and populates the Image table in the database
    if they don't already exist.
    """
    with app.app_context():
        for gender in ['male', 'female']:
            gender_path = os.path.join(DATASET_PATH, gender)
            if os.path.exists(gender_path):
                for filename in os.listdir(gender_path):
                    if filename.endswith(('.jpg', '.jpeg', '.png')): # Only consider image files
                        # Check if image already exists in DB
                        existing_image = Image.query.filter_by(filename=filename, gender=gender).first()
                        if not existing_image:
                            new_image = Image(filename=filename, gender=gender)
                            db.session.add(new_image)
        db.session.commit()
    print("Image table populated/updated from filesystem.")


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
        'gender': img.gender
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

@app.route('/images/<gender>/<path:filename>')
def serve_image(gender, filename):
    """
    Serves the image from the specified gender directory.
    """
    image_dir = os.path.join(DATASET_PATH, gender)
    return send_from_directory(image_dir, filename)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        # _populate_images_from_filesystem() is called within the app context now
    
    # Run image population once at startup
    _populate_images_from_filesystem()

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
