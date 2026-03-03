<div align="center">
  <h1>LIPA-PY</h1>
  <p><em>Empowering Seamless Payments Across East Africa</em></p>

  <p>
    <img src="https://img.shields.io/github/last-commit/PatzPaul/lipa-py/main?color=blue&style=flat-square" alt="last commit">
    <img src="https://img.shields.io/github/languages/top/PatzPaul/lipa-py?color=blue&style=flat-square" alt="python 100%">
    <img src="https://img.shields.io/github/languages/count/PatzPaul/lipa-py?color=blue&style=flat-square" alt="languages 1">
  </p>

  <p><em>Built with the tools and technologies:</em></p>
  <p>
    <img src="https://img.shields.io/badge/Markdown-000000?style=flat-square&logo=markdown&logoColor=white" alt="Markdown">
    <img src="https://img.shields.io/badge/TOML-8B4513?style=flat-square&logo=toml&logoColor=white" alt="TOML">
    <img src="https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white" alt="FastAPI">
    <img src="https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python">
    <img src="https://img.shields.io/badge/GitHub_Actions-2088FF?style=flat-square&logo=github-actions&logoColor=white" alt="GitHub Actions">
    <img src="https://img.shields.io/badge/uv-DE5FE9?style=flat-square&logo=python&logoColor=white" alt="uv">
    <img src="https://img.shields.io/badge/Pydantic-E92063?style=flat-square&logo=pydantic&logoColor=white" alt="Pydantic">
  </p>
</div>

---

## Table of Contents

- [Overview](#overview)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Usage](#usage)
- [Testing & Requirements](#testing--requirements)
- [Contributing](#contributing)

---

## Overview

`lipa-py` is a modern, asynchronous Python library that simplifies integrating East African mobile money services such as M-Pesa, Selcom, Safaricom Daraja, TIPS, Airtel Money, and Tigo Pesa. It provides a unified, type-safe interface for payment processing, webhook handling, and secure transaction management.

**Why lipa-py?**

This project aims to streamline mobile money integrations, enabling developers to build scalable, reliable payment solutions within the broader financial ecosystem. The core features include:

- Unified API for multiple mobile money providers, abstracting provider-specific details.
- Asynchronous webhooks with background processing for real-time notifications.
- Cryptographic functions ensuring secure communication and request integrity.
- Strong type safety with schemas and static analysis support.
- Automated CI workflows to maintain code quality and stability.

---

## Getting Started

### Prerequisites

This project requires the following dependencies:

- **Programming Language:** Python
- **Package Manager:** uv

### Installation

Build `lipa-py` from the source and install dependencies:

1. **Clone the repository:**
   ```bash
   git clone https://github.com/PatzPaul/lipa-py.git
   ```

2. **Navigate to the project directory:**
   ```bash
   cd lipa-py
   ```

3. **Install the dependencies:**

   **Using [uv](https://docs.astral.sh/uv/):**
   ```bash
   uv sync --all-extras --dev
   ```

### Usage

Run the project with:

**Using [uv](https://docs.astral.sh/uv/):**

#### 1. The Unified Payment Interface (Recommended)

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

Handling asynchronous webhooks correctly is difficult due to MNO timeouts. We provide native FastAPI routers that handle the required response codes instantly while delegating your logic to the background.

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

Because `lipa-py` interacts with strict MNOs and Gateways, there are some hard requirements before you can successfully make a test API call:

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
