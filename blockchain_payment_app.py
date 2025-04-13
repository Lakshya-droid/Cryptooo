import streamlit as st
from web3 import Web3
from web3.exceptions import ContractLogicError
import qrcode
from PIL import Image
import io
import json
import os
from dotenv import load_dotenv
import time
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
import urllib.parse
import webbrowser

# Load environment variables
load_dotenv()

# Connect to blockchain
BLOCKCHAIN_URL = os.getenv("BLOCKCHAIN_URL", "http://127.0.0.1:8545")
SMART_CONTRACT_ADDRESS = os.getenv("SMART_CONTRACT_ADDRESS")
ADMIN_ADDRESS = os.getenv("ADMIN_ADDRESS", "0x90F8bf6A479f320ead074411a4B0e7944Ea8c9C1")

w3 = Web3(Web3.HTTPProvider(BLOCKCHAIN_URL))

# Smart contract ABI
CONTRACT_ABI = [
    {
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "anonymous": False,
        "inputs": [
            {
                "indexed": True,
                "internalType": "address",
                "name": "merchant",
                "type": "address"
            },
            {
                "indexed": True,
                "internalType": "address",
                "name": "payer",
                "type": "address"
            },
            {
                "indexed": False,
                "internalType": "uint256",
                "name": "amount",
                "type": "uint256"
            },
            {
                "indexed": True,
                "internalType": "string",
                "name": "paymentId",
                "type": "string"
            }
        ],
        "name": "PaymentProcessed",
        "type": "event"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "merchant",
                "type": "address"
            }
        ],
        "name": "addMerchant",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "paymentId",
                "type": "string"
            }
        ],
        "name": "isPaymentProcessed",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "name": "merchants",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "owner",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address payable",
                "name": "merchant",
                "type": "address"
            },
            {
                "internalType": "string",
                "name": "paymentId",
                "type": "string"
            }
        ],
        "name": "processPayment",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "string",
                "name": "",
                "type": "string"
            }
        ],
        "name": "processedPayments",
        "outputs": [
            {
                "internalType": "bool",
                "name": "",
                "type": "bool"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {
                "internalType": "address",
                "name": "merchant",
                "type": "address"
            }
        ],
        "name": "removeMerchant",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

# Initialize contract
payment_contract = None
if SMART_CONTRACT_ADDRESS:
    payment_contract = w3.eth.contract(address=Web3.to_checksum_address(SMART_CONTRACT_ADDRESS), abi=CONTRACT_ABI)

# Local server setup
local_server = None
local_server_thread = None

def get_local_ip():
    """Get the local IP address of the machine"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "127.0.0.1"

local_ip = get_local_ip()

class PaymentRequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """Handle GET requests from mobile devices"""
        parsed_path = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed_path.query)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        if 'payment_data' in query:
            try:
                payment_data = json.loads(query['payment_data'][0])
            except:
                payment_data = None
        else:
            payment_data = {
                'merchant': query.get('merchant', [''])[0],
                'amount': float(query.get('amount', [0])[0]),
                'paymentId': query.get('paymentId', [''])[0]
            }
        
        if payment_data and payment_data['merchant']:
            try:
                payment_data = json.loads(query['payment_data'][0])
                response = f"""
                <html>
                    <head>
                        <title>Blockchain Payment</title>
                        <meta name="viewport" content="width=device-width, initial-scale=1.0">
                        <style>
                            body {{ font-family: Arial, sans-serif; padding: 20px; }}
                            .container {{ max-width: 500px; margin: 0 auto; }}
                            .payment-info {{ background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
                            .form-group {{ margin-bottom: 15px; }}
                            label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
                            input[type="text"], input[type="password"] {{
                                width: 100%;
                                padding: 8px;
                                border: 1px solid #ddd;
                                border-radius: 4px;
                                box-sizing: border-box;
                            }}
                            .button {{
                                display: inline-block;
                                padding: 10px 20px;
                                margin: 5px;
                                border: none;
                                border-radius: 5px;
                                font-size: 16px;
                                cursor: pointer;
                                text-decoration: none;
                                text-align: center;
                            }}
                            .approve {{ background: #4CAF50; color: white; }}
                            .cancel {{ background: #f44336; color: white; }}
                            .button-container {{ text-align: center; margin-top: 20px; }}
                        </style>
                    </head>
                    <body>
                        <div class="container">
                            <h1>Payment Request</h1>
                            <div class="payment-info">
                                <p><strong>Merchant:</strong> {payment_data.get('merchant', '')}</p>
                                <p><strong>Amount:</strong> {payment_data.get('amount', '')} ETH</p>
                                <p><strong>Payment ID:</strong> {payment_data.get('paymentId', '')}</p>
                            </div>
                            <form action="/approve" method="post">
                                <input type="hidden" name="payment_data" value='{query['payment_data'][0]}'>
                                <div class="form-group">
                                    <label for="account_id">Your Wallet Address:</label>
                                    <input type="text" id="account_id" name="account_id" required>
                                </div>
                                <div class="form-group">
                                    <label for="secret_key">Your Private Key:</label>
                                    <input type="password" id="secret_key" name="secret_key" required>
                                </div>
                                <div class="button-container">
                                    <button type="submit" class="button approve">Approve Payment</button>
                                    <a href="/cancel" class="button cancel">Cancel</a>
                                </div>
                            </form>
                        </div>
                    </body>
                </html>
                """
                self.wfile.write(response.encode('utf-8'))
            except Exception as e:
                self.wfile.write(f"Error processing payment: {str(e)}".encode('utf-8'))
        
        elif self.path == '/cancel':
            response = """
            <html>
                <head>
                    <title>Payment Cancelled</title>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <style>
                        body { font-family: Arial, sans-serif; padding: 20px; text-align: center; }
                        .error { color: #f44336; font-size: 24px; }
                    </style>
                </head>
                <body>
                    <div class="error">✗</div>
                    <h1>Payment Cancelled</h1>
                    <p>The payment was not processed.</p>
                </body>
            </html>
            """
            self.wfile.write(response.encode('utf-8'))
        else:
            self.wfile.write("Invalid request".encode('utf-8'))

    def do_POST(self):
        """Handle POST requests for payment approval"""
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        post_params = urllib.parse.parse_qs(post_data)
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        
        if self.path == '/approve':
            try:
                payment_data = json.loads(post_params['payment_data'][0])
                account_id = post_params['account_id'][0]
                secret_key = post_params['secret_key'][0]
                
                # Process the payment immediately
                success, result = process_mobile_payment(payment_data, account_id, secret_key)
                
                if success:
                    st.session_state.mobile_payment_data = payment_data
                    st.session_state.last_payment_result = f"Payment successful! TX Hash: {result}"
                    response = f"""
                    <html>
                        <head>
                            <title>Payment Successful</title>
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <style>
                                body {{ font-family: Arial, sans-serif; padding: 20px; text-align: center; }}
                                .success {{ color: #4CAF50; font-size: 24px; }}
                            </style>
                        </head>
                        <body>
                            <div class="success">✓</div>
                            <h1>Payment Successful</h1>
                            <p>Transaction hash: {result}</p>
                            <p>You can close this window now.</p>
                        </body>
                    </html>
                    """
                else:
                    response = f"""
                    <html>
                        <head>
                            <title>Payment Failed</title>
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <style>
                                body {{ font-family: Arial, sans-serif; padding: 20px; text-align: center; }}
                                .error {{ color: #f44336; font-size: 24px; }}
                            </style>
                        </head>
                        <body>
                            <div class="error">✗</div>
                            <h1>Payment Failed</h1>
                            <p>{result}</p>
                        </body>
                    </html>
                    """
                self.wfile.write(response.encode('utf-8'))
            except Exception as e:
                self.wfile.write(f"Error processing payment: {str(e)}".encode('utf-8'))

def start_local_server():
    """Start a local HTTP server to handle mobile payment requests"""
    global local_server
    server_address = ('', 8000)
    local_server = HTTPServer(server_address, PaymentRequestHandler)
    local_server.serve_forever()

def start_server_in_thread():
    """Start the local server in a separate thread"""
    global local_server_thread
    local_server_thread = threading.Thread(target=start_local_server)
    local_server_thread.daemon = True
    local_server_thread.start()

def generate_payment_qr(merchant_address, amount, payment_id):
    """Generate a QR code with payment information"""
    payment_data = {
        "merchant": merchant_address,
        "amount": amount,
        "paymentId": payment_id,
        "contract": SMART_CONTRACT_ADDRESS
    }
    
    # Create a clean URL without complex encoding
    base_url = f"http://{local_ip}:8000"
    query_string = f"merchant={merchant_address}&amount={amount}&paymentId={payment_id}"
    payment_url = f" http://{local_ip}:8000/?payment_data={json.dumps({'merchant': merchant_address, 'amount': payment_amount, 'paymentId': payment_id})}"
    
    # Generate QR code with the clean URL
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(payment_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='PNG')
    
    # Store the clean URL in session state for display
    st.session_state.payment_url = payment_url
    
    return img_bytes.getvalue()
def check_payment_status(payment_id):
    """Check if a payment has been processed"""
    if payment_contract:
        return payment_contract.functions.processedPayments(payment_id).call()
    return False

def is_registered_merchant(address):
    """Check if an address is registered as a merchant"""
    if payment_contract and Web3.is_address(address):
        return payment_contract.functions.merchants(Web3.to_checksum_address(address)).call()
    return False

def process_mobile_payment(payment_data, payer_address, payer_private_key):
    """Process payment from mobile device"""
    try:
        if not payment_contract:
            return False, "Smart contract not configured"
        
        if not Web3.is_address(payer_address):
            return False, "Invalid payer address"
            
        merchant_address = Web3.to_checksum_address(payment_data['merchant'])
        payment_id = payment_data['paymentId']
        amount = float(payment_data['amount'])
        
        # Check for existing payment
        is_processed = payment_contract.functions.processedPayments(payment_id).call()
        if is_processed:
            return False, "This payment ID has already been processed"
            
        # Convert ETH amount to Wei
        amount_wei = w3.to_wei(amount, 'ether')
        
        # Get nonce for sender account
        sender_address = Web3.to_checksum_address(payer_address)
        nonce = w3.eth.get_transaction_count(sender_address)
        
        # Prepare the transaction
        txn = payment_contract.functions.processPayment(
            merchant_address,
            payment_id
        ).build_transaction({
            'from': sender_address,
            'value': amount_wei,
            'gas': 200000,
            'gasPrice': w3.eth.gas_price,
            'nonce': nonce,
        })
        
        # Sign the transaction
        signed_txn = w3.eth.account.sign_transaction(txn, private_key=payer_private_key)
        
        # Send the transaction
        txn_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        
        # Wait for transaction receipt
        txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
        
        return txn_receipt.status == 1, txn_hash.hex()
    except ContractLogicError as e:
        return False, f"Contract error: {str(e)}"
    except ValueError as e:
        return False, f"Value error: {str(e)}"
    except Exception as e:
        return False, f"Error processing payment: {str(e)}"

# Streamlit app
st.title("Blockchain Payment Gateway")

# Start local server for mobile payments
if 'server_started' not in st.session_state:
    try:
        start_server_in_thread()
        st.session_state.server_started = True
    except Exception as e:
        st.warning(f"Could not start local server: {str(e)}")

# App mode selection
app_mode = st.sidebar.selectbox(
    "Choose the app mode",
    ["Merchant Dashboard", "Payment Simulator", "Merchant Registration", "Mobile Payment"]
)

# Check blockchain connection
if w3.is_connected():
    st.sidebar.success("✅ Connected to blockchain network")
else:
    st.sidebar.error("❌ Not connected to blockchain network. Please check your connection settings.")
    if app_mode != "Merchant Registration":
        st.error("Cannot connect to blockchain. Please check your connection settings.")
        st.stop()

# Check if contract is available
if not payment_contract:
    st.sidebar.warning("⚠️ Smart contract address not configured. Set the SMART_CONTRACT_ADDRESS in .env file.")
    if app_mode != "Merchant Registration":
        st.warning("Smart contract address not configured. Some features may not work correctly.")

if app_mode == "Merchant Dashboard":
    st.header("Merchant Dashboard")
    
    merchant_address = st.text_input("Enter Your Merchant Wallet Address", "0xFFcf8FDEE72ac11b5c542428B35EEF5769C409f0")
    
    # Check if the merchant is registered
    is_merchant = is_registered_merchant(merchant_address)
    if merchant_address:
        if is_merchant:
            st.success(f"✅ {merchant_address} is a registered merchant")
        else:
            st.error(f"❌ {merchant_address} is not registered as a merchant. Please register first.")
    
    # Create payment form
    st.subheader("Create Payment Request")
    
    col1, col2 = st.columns(2)
    with col1:
        payment_amount = st.number_input("Payment Amount (ETH)", min_value=0.0001, max_value=10.0, value=0.01, step=0.001)
        payment_description = st.text_input("Payment Description", "Product or service payment")
    
    with col2:
        payment_id = st.text_input("Payment ID", f"PAY-{int(time.time())}")
        generate_button = st.button("Generate Payment QR")
    
    # Generate QR code when button is clicked
    if generate_button:
        if not is_merchant:
            st.error("Cannot generate QR code - merchant not registered.")
        else:
            qr_code = generate_payment_qr(merchant_address, payment_amount, payment_id)
            
            # Save QR code to session state
            st.session_state.qr_code = qr_code
            st.session_state.payment_id = payment_id
            st.session_state.payment_amount = payment_amount
            st.session_state.merchant_address = merchant_address
            
            # Display connection instructions for mobile
            st.info(f"To pay from your mobile device on the same WiFi network:")
            st.write(f"1. Connect to the same WiFi network as this computer")
            st.write(f"2. Open your camera or QR code scanner app")
            st.write(f"3. Scan the QR code below")
            st.write(f"Or visit: http://{local_ip}:8000/?payment_data={json.dumps({'merchant': merchant_address, 'amount': payment_amount, 'paymentId': payment_id})}")
    
    # Display QR code and payment information if available
    if 'qr_code' in st.session_state:
        col1, col2 = st.columns(2)
    
        with col1:
            st.image(st.session_state.qr_code, caption="Scan this QR code to pay")
            st.write("Or open this link on your mobile device:")
            st.code(st.session_state.payment_url)
    
        with col2:
            st.subheader("Payment Details")
            st.write(f"**Merchant:** {st.session_state.merchant_address}")
            st.write(f"**Amount:** {st.session_state.payment_amount} ETH")
            st.write(f"**Payment ID:** {st.session_state.payment_id}")
            
            # Payment status
            status = check_payment_status(st.session_state.payment_id)
            if status:
                st.success("✅ Payment completed")
            else:
                st.warning("⏳ Awaiting payment...")
                if st.button("Check Payment Status"):
                    status = check_payment_status(st.session_state.payment_id)
                    if status:
                        st.success("✅ Payment completed")
                    else:
                        st.warning("⏳ Still awaiting payment...")

elif app_mode == "Payment Simulator":
    st.header("Payment Simulator")
    
    st.info("This interface simulates a user scanning the QR code and making a payment")
    
    # Manually enter payment details
    st.subheader("Enter Payment Details")
    sim_merchant = st.text_input("Merchant Address", "0x22d491Bde2303f2f43325b2108D26f1eAbA1e32b")
    sim_amount = st.number_input("Amount (ETH)", min_value=0.0001, value=0.01, step=0.001)
    sim_payment_id = st.text_input("Payment ID", "PAY-123456789")
    
    # Verify if merchant is registered
    is_merchant = is_registered_merchant(sim_merchant)
    if is_merchant:
        st.success(f"✅ {sim_merchant} is a registered merchant")
    else:
        st.error(f"❌ {sim_merchant} is not registered as a merchant. Payment cannot be processed.")
    
    # Simulated payer info
    st.subheader("Payer Information")
    payer_address = st.text_input("Your Wallet Address")
    payer_private_key = st.text_input("Your Private Key (for demo only)", type="password")
    
    # Process payment button
    if st.button("Process Payment"):
        if not payment_contract:
            st.error("Smart contract not configured")
        elif not w3.is_connected():
            st.error("Not connected to blockchain. Please check your connection.")
        elif not is_merchant:
            st.error("Cannot process payment - merchant not registered.")
        else:
            try:
                if not Web3.is_address(sim_merchant):
                    st.error("Invalid merchant address")
                    st.stop()
                
                if not Web3.is_address(payer_address):
                    st.error("Invalid payer address")
                    st.stop()
                
                merchant_address = Web3.to_checksum_address(sim_merchant)
                
                # Check for existing payment
                is_processed = payment_contract.functions.processedPayments(sim_payment_id).call()
                if is_processed:
                    st.error("This payment ID has already been processed")
                    st.stop()
                    
                # Convert ETH amount to Wei
                amount_wei = w3.to_wei(sim_amount, 'ether')
                
                # Build the transaction
                if payer_private_key:
                    sender_address = Web3.to_checksum_address(payer_address)
                    nonce = w3.eth.get_transaction_count(sender_address)
                    
                    txn = payment_contract.functions.processPayment(
                        merchant_address,
                        sim_payment_id
                    ).build_transaction({
                        'from': sender_address,
                        'value': amount_wei,
                        'gas': 200000,
                        'gasPrice': w3.eth.gas_price,
                        'nonce': nonce,
                    })
                    
                    signed_txn = w3.eth.account.sign_transaction(txn, private_key=payer_private_key)
                    txn_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                    
                    with st.spinner('Processing transaction...'):
                        txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
                    
                    if txn_receipt.status == 1:
                        st.success(f"Payment of {sim_amount} ETH to {merchant_address} completed!")
                        st.write(f"Transaction hash: {txn_hash.hex()}")
                        st.balloons()
                    else:
                        st.error("Transaction failed")
                else:
                    st.error("Private key is required to sign the transaction")
            except Exception as e:
                st.error(f"Error processing payment: {str(e)}")

elif app_mode == "Merchant Registration":
    st.header("Merchant Registration")
    
    if not payment_contract:
        st.error("Smart contract address not configured. Set the SMART_CONTRACT_ADDRESS in .env file.")
        st.stop()
    
    st.write("Use this page to register new merchants with the payment gateway.")
    
    # Show the contract owner
    try:
        contract_owner = payment_contract.functions.owner().call()
        st.write(f"Contract Owner: {contract_owner}")
    except Exception as e:
        st.error(f"Error getting contract owner: {str(e)}")
        contract_owner = "Unknown"
    
    # Admin information
    st.subheader("Admin Authentication")
    admin_address = st.text_input("Admin Address (Contract Owner)", ADMIN_ADDRESS or contract_owner)
    admin_private_key = st.text_input("Admin Private Key", type="password")
    
    # Merchant to register
    st.subheader("New Merchant Details")
    new_merchant = st.text_input("Merchant Address to Register")
    
    # Validate merchant address
    is_valid_address = Web3.is_address(new_merchant) if new_merchant else False
    is_already_merchant = is_registered_merchant(new_merchant) if is_valid_address else False
    
    if new_merchant:
        if not is_valid_address:
            st.error("Invalid Ethereum address format")
        elif is_already_merchant:
            st.info(f"✅ {new_merchant} is already registered as a merchant")
        else:
            st.info(f"Address is valid and not yet registered as a merchant")
    
    # Registration button
    if st.button("Register Merchant"):
        if not admin_private_key:
            st.error("Admin private key is required")
        elif not is_valid_address:
            st.error("Please enter a valid merchant address")
        elif is_already_merchant:
            st.error("This address is already registered as a merchant")
        else:
            try:
                merchant_to_add = Web3.to_checksum_address(new_merchant)
                admin_checksum = Web3.to_checksum_address(admin_address)
                
                nonce = w3.eth.get_transaction_count(admin_checksum)
                
                txn = payment_contract.functions.addMerchant(
                    merchant_to_add
                ).build_transaction({
                    'from': admin_checksum,
                    'gas': 200000,
                    'gasPrice': w3.eth.gas_price,
                    'nonce': nonce,
                })
                
                signed_txn = w3.eth.account.sign_transaction(txn, admin_private_key)
                txn_hash = w3.eth.send_raw_transaction(signed_txn.raw_transaction)
                
                with st.spinner('Registering merchant...'):
                    txn_receipt = w3.eth.wait_for_transaction_receipt(txn_hash)
                
                if txn_receipt.status == 1:
                    st.success(f"Merchant {merchant_to_add} successfully registered!")
                    st.write(f"Transaction hash: {txn_hash.hex()}")
                else:
                    st.error("Transaction failed")
            except Exception as e:
                st.error(f"Error registering merchant: {str(e)}")

elif app_mode == "Mobile Payment":
    st.header("Mobile Payment Processing")
    
    if 'last_payment_result' in st.session_state:
        st.success(st.session_state.last_payment_result)
        del st.session_state.last_payment_result
    
    if 'mobile_payment_data' in st.session_state:
        payment_data = st.session_state.mobile_payment_data
        st.success("Mobile payment request received!")
        
        st.subheader("Payment Details")
        st.write(f"**Merchant:** {payment_data.get('merchant', '')}")
        st.write(f"**Amount:** {payment_data.get('amount', '')} ETH")
        st.write(f"**Payment ID:** {payment_data.get('paymentId', '')}")
        
        if 'last_payment_result' in st.session_state:
            st.success(st.session_state.last_payment_result)
            del st.session_state.mobile_payment_data
    else:
        st.info("No pending mobile payments. Scan a QR code from a merchant to initiate a payment.")

# Display blockchain info
st.sidebar.subheader("Blockchain Information")
if w3.is_connected():
    st.sidebar.write(f"Connected to: {BLOCKCHAIN_URL}")
    st.sidebar.write(f"Current block: {w3.eth.block_number}")
else:
    st.sidebar.error("Not connected to blockchain")

# Display local server info
if local_ip and 'server_started' in st.session_state:
    st.sidebar.subheader("Mobile Payment Server")
    st.sidebar.write(f"Local IP: {local_ip}")
    st.sidebar.write("Port: 8000")
    st.sidebar.info("Mobile devices on the same network can connect to this server")

# Clean up when app is closed
def cleanup():
    if local_server:
        local_server.shutdown()

import atexit
atexit.register(cleanup)