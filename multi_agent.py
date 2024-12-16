from dotenv import load_dotenv
import logging
import requests
import time

_ = load_dotenv()

from agent import Agent, Swarm
from langchain_community.tools import DuckDuckGoSearchResults


# Initialize Swarm with telemetry (for Rivalz AI Network)
client = Swarm()

from langchain_community.tools import DuckDuckGoSearchResults

from langchain_community.tools import DuckDuckGoSearchResults

def rivalz_network_info(query: str) -> dict:
    """
    Perform a search to retrieve information about Rivalz AI and return structured, relevant results.

    Parameters:
    - query (str): The specific query about Rivalz AI.

    Returns:
    - dict: A dictionary containing relevant search results or an error message.
    """
    try:
        # Initialize DuckDuckGo Search Results tool
        search_tool = DuckDuckGoSearchResults()
        
        # Add specific context for Rivalz AI to the query
        full_query = f"Rivalz AI {query}"
        
        # Perform the search and retrieve the results
        results = search_tool.run(full_query)
        
        # Validate results and filter for relevance
        if not results:
            return {"message": f"No results found for query: '{query}'."}
        
        # Filter and structure the output for clarity
        relevant_results = [
            {
                "title": result.get("title", "No Title"),
                "url": result.get("link", "No URL"),
                "snippet": result.get("snippet", "No Snippet")
            }
            for result in results if "Rivalz AI" in result.get("title", "") or "Rivalz AI" in result.get("snippet", "")
        ]
        
        # If no relevant results, return a fallback message
        if not relevant_results:
            return {"message": f"No relevant results found for Rivalz AI query: '{query}'."}
        
        return {"results": relevant_results[:5]}  # Return up to 5 relevant results

    except Exception as e:
        return {"error": "Search Tool Error", "message": str(e)}



def monitor_tvl_changes(retries: int = 3):
    """
    Fetch the Total Value Locked (TVL) for all chains using DeFiLlama's /v2/chains endpoint.
    Includes retries for handling failures.
    """
    url = "https://api.llama.fi/v2/chains"  # Endpoint for TVL of all chains

    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()  # Raise error for non-2xx status codes
            data = response.json()

            # Print or process the TVL data for all chains
            for chain in data:
                print(f"Chain: {chain['name']}, TVL: {chain['tvl']}")
            
            return data  # Return the list of TVLs for further processing if needed

        except requests.RequestException as e:
            logging.error(f"Attempt {attempt + 1} failed: {e}")
        except ValueError as ve:
            logging.error(f"Data error: {ve}")
            raise

    raise RuntimeError("Failed to fetch TVL for all chains after multiple attempts")


def crypto_price(query: str) -> dict:
    """
    Fetch current cryptocurrency prices.

    Parameters:
    - query (str): The cryptocurrency name or symbol (e.g., BTC, ETH, Bitcoin).

    Returns:
    - dict: A dictionary containing the current price in USD or an error message.
    """
    # Use CoinGecko's simple/price endpoint
    url = "https://api.coingecko.com/api/v3/simple/price"
    params = {"ids": query.lower(), "vs_currencies": "usd"}

    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()

        # Check if the response contains valid data
        data = response.json()
        if query.lower() in data:
            price = data[query.lower()]["usd"]
            return {"message": f"The current price of {query.upper()} is ${price:.2f} USD."}
        else:
            return {"message": f"Unable to retrieve the price for '{query}'. Check the cryptocurrency name or symbol."}
    except requests.RequestException as e:
        return {"error": "Network Error", "message": str(e)}
    except KeyError:
        return {"error": "Data Error", "message": f"Invalid response for query: {query}"}



def process_onchain_request(request_id, request_type="NOT SPECIFIED"):
    """Process on-chain requests (e.g., token transfers, staking operations). Ask for user confirmation before proceeding."""
    print(f"[mock] Processing on-chain request {request_id} of type {request_type}...")
    return "Request processed!"

def notify_rivalz_agents():
    """Notify relevant Rivalz agents about network updates or user actions."""
    print("[mock] Notifying Rivalz agents about updates...")
    return "Agents notified!"

# Create the agents
triage_agent = Agent(
    name="Rivalz Triage Agent",
    instructions="""Handle general queries about  RIVALZ, also you direct the user to which agent is best suited to handle the user's request and transfer the conversation to that agent.
    - For token transfers, staking and on-chain operations -> On-Chain Operations Agent
    - For TVL monitoring, crypto price and financial analysis -> Financial Analyst Agent
    In specific cases - always transfer to the appropriate specialist.""",
    functions=[rivalz_network_info]  # <-- COMMA ADDED HERE
)

onchain_operations_agent = Agent(
    name="On-Chain Operations Agent",
    instructions="Handle token transfers, staking, and on-chain operations for users.",
    functions=[process_onchain_request]
)

financial_analyst_agent = Agent(
    name="Financial Analyst Agent",
    instructions="Analyze and monitor financial data, crypto price including TVL changes and network activity in the blockchain ecosystem.",
    functions=[monitor_tvl_changes, crypto_price]
)

# Define transfer functions
def transfer_back_to_triage():
    """Call this function if the user request needs to be handled by the triage agent."""
    return triage_agent

def transfer_to_onchain_operations():
    """Transfer the conversation to the On-Chain Operations Agent."""
    return onchain_operations_agent

def transfer_to_financial_analyst():
    """Transfer the conversation to the Financial Analyst Agent."""
    return financial_analyst_agent

# Assign functions to the agents
triage_agent.functions = [transfer_to_onchain_operations, transfer_to_financial_analyst]
onchain_operations_agent.functions.append(transfer_back_to_triage)
financial_analyst_agent.functions.append(transfer_back_to_triage)

print("Starting Rivalz AI Agents - Triage, On-Chain Operations, and Financial Analyst Agents")

messages = []
agent = triage_agent

while True:
    user_input = input("\033[90mUser\033[0m: ")
    messages.append({"role": "user", "content": user_input})

    response = client.run(agent=agent, messages=messages)
    
    for message in response.messages:
        if message["role"] == "assistant" and message.get("content"):
            print(f"\033[94m{message['sender']}\033[0m: {message['content']}")
        elif message["role"] == "tool":
            tool_name = message.get("tool_name", "")
            if tool_name in ["process_onchain_request", "monitor_tvl_changes"]:
                print(f"\033[93mSystem\033[0m: {message['content']}")
    
    messages.extend(response.messages)
    agent = response.agent
