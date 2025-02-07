# TCS Payment Service

A serverless payment processing service built with Python, Flask, and Stripe, deployed on AWS Lambda through the Serverless Framework. This service handles payment processing and credit system integration for Tiger Campus Services.

## Features

- 💳 Stripe payment processing with checkout sessions
- 📊 Credit purchase system with configurable conversion rates
- 💰 Autopay setup functionality
- 🪝 Stripe webhook handling
- 🔐 Secure API endpoints with action secrets
- 📡 Hasura GraphQL integration

## Prerequisites

- Python 3.8+
- Node.js 14+
- AWS CLI configured
- Stripe account
- Hasura instance

## Installation

1. Clone the repository and navigate to the project:
```bash
git clone [repository-url]
cd tcs-payment-service
```

2. Create and activate Python virtual environment:
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install flask stripe gql requests
pip freeze > requirements.txt
```

4. Install Serverless Framework and plugins:
```bash
npm install -g serverless
npm install --save-dev serverless-python-requirements serverless-wsgi
```

## Database Schema

### Clients Table
```sql
CREATE TABLE clients (
    id uuid PRIMARY KEY,
    stripe_customer_id TEXT UNIQUE,
    email TEXT NOT NULL,
    credits_balance NUMERIC DEFAULT 0
);
```

### Transactions Table
```sql
CREATE TABLE transactions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES clients(id),
    amount INTEGER NOT NULL,
    credits_amount NUMERIC NOT NULL,
    stripe_payment_intent_id TEXT,
    checkout_session_id TEXT,
    type TEXT NOT NULL,
    status TEXT NOT NULL,
    currency TEXT NOT NULL,
    receipt_url TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Payment Methods Table
```sql
CREATE TABLE payment_methods (
    uuid uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id uuid REFERENCES clients(id),
    type TEXT NOT NULL,
    auto_pay_amount NUMERIC,
    auto_pay_day INTEGER,
    auto_pay_enabled BOOLEAN DEFAULT false,
    stripe_payment_method_id TEXT,
    CONSTRAINT payment_methods_user_id_key UNIQUE (user_id)
);
```

### System Settings Table
```sql
CREATE TABLE system_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
```

### Payment Settings Table
```sql
CREATE TABLE payment_settings (
    min_payment_amount INTEGER NOT NULL,
    max_payment_amount INTEGER NOT NULL
);
```

## Project Structure
```
tcs-payment-service/
├── venv/
├── node_modules/
├── src/
│   ├── __init__.py
│   ├── action_handler.py
│   └── webhook_handler.py
├── serverless.yml
├── requirements.txt
├── package.json
├── package-lock.json
└── .env
```

## API Endpoints

### Payment Processing
- **URL**: `/create-payment`
- **Method**: POST
- **Headers**: `ACTION-SECRET`
- **Purpose**: Creates Stripe checkout session for credit purchases
- **Request Body**:
```json
{
    "input": {
        "amount": 100,
        "email": "user@example.com"
    },
    "session_variables": {
        "x-hasura-user-id": "uuid"
    }
}
```

### Autopay Setup
- **URL**: `/setup-autopay`
- **Method**: POST
- **Headers**: `ACTION-SECRET`
- **Purpose**: Sets up recurring payments
- **Request Body**:
```json
{
    "input": {
        "amount": 100,
        "day_of_month": 1
    },
    "session_variables": {
        "x-hasura-user-id": "uuid"
    }
}
```

### Webhook Handler
- **URL**: `/stripe-webhook`
- **Method**: POST
- **Purpose**: Processes Stripe webhook events
- **Security**: Validates Stripe signature

## Environment Variables

```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Hasura Configuration
HASURA_ENDPOINT=https://your-hasura-endpoint/v1/graphql
HASURA_ADMIN_SECRET=your-hasura-admin-secret

# Frontend Configuration
FRONTEND_URL=https://your-frontend-url

# Action Security
ACTION_SECRET=your-action-secret
```

## Deployment

1. Configure AWS credentials:
```bash
aws configure
```

2. Deploy to AWS:
```bash
serverless deploy
```

## Local Development

1. Start local development server:
```bash
serverless wsgi serve
```

2. Test webhook handling using Stripe CLI:
```bash
stripe listen --forward-to localhost:5000/stripe-webhook
```

## Testing

1. Install test dependencies:
```bash
pip install pytest pytest-mock
```

2. Run tests:
```bash
pytest
```

## Security Implementations

1. Webhook signature verification
2. Action secret validation
3. Payment amount validation
4. Secure customer data handling
5. Transaction status tracking

## Monitoring

- Monitor Lambda functions in AWS CloudWatch
- View webhook events in Stripe Dashboard
- Check logs using:
```bash
serverless logs -f app
```

## Common Issues

1. **Webhook Processing Issues**
   - Verify Stripe webhook secret
   - Check webhook signature headers
   - Monitor webhook logs
   - Verify transaction status updates

2. **Payment Processing Issues**
   - Check Stripe API key configuration
   - Verify payment amount validation
   - Monitor checkout session creation
   - Check credit conversion calculations

3. **Database Integration Issues**
   - Verify Hasura endpoint configuration
   - Check GraphQL mutation responses
   - Monitor transaction records
   - Verify credit balance updates

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## Support

For support:
- Create GitHub issue
- Contact development team
- Check documentation

## License

[Your License Here]

## Documentation Updates

Last updated: February 2025
Version: 1.0.0

For more detailed documentation:
- Stripe API Documentation
- Hasura Documentation
- AWS Lambda Documentation
- Serverless Framework Documentation