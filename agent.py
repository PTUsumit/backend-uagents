from uagents import Agent, Context, Model
import requests
from dotenv import load_dotenv
import os
from dataclasses import dataclass

load_dotenv()
api_key = os.getenv('API_KEY')

class TestRequest(Model):
    city_name: str
    state_code: str
    country_code: str

class Response(Model):
    status: str
    message: str
    data: dict

agent = Agent(
    name="weather_agent",
    seed="weather_seed",
    port=8001,
    endpoint="https://backend-uagents-k82dco92y-sumit-srimanis-projects.vercel.app/submit",
)

@dataclass
class WeatherData:
    main: str
    description: str
    icon: str
    temperature: int
    feels_like:int
    max_temp:int
    min_temp:int
    humidity:int
    pressure:int
    visibility:int
    wind_speed:int
    wind_degree:int

def get_lat_lon(city_name, state_code, country_code, API_key):
    try:
        response = requests.get(f'http://api.openweathermap.org/geo/1.0/direct?q={city_name},{state_code},{country_code}&appid={API_key}')
        response.raise_for_status()
        data = response.json()[0]
        lat, lon = data.get('lat'), data.get('lon')
        return lat, lon
    except Exception as e:
        print(f"Error in get_lat_lon: {e}")
        return None, None

def get_current_weather(lat, lon, API_key):
    try:
        response = requests.get(f'https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_key}&units=metric')
        response.raise_for_status()
        data = response.json()
        weather_data = WeatherData(
            main=data['weather'][0]['main'],
            description=data['weather'][0]['description'],
            icon=data['weather'][0]['icon'],
            temperature=int(data['main']['temp']),
            feels_like=int(data['main']['feels_like']),
            min_temp=int(data['main']['temp_min']),
            max_temp=int(data['main']['temp_max']),
            humidity=data['main']['humidity'],
            pressure=data['main']['pressure'],
            visibility=data['visibility'],
            wind_speed=int(data['wind']['speed']),
            wind_degree=data['wind']['deg']
        )
        return weather_data
    except Exception as e:
        print(f"Error in get_current_weather: {e}")
        return None

@agent.on_event("startup")
async def startup(ctx: Context):
    ctx.logger.info(f"Starting up {agent.name}")
    ctx.logger.info(f"With address: {agent.address}")
    ctx.logger.info(f"And wallet address: {agent.wallet.address()}")

@agent.on_query(model=TestRequest, replies={Response})
async def query_handler(ctx: Context, sender: str, msg: TestRequest):
    ctx.logger.info(f"Query received from {sender}")
    try:
        lat, lon = get_lat_lon(msg.city_name, msg.state_code, msg.country_code, api_key)
        if lat is None or lon is None:
            raise Exception("Failed to get lat/lon")
        
        weather_data = get_current_weather(lat, lon, api_key)
        if weather_data is None:
            raise Exception("Failed to get weather data")

        ctx.logger.info("Received Weather Data:")
        ctx.logger.info(f"Main: {weather_data.main}")
        ctx.logger.info(f"Description: {weather_data.description}")
        ctx.logger.info(f"Icon: {weather_data.icon}")
        ctx.logger.info(f"Temperature: {weather_data.temperature}") 
        ctx.logger.info(f"Feels Like: {weather_data.feels_like}") 
        ctx.logger.info(f"Max Temp: {weather_data.max_temp}") 
        ctx.logger.info(f"Min Temp: {weather_data.min_temp}") 
        ctx.logger.info(f"Pressure: {weather_data.pressure}") 
        ctx.logger.info(f"Humidity: {weather_data.humidity}") 
        ctx.logger.info(f"Visibility: {weather_data.visibility}") 
        ctx.logger.info(f"Wind Speed: {weather_data.wind_speed}")
        ctx.logger.info(f"Wind Degree: {weather_data.wind_degree}")  
            
        response_data = {
            "main": weather_data.main,
            "description": weather_data.description,
            "icon": weather_data.icon,
            "temperature": weather_data.temperature,
            "feels_like":weather_data.feels_like,
            "max_temp":weather_data.max_temp,
            "min_temp":weather_data.min_temp,
            "pressure":weather_data.pressure,
            "humidity":weather_data.humidity,
            "visibility":weather_data.visibility,
            "wind_speed":weather_data.wind_speed,
            "wind_degree":weather_data.wind_degree
        }
        
        response = Response(status="success", message="Weather data retrieved successfully", data=response_data)
        await ctx.send(sender, response)
    except Exception as e:
        ctx.logger.error(f"Error processing query: {str(e)}")
        response = Response(status="fail", message=str(e), data={})
        await ctx.send(sender, response)

if __name__ == "__main__":
    agent.run()
