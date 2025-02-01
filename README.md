# Solana Vanity Address Generator API

This is a simple Flask-based API that allows you to generate Solana keypairs with a custom prefix or suffix using the `solana-keygen grind` command.

## How It Works
The user provides a prefix (e.g., "bob") and specifies whether the address should start or end with that prefix. The API uses the `solana-keygen grind` command to generate a keypair that matches the prefix. The API is rate-limited to one request per day per user IP.

## API Endpoint

### POST /generate-wallet

Generates a Solana keypair based on the provided prefix and whether it should start or end with that prefix.

Request Body:
{
  "prefix": "bob",
  "is_prefix": true
}

- **prefix**: The prefix or suffix to match (max 3 characters).
- **is_prefix**: If true, the keypair should start with the prefix. If false, it should end with the prefix.

Response:
{
  "public_key": "bobV7ag1mCnkhGPvQzr8Fri7X6rA5itJsV5Q1Hje8iR",
  "recovery_phrase": "act remind dizzy light warfare want hollow pilot around object suggest raw"
}

- **public_key**: The generated public key.
- **recovery_phrase**: The BIP39 recovery phrase for the keypair.

Error Responses:
- **Rate Limit Exceeded**: If the user tries to generate a keypair more than once in 24 hours.
- **Invalid Prefix**: If the prefix is too long (more than 3 characters).

## Setup

1. Clone the repository:

    git clone https://github.com/yourusername/vanity-address-api.git
    cd vanity-address-api

2. Install dependencies:

    pip install -r requirements.txt

3. Run the Flask app:

    python app.py

## License
