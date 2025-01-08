import requests
import random
import time
import os
from web3 import Web3
from eth_account.messages import encode_defunct
from datetime import datetime
from fake_useragent import UserAgent
from colorama import init, Fore, Style

init(autoreset=True)

def get_headers():
    ua = UserAgent()
    return {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9',
        'Content-Type': 'application/json',
        'Origin': 'https://earn.taker.xyz',
        'Referer': 'https://earn.taker.xyz/',
        'User-Agent': ua.random
    }

def fetch_response(url, headers, proxies_dict, data=None, method="POST"):
    try:
        if method == "POST":
            response = requests.post(url, headers=headers, json=data, proxies=proxies_dict, timeout=10)
        elif method == "GET":
            response = requests.get(url, headers=headers, proxies=proxies_dict, timeout=10)
        else:
            raise ValueError("Invalid method")
        
        if response.status_code == 200:
            return response.json()
        else:
            print(f"Error: Received status code {response.status_code} from {url}")
            return None
    except requests.exceptions.ProxyError as e:
        print(f"Proxy error: {e}")
        return None
    except Exception as e:
        print(f"Request error: {e}")
        return None

def generate_wallet():
    w3 = Web3()
    acct = w3.eth.account.create()
    return acct.key.hex(), acct.address

def sign_message(private_key, message):
    w3 = Web3()
    message_hash = encode_defunct(text=message)
    signed_message = w3.eth.account.sign_message(message_hash, private_key)
    return signed_message.signature.hex()

def save_account(private_key, address, referral_code):
    with open('accounts.txt', 'a') as f:
        f.write(f"Wallet Privatekey: {private_key}\n")
        f.write(f"Wallet Address: {address}\n")
        f.write(f"Referred to: {referral_code}\n")
        f.write("-" * 85 + "\n")

def load_proxies():
    if not os.path.exists('proxies.txt'):
        return []
    with open('proxies.txt', 'r') as f:
        return [line.strip() for line in f.readlines() if line.strip()]

def get_random_proxy(proxies):
    while proxies:
        proxy = random.choice(proxies)
        try:
            response = requests.get("https://www.google.com", proxies={"http": proxy, "https": proxy}, timeout=5)
            if response.status_code == 200:
                return proxy
        except Exception:
            proxies.remove(proxy)  # Remove invalid proxy
    return None

def create_account(referral_code, account_number, total_accounts, proxies):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    private_key, address = generate_wallet()
    request_headers = get_headers()
    proxy = get_random_proxy(proxies)
    proxies_dict = {'http': proxy, 'https': proxy} if proxy else None

    if not proxy:
        print(f"{Fore.YELLOW}No valid proxy available, skipping this account.")
        return False

    nonce_response = fetch_response(
        'https://lightmining-api.taker.xyz/wallet/generateNonce',
        request_headers,
        proxies_dict,
        data={"walletAddress": address}
    )

    if not nonce_response or 'data' not in nonce_response or 'nonce' not in nonce_response['data']:
        print(f"{Fore.RED}Invalid nonce response: {nonce_response}")
        return False

    message = nonce_response['data']['nonce']
    signature = sign_message(private_key, message)

    login_response = fetch_response(
        'https://lightmining-api.taker.xyz/wallet/login',
        request_headers,
        proxies_dict,
        data={
            "address": address,
            "signature": signature,
            "message": message,
            "invitationCode": referral_code
        }
    )

    if login_response and 'data' in login_response and 'token' in login_response['data']:
        token = login_response['data']['token']
        print(f"[ {timestamp} ] [ {account_number}/{total_accounts} ] [ {Fore.GREEN}SUCCESS {Fore.WHITE}] Address: {address}")
        save_account(private_key, address, referral_code)
        return True
    else:
        print(f"[ {timestamp} ] [ {account_number}/{total_accounts} ] [ {Fore.RED}LOGIN FAILED {Fore.WHITE}] Address: {address}")
        return False

def main():
    print("Taker.xyz Referral Bot + Auto Tasks")
    referral_code = input("Enter referral code: ")
    num_accounts = int(input("Enter how many referral: "))

    proxies = load_proxies()
    if not proxies:
        print("No proxies found in proxies.txt, running without proxies")

    successful = 0
    for i in range(1, num_accounts + 1):
        if create_account(referral_code, i, num_accounts, proxies):
            successful += 1

    print(f"\n[✓] All Process Completed!")
    print(f"Total: {num_accounts} | Success: {successful} | Failed: {num_accounts - successful}")

if __name__ == "__main__":
    main()
