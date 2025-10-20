
import os
import requests
import base64
import hashlib
import re
# --- Configuration ---
CLIENT_ID = os.environ.get("TWITTER_CLIENT_ID")
CLIENT_SECRET = os.environ.get("TWITTER_CLIENT_SECRET")
REDIRECT_URI = "http://localhost:8080"
SCOPES = ["tweet.read", "tweet.write", "users.read", "offline.access"]

# --- 1. Create a code verifier and code challenge ---
def create_code_challenge():
    code_verifier = base64.urlsafe_b64encode(os.urandom(30)).decode("utf-8")
    code_verifier = re.sub(r"[^a-zA-Z0-9-_.~]+", "", code_verifier)

    code_challenge = hashlib.sha256(code_verifier.encode("utf-8")).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge).decode("utf-8")
    code_challenge = code_challenge.replace("=", "")
    return code_verifier, code_challenge

# --- 2. Create the authorization URL ---
def create_authorization_url(code_challenge):
    params = {
        "response_type": "code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
        "state": "state",
        "code_challenge": code_challenge,
        "code_challenge_method": "S256",
    }
    url = "https://x.com/i/oauth2/authorize"
    auth_url = requests.Request("GET", url, params=params).prepare().url
    return auth_url

# --- 3. Start a local server to listen for the redirect ---


# --- 4. Exchange the authorization code for an access token ---
def exchange_code_for_token(code, code_verifier):
    token_url = "https://api.x.com/2/oauth2/token"
    payload = {
        "code": code,
        "grant_type": "authorization_code",
        "client_id": CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "code_verifier": code_verifier,
    }
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Authorization": f"Basic {base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode()).decode()}",
    }
    response = requests.post(token_url, data=payload, headers=headers)
    return response.json()

def main():
    if not CLIENT_ID or not CLIENT_SECRET:
        print("Please set the TWITTER_CLIENT_ID and TWITTER_CLIENT_SECRET environment variables.")
        return

    code_verifier, code_challenge = create_code_challenge()
    auth_url = create_authorization_url(code_challenge)

    print(f"Please open the following URL in your browser to authorize the application:\n{auth_url}")

    redirect_url = input("\nPlease paste the full redirect URL here: ")

    try:
        authorization_code = redirect_url.split("code=")[1].split("&")[0]
        print(f"Authorization code received: {authorization_code}")
        token_data = exchange_code_for_token(authorization_code, code_verifier)
        print("\n--- Tokens ---")
        print(f"Access Token: {token_data.get('access_token')}")
        print(f"Refresh Token: {token_data.get('refresh_token')}")
        print("\n")
    except IndexError:
        print("Could not find authorization code in the redirect URL.")


if __name__ == "__main__":
    main()
