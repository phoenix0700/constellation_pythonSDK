"""
Offline usage examples for Constellation Network Python SDK.
These examples work without network connectivity.
"""

import json

from constellation_sdk import Account
from constellation_sdk.config import DEFAULT_CONFIGS


def main():
    print("🌟 Constellation SDK - Offline Examples")
    print("=" * 50)

    # Example 1: Create and manage accounts
    print("\n📱 Account Management")
    print("-" * 30)

    # Create new account
    account = Account()
    print(f"✅ New Account Created")
    print(f"   Address: {account.address}")
    print(f"   Public Key: {account.get_public_key_hex()}")
    print(f"   Private Key: {account.get_private_key_hex()}")

    # Save account info
    account_info = {
        "address": account.address,
        "private_key": account.get_private_key_hex(),
        "public_key": account.get_public_key_hex(),
    }

    # Test loading from private key
    loaded_account = Account.from_private_key(account_info["private_key"])
    print(f"\n✅ Account Loaded from Private Key")
    print(f"   Original: {account.address}")
    print(f"   Loaded:   {loaded_account.address}")
    print(f"   Match: {account.address == loaded_account.address}")

    # Example 2: Message signing
    print("\n🔐 Message Signing")
    print("-" * 30)

    messages = [
        "Hello Constellation Network!",
        "Transaction data",
        "Custom message for signing",
    ]

    for i, message in enumerate(messages, 1):
        signature = account.sign(message)
        print(f"✅ Message {i} signed")
        print(f"   Message: {message}")
        print(f"   Signature: {signature.hex()[:20]}... ({len(signature)} bytes)")

    # Example 3: Transaction signing
    print("\n💸 Transaction Signing")
    print("-" * 30)

    # Create sample transaction data
    transaction_data = {
        "source": account.address,
        "destination": "DAGexampleRecipientAddress123",
        "amount": 1000000000,  # 1 DAG in nano-DAG
        "fee": 0,
        "lastRef": "sample_last_ref_hash",
    }

    tx_signature = account.sign_transaction(transaction_data)
    print(f"✅ Transaction Signed")
    print(f"   From: {transaction_data['source']}")
    print(f"   To: {transaction_data['destination']}")
    print(f"   Amount: {transaction_data['amount'] / 1_000_000_000} DAG")
    print(f"   Signature: {tx_signature[:20]}...")

    # Example 4: Multiple accounts
    print("\n👥 Multiple Accounts")
    print("-" * 30)

    accounts = []
    for i in range(3):
        acc = Account()
        accounts.append(acc)
        print(f"✅ Account {i+1}: {acc.address}")

    # Example 5: Network configurations (offline)
    print("\n🌐 Network Configurations")
    print("-" * 30)

    for name, config in DEFAULT_CONFIGS.items():
        print(f"✅ {config.name}")
        print(f"   Network: {name}")
        print(f"   L0 URL: {config.l0_url}")
        print(f"   L1 URL: {config.l1_url}")
        print(f"   BE URL: {config.be_url}")
        print()

    # Example 6: Account export/import
    print("\n💾 Account Export/Import")
    print("-" * 30)

    # Export account
    exported_data = {
        "address": account.address,
        "private_key": account.get_private_key_hex(),
        "public_key": account.get_public_key_hex(),
        "created": "2024-01-01T00:00:00Z",
    }

    print("✅ Account exported:")
    print(json.dumps(exported_data, indent=2))

    # Import account
    imported_account = Account.from_private_key(exported_data["private_key"])
    print(f"\n✅ Account imported successfully")
    print(f"   Matches original: {imported_account.address == account.address}")

    print("\n🎉 All offline examples completed successfully!")
    print("\n💡 Next steps:")
    print("   1. Save your private keys securely")
    print("   2. Get TestNet tokens from Constellation community")
    print("   3. Update network endpoints when available")
    print("   4. Test network operations with correct endpoints")


if __name__ == "__main__":
    main()
