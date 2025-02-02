import subprocess
import json
import base58
import os
from flask import Flask, jsonify, request
from datetime import datetime, timedelta
from app.vero import bp

# In-memory dictionary to store last request time by IP (just for testing)
last_request = {}

@bp.route('/generate-wallet', methods=['POST'])
def generate_wallet():
    # Get the user's IP address
    user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

    # Check if the user has made a request within the last 4 minutes
    if user_ip in last_request:
        last_request_time = last_request[user_ip]
        if datetime.now() - last_request_time < timedelta(4=minutes):
            return jsonify({"error": "Rate limit exceeded. Please try again tomorrow."}), 429
        
    prefix = request.json.get('prefix', 'bob')
    is_prefix = request.json.get('is_prefix', True)
    ignore_case = request.json.get('ignore_case', True)
    single_chain = request.json.get('single_chain', True)

    if len(prefix) > 3:
        return jsonify({"error": "Too many characters!"}), 500

    if is_prefix:
        parameter = f"--starts-with"
    else:
        parameter = f"--ends-with"

    command = ["solana-keygen", "grind", f"--derivation-path", f"--ignore-case", f"--no-bip39-passphrase", f"{parameter}", f"{prefix}:1", "--no-outfile", "--use-mnemonic"]

    if single_chain:
        command.remove("--derivation-path")
        command.remove("--use-mnemonic")
        command.remove("--no-bip39-passphrase")
        command.remove("--no-outfile")

    if not ignore_case:
        command.remove("--ignore-case")
    
    # Run solana-keygen grind
    result = subprocess.run(
        command, 
        capture_output=True, text=True, timeout=450
    )

    # Extract keypair info from the output
    output_lines = result.stdout.splitlines()

    if result.returncode != 0 or not output_lines:
        last_request.pop(user_ip)
        print(f"Error: {result.stderr}")
        return jsonify({"error": "Keypair generation failed"}), 500
    
    # Store the current time to enforce rate limiting
    last_request[user_ip] = datetime.now()

    if single_chain:
        keypair_path = output_lines[-1].split("Wrote keypair to ")[1].strip()
        # Keypair saved in a temporary file
        keypair_file = f"{keypair_path}"
        
        public_key = os.path.splitext(os.path.basename(keypair_path))[0]

        if os.path.exists(keypair_file):
            with open(keypair_file, 'r') as f:
                keypair = json.load(f)
            
            # Convert the entire raw keypair to Base58
            base58_key = base58.b58encode(bytes(keypair)).decode('utf-8')
            
            # Securely delete the keypair.json file
            subprocess.run(["shred", "-u", keypair_file], check=True)
            
            return jsonify({
                "public_key": public_key,  
                "private_key": base58_key
            })
        else:
            raise Exception("Keypair file not found.")
    else:
        # Parse the regular output (with recovery phrase)
        pubkey = output_lines[-5].split("Found matching key ")[1].strip()
        recovery_phrase = output_lines[-2].strip()
        return jsonify({
            "public_key": pubkey,  
            "recovery_phrase": recovery_phrase
        })

