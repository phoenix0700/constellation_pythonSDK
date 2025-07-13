import json
from constellation_sdk import MetagraphClient, GraphQLClient

def get_rich_metagraph_details():
    """
    Discovers production metagraphs and then uses the GraphQL client to fetch
    rich analytics for the first metagraph, printing the raw server response.
    """
    print("Connecting to the Constellation network to discover metagraphs...")

    try:
        # 1. Discover all production-ready metagraphs to get their IDs
        discovery_client = MetagraphClient('mainnet')
        metagraphs = discovery_client.discover_production_metagraphs()

        if not metagraphs:
            print("No production metagraphs found at this time.")
            return

        print(f"\n✅ Found {len(metagraphs)} production metagraphs. Now fetching raw details for the first one...\n")

        # 2. Initialize the GraphQLClient to get detailed analytics
        graphql_client = GraphQLClient('mainnet')
        
        # 3. Query details for the first metagraph
        first_metagraph_id = metagraphs[0]['id']
        print(f"--- Querying details for: {first_metagraph_id} ---")

        query = f"""
        query GetMetagraphDetails {{
          metagraph(id: "{first_metagraph_id}") {{
            id
            name
            tokenSymbol
            totalSupply
            transactionCount
          }}
        }}
        """
        
        try:
            # 4. Execute the query and get the raw response object
            response = graphql_client.execute(query)

            # 5. Print the raw data and errors from the response object
            print("\n--- Raw Server Response ---")
            response_dict = {
                "data": response.data,
                "errors": response.errors
            }
            print(json.dumps(response_dict, indent=2))

        except Exception as e:
             print(f"An error occurred during GraphQL query: {e}")

    except Exception as e:
        print(f"\nAn error occurred during discovery: {e}")
        print("Please ensure you have an internet connection and the SDK is installed correctly.")

if __name__ == "__main__":
    get_rich_metagraph_details() 