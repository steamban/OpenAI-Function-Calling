import openai
import requests
from dotenv import load_dotenv
import os
import json
import time
import random
from datetime import datetime

# Load environment variables
load_dotenv()

# Set up OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# OpenWeather API key
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY")

# Function to get coordinates for a city
def get_coordinates(city):
    geocoding_url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&limit=1&appid={OPENWEATHER_API_KEY}"
    response = requests.get(geocoding_url)
    if response.status_code == 200:
        data = response.json()
        if data:
            lat = data[0]['lat']
            lon = data[0]['lon']
            return lat, lon
    return None, None

# Function to get current weather
def get_current_weather(city):
    lat, lon = get_coordinates(city)
    if lat is None or lon is None:
        return f"Unable to find coordinates for {city}"
    
    # Use the One Call API endpoint
    base_url = "https://api.openweathermap.org/data/2.5/weather"
    params = {
        "lat": lat,
        "lon": lon,
        "appid": OPENWEATHER_API_KEY,
        "units": "metric"
    }
    response = requests.get(base_url, params=params)
    if response.status_code == 200:
        try:
            data = response.json()
            
            weather_info = {}
            
            # Extract temperature
            if "current" in data:
                weather_info["Temperature"] = f"{data['current']['temp']}°C"
            elif "main" in data:
                weather_info["Temperature"] = f"{data['main']['temp']}°C"
            
            # Extract weather description
            if "current" in data and "weather" in data["current"]:
                weather_info["Description"] = data["current"]["weather"][0]["description"].capitalize()
            elif "weather" in data and isinstance(data["weather"], list):
                weather_info["Description"] = data["weather"][0]["description"].capitalize()
            
            # Extract humidity
            if "current" in data:
                weather_info["Humidity"] = f"{data['current']['humidity']}%"
            elif "main" in data:
                weather_info["Humidity"] = f"{data['main']['humidity']}%"
            
            # Format the weather information into a readable string
            weather_report = f"Weather in {city}:\n"
            for key, value in weather_info.items():
                weather_report += f"- {key}: {value}\n"
            
            return weather_report.strip()
        
        except KeyError:
            return "Error: Could not retrieve some weather data."
    else:
        return f"Error fetching weather data: {response.status_code}"

# Function for Travel Advisory API
def get_travel_advisory(city, country):
    if not city:
        return "Error: City is required for travel advisory."
    if not country:
        return "Error: Country is required for travel advisory."
    
    # This is a dummy function that simulates an API call
    advisories = {
        "low": "Exercise normal precautions",
        "medium": "Exercise increased caution",
        "high": "Reconsider travel",
        "extreme": "Do not travel"
    }
    
    # Simulate some logic based on the city and country
    risk_level = hash(f"{city}{country}") % 4
    risk_levels = list(advisories.keys())
    
    advisory = f"Travel Advisory for {city}, {country}:\n"
    advisory += f"Risk Level: {risk_levels[risk_level]}\n"
    advisory += f"Advisory: {advisories[risk_levels[risk_level]]}"
    
    return advisory

# New function for handling investments
def process_investment(amount=None, payment_mode=None, wire_id=None, transaction_date=None):
    if amount is None:
        return "Please provide the amount you'd like to invest."
    
    if payment_mode is None:
        return "Please choose a payment mode: ACH or wire transfer."
    
    if payment_mode.lower() not in ["ach", "wire transfer"]:
        return "Invalid payment mode. Please choose either ACH or wire transfer."
    
    if payment_mode.lower() == "wire transfer" and wire_id is None:
        return "Please provide the wire ID for your wire transfer."
    
    if transaction_date is None:
        return "Please provide the transaction date in YYYY-MM-DD format."
    
    try:
        date = datetime.strptime(transaction_date, "%Y-%m-%d")
        if date > datetime.now():
            return "The transaction date cannot be in the future. Please provide a valid date."
    except ValueError:
        return "Invalid date format. Please use YYYY-MM-DD."
    
    # Summarize the investment details
    summary = f"Investment Summary:\n"
    summary += f"Amount: ${amount}\n"
    summary += f"Payment Mode: {payment_mode}\n"
    if payment_mode.lower() == "wire transfer":
        summary += f"Wire ID: {wire_id}\n"
    summary += f"Transaction Date: {transaction_date}\n"
    
    return summary

# Function to simulate investment transaction
def process_transaction():
    # Simulate a transaction with 80% success rate
    return random.random() < 0.8

# Create an assistant
assistant = openai.beta.assistants.create(
    name="Weather, Travel, and Investment Assistant",
    instructions="""You are a helpful assistant that can provide current weather information, travel advisories, and process investments for the company you represent. 
    For weather and travel queries, ask for missing information before making API calls. For investments, follow these steps:
    1. Ask for the investment amount.
    2. Ask for the payment mode (ACH or wire transfer).
    3. If wire transfer, ask for the wire ID.
    4. Ask for the transaction date (YYYY-MM-DD format, not in the future).
    5. Summarize the investment details and ask for confirmation.
    6. Process the transaction and inform the user of the result.
    7. If successful, congratulate the user. If failed, offer to retry.
    At any point, if the user wants to exit the investment process, ask for confirmation before stopping.
    """,
    model="gpt-4-1106-preview",
    tools=[{
        "type": "function",
        "function": {
            "name": "get_current_weather",
            "description": "Get the current weather for a given city",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city"
                    }
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_travel_advisory",
            "description": "Get the travel advisory for a given city and country",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city"
                    },
                    "country": {
                        "type": "string",
                        "description": "The name of the country"
                    }
                },
                "required": ["city", "country"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_investment",
            "description": "Process an investment transaction",
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {
                        "type": "number",
                        "description": "The amount to invest"
                    },
                    "payment_mode": {
                        "type": "string",
                        "enum": ["ACH", "wire transfer"],
                        "description": "The mode of payment"
                    },
                    "wire_id": {
                        "type": "string",
                        "description": "The wire ID for wire transfers"
                    },
                    "transaction_date": {
                        "type": "string",
                        "description": "The date of the transaction (YYYY-MM-DD)"
                    }
                },
                "required": ["amount", "payment_mode", "transaction_date"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "process_transaction",
            "description": "Simulate processing the investment transaction",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    }]
)

# Create a thread
thread = openai.beta.threads.create()

# Update the chat_with_assistant function
def chat_with_assistant(user_input):
    try:
        # Add the user's message to the thread
        openai.beta.threads.messages.create(
            thread_id=thread.id,
            role="user",
            content=user_input
        )

        # Run the assistant
        run = openai.beta.threads.runs.create(
            thread_id=thread.id,
            assistant_id=assistant.id
        )

        # Wait for the run to complete or fail with a timeout   
        timeout = 60  # 60 seconds timeout
        start_time = time.time()
        while True:
            if time.time() - start_time > timeout:
                raise TimeoutError("The request timed out. Please try again later.")
            
            run = openai.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)

            if run.status == "requires_action":
                for tool_call in run.required_action.submit_tool_outputs.tool_calls:
                    try:
                        arguments = json.loads(tool_call.function.arguments)
                        if tool_call.function.name == "get_current_weather":
                            city = arguments.get("city")
                            if city:
                                weather = get_current_weather(city)
                                openai.beta.threads.runs.submit_tool_outputs(
                                    thread_id=thread.id,
                                    run_id=run.id,
                                    tool_outputs=[{
                                        "tool_call_id": tool_call.id,
                                        "output": str(weather)
                                    }]
                                )
                        elif tool_call.function.name == "get_travel_advisory":
                            city = arguments.get("city")
                            country = arguments.get("country")
                            advisory = get_travel_advisory(city, country)
                            openai.beta.threads.runs.submit_tool_outputs(
                                thread_id=thread.id,
                                run_id=run.id,
                                tool_outputs=[{
                                    "tool_call_id": tool_call.id,
                                    "output": str(advisory)
                                }]
                            )
                        elif tool_call.function.name == "process_investment":
                            result = process_investment(**arguments)
                            openai.beta.threads.runs.submit_tool_outputs(
                                thread_id=thread.id,
                                run_id=run.id,
                                tool_outputs=[{
                                    "tool_call_id": tool_call.id,
                                    "output": str(result)
                                }]
                            )
                        elif tool_call.function.name == "process_transaction":
                            result = process_transaction()
                            openai.beta.threads.runs.submit_tool_outputs(
                                thread_id=thread.id,
                                run_id=run.id,
                                tool_outputs=[{
                                    "tool_call_id": tool_call.id,
                                    "output": str(result)
                                }]
                            )
                    except json.JSONDecodeError:
                        pass
                    except Exception as e:
                        print(f"Error in tool call: {str(e)}")

            elif run.status == "completed":
                break
            elif run.status == "failed":
                return "I'm sorry, but I encountered an error while processing your request. Please try again."

            time.sleep(1)

        # Retrieve and return the assistant's response
        messages = openai.beta.threads.messages.list(thread_id=thread.id)
        if messages.data:
            for message in messages.data:
                if message.role == "assistant":
                    if isinstance(message.content, list):
                        return " ".join([item.text.value for item in message.content if hasattr(item, 'text')])
                    elif isinstance(message.content, str):
                        return message.content
                    else:
                        return str(message.content)
            return "No response received from assistant."
        else:
            return "No response received from assistant."

    except TimeoutError as e:
        return str(e)
    except Exception as e:
        return f"An error occurred: {str(e)}. Please try again."

# Main chat loop
print("Weather, Travel, and Investment Assistant: Hello! How can I help you today?")
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit", "bye"]:
        print("Weather, Travel, and Investment Assistant: Goodbye!")
        break
    response = chat_with_assistant(user_input)
    print("Weather, Travel, and Investment Assistant:", response)