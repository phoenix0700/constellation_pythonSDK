"""
Example of using the Constellation SDK to get the full list of DAG holders
from a mainnet snapshot.
"""

from constellation_sdk.network import Network


def main():
    """
    Fetches the full list of DAG holders and prints a summary.
    """
    print("Initializing Constellation Network interface for mainnet...")
    # Initialize the network object for the 'mainnet'
    network = Network("mainnet")

    print("Fetching snapshot holders...")
    try:
        # Get the list of all holders from the latest snapshot
        holders = network.get_snapshot_holders()

        if not holders:
            print("No holders found or snapshot data is unavailable.")
            return

        # Sort holders by amount in descending order
        sorted_holders = sorted(holders, key=lambda x: x["amount"], reverse=True)

        # Print summary
        print(f"\nSuccessfully fetched snapshot data.")
        print(f"Total unique holders: {len(holders)}")

        # Print top 5 holders
        print("\nTop 5 DAG Holders:")
        for i, holder in enumerate(sorted_holders[:5]):
            print(
                f"  {i+1}. Wallet: {holder['wallet']}, Amount: {holder['amount']:,.2f} DAG"
            )

    except Exception as e:
        print(f"An error occurred: {e}")


if __name__ == "__main__":
    main()
