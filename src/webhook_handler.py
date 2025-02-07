import os
from flask import Flask, request, jsonify
import stripe
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Initialize Flask
app = Flask(__name__)

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')

# Configure GraphQL client
transport = RequestsHTTPTransport(
    url=os.getenv('HASURA_ENDPOINT'),
    headers={'x-hasura-admin-secret': os.getenv('HASURA_ADMIN_SECRET')}
)
client = Client(transport=transport, fetch_schema_from_transport=True)

@app.route('/stripe-webhook', methods=['POST'])
def stripe_webhook():
    print("Webhook received!")  # Basic debug print
    print("Request JSON:", request.get_json())  # Print the incoming JSON
    payload = request.get_data()
    sig_header = request.headers.get('stripe-signature')
    
    # Debugging prints
    print("Payload:", payload)
    print("Stripe Signature Header:", sig_header)

    # If signature is missing, return an error
    if not sig_header:
        print("Missing stripe-signature header")
        return jsonify({'error': 'Missing Stripe signature'}), 400
    
    try:
        # Construct the event with the signature
        event = stripe.Webhook.construct_event(payload, sig_header, WEBHOOK_SECRET)
        print("Event successfully constructed:", event)
    except ValueError as e:
        print("Invalid payload error:", str(e))
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError as e:
        print("Signature verification error:", str(e))
        return jsonify({'error': 'Invalid signature'}), 400

    # Handle the event
    if event.type == 'payment_intent.succeeded':
        payment_intent = event.data.object
        print("Payment Intent:", payment_intent)

        # Update transaction status in GraphQL
        mutation = gql("""
            mutation UpdateTransaction($payment_id: String!, $status: String!, $receipt_url: String!) {
                update_transactions(
                    where: {stripe_payment_intent_id: {_eq: $payment_id}},
                    _set: {
                        status: $status,
                        receipt_url: $receipt_url,
                        updated_at: "now()"
                    }
                ) {
                    affected_rows
                    returning {
                        id
                        user_id
                        credits_amount
                    }
                }
            }
        """)

        try:
            variables = {
                "payment_id": payment_intent.id,
                "status": "completed",
                "receipt_url": payment_intent.charges.data[0].receipt_url if payment_intent.charges.data else None
            }

            result = client.execute(mutation, variable_values=variables)
            print("GraphQL result:", result)

            # If transaction was updated, update user's credits
            if result['update_transactions']['affected_rows'] > 0:
                transaction = result['update_transactions']['returning'][0]

                credit_mutation = gql("""
                    mutation UpdateUserCredits($user_id: uuid!, $credits: numeric!) {
                        update_clients(
                            where: {id: {_eq: $user_id}},
                            _inc: {credits_balance: $credits}
                        ) {
                            affected_rows
                        }
                    }
                """)

                client.execute(credit_mutation, variable_values={
                    "user_id": transaction['user_id'],
                    "credits": transaction['credits_amount']
                })

        except Exception as e:
            print("Error updating transaction:", str(e))
            return jsonify({'error': 'Database update failed'}), 500

    return jsonify({'received': True}), 200
