# src/action_handler.py
import os
from flask import request, jsonify
import stripe
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

# Configure Stripe
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Configure GraphQL client
transport = RequestsHTTPTransport(
    url=os.getenv('HASURA_ENDPOINT'),
    headers={'x-hasura-admin-secret': os.getenv('HASURA_ADMIN_SECRET')}
)
client = Client(transport=transport, fetch_schema_from_transport=True)

def require_action_secret():
    # provided_secret = request.headers.get('ACTION_SECRET')
    # required_secret = os.getenv('ACTION_SECRET')
    # print(f"[DEBUG] All headers: {request.headers}")

    # print(f"[DEBUG] Provided ACTION_SECRET: {provided_secret}")
    # print(f"[DEBUG] Required ACTION_SECRET: {required_secret}")

    # if provided_secret != required_secret:
    #     print("[DEBUG] Unauthorized request: ACTION_SECRET mismatch")
    #     return jsonify({'message': 'Unauthorized'}), 403

    return None


def validate_payment_amount(amount):
    query = gql("""
        query GetPaymentSettings {
            payment_settings {
                min_payment_amount
                max_payment_amount
            }
        }
    """)
    result = client.execute(query)
    settings = result['payment_settings'][0]
    
    if amount < settings['min_payment_amount'] or amount > settings['max_payment_amount']:
        raise ValueError("Payment amount outside allowed range")

def get_conversion_rate():
    query = gql("""
        query GetConversionRate {
            system_settings(where: {key: {_eq: "credit_conversion_rate"}}) {
                value
            }
        }
    """)
    
    result = client.execute(query)
    return float(result['system_settings'][0]['value'])

def create_payment():
    auth_error = require_action_secret()
    if auth_error:
        return auth_error
        
    try:
        # Extract data from Hasura action format
        data = request.json
        print(f"[DEBUG] Request Data: {data}")  # Debug: Check the incoming data
        
        user_id = data['session_variables']['x-hasura-user-id']
        amount = data['input'].get('amount', 100)

        print(f"[DEBUG] User ID: {user_id}, Amount: {amount}")  # Debug: Log user_id and amount
        
        # Validate payment amount
        try:
            validate_payment_amount(amount)
        except ValueError as e:
            print(f"[DEBUG] Validation Error: {str(e)}")  # Debug: Log the error message
            return jsonify({
                "message": str(e),
                "extensions": {
                    "code": "VALIDATION_ERROR",
                    "path": "$.amount"
                }
            }), 400
        
        # Get conversion rate and calculate credits
        conversion_rate = get_conversion_rate()
        credits = amount * conversion_rate
        
        print(f"[DEBUG] Conversion Rate: {conversion_rate}, Credits: {credits}")  # Debug: Log conversion rate and credits
        
        # Create Stripe Checkout Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'hkd',
                    'unit_amount': amount * 100,  # Stripe expects amounts in cents
                    'product_data': {
                        'name': f'{credits} Credits',
                    },
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{os.getenv('FRONTEND_URL')}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{os.getenv('FRONTEND_URL')}/payment/cancel",
            customer_email=data['input'].get('email'),
        )
        
        print(f"[DEBUG] Stripe Checkout Session: {checkout_session}")  # Debug: Log the checkout session
        
        # Create transaction record
        mutation = gql("""
            mutation CreateTransaction(
                $user_id: uuid!,
                $amount: Int!,
                $credits: numeric!,
                $payment_intent_id: String!,
                $checkout_session_id: String!
            ) {
                insert_transactions_one(object: {
                    user_id: $user_id,
                    amount: $amount,
                    credits_amount: $credits,
                    stripe_payment_intent_id: $payment_intent_id,
                    type: "credit_purchase",
                    status: "pending",
                    currency: "HKD"
                }) {
                    id
                }
            }
        """)
        
        variables = {
            "user_id": user_id,
            "amount": amount,
            "credits": credits,
            "payment_intent_id": checkout_session.payment_intent,
            "checkout_session_id": checkout_session.id
        }
        
        print(f"[DEBUG] GraphQL Mutation Variables: {variables}")  # Debug: Log the variables being sent to the mutation
        
        result = client.execute(mutation, variable_values=variables)
        
        print(f"[DEBUG] GraphQL Mutation Result: {result}")  # Debug: Log the result of the mutation
        
        return jsonify({
            "checkout_session_id": checkout_session.id,
            "transaction_id": result['insert_transactions_one']['id']
        })
        
    except Exception as e:
        print(f"[DEBUG] Error: {str(e)}")  # Debug: Log the error message
        return jsonify({
            "message": str(e),
            "extensions": {
                "code": "INTERNAL_ERROR",
                "path": "$"
            }
        }), 400


def setup_autopay():
    auth_error = require_action_secret()
    if auth_error:
        return auth_error

    try:
        data = request.json
        user_id = data['session_variables']['x-hasura-user-id']
        amount = data['input'].get('amount', 100)
        day_of_month = data['input'].get('day_of_month', 1)
        
        # Validate payment amount
        try:
            validate_payment_amount(amount)
        except ValueError as e:
            return jsonify({
                "message": str(e),
                "extensions": {
                    "code": "VALIDATION_ERROR",
                    "path": "$.amount"
                }
            }), 400
        
        # Get or create Stripe customer
        query = gql("""
            query GetClient($user_id: uuid!) {
                clients_by_pk(id: $user_id) {
                    stripe_customer_id
                    email
                }
            }
        """)
        
        result = client.execute(query, variable_values={"user_id": user_id})
        client_data = result['clients_by_pk']
        
        if not client_data['stripe_customer_id']:
            customer = stripe.Customer.create(
                email=client_data['email']
            )
            
            mutation = gql("""
                mutation UpdateClient($user_id: uuid!, $customer_id: String!) {
                    update_clients_by_pk(
                        pk_columns: {id: $user_id}, 
                        _set: {stripe_customer_id: $customer_id}
                    ) {
                        id
                    }
                }
            """)
            
            client.execute(mutation, variable_values={
                "user_id": user_id,
                "customer_id": customer.id
            })
            
            stripe_customer_id = customer.id
        else:
            stripe_customer_id = client_data['stripe_customer_id']
        
        # Create setup intent
        setup_intent = stripe.SetupIntent.create(
            customer=stripe_customer_id,
            payment_method_types=['card'],
        )
        
        # Save payment method with autopay settings
        mutation = gql("""
            mutation UpsertPaymentMethod(
                $user_id: uuid!,
                $amount: numeric!,
                $day: Int!,
                $setup_intent_id: String!
            ) {
                insert_payment_methods_one(
                    object: {
                        user_id: $user_id,
                        auto_pay_amount: $amount,
                        auto_pay_day: $day,
                        auto_pay_enabled: true,
                        stripe_payment_method_id: $setup_intent_id,
                        type: "card"
                    },
                    on_conflict: {
                        constraint: payment_methods_user_id_key,
                        update_columns: [auto_pay_amount, auto_pay_day, stripe_payment_method_id]
                    }
                ) {
                    uuid
                }
            }
        """)
        
        variables = {
            "user_id": user_id,
            "amount": amount,
            "day": day_of_month,
            "setup_intent_id": setup_intent.id
        }
        
        result = client.execute(mutation, variable_values=variables)
        
        return jsonify({
            "client_secret": setup_intent.client_secret,
            "setup_intent_id": setup_intent.id
        })
        
    except Exception as e:
        return jsonify({
            "message": str(e),
            "extensions": {
                "code": "INTERNAL_ERROR",
                "path": "$"
            }
        }), 400