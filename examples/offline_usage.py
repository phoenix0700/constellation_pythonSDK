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
    print(f"   Public Key: {account.public_key_hex}")
    print(f"   Private Key: {account.private_key_hex}")

    # Save account info
    account_info = {
        "address": account.address,
        "private_key": account.private_key_hex,
        "public_key": account.public_key_hex,
    }

    # Test loading from private key
    loaded_account = Account(account_info["private_key"])
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
        signature = account.sign_message(message)
        print(f"✅ Message {i} signed")
        print(f"   Message: {message}")
        print(f"   Signature: {signature[:20]}... ({len(signature)} chars)")

    # Example 3: Transaction signing
    print("\n💸 Transaction Signing")
    print("-" * 30)

    # Create sample transaction data using Transactions class
    from constellation_sdk import Transactions

    transaction_data = Transactions.create_dag_transfer(
        source=account.address,
        destination="DAG9a36ad52d8b6c67d7baa03397f4c90782a8",
        amount=1000000000,  # 1 DAG in nano-DAG
        fee=0,
    )

    signed_tx = account.sign_transaction(transaction_data)
    print(f"✅ Transaction Signed")
    print(f"   From: {transaction_data['source']}")
    print(f"   To: {transaction_data['destination']}")
    print(f"   Amount: {transaction_data['amount'] / 1_000_000_000} DAG")
    print(f"   Signed: {bool(signed_tx.get('proofs'))}")

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
        "private_key": account.private_key_hex,
        "public_key": account.public_key_hex,
        "created": "2024-01-01T00:00:00Z",
    }

    print("✅ Account exported:")
    print(json.dumps(exported_data, indent=2))

    # Import account
    imported_account = Account(exported_data["private_key"])
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
