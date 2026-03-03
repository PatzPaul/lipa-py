#  <div align="center">          Lipa-py </div>

<div align="center">
  <h3>The Ultimate Assisant for Payments in Tanzania.</h3>
  <p>A modern, strictly typed, async-first package designed to integrate Tanzanian Mobile Network Operators (Vodacom M-Pesa, Tigo Pesa, Airtel Money) and Gateways (Selcom, TIPS) seamlessly into Python backend applications.</p>
</div>

---

##  Features

*   **Unified Orchestrator**: Write one simple abstract `UnifiedPaymentRequest` and let `lipa-py` route it perfectly based on phone prefixes or your configured fallback gateways (e.g., automatically routing Vodacom numbers to M-Pesa, and Airtel numbers to Selcom).
*   **Fully Async**: Built from the ground up on `httpx` async clients to keep your API responsive without blocking requests.
*   **100% Type Safe**: Powered by Pydantic V2. Absolutely no raw `dicts` returned. Everything is perfectly schema'd for your IDE intellisense.
*   **Batteries-Included Webhooks**: Ships with pre-configured, dependency-injectable FastAPI routers specifically crafted to respond to MNO Webhooks with an immediate `HTTP 200` while pushing your database logic correctly into Background Tasks.
*   **Strict Security**: Implements all vendor-specific cryptography natively. No struggling with RSA Public Keys. We handle the math; you handle the business.

## Installation

```bash
# Using uv (Recommended)
uv add lipa-py

# Or pip
pip install lipa-py
```

## Quick Start

### 1. The Unified Payment Interface (Recommended)

This is the fastest way to accept payments without caring about the underlying MNO.

```python
import asyncio
from lipa_py import UnifiedPaymentClient, UnifiedPaymentRequest

async def accept_payment():
    # 1. Define your active gateways
    client = UnifiedPaymentClient({
        "mpesa": {
            "api_key": "example_vodacom_api_key",
            "public_key": "example_vodacom_public_key_pem",
            "environment": "sandbox"
        },
        "selcom": {
            "vendor_id": "example_SELCOM_VENDOR",
            "api_key": "example_selcom_key",
            "api_secret": "example_selcom_secret",
            "environment": "sandbox"
        },
        "safaricom": {
            "consumer_key": "example_safaricom_key",
            "consumer_secret": "example_safaricom_secret",
            "passkey": "example_passkey",
            "shortcode": "174379",
            "environment": "sandbox"
        },
        "tigo_pesa": {
            "client_id": "example_tigo_client_id",
            "client_secret": "example_tigo_secret",
            "biller_code": "example_BILLER_CODE",
            "environment": "sandbox"
        },
        "airtel_money": {
            "client_id": "example_airtel_id",
            "client_secret": "example_airtel_secret",
            "environment": "sandbox"
        },
        "tips": {
            "api_key": "example_tips_token",
            "institution_id": "example_INSTITUTION",
            "environment": "sandbox"
        }
    })

    # 2. Provide the customer details.
    # lipa-py automatically detects the prefixes!
    # 075x -> M-Pesa 
    # 071x -> Tigo Pesa
    # 078x -> Airtel Money
    # 2547x -> Safaricom Daraja
    # If the number is unrecognized, it falls back to Gateway aggregators (Selcom, TIPS)
    request = UnifiedPaymentRequest(
        phone_number="255716000000",
        amount=1000.0,
        reference="TICKET-123",
        email="customer@example.com" 
    )

    response = await client.request_payment(request)
    print(f"Payment via {response.provider} initialized. Trx ID: {response.transaction_id}")
    
    # Clean up graceful
    await client.close()

if __name__ == "__main__":
    asyncio.run(accept_payment())
```

### 2. Using Specific MNO Clients Directly

If you don't need the Orchestrator and want to talk to M-Pesa directly:

```python
import asyncio
from lipa_py.mpesa import MPesaClient, STKPushRequest

async def mpesa_only():
    async with MPesaClient(api_key="...", public_key="...") as mpesa:
        req = STKPushRequest(
            phone_number="255754000000",
            amount=5000,
            reference="TICKET-456",
            third_party_conversation_id="ABC-123"
        )
        res = await mpesa.stk_push(req)
        print(f"STK Push Sent: {res.output_ConversationID}")

asyncio.run(mpesa_only())
```

### 3. FastAPI Webhook Integration

Handling asynchronous webhooks correctly in Africa is difficult due to MNO timeouts. We provide native FastAPI routers that handle the required response codes instantly while delegating your logic to the background.

```python
from fastapi import FastAPI
from lipa_py.mpesa import mpesa_router, set_webhook_handler, MpesaWebhookData

app = FastAPI()

# 1. Write the logic you want to execute when a payment completes
async def handle_successful_payment(data: MpesaWebhookData):
    # This runs safely in a BackgroundTask!
    if data.input_ResultCode == "0": # 0 typically means success in M-Pesa 
        print(f"Payment of {data.input_TransactionID} succeeded!")
        # -> UPDATE YOUR DATABASE HERE <-

# 2. Register your handler
set_webhook_handler(handle_successful_payment)

# 3. Mount the pre-built router
app.include_router(mpesa_router, prefix="/payments/mpesa")
```
Your webhook is now live at `POST /payments/mpesa/webhook`.

## Testing & Requirements

Because `lipa-py` interacts with strict African MNOs and Gateways, there are some hard requirements before you can successfully make a test API call:

### 1. Vodacom M-Pesa Requirements
To use the M-Pesa client, you cannot just use dummy strings. You must have:
- **API Key**: Available from the [Vodacom M-Pesa Developer Portal](https://openapi.m-pesa.com/).
- **Public Key (PEM Format)**: Vodacom requires your requests to be RSA encrypted using their specific Certificate. You must download this `.pem` file from the Developer Portal, open it, and pass its contents into the `public_key` field. Without this, the `crypto.py` module will throw an error.

### 2. Tigo Pesa Requirements
To use the Tigo Pesa integration:
- **Client ID & Client Secret**: Obtained from the Tigo Pesa Developer Portal after registering an application.
- **Biller Code**: A unique identifier for your business on the Tigo Pesa network.

### 3. Airtel Money Requirements
To use the Airtel Money integration:
- **Client ID & Client Secret**: Provided by Airtel Money when you create an integration application on their portal.

### 4. Safaricom (Kenya) Requirements
To use the Safaricom Daraja STK Push integration:
- **Consumer Key & Secret**: Generated by creating an App on the [Safaricom Daraja Portal](https://developer.safaricom.co.ke/). (Ensure your Sandbox App has the *M-Pesa Express* scope checked!).
- **Passkey & Shortcode**: The Sandbox provides default values for these. For production, these are provided to you by Safaricom when you Go Live.

### 5. Selcom Gateway Requirements
To use the Selcom integration:
- **Vendor ID**: Your registered Selcom Vendor/Till number.
- **API Key & API Secret**: Provided by Selcom upon account registration. Selcom uses this to validate the HMAC-SHA256 signature generated by `lipa-py` on every request.

### 6. TIPS Gateway Requirements
To use the TIPS integration:
- **API Key**: A token provided by TIPS for authenticating requests.
- **Institution ID**: Your registered institution identifier within the TIPS network.

*If you try to run the quickstart using fake keys, the initial Pydantic schema validation will succeed, but the subsequent asynchronous `httpx` call to the Sandbox/Live URL will be rejected by the Gateway with an Authentication Error HTTP Status Code.*


## Contributing

We want to make `lipa-py` the definitive standard for Tanzanian and East African payments in Python. Pull Requests are always welcome for:
- Improving test suites and coverage
- Incorporating missing Gateways / Aggregators (e.g. DPO, Pesapal)
- Real-world production edge case fixes

### Sponsors
_Support `lipa-py` and get your logo here!_

## License
MIT License
