"""
Comprehensive unit tests for Transactions functionality.
"""

import time
from unittest.mock import Mock, patch

import pytest

from constellation_sdk.transactions import Transactions, ValidationError


@pytest.mark.unit
class TestDAGTransfers:
    """Test DAG token transfer creation."""

    def test_create_dag_transfer_basic(
        self, alice_account, bob_account, transaction_validator
    ):
        """Test basic DAG transfer creation."""
        transfer = Transactions.create_dag_transfer(
            source=alice_account.address,
            destination=bob_account.address,
            amount=100000000,  # 1 DAG
        )

        # Validate structure
        assert transaction_validator(transfer, "dag")

        # Validate content
        assert transfer["source"] == alice_account.address
        assert transfer["destination"] == bob_account.address
        assert transfer["amount"] == 100000000
        assert transfer["fee"] == 0
        assert "salt" in transfer
        assert isinstance(transfer["salt"], int)

    def test_create_dag_transfer_with_fee(self, alice_account, bob_account):
        """Test DAG transfer with custom fee."""
        transfer = Transactions.create_dag_transfer(
            source=alice_account.address,
            destination=bob_account.address,
            amount=100000000,
            fee=1000000,
        )

        assert transfer["fee"] == 1000000

    def test_create_dag_transfer_with_custom_salt(self, alice_account, bob_account):
        """Test DAG transfer with custom salt."""
        custom_salt = 12345
        transfer = Transactions.create_dag_transfer(
            source=alice_account.address,
            destination=bob_account.address,
            amount=100000000,
            salt=custom_salt,
        )

        assert transfer["salt"] == custom_salt

    def test_create_dag_transfer_with_parent(self, alice_account, bob_account):
        """Test DAG transfer with parent transaction."""
        parent_hash = "abc123def456"
        transfer = Transactions.create_dag_transfer(
            source=alice_account.address,
            destination=bob_account.address,
            amount=100000000,
            parent=parent_hash,
        )

        assert transfer["parent"] == parent_hash

    def test_dag_transfer_validation_errors(self, alice_account, invalid_dag_addresses):
        """Test DAG transfer validation with invalid inputs."""

        # Invalid source address
        with pytest.raises(ValidationError):
            Transactions.create_dag_transfer(
                source="INVALID", destination=alice_account.address, amount=100000000
            )

        # Invalid destination address
        with pytest.raises(ValidationError):
            Transactions.create_dag_transfer(
                source=alice_account.address, destination="INVALID", amount=100000000
            )

        # Negative amount
        with pytest.raises(ValidationError):
            Transactions.create_dag_transfer(
                source=alice_account.address,
                destination=alice_account.address,
                amount=-1000000,
            )

        # Zero amount
        with pytest.raises(ValidationError):
            Transactions.create_dag_transfer(
                source=alice_account.address,
                destination=alice_account.address,
                amount=0,
            )

        # Negative fee
        with pytest.raises(ValidationError):
            Transactions.create_dag_transfer(
                source=alice_account.address,
                destination=alice_account.address,
                amount=100000000,
                fee=-1000,
            )


@pytest.mark.unit
class TestTokenTransfers:
    """Test metagraph token transfer creation."""

    def test_create_token_transfer_basic(
        self, alice_account, bob_account, test_metagraph_id, transaction_validator
    ):
        """Test basic token transfer creation."""
        transfer = Transactions.create_token_transfer(
            source=alice_account.address,
            destination=bob_account.address,
            amount=1000000000,  # 10 tokens
            metagraph_id=test_metagraph_id,
        )

        # Validate structure
        assert transaction_validator(transfer, "token")

        # Validate content
        assert transfer["source"] == alice_account.address
        assert transfer["destination"] == bob_account.address
        assert transfer["amount"] == 1000000000
        assert transfer["metagraph_id"] == test_metagraph_id
        assert transfer["fee"] == 0
        assert "salt" in transfer

    def test_create_token_transfer_with_fee(
        self, alice_account, bob_account, test_metagraph_id
    ):
        """Test token transfer with custom fee."""
        transfer = Transactions.create_token_transfer(
            source=alice_account.address,
            destination=bob_account.address,
            amount=1000000000,
            metagraph_id=test_metagraph_id,
            fee=5000000,
        )

        assert transfer["fee"] == 5000000

    def test_token_transfer_validation_errors(self, alice_account):
        """Test token transfer validation with invalid inputs."""

        # Invalid metagraph ID
        with pytest.raises(ValidationError):
            Transactions.create_token_transfer(
                source=alice_account.address,
                destination=alice_account.address,
                amount=1000000000,
                metagraph_id="INVALID_METAGRAPH",
            )

        # Empty metagraph ID
        with pytest.raises(ValidationError):
            Transactions.create_token_transfer(
                source=alice_account.address,
                destination=alice_account.address,
                amount=1000000000,
                metagraph_id="",
            )


@pytest.mark.unit
class TestDataSubmissions:
    """Test metagraph data submission creation."""

    def test_create_data_submission_basic(
        self, alice_account, test_metagraph_id, test_sensor_data, transaction_validator
    ):
        """Test basic data submission creation."""
        submission = Transactions.create_data_submission(
            source=alice_account.address,
            data=test_sensor_data,
            metagraph_id=test_metagraph_id,
        )

        # Validate structure
        assert transaction_validator(submission, "data")

        # Validate content
        assert submission["source"] == alice_account.address
        assert (
            submission["destination"] == alice_account.address
        )  # Data submissions to self
        assert submission["data"] == test_sensor_data
        assert submission["metagraph_id"] == test_metagraph_id
        assert "timestamp" in submission
        assert "salt" in submission

    def test_create_data_submission_with_custom_destination(
        self, alice_account, bob_account, test_metagraph_id, test_sensor_data
    ):
        """Test data submission with custom destination."""
        submission = Transactions.create_data_submission(
            source=alice_account.address,
            destination=bob_account.address,
            data=test_sensor_data,
            metagraph_id=test_metagraph_id,
        )

        assert submission["destination"] == bob_account.address

    def test_create_data_submission_with_timestamp(
        self, alice_account, test_metagraph_id, test_sensor_data
    ):
        """Test data submission with custom timestamp."""
        custom_timestamp = 1642248600
        submission = Transactions.create_data_submission(
            source=alice_account.address,
            data=test_sensor_data,
            metagraph_id=test_metagraph_id,
            timestamp=custom_timestamp,
        )

        assert submission["timestamp"] == custom_timestamp

    def test_data_submission_validation_errors(self, alice_account, test_metagraph_id):
        """Test data submission validation with invalid inputs."""

        # Empty data
        with pytest.raises(ValidationError):
            Transactions.create_data_submission(
                source=alice_account.address, data={}, metagraph_id=test_metagraph_id
            )

        # None data
        with pytest.raises(ValidationError):
            Transactions.create_data_submission(
                source=alice_account.address, data=None, metagraph_id=test_metagraph_id
            )

        # Invalid timestamp
        with pytest.raises(ValidationError):
            Transactions.create_data_submission(
                source=alice_account.address,
                data={"test": "value"},
                metagraph_id=test_metagraph_id,
                timestamp=-1,
            )


@pytest.mark.unit
class TestBatchTransfers:
    """Test batch transfer functionality."""

    def test_create_batch_transfer_dag_only(self, alice_account, valid_dag_addresses):
        """Test batch transfer with only DAG transfers."""
        transfers = [
            {"destination": valid_dag_addresses[0], "amount": 100000000},
            {"destination": valid_dag_addresses[1], "amount": 200000000},
            {"destination": valid_dag_addresses[2], "amount": 300000000},
        ]

        result = Transactions.create_batch_transfer(
            source=alice_account.address, transfers=transfers
        )

        # Validate structure
        assert "dag_transfers" in result
        assert len(result["dag_transfers"]) == 3
        assert result.get("token_transfers", []) == []
        assert result.get("data_submissions", []) == []

        # Validate content
        for i, transfer in enumerate(result["dag_transfers"]):
            assert transfer["source"] == alice_account.address
            assert transfer["destination"] == valid_dag_addresses[i]
            assert transfer["amount"] == (i + 1) * 100000000

    def test_create_batch_transfer_mixed_types(
        self, alice_account, valid_dag_addresses, test_metagraph_id, test_sensor_data
    ):
        """Test batch transfer with mixed transaction types."""
        dag_transfers = [{"destination": valid_dag_addresses[0], "amount": 100000000}]

        token_transfers = [
            {
                "destination": valid_dag_addresses[1],
                "amount": 1000000000,
                "metagraph_id": test_metagraph_id,
            }
        ]

        data_submissions = [
            {"data": test_sensor_data, "metagraph_id": test_metagraph_id}
        ]

        result = Transactions.create_batch_transfer(
            source=alice_account.address,
            transfers=dag_transfers,
            token_transfers=token_transfers,
            data_submissions=data_submissions,
        )

        # Validate all types present
        assert len(result["dag_transfers"]) == 1
        assert len(result["token_transfers"]) == 1
        assert len(result["data_submissions"]) == 1

        # Validate content
        assert result["dag_transfers"][0]["destination"] == valid_dag_addresses[0]
        assert result["token_transfers"][0]["metagraph_id"] == test_metagraph_id
        assert result["data_submissions"][0]["data"] == test_sensor_data

    def test_batch_transfer_with_custom_fee(self, alice_account, valid_dag_addresses):
        """Test batch transfer with custom fee for all transactions."""
        transfers = [{"destination": valid_dag_addresses[0], "amount": 100000000}]

        result = Transactions.create_batch_transfer(
            source=alice_account.address, transfers=transfers, fee=1000000
        )

        # All transfers should have custom fee
        assert result["dag_transfers"][0]["fee"] == 1000000

    def test_batch_transfer_validation_errors(self, alice_account):
        """Test batch transfer validation errors."""

        # Empty transfers
        with pytest.raises(ValidationError):
            Transactions.create_batch_transfer(
                source=alice_account.address, transfers=[]
            )

        # No transfers provided
        with pytest.raises(ValidationError):
            Transactions.create_batch_transfer(source=alice_account.address)


@pytest.mark.unit
class TestTransactionUtilities:
    """Test transaction utility methods."""

    def test_validate_dag_address_valid(self, valid_dag_addresses):
        """Test validation of valid DAG addresses."""
        for address in valid_dag_addresses:
            # Should not raise exception
            Transactions._validate_dag_address(address)

    def test_validate_dag_address_invalid(self, invalid_dag_addresses):
        """Test validation of invalid DAG addresses."""
        for address in invalid_dag_addresses:
            with pytest.raises(ValidationError):
                Transactions._validate_dag_address(address)

    def test_validate_amount_valid(self):
        """Test validation of valid amounts."""
        valid_amounts = [1, 1000000, 100000000, 999999999999]

        for amount in valid_amounts:
            # Should not raise exception
            Transactions._validate_amount(amount)

    def test_validate_amount_invalid(self):
        """Test validation of invalid amounts."""
        invalid_amounts = [0, -1, -1000000, "100", None, 1.5, float("inf")]

        for amount in invalid_amounts:
            with pytest.raises(ValidationError):
                Transactions._validate_amount(amount)

    def test_generate_salt(self):
        """Test salt generation."""
        salt1 = Transactions._generate_salt()
        salt2 = Transactions._generate_salt()

        # Should be different values
        assert salt1 != salt2

        # Should be integers
        assert isinstance(salt1, int)
        assert isinstance(salt2, int)

        # Should be in reasonable range
        assert 0 < salt1 < 2**32
        assert 0 < salt2 < 2**32

    def test_get_timestamp(self):
        """Test timestamp generation."""
        timestamp = Transactions._get_timestamp()
        current_time = int(time.time())

        # Should be close to current time (within 1 second)
        assert abs(timestamp - current_time) <= 1
        assert isinstance(timestamp, int)


@pytest.mark.unit
class TestTransactionSizeEstimation:
    """Test transaction size estimation functionality."""

    def test_estimate_dag_transaction_size(self, alice_account, bob_account):
        """Test DAG transaction size estimation."""
        transfer = Transactions.create_dag_transfer(
            source=alice_account.address,
            destination=bob_account.address,
            amount=100000000,
        )

        estimated_size = Transactions.estimate_transaction_size(transfer)

        # Should return reasonable size estimate
        assert isinstance(estimated_size, int)
        assert estimated_size > 100  # Minimum reasonable size
        assert estimated_size < 5000  # Maximum reasonable size for simple transaction

    def test_estimate_token_transaction_size(
        self, alice_account, bob_account, test_metagraph_id
    ):
        """Test token transaction size estimation."""
        transfer = Transactions.create_token_transfer(
            source=alice_account.address,
            destination=bob_account.address,
            amount=1000000000,
            metagraph_id=test_metagraph_id,
        )

        estimated_size = Transactions.estimate_transaction_size(transfer)

        # Token transactions should be larger than DAG transactions
        assert isinstance(estimated_size, int)
        assert estimated_size > 200

    def test_estimate_data_transaction_size(
        self, alice_account, test_metagraph_id, test_sensor_data
    ):
        """Test data transaction size estimation."""
        submission = Transactions.create_data_submission(
            source=alice_account.address,
            data=test_sensor_data,
            metagraph_id=test_metagraph_id,
        )

        estimated_size = Transactions.estimate_transaction_size(submission)

        # Data transactions should be largest
        assert isinstance(estimated_size, int)
        assert estimated_size > 300


@pytest.mark.unit
class TestTransactionEdgeCases:
    """Test edge cases and error conditions."""

    def test_create_dag_transfer_minimum_values(self, alice_account, bob_account):
        """Test DAG transfer with minimum valid values."""
        transfer = Transactions.create_dag_transfer(
            source=alice_account.address,
            destination=bob_account.address,
            amount=1,  # Minimum amount
            fee=0,  # Minimum fee
        )

        assert transfer["amount"] == 1
        assert transfer["fee"] == 0

    def test_create_dag_transfer_maximum_values(self, alice_account, bob_account):
        """Test DAG transfer with maximum values."""
        max_amount = 2**53 - 1  # JavaScript safe integer
        transfer = Transactions.create_dag_transfer(
            source=alice_account.address,
            destination=bob_account.address,
            amount=max_amount,
            fee=max_amount,
        )

        assert transfer["amount"] == max_amount
        assert transfer["fee"] == max_amount

    def test_self_transfer(self, alice_account):
        """Test transfer to self (should be valid)."""
        transfer = Transactions.create_dag_transfer(
            source=alice_account.address,
            destination=alice_account.address,
            amount=100000000,
        )

        assert transfer["source"] == transfer["destination"]

    def test_large_data_submission(self, alice_account, test_metagraph_id):
        """Test data submission with large data payload."""
        large_data = {
            "sensor_readings": [{"value": i, "timestamp": i} for i in range(1000)],
            "metadata": {"description": "x" * 1000},
        }

        submission = Transactions.create_data_submission(
            source=alice_account.address,
            data=large_data,
            metagraph_id=test_metagraph_id,
        )

        assert submission["data"] == large_data

        # Size estimation should handle large data
        estimated_size = Transactions.estimate_transaction_size(submission)
        assert estimated_size > 10000  # Should be large


@pytest.mark.unit
class TestConvenienceFunctions:
    """Test backward compatibility and convenience functions."""

    def test_convenience_import(self):
        """Test that convenience functions can be imported."""
        from constellation_sdk import (create_dag_transfer,
                                       create_data_submission,
                                       create_token_transfer)

        # Should be callable functions
        assert callable(create_dag_transfer)
        assert callable(create_token_transfer)
        assert callable(create_data_submission)

    def test_convenience_dag_transfer(self, alice_account, bob_account):
        """Test convenience function for DAG transfers."""
        from constellation_sdk import create_dag_transfer

        transfer = create_dag_transfer(
            source=alice_account.address,
            destination=bob_account.address,
            amount=100000000,
        )

        # Should produce same result as Transactions.create_dag_transfer
        expected = Transactions.create_dag_transfer(
            source=alice_account.address,
            destination=bob_account.address,
            amount=100000000,
            salt=transfer["salt"],  # Use same salt for comparison
        )

        assert transfer["source"] == expected["source"]
        assert transfer["destination"] == expected["destination"]
        assert transfer["amount"] == expected["amount"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
