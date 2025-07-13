import json
from constellation_sdk import GraphQLClient

# --- Configuration ---
# You can change this to any metagraph ID you want to inspect.
# We are using one of the production metagraphs we discovered earlier.
METAGRAPH_ID = "DAG7Ghth1WhWK83SB3MtXnnHYZbCsmiRTwJrgaW1"
NETWORK = "mainnet"

def fetch_metagraph_transactions(metagraph_id: str):
    """
    Demonstrates how to fetch recent transactions for a specific metagraph
    using the SDK's GraphQLClient.
    """
    print(f"Attempting to fetch recent transactions for Metagraph ID: {metagraph_id}...")

    try:
        # 1. Initialize the GraphQLClient
        # This is the most powerful way to query detailed on-chain data.
        graphql_client = GraphQLClient(NETWORK)

        # 2. Construct a GraphQL query to ask for transactions
        # We request the 'first: 10' transactions. You can change this number.
        # We ask for the hash, amount, timestamp, and type of each transaction.
        query = f"""
        query GetMetagraphTransactions {{
          metagraph(id: "{metagraph_id}") {{
            id
            recentTransactions: transactions(first: 10) {{
              hash
              amount
              timestamp
              type
              source
              destination
            }}
          }}
        }}
        """

        # 3. Execute the query
        print("Sending GraphQL query to the network...")
        response = graphql_client.execute(query)

        # 4. Process and display the response
        print("\n--- Query Result ---")
        if response.is_successful and response.data.get('metagraph'):
            metagraph_data = response.data['metagraph']
            transactions = metagraph_data.get('recentTransactions', [])
            
            print(f"Successfully queried Metagraph: {metagraph_data.get('id')}")
            
            if transactions:
                print("Found recent transactions:")
                print(json.dumps(transactions, indent=2))
            else:
                print("No recent transactions were found for this metagraph.")
                print("This could be because it's new, inactive, or its transactions are not public via this API.")

        else:
            print("Failed to retrieve metagraph data.")
            print("Raw server response:")
            response_dict = {
                "data": response.data,
                "errors": response.errors
            }
            print(json.dumps(response_dict, indent=2))

    except Exception as e:
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    fetch_metagraph_transactions(METAGRAPH_ID) 