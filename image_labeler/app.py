import os
import socket
import qrcode
from flask import Flask, render_template, jsonify, request, send_from_directory

app = Flask(__name__)

# The path to the filtered_dataset directory
DATASET_PATH = '/home/tm/img-science/Datasets/UTK-FACE/filtered_dataset'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/images/<gender>')
def get_images(gender):
    """
    Returns a list of image filenames for the specified gender.
    """
    image_dir = os.path.join(DATASET_PATH, gender)
    
    # Create kept and discarded directories if they don't exist
    os.makedirs(os.path.join(image_dir, 'kept'), exist_ok=True)
    os.makedirs(os.path.join(image_dir, 'discarded'), exist_ok=True)

    # Get list of images that are not in kept or discarded folders yet
    images = [f for f in os.listdir(image_dir) if os.path.isfile(os.path.join(image_dir, f))]
    
    return jsonify(images)

@app.route('/api/label', methods=['POST'])
def label_image():
    """
    Moves the image to the 'kept' or 'discarded' folder based on the label.
    """
    data = request.json
    image_name = data.get('image')
    gender = data.get('gender')
    label = data.get('label')

    if not all([image_name, gender, label]):
        return jsonify({'error': 'Missing data'}), 400

    source_dir = os.path.join(DATASET_PATH, gender)
    
    if label == 'keep':
        dest_dir = os.path.join(source_dir, 'kept')
    elif label == 'discard':
        dest_dir = os.path.join(source_dir, 'discarded')
    else:
        return jsonify({'error': 'Invalid label'}), 400

    source_path = os.path.join(source_dir, image_name)
    dest_path = os.path.join(dest_dir, image_name)

    try:
        os.rename(source_path, dest_path)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/images/<gender>/<path:filename>')
def serve_image(gender, filename):
    """
    Serves the image from the specified gender directory.
    """
    image_dir = os.path.join(DATASET_PATH, gender)
    return send_from_directory(image_dir, filename)

if __name__ == '__main__':
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
