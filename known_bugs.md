# File for documenting known bugs in the application

# Airports
- CACHE BUG: When tests are run with pytest, all of them are ok except for 1:

'''
coding-challenge-amo-promo % docker-compose exec web pytest airports/tests.py 

======================================================================================= test session starts ========================================================================================
platform linux -- Python 3.13.5, pytest-8.4.1, pluggy-1.6.0
django: version: 5.2.5, settings: amopromo.settings (from env)
rootdir: /app
configfile: pytest.ini
plugins: django-4.11.1
collected 33 items                                                                                                                                                                                 

airports/tests.py ................................F                                                                                                                                          [100%]

============================================================================================= FAILURES =============================================================================================
__________________________________________________________________________________ test_cache_service_with_pytest __________________________________________________________________________________

api_response_data = {'GRU': {'city': 'São Paulo', 'iata': 'GRU', 'lat': -23.432075, 'lon': -46.469511, ...}, 'JFK': {'city': 'New York', 'iata': 'JFK', 'lat': 40.641766, 'lon': -73.780968, ...}}

    @pytest.mark.django_db
    def test_cache_service_with_pytest(api_response_data):
        """Test cache service using pytest style"""
        cache.clear()
        cache_service = AirportCacheService()
    
        # Test caching
        result = cache_service.cache_airports_data(api_response_data)
>       assert result is True
E       assert False is True

airports/tests.py:634: AssertionError
---------------------------------------------------------------------------------------- Captured log call -----------------------------------------------------------------------------------------
ERROR    airports.services:services.py:38 Failed to cache airports data
===================================================================================== short test summary info ======================================================================================
FAILED airports/tests.py::test_cache_service_with_pytest - assert False is True
=================================================================================== 1 failed, 32 passed in 0.23s ===================================================================================
'''

# Flights