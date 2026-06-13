from curl_cffi import requests
from urllib.parse import urlencode


def run(headers, user_input):
    """
    List available transportation options for a given city at Fattal Terminal.

    Returns transport services (taxi, shuttle, etc.) with IDs and prices.
    Options vary based on city, direction (arrival/departure), and passenger count.
    """
    base_url = BASE_URL.rstrip('/').replace('/fattal_booking/base/reg_page.php', '')
    api_base = f"{base_url}/fattal_booking/base"

    city = user_input.get("city")
    direction = user_input.get("direction", "departure")
    passenger_count = user_input.get("passenger_count", 1)

    if not city:
        return {'status_code': 400, 'body': {'error': 'city is required'}}

    # Map city names to codes
    city_map = {
        "jerusalem": "3000",
        "haifa": "4000",
        "tel_aviv": "5000",
        "herzliya": "6400"
    }

    city_code = city_map.get(city.lower())
    if not city_code:
        return {
            'status_code': 400,
            'body': {
                'error': f'Invalid city: {city}',
                'valid_cities': list(city_map.keys())
            }
        }

    # Map direction to service type
    # A = Arrival (picking up from airport)
    # D = Departure (dropping off at airport)
    service_type = "A" if direction == "arrival" else "D"

    req_headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"{api_base}/reg_page.php",
    }
    if "cookie" in headers:
        req_headers["Cookie"] = headers["cookie"]
    elif "Cookie" in headers:
        req_headers["Cookie"] = headers["Cookie"]

    response = requests.post(
        f"{api_base}/get_transfers_options.php",
        data=urlencode({
            "i_transp_city": city_code,
            "i_service_type": service_type,
            "i_pax_no": passenger_count
        }),
        headers=req_headers,
        impersonate="chrome131",
        timeout=30,
        verify=False  # Server certificate chain not fully trusted
    )

    if response.status_code in [401, 403]:
        return {'status_code': 401, 'body': {'error': 'Session expired'}}

    if response.status_code != 200:
        return {'status_code': response.status_code, 'body': {'error': f'Request failed: {response.text}'}}

    try:
        data = response.json()
    except:
        if 'login' in response.text.lower():
            return {'status_code': 401, 'body': {'error': 'Session expired'}}
        return {'status_code': 500, 'body': {'error': f'Invalid response: {response.text}'}}

    # Parse the response - format: [{"TotalRows": N, "Rows": [...]}]
    if not data or not isinstance(data, list) or len(data) == 0:
        return {'status_code': 200, 'body': {'options': []}}

    rows = data[0].get("Rows", [])

    options = []
    for row in rows:
        option = {
            "id": row.get("TRANS_ID"),
            "name": row.get("TRANS_DESC_EN"),
            "name_hebrew": row.get("TRANS_DESC_HE"),
            "price_usd": float(row.get("TRANS_PRICE", 0)),
        }
        options.append(option)

    return {
        'status_code': 200,
        'body': {
            'city': city,
            'city_code': city_code,
            'direction': direction,
            'passenger_count': passenger_count,
            'options': options,
            'child_seat_price': 12,
            'note': 'Child seats cost $12 each and are added separately'
        }
    }
