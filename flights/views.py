from django.shortcuts import render
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from django.conf import settings
from datetime import datetime
from airports.models import Airport
from airports.services import AirportCacheService
import urllib.request
import urllib.parse
import base64
import json
import math
import logging

logger = logging.getLogger(__name__)

def flight_search(request):

    # TO-DO: use a random token validation logic (with 24 hours TTL). API is insecure as it is.
    logger.debug(f"Received request with params: {request.GET}")

    try: 
        origin = request.GET.get('origin').upper() if request.GET.get('origin') else None
        destination_airport = request.GET.get('destination').upper() if request.GET.get('destination') else None
        departure_date_str = request.GET.get('departure_date')
        return_date_str = request.GET.get('return_date')

        if not all([origin, destination_airport, departure_date_str, return_date_str]):
            logger.error("Missing parameters")
            return HttpResponseBadRequest({'error': 'Missing parameters'})

        if origin == destination_airport:
            logger.error("Origin and destination cannot be the same")
            return HttpResponseBadRequest({'error': 'Origin and destination cannot be the same'})

        try:
            dep_date = datetime.strptime(departure_date_str, '%Y-%m-%d').date()
            ret_date = datetime.strptime(return_date_str, '%Y-%m-%d').date()
            today = timezone.now().date()
            if dep_date < today or ret_date < dep_date:
                logger.error("Invalid dates")
                return HttpResponseBadRequest({'error': 'Invalid dates'})
        except ValueError:
            logger.error("Invalid date format")
            return HttpResponseBadRequest({'error': 'Invalid date format (use YYYY-MM-DD)'})

        # TO-DO: Test to see if Redis is working correctly. Check airports exist and are active.

        cache_service = AirportCacheService()
        origin_data = cache_service.get_airport_by_iata(origin)
        if not origin_data:
            logger.error(f"Invalid airport code: origin={origin}")
            return HttpResponseBadRequest({'error': f'Invalid airport code: {origin}'})

        dest_data = cache_service.get_airport_by_iata(destination_airport)
        if not dest_data:
            logger.error(f"Invalid airport code: destination={destination_airport}")
            return HttpResponseBadRequest({'error': f'Invalid airport code: {destination_airport}'})

        origin_airport = Airport(
            iata=origin_data['iata'],
            city=origin_data['city'],
            lat=origin_data['lat'],
            lon=origin_data['lon'],
            state=origin_data['state']
        )
        dest_airport = Airport(
            iata=dest_data['iata'],
            city=dest_data['city'],
            lat=dest_data['lat'],
            lon=dest_data['lon'],
            state=dest_data['state']
        )

        outbound_data = call_mock_api(origin, destination_airport, departure_date_str)
        outbound_options = outbound_data['options']

        distance = haversine(origin_airport.lat, origin_airport.lon, dest_airport.lat, dest_airport.lon)

        process_flight_options(outbound_options, distance)

        return_data = call_mock_api(destination_airport, origin, return_date_str)
        return_options = return_data['options']

        process_flight_options(return_options, distance)

        # Now for the combinations:

        combinations = []
        for out_opt in outbound_options:
            for ret_opt in return_options:
                comb_fare = out_opt['price']['fare'] + ret_opt['price']['fare']
                comb_fee = out_opt['price']['fee'] + ret_opt['price']['fee']
                comb_total = out_opt['price']['total'] + ret_opt['price']['total']
                combinations.append({
                    'outbound': out_opt,
                    'return': ret_opt,
                    'combined_price': {'fare': comb_fare, 'fee': comb_fee, 'total': comb_total}
                })

        # Sort by combined total ascending
        combinations.sort(key=lambda x: x['combined_price']['total'])

        # The return values
        response = {
            'summary': {
                'outbound': {
                    'departure_date': departure_date_str,
                    'from': {
                        'iata': origin_airport.iata,
                        'city': origin_airport.city,
                        'state': origin_airport.state,
                        'lat': float(origin_airport.lat),
                        'lon': float(origin_airport.lon)
                    },
                    'to': {
                        'iata': dest_airport.iata,
                        'city': dest_airport.city,
                        'state': dest_airport.state,
                        'lat': float(dest_airport.lat),
                        'lon': float(dest_airport.lon)
                    },
                    'currency': outbound_data['summary'].get('currency', 'BRL')
                },
                'return': {
                    'departure_date': return_date_str,
                    'from': {
                        'iata': dest_airport.iata,
                        'city': dest_airport.city,
                        'state': dest_airport.state,
                        'lat': float(dest_airport.lat),
                        'lon': float(dest_airport.lon)
                    },
                    'to': {
                        'iata': origin_airport.iata,
                        'city': origin_airport.city,
                        'state': origin_airport.state,
                        'lat': float(origin_airport.lat),
                        'lon': float(origin_airport.lon)
                    },
                    'currency': return_data['summary'].get('currency', 'BRL')
                }
            },
            'combinations': combinations
        }
        return JsonResponse(response)
    
    except Exception as e:
        logger.error(f"Error in flight_search: {str(e)}", exc_info=True)
        return JsonResponse({'error': 'Internal server error'}, status=500)


def process_flight_options(options, distance):
    for option in options:
        dep_time = datetime.fromisoformat(option['departure_time'])
        arr_time = datetime.fromisoformat(option['arrival_time'])
        duration_hours = (arr_time - dep_time).total_seconds() / 3600
        fare = option['price']['fare']
        fee = max(0.1 * fare, 40.0)
        total = fare + fee
        option['price'] = {'fare': fare, 'fee': fee, 'total': total}
        cruise_speed = round(distance / duration_hours) if duration_hours > 0 else 0
        cost_per_km = round(fare / distance, 2) if distance > 0 else 0.0
        option['meta'] = {'range': round(distance), 'cruise_speed_kmh': cruise_speed, 'cost_per_km': cost_per_km}

# Haversine calculation generated by Grok AI:
def haversine(lat1, lon1, lat2, lon2):
    R = 6371  # Earth radius in km
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# API call generated by Deepseek AI:
def call_mock_api(from_iata: str, to_iata: str, departure_date_str: str) -> dict:
    """
    Calls the mock flights API using credentials from Django settings.
    
    Args:
        from_iata: Departure airport IATA code (3 letters)
        to_iata: Arrival airport IATA code (3 letters)
        departure_date_str: Date in YYYY-MM-DD format
        
    Returns:
        API response as a dictionary
        
    Raises:
        ValueError: If required settings are missing
        urllib.error.URLError: For API connection issues
    """
    # Validate settings
    required_settings = {
        'FLIGHTS_API_URL': getattr(settings, 'FLIGHTS_API_URL', None),
        'API_LOGIN': getattr(settings, 'API_LOGIN', None),
        'API_PASSWORD': getattr(settings, 'API_PASSWORD', None),
        'API_KEY': getattr(settings, 'API_KEY', None)
    }
    
    missing = [k for k, v in required_settings.items() if not v]
    if missing:
        raise ValueError(f"Missing required settings: {', '.join(missing)}")

    try:
        # Build URL
        base_url = settings.FLIGHTS_API_URL.rstrip('/')
        endpoint = f"{base_url}/{settings.API_KEY}/{from_iata}/{to_iata}/{departure_date_str}"
        
        # Prepare authentication
        auth_string = f"{settings.API_LOGIN}:{settings.API_PASSWORD}"
        auth_bytes = auth_string.encode('utf-8')
        auth_token = base64.b64encode(auth_bytes).decode('utf-8')
        
        headers = {
            'Authorization': f'Basic {auth_token}',
            'Content-Type': 'application/json'
        }

        # Make request
        req = urllib.request.Request(endpoint, headers=headers)
        
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                logger.error(f"API returned status {response.status}")
                raise urllib.error.URLError(f"API error: {response.status}")
                
            data = json.loads(response.read().decode('utf-8'))
            return data
            
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode API response: {str(e)}")
        raise
    except urllib.error.URLError as e:
        logger.error(f"API request failed: {str(e)}")
        raise