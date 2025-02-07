# src/app.py
from flask import Flask
app = Flask(__name__)

# Import all the route functions
from .action_handler import create_payment, setup_autopay, require_action_secret
from .webhook_handler import stripe_webhook

# Register the routes
app.add_url_rule('/create-payment', 'create_payment', create_payment, methods=['POST'])
app.add_url_rule('/setup-autopay', 'setup_autopay', setup_autopay, methods=['POST'])
app.add_url_rule('/stripe-webhook', 'stripe_webhook', stripe_webhook, methods=['POST'])

if __name__ == '__main__':
    app.run(debug=True, port=5001)