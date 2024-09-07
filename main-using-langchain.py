import os
from datetime import datetime
from typing import List, Dict, Any
from dotenv import load_dotenv
from langchain.chains import LLMChain
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.tools import Tool
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.schema import SystemMessage, HumanMessage
from langchain_core.messages.ai import AIMessage
import requests
import random

# Load environment variables
load_dotenv()

# Set up API keys
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Function to get current weather
def get_current_weather(city: str) -> str:
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "q": city,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        data = response.json()
        weather_info = {
            "Temperature": f"{data['main']['temp']}°C",
            "Description": data['weather'][0]['description'].capitalize(),
            "Humidity": f"{data['main']['humidity']}%"
        }
        return "\n".join([f"{k}: {v}" for k, v in weather_info.items()])
    else:
        return f"Error fetching weather data: {response.status_code}"

# Function to get travel advisory
def get_travel_advisory(city: str, country: str) -> str:
    # This is a dummy function that simulates an API call
    advisories = ["Exercise normal precautions", "Exercise increased caution", "Reconsider travel", "Do not travel"]
    risk_level = hash(f"{city}{country}") % 4
    return f"Travel Advisory for {city}, {country}:\nRisk Level: {advisories[risk_level]}"

# Function to process investment
def process_investment(amount: float, payment_mode: str, wire_id: str = None, transaction_date: str = None) -> str:
    if payment_mode.lower() not in ["ach", "wire transfer"]:
        return "Invalid payment mode. Please choose either ACH or wire transfer."
    
    if payment_mode.lower() == "wire transfer" and not wire_id:
        return "Please provide the wire ID for your wire transfer."
    
    if transaction_date:
        try:
            date = datetime.strptime(transaction_date, "%Y-%m-%d")
            if date > datetime.now():
                return "The transaction date cannot be in the future. Please provide a valid date."
        except ValueError:
            return "Invalid date format. Please use YYYY-MM-DD."
    
    summary = f"Investment Summary:\n"
    summary += f"Amount: ${amount}\n"
    summary += f"Payment Mode: {payment_mode}\n"
    if payment_mode.lower() == "wire transfer":
        summary += f"Wire ID: {wire_id}\n"
    summary += f"Transaction Date: {transaction_date}\n"
    
    return summary

# Function to simulate investment transaction
def process_transaction() -> bool:
    return random.random() < 0.8

# Define tools
tools = [
    Tool(
        name="CurrentWeather",
        func=get_current_weather,
        description="Get the current weather for a given city"
    ),
    Tool(
        name="TravelAdvisory",
        func=get_travel_advisory,
        description="Get the travel advisory for a given city and country"
    ),
    Tool(
        name="ProcessInvestment",
        func=process_investment,
        description="Process an investment transaction"
    ),
    Tool(
        name="ProcessTransaction",
        func=process_transaction,
        description="Simulate processing the investment transaction"
    )
]

# Set up the language model
llm = ChatOpenAI(temperature=0, model="gpt-4-1106-preview")

# Define the prompt template
prompt = ChatPromptTemplate.from_messages([
    SystemMessage(content="""You are a helpful assistant that can provide current weather information, travel advisories, and process investments for the company you represent. 
    For weather and travel queries, ask for missing information before making API calls. For investments, follow these steps:
    1. Ask for the investment amount.
    2. Ask for the payment mode (ACH or wire transfer).
    3. If wire transfer, ask for the wire ID.
    4. Ask for the transaction date (YYYY-MM-DD format, not in the future).
    5. Summarize the investment details and ask for confirmation.
    6. Process the transaction and inform the user of the result.
    7. If successful, congratulate the user. If failed, offer to retry.
    At any point, if the user wants to exit the investment process, ask for confirmation before stopping."""),
    MessagesPlaceholder(variable_name="chat_history"),
    HumanMessage(content="{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad")
])

# Set up the agent
# agent = OpenAIFunctionsAgent(llm=llm, tools=tools, prompt=prompt)
agent = create_openai_functions_agent(llm=llm, tools=tools, prompt=prompt)

# Set up the agent executor
agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

# Main chat loop
print("Weather, Travel, and Investment Assistant: Hello! How can I help you today?")
chat_history = []
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit", "bye"]:
        print("Weather, Travel, and Investment Assistant: Goodbye!")
        break
    
    response = agent_executor.invoke(
        {
            "input": user_input,
            "chat_history": chat_history
        }
    )
    assistant_response = response["output"]
    print("Weather, Travel, and Investment Assistant:", assistant_response)
    chat_history.extend([HumanMessage(content=user_input), AIMessage(content=assistant_response)])