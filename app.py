from firebase_admin import initialize_app, credentials, messaging, firestore 
from flask import Flask, jsonify, request
from flask_cors import CORS
import os
import json
from dotenv import load_dotenv
load_dotenv()


# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=['http://localhost:3000',"https://fyp-frontend-lake.vercel.app"])


def create_keyfile_dict():
    # Construct the Firebase credentials dictionary from environment variables
    variables_keys = {
        "type": os.getenv("TYPE"),
        "project_id": os.getenv("PROJECT_ID"),
        "private_key_id": os.getenv("PRIVATE_KEY_ID"),
        "private_key": os.getenv("PRIVATE_KEY"),
        "client_email": os.getenv("CLIENT_EMAIL"),
        "client_id": os.getenv("CLIENT_ID"),
        "auth_uri": os.getenv("AUTH_URI"),
        "token_uri": os.getenv("TOKEN_URI"),
        "auth_provider_x509_cert_url": os.getenv("AUTH_PROVIDER_X509_CERT_URL"),
        "client_x509_cert_url": os.getenv("CLIENT_X509_CERT_URL")
    }
    return variables_keys

cred_dict = create_keyfile_dict()    

# Initialize Firebase Admin
cred = credentials.Certificate(cred_dict)
firebase_app = initialize_app(cred)
db = firestore.client()

@app.route('/')
def index():
    return jsonify({'message': 'Flask + Firebase API is running!'})

def send_notification_util(token, title, body, link='https://fyp-frontend-lake.vercel.app'):
    try:
        message = messaging.Message(
            notification=messaging.Notification(
                title=title,
                body=body
            ),
            token=token,
            webpush=messaging.WebpushConfig(
                fcm_options=messaging.WebpushFCMOptions(
                    link=link
                )
            )
        )
        response = messaging.send(message)
        return response
    except Exception as e:
        return str(e)

@app.route('/api/toggle-light', methods=['POST'])
def toggle_light():
    try:
        data = request.json
        home_id = data.get('home_id')

        print(home_id)
        if not home_id:
            return jsonify({'error': 'Missing home_id'}), 400

        home_ref = db.collection('Home').document(home_id)
        home = home_ref.get()

        if not home.exists:
            return jsonify({'error': 'Home not found'}), 404

        home_data = home.to_dict()
        push_token = home_data.get('push_token', '')

        if not push_token:
            return jsonify({'error': 'No push token found'}), 404

        current_light_status = home_data.get('light', False)
        new_light_status = not current_light_status

        # Update Firestore
        home_ref.update({'light': new_light_status})

        # Send push notification
        response = send_notification_util(
            token=push_token,
            title="Light Status",
            body=f"The light has been turned {'ON' if new_light_status else 'OFF'}"
        )

        return jsonify({
            'message': f'Light is now {"ON" if new_light_status else "OFF"}',
            'new_status': new_light_status,
            'firebase_response': response
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/send-noti', methods=['POST'])
def simulate_prediction():
    try:
        data = request.json
        home_id = data.get('home_id')

        if not home_id:
            return jsonify({'error': 'Missing home_id'}), 400

        home_ref = db.collection('Home').document(home_id)
        home = home_ref.get()
        
        if not home.exists:
            return jsonify({'error': 'Home not found'}), 404

        home_data = home.to_dict()
        push_token = home_data.get('push_token', '')

        if not push_token:
            return jsonify({'error': 'No push token found'}), 404

        # Update light value to True
        home_ref.update({'light': True})

        # Send push notification
        response = send_notification_util(
            token=push_token,
            title="Light Status",
            body="The light has been turned ON"
        )

        return jsonify({
            'message': 'Light is turned on. Notification sent.',
            'firebase_response': response
        }), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
