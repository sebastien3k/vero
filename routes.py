import subprocess
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from app.vero import bp

# In-memory dictionary to store last request time by IP
last_request = {}

@bp.route('/generate-wallet', methods=['POST'])
def generate_wallet():
    # Get the user's IP address
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    # Check if the user has made a request within the last 24 hours
    if user_ip in last_request:
        last_request_time = last_request[user_ip]
        if datetime.now() - last_request_time < timedelta(days=1):
            return jsonify({"error": "Rate limit exceeded. Please try again tomorrow."}), 429
        
    prefix = request.json.get('prefix', 'bob')
    is_prefix = request.json.get('is_prefix', True)

    if len(prefix) > 3:
        return jsonify({"error": "Too many characters!"}), 500
    
    if is_prefix:
        parameter = f"--starts-with"
    else:
        parameter = f"--ends-with"

    # Run solana-keygen grind without writing to disk
    result = subprocess.run(
        ["solana-keygen", "grind", f"--derivation-path", f"--no-bip39-passphrase", f"{parameter}", f"{prefix}:1", "--no-outfile", "--use-mnemonic"],
        capture_output=True, text=True
    )

    # Extract keypair from the output
    output_lines = result.stdout.splitlines()

    if not output_lines:
        return jsonify({"error": "Keypair generation failed"}), 500
    
    pubkey = output_lines[-5].split("Found matching key ")[1].strip()
    recovery_phrase = output_lines[-2].strip()  # This will give the recovery phrase

    # Store the current time to enforce rate limiting
    last_request[user_ip] = datetime.now()

    return jsonify({
        "public_key": pubkey,  # The generated public key
        "recovery_phrase": recovery_phrase
    })
