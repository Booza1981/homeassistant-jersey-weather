#!/usr/bin/env python3
"""
Jersey Weather API Test Script

This script tests the Jersey Weather API endpoints and displays the data structure.
Use this to verify that the API is working before installing the Home Assistant integration.
"""

import json
import asyncio
import aiohttp
from datetime import datetime

# API endpoints
FORECAST_URL = "https://prodgojweatherstorage.blob.core.windows.net/data/jerseyForecast.json"
TIDE_URL = "https://prodgojweatherstorage.blob.core.windows.net/data/JerseyTide5Day.json"
RADAR_IMAGE_URL = "https://sojpublicdata.blob.core.windows.net/jerseymet/Radar10.JPG"
SATELLITE_IMAGE_URL = "https://sojpublicdata.blob.core.windows.net/jerseymet/Satellite10.JPG"

async def test_api():
    """Test the Jersey Weather API endpoints."""
    print("Testing Jersey Weather API...\n")
    
    async with aiohttp.ClientSession() as session:
        # Test forecast API
        print(f"Testing forecast endpoint: {FORECAST_URL}")
        try:
            async with session.get(FORECAST_URL) as resp:
                if resp.status == 200:
                    forecast_data = await resp.json()
                    print("✅ Forecast API: OK")
                    print(f"  Current Temperature: {forecast_data.get('currentTemprature')}")
                    print(f"  Forecast Date: {forecast_data.get('forecastDate')}")
                    print(f"  Days in Forecast: {len(forecast_data.get('forecastDay', []))}")
                    print(f"  Current Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                    print(f"  Last Update: {forecast_data.get('cacheTime')}")
                else:
                    print(f"❌ Forecast API Error: Status code {resp.status}")
        except Exception as e:
            print(f"❌ Forecast API Error: {str(e)}")
            
        print("\n" + "-" * 50 + "\n")
            
        # Test tide API
        print(f"Testing tide endpoint: {TIDE_URL}")
        try:
            async with session.get(TIDE_URL) as resp:
                if resp.status == 200:
                    tide_data = await resp.json()
                    print("✅ Tide API: OK")
                    print(f"  Days of tide data: {len(tide_data)}")
                    if tide_data:
                        first_day = tide_data[0]
                        print(f"  First day: {first_day.get('formattedDate')}")
                        print(f"  Tide events today: {len(first_day.get('TideTimes', []))}")
                        for tide in first_day.get('TideTimes', []):
                            print(f"    {tide.get('Time')} - {tide.get('highLow')} ({tide.get('Height')}m)")
                else:
                    print(f"❌ Tide API Error: Status code {resp.status}")
        except Exception as e:
            print(f"❌ Tide API Error: {str(e)}")
            
        print("\n" + "-" * 50 + "\n")
            
        # Test image endpoints
        print("Testing image endpoints:")
        
        for name, url in [
            ("Radar", RADAR_IMAGE_URL),
            ("Satellite", SATELLITE_IMAGE_URL),
        ]:
            try:
                async with session.head(url) as resp:
                    if resp.status == 200:
                        content_type = resp.headers.get('content-type', '')
                        content_length = resp.headers.get('content-length', '0')
                        print(f"✅ {name} Image: OK")
                        print(f"  Type: {content_type}")
                        print(f"  Size: {int(content_length) / 1024:.1f} KB")
                    else:
                        print(f"❌ {name} Image Error: Status code {resp.status}")
            except Exception as e:
                print(f"❌ {name} Image Error: {str(e)}")
            
        print("\n" + "-" * 50 + "\n")
        
        print("API Test Complete!")
        print("\nIf all tests passed, you can proceed with installing the Home Assistant integration.")
        print("If any test failed, the API might be temporarily unavailable or has changed.")

if __name__ == "__main__":
    asyncio.run(test_api())
