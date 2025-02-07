Here's a comprehensive README.md:

```markdown
# TCS Payment Service

A serverless payment processing service built with Python, Flask, and Stripe, deployed on AWS Lambda through the Serverless Framework. This service handles payment processing, subscription management, and credit system integration for Tiger Campus Services.

## Features

- 💳 Stripe payment processing
- 📊 Credit system management
- 🔄 Subscription handling
- 🪝 Webhook processing
- 🔐 Secure API endpoints
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

## Configuration

1. Create `.env` file in project root:
```bash
# Stripe Configuration
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Hasura Configuration
HASURA_ENDPOINT=https://api.dev.tcs.tigercampus.com/v1/graphql
HASURA_ADMIN_SECRET=your_hasura_admin_secret

# Action Secret
ACTION_SECRET=your_custom_action_secret

# Business Logic Configuration
CREDIT_CONVERSION_RATE=1

# Stripe Price IDs
STRIPE_PRICE_ID_100=price_xxx
STRIPE_PRICE_ID_200=price_yyy
```

2. Create Hasura tables:

### Customers Table
```sql
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    stripe_customer_id TEXT UNIQUE NOT NULL,
    credits INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Payments Table
```sql
CREATE TABLE payments (
    id SERIAL PRIMARY KEY,
    payment_id TEXT UNIQUE NOT NULL,
    customer_id TEXT REFERENCES customers(stripe_customer_id),
    status TEXT NOT NULL,
    amount DECIMAL(10,2) NOT NULL,
    credits INTEGER NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Subscriptions Table
```sql
CREATE TABLE subscriptions (
    id SERIAL PRIMARY KEY,
    subscription_id TEXT UNIQUE NOT NULL,
    customer_id TEXT REFERENCES customers(stripe_customer_id),
    status TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Project Structure
```
tcs-payment-service/
├── venv/
├── node_modules/
├── src/
│   ├── __init__.py
│   └── app.py
├── serverless.yml
├── requirements.txt
├── package.json
├── package-lock.json
└── .env
```

## API Endpoints

### Stripe Webhook Handler
- **URL**: `/webhook`
- **Method**: POST
- **Purpose**: Processes Stripe webhook events (payments, subscriptions)

### Payment Actions
- **URL**: `/create-payment`
- **Method**: POST
- **Headers**: `Action-Secret`
- **Purpose**: Creates new payment intents

### Subscription Actions
- **URL**: `/setup-subscription`
- **Method**: POST
- **Headers**: `Action-Secret`
- **Purpose**: Sets up new subscriptions

- **URL**: `/get-subscription`
- **Method**: POST
- **Headers**: `Action-Secret`
- **Purpose**: Retrieves subscription status

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
stripe listen --forward-to localhost:5000/webhook
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

## Monitoring

- Monitor Lambda functions in AWS CloudWatch
- View webhook events in Stripe Dashboard
- Check logs using:
```bash
serverless logs -f app
```

## Security Considerations

- Store sensitive data in AWS Secrets Manager
- Validate Stripe webhook signatures
- Use environment variables for secrets
- Implement rate limiting
- Regular security audits
- Keep dependencies updated

## Common Issues

1. **Deployment Failures**
   - Ensure AWS credentials are configured
   - Check Lambda function permissions
   - Verify memory/timeout settings

2. **Webhook Issues**
   - Verify Stripe webhook secret
   - Check webhook URL accessibility
   - Monitor webhook logs

## Contributing

1. Fork the repository
2. Create feature branch
3. Commit changes
4. Push to branch
5. Create Pull Request

## License

[Your License Here]

## Support

For support:
- Create GitHub issue
- Contact development team
- Check documentation

## Authors

[Your Name/Team]
```

Would you like me to explain any specific section in more detail or add additional information?