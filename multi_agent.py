from dotenv import load_dotenv
import logging
import requests
import time

_ = load_dotenv()

from agent import Agent, Swarm

# Initialize Swarm with telemetry (for Rivalz AI Network)
client = Swarm()

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
    instructions="""Determine which agent is best suited to handle the user's request within the Rivalz AI network and transfer the conversation to that agent.
    - For token transfers, staking and on-chain operations -> On-Chain Operations Agent
    - For TVL monitoring and financial analysis -> Financial Analyst Agent
    Never handle requests directly - always transfer to the appropriate specialist."""
)
onchain_operations_agent = Agent(
    name="On-Chain Operations Agent",
    instructions="Handle token transfers, staking, and on-chain operations for users within the Rivalz network.",
    functions=[process_onchain_request]
)
financial_analyst_agent = Agent(
    name="Financial Analyst Agent",
    instructions="Analyze and monitor financial data, including TVL changes and network activity in the blockchain ecosystem.",
    functions=[monitor_tvl_changes]
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
wha