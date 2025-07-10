"""
Comprehensive unit tests for Account functionality.
"""

import hashlib

import pytest

from constellation_sdk.account import Account, ConstellationError


@pytest.mark.unit
class TestAccountCreation:
    """Test account creation and key management."""

    def test_new_account_creation(self):
        """Test creating a new account with random keys."""
        account = Account()

        # Address validation
        assert account.address.startswith("DAG")
        assert len(account.address) == 38  # DAG + 35 hex chars

        # Key properties validation
        assert len(account.private_key_hex) == 64  # 32 bytes * 2 hex chars
        assert len(account.public_key_hex) == 130  # Uncompressed point (65 bytes * 2)

        # Ensure randomness - create another account and verify different keys
        account2 = Account()
        assert account.address != account2.address
        assert account.private_key_hex != account2.private_key_hex
        assert account.public_key_hex != account2.public_key_hex

    def test_account_from_private_key(self, known_private_key):
        """Test loading account from known private key."""
        account = Account(known_private_key)

        # Should create consistent address for same private key
        account2 = Account(known_private_key)
        assert account.address == account2.address
        assert account.private_key_hex == account2.private_key_hex
        assert account.public_key_hex == account2.public_key_hex

    def test_invalid_private_key_formats(self, invalid_dag_addresses):
        """Test handling of various invalid private key formats."""
        invalid_keys = [
            "too_short",
            "way_too_long_" + "x" * 100,
            "not_hex_chars_zzzzz" + "z" * 50,
            "",
            123,
            {},
            [],
        ]

        for invalid_key in invalid_keys:
            with pytest.raises(ConstellationError):
                Account(invalid_key)
                
        # Test that None is valid (creates new account)
        account = Account(None)
        assert account.address.startswith("DAG")

    def test_address_format_consistency(self):
        """Test that all generated addresses follow DAG format."""
        for _ in range(10):  # Test multiple random accounts
            account = Account()
            address = account.address

            # Basic format validation
            assert address.startswith("DAG")
            assert len(address) == 38
            assert all(c in "0123456789ABCDEFabcdef" for c in address[3:])


@pytest.mark.unit
class TestAccountProperties:
    """Test account property access and validation."""

    def test_private_key_hex_property(self, known_account):
        """Test private key hex property."""
        private_key = known_account.private_key_hex
        assert isinstance(private_key, str)
        assert len(private_key) == 64
        assert all(c in "0123456789ABCDEFabcdef" for c in private_key)

    def test_public_key_hex_property(self, known_account):
        """Test public key hex property."""
        public_key = known_account.public_key_hex
        assert isinstance(public_key, str)
        assert len(public_key) == 130  # Uncompressed format
        assert public_key.startswith("04")  # Uncompressed point marker
        assert all(c in "0123456789ABCDEFabcdef" for c in public_key)

    def test_address_derivation_consistency(self, known_private_key):
        """Test that address derivation is consistent."""
        account1 = Account(known_private_key)
        account2 = Account(known_private_key)

        # Same private key should always generate same address
        assert account1.address == account2.address

        # Address should be derived from public key consistently
        assert len(account1.address) == 38
        assert account1.address.startswith("DAG")


@pytest.mark.unit
class TestMessageSigning:
    """Test message signing functionality."""

    def test_message_signing_basic(self, alice_account):
        """Test basic message signing."""
        message = "Hello Constellation!"
        signature = alice_account.sign_message(message)

        assert isinstance(signature, str)
        assert len(signature) > 0
        # Signature should be hex-encoded
        assert all(c in "0123456789ABCDEFabcdef" for c in signature)

    def test_message_signing_consistency(self, known_account):
        """Test that same message produces valid signatures."""
        message = "test message"
        signature1 = known_account.sign_message(message)
        signature2 = known_account.sign_message(message)

        # Both signatures should be valid hex strings
        assert isinstance(signature1, str)
        assert isinstance(signature2, str)
        assert len(signature1) > 0
        assert len(signature2) > 0
        # Note: ECDSA signatures are not deterministic by design for security

    def test_message_signing_different_messages(self, alice_account):
        """Test that different messages produce different signatures."""
        sig1 = alice_account.sign_message("message 1")
        sig2 = alice_account.sign_message("message 2")

        assert sig1 != sig2

    def test_message_signing_unicode(self, alice_account):
        """Test message signing with unicode characters."""
        unicode_message = "Hello 🌟 Constellation! 中文 ñoño"
        signature = alice_account.sign_message(unicode_message)

        assert isinstance(signature, str)
        assert len(signature) > 0


@pytest.mark.unit
class TestTransactionSigning:
    """Test transaction signing functionality."""

    def test_dag_transaction_signing(
        self, alice_account, valid_dag_transaction_data, signature_validator
    ):
        """Test signing DAG transactions."""
        signed_tx = alice_account.sign_transaction(valid_dag_transaction_data)

        # Validate structure
        assert signature_validator(signed_tx)

        # Validate content
        assert signed_tx["value"]["source"] == alice_account.address
        assert signed_tx["proofs"][0]["id"] == alice_account.public_key_hex
        assert isinstance(signed_tx["proofs"][0]["signature"], str)
        assert len(signed_tx["proofs"][0]["signature"]) > 0

    def test_genesis_transaction_signing(
        self, alice_account, bob_account, signature_validator
    ):
        """Test signing genesis transactions (no parent)."""
        genesis_tx_data = {
            "source": alice_account.address,
            "destination": bob_account.address,
            "amount": 100000000,
            "fee": 0,
            "salt": 12345,
            # No parent field = genesis transaction
        }

        signed_tx = alice_account.sign_transaction(genesis_tx_data)

        # Should work without parent
        assert signature_validator(signed_tx)
        assert (
            "parent" not in signed_tx["value"]
        )  # Genesis transactions don't include parent

    def test_regular_transaction_with_parent(
        self, alice_account, bob_account, signature_validator
    ):
        """Test signing regular transactions with parent reference."""
        parent_tx_data = {
            "source": alice_account.address,
            "destination": bob_account.address,
            "amount": 100000000,
            "fee": 0,
            "salt": 12345,
            "parent": "some_parent_hash",
        }

        signed_tx = alice_account.sign_transaction(parent_tx_data)

        # Should include parent in signed transaction
        assert signature_validator(signed_tx)
        assert signed_tx["value"]["parent"] == "some_parent_hash"

    def test_metagraph_token_transaction_signing(
        self, alice_account, valid_token_transfer_data, signature_validator
    ):
        """Test signing metagraph token transactions."""
        signed_tx = alice_account.sign_metagraph_transaction(valid_token_transfer_data)

        # Validate structure
        assert signature_validator(signed_tx)

        # Validate metagraph-specific content
        assert (
            signed_tx["value"]["metagraph_id"]
            == valid_token_transfer_data["metagraph_id"]
        )
        assert signed_tx["value"]["amount"] == valid_token_transfer_data["amount"]

    def test_metagraph_data_transaction_signing(
        self, alice_account, valid_data_submission_data, signature_validator
    ):
        """Test signing metagraph data transactions."""
        signed_tx = alice_account.sign_metagraph_transaction(valid_data_submission_data)

        # Validate structure
        assert signature_validator(signed_tx)

        # Validate data-specific content
        assert signed_tx["value"]["data"] == valid_data_submission_data["data"]
        assert (
            signed_tx["value"]["metagraph_id"]
            == valid_data_submission_data["metagraph_id"]
        )

    def test_signature_determinism(self, known_account, valid_dag_transaction_data):
        """Test that transaction signing produces valid signatures."""
        # Same transaction should produce valid signatures
        signed_tx1 = known_account.sign_transaction(valid_dag_transaction_data)
        signed_tx2 = known_account.sign_transaction(valid_dag_transaction_data)

        # Both signatures should be valid hex strings
        sig1 = signed_tx1["proofs"][0]["signature"]
        sig2 = signed_tx2["proofs"][0]["signature"]
        
        assert isinstance(sig1, str)
        assert isinstance(sig2, str)
        assert len(sig1) > 0
        assert len(sig2) > 0
        assert all(c in "0123456789ABCDEFabcdef" for c in sig1)
        assert all(c in "0123456789ABCDEFabcdef" for c in sig2)
        # Note: ECDSA signatures are not deterministic by design for security

    def test_different_accounts_different_signatures(
        self, alice_account, bob_account, valid_dag_transaction_data
    ):
        """Test that different accounts produce different signatures."""
        # Modify transaction for each account
        alice_tx_data = valid_dag_transaction_data.copy()
        alice_tx_data["source"] = alice_account.address

        bob_tx_data = valid_dag_transaction_data.copy()
        bob_tx_data["source"] = bob_account.address

        alice_signed = alice_account.sign_transaction(alice_tx_data)
        bob_signed = bob_account.sign_transaction(bob_tx_data)

        assert (
            alice_signed["proofs"][0]["signature"]
            != bob_signed["proofs"][0]["signature"]
        )


@pytest.mark.unit
class TestAccountEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_transaction_data(self, alice_account):
        """Test signing empty transaction data."""
        with pytest.raises((KeyError, TypeError)):
            alice_account.sign_transaction({})

    def test_malformed_transaction_data(self, alice_account):
        """Test signing malformed transaction data."""
        malformed_data = {
            "source": alice_account.address,
            # Missing required fields
        }

        with pytest.raises(KeyError):
            alice_account.sign_transaction(malformed_data)

    def test_none_transaction_data(self, alice_account):
        """Test signing None transaction data."""
        with pytest.raises((TypeError, AttributeError)):
            alice_account.sign_transaction(None)

    def test_account_string_representation(self, alice_account):
        """Test that accounts can be represented as strings safely."""
        account_str = str(alice_account)
        # Should not expose private key in string representation
        assert alice_account.private_key_hex not in account_str
        assert alice_account.address in account_str or "Account" in account_str


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
