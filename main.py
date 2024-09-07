import openai
import requests
from dotenv import load_dotenv
import os
import json
import time

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

# Create an assistant
assistant = openai.beta.assistants.create(
    name="Travel and Weather Assistant",
    instructions="""You are a helpful assistant that can provide current weather information and travel advisories for cities and countries.
    If a user asks for weather information or a travel advisory without providing all necessary information (city for weather, city and country for travel advisory),
    politely ask for the missing information before making the API call. For weather queries, only the city is required. For travel advisories, both city and country are required.""",
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
    }]
)

# Create a thread
thread = openai.beta.threads.create()

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
print("Travel and Weather Assistant: Hello! How can I help you today?")
while True:
    user_input = input("You: ")
    if user_input.lower() in ["exit", "quit", "bye"]:
        print("Travel and Weather Assistant: Goodbye!")
        break
    response = chat_with_assistant(user_input)
    print("Travel and Weather Assistant:", response)