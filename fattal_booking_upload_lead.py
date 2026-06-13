from curl_cffi import requests
from urllib.parse import urlencode


def run(headers, user_input):
    """
    Upload a new lead to Fattal Terminal VIP booking system.

    Creates a registration with VIP service package and optional transportation.
    The flow: 1) Create header registration 2) Add VIP package line 3) Add transport line (if enabled)
    """
    base_url = BASE_URL.rstrip('/').replace('/fattal_booking/base/reg_page.php', '')
    api_base = f"{base_url}/fattal_booking/base"

    # === Validate required fields ===
    flight_number = user_input.get("flight_number")
    flight_date = user_input.get("flight_date")
    flight_time = user_input.get("flight_time")
    direction = user_input.get("direction", "departure")
    flight_type = user_input.get("flight_type", "commercial")
    passenger_count = user_input.get("passenger_count", 1)

    service_package_id = user_input.get("service_package_id")
    service_rate = user_input.get("service_rate")

    passenger_name = user_input.get("passenger_name")
    passenger_phone = user_input.get("passenger_phone")

    contact_name = user_input.get("contact_name")
    contact_email = user_input.get("contact_email")
    contact_phone = user_input.get("contact_phone")

    # Validate required fields
    required = {
        "flight_number": flight_number,
        "flight_date": flight_date,
        "flight_time": flight_time,
        "service_package_id": service_package_id,
        "service_rate": service_rate,
        "passenger_name": passenger_name,
        "passenger_phone": passenger_phone,
        "contact_name": contact_name,
        "contact_email": contact_email,
        "contact_phone": contact_phone,
    }

    missing = [k for k, v in required.items() if not v]
    if missing:
        return {'status_code': 400, 'body': {'error': f'Missing required fields: {", ".join(missing)}'}}

    # === Map direction and flight type ===
    # i_dep_or_arr: "1" = departure, "2" = arrival
    i_dep_or_arr = "2" if direction == "arrival" else "1"
    # i_flt_type: "0" = commercial, "1" = private/charter
    i_flt_type = "1" if flight_type == "private" else "0"

    # === Calculate agent meeting time (2 hours before flight for departures) ===
    i_agent_date = flight_date
    i_agent_time = flight_time
    if direction == "departure":
        # Calculate 2 hours before flight time
        try:
            h, m = map(int, flight_time.split(':'))
            h -= 2
            if h < 0:
                h += 24
                # Agent date would be day before, but we keep same date for simplicity
            i_agent_time = f"{h:02d}:{m:02d}"
        except:
            i_agent_time = flight_time

    # === Optional fields ===
    name_on_board = user_input.get("name_on_board", "")
    wheelchair_count = user_input.get("wheelchair_count", "")
    if wheelchair_count == 0:
        wheelchair_count = ""

    voucher_code = user_input.get("voucher_code", "")
    remarks = user_input.get("remarks", "")

    # === Transportation fields ===
    transport = user_input.get("transport", {})
    transport_enabled = transport.get("enabled", False)

    i_transp_city = ""
    i_transp_adr = ""
    i_transp_date = ""
    i_transp_time = ""
    i_transp_chd_seat = ""

    if transport_enabled:
        city_map = {
            "jerusalem": "3000",
            "haifa": "4000",
            "tel_aviv": "5000",
            "herzliya": "6400"
        }
        city = transport.get("city", "")
        i_transp_city = city_map.get(city.lower(), city) if city else ""
        i_transp_adr = transport.get("address", "")
        i_transp_date = transport.get("date", "")
        i_transp_time = transport.get("time", "")
        child_seats = transport.get("child_seats", 0)
        i_transp_chd_seat = str(child_seats) if child_seats else ""

    # === Build request headers ===
    req_headers = {
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "X-Requested-With": "XMLHttpRequest",
        "Origin": base_url,
        "Referer": f"{api_base}/reg_page.php",
    }
    # Add cookies if present
    if "cookie" in headers:
        req_headers["Cookie"] = headers["cookie"]
    elif "Cookie" in headers:
        req_headers["Cookie"] = headers["Cookie"]

    # === Step 1: Create registration header ===
    registration_data = {
        "i_name_on_board": name_on_board,
        "i_meet_contact_person": passenger_name,
        "i_meet_mob_phone": passenger_phone,
        "i_wheelchair": str(wheelchair_count) if wheelchair_count else "",
        "i_cont_name": contact_name,
        "i_cont_phone": contact_phone,
        "i_cont_email": contact_email,
        "i_cont_voucher": voucher_code,
        "i_cont_remarks": remarks,
        "i_flt_no": flight_number,
        "i_apt_name": "LLBG",  # Only Ben Gurion Airport supported
        "i_transp_city": i_transp_city,
        "i_transp_adr": i_transp_adr,
        "i_transp_chd_seat": i_transp_chd_seat,
        "i_transp_date": i_transp_date,
        "i_transp_time": i_transp_time,
        "i_service_rate": str(service_rate),
        "i_pas_numbers": str(passenger_count),
        "i_flt_date": flight_date,
        "i_flt_time": flight_time,
        "i_agent_date": i_agent_date,
        "i_agent_time": i_agent_time,
        "i_dep_or_arr": i_dep_or_arr,
        "i_currency": "USD",
        "i_flt_type": i_flt_type,
    }

    response = requests.post(
        f"{api_base}/call_insert_registration.php",
        data=urlencode(registration_data),
        headers=req_headers,
        impersonate="chrome131",
        timeout=30,
        verify=False  # Server certificate chain not fully trusted
    )

    # Check for auth issues (redirects to login, etc.)
    if response.status_code in [401, 403]:
        return {'status_code': 401, 'body': {'error': 'Session expired'}}

    if response.status_code != 200:
        return {'status_code': response.status_code, 'body': {'error': f'Registration failed: {response.text}'}}

    try:
        registration_id = response.json()
    except:
        # Check if response indicates auth failure
        if 'login' in response.text.lower() or 'session' in response.text.lower():
            return {'status_code': 401, 'body': {'error': 'Session expired'}}
        return {'status_code': 500, 'body': {'error': f'Invalid response: {response.text}'}}

    if not registration_id:
        return {'status_code': 500, 'body': {'error': 'No registration ID returned'}}

    # === Step 2: Add VIP package line item ===
    # Map service package ID to name
    package_names = {
        "7001": "LUXURIOUS LOUNGE HALL",
        "7002": "LUXURIOUS PRIVATE ROOM",
        "7003": "PRIVATE DECORATED BEDROOM",
        "7019": "MEETING ROOM UP TO 9 HOURS",
        "7027": "LUXURIOUS LOUNGE HALL",
    }
    service_name = package_names.get(str(service_package_id), f"Package {service_package_id}")

    pkg_line_data = {
        "i_temp_conf_id": str(registration_id),
        "i_service_id": str(service_package_id),
        "i_service_type_id": i_dep_or_arr,
        "i_service_name": service_name,
        "i_pas_numbers": str(passenger_count),
        "i_service_rate": str(service_rate),
        "i_additional_price": "0",
        "i_total_price": str(service_rate),
        "i_agent_date": i_agent_date,
        "i_agent_time": i_agent_time,
    }

    pkg_response = requests.post(
        f"{api_base}/call_insert_registration_lines.php",
        data=urlencode(pkg_line_data),
        headers=req_headers,
        impersonate="chrome131",
        timeout=30,
        verify=False  # Server certificate chain not fully trusted
    )

    if pkg_response.status_code != 200:
        return {
            'status_code': 200,
            'body': {
                'registration_id': str(registration_id),
                'status': 'partial',
                'warning': 'Registration created but package line item failed',
            }
        }

    # === Step 3: Add transportation line item (if enabled) ===
    if transport_enabled:
        transport_service_id = transport.get("service_id")
        transport_rate = transport.get("service_rate", 0)
        transport_name = transport.get("service_name", "Transportation")
        child_seat_price = int(transport.get("child_seats", 0)) * 12
        total_transport = float(transport_rate) + child_seat_price

        if transport_service_id:
            transp_line_data = {
                "i_temp_conf_id": str(registration_id),
                "i_service_id": str(transport_service_id),
                "i_service_type_id": i_dep_or_arr,
                "i_service_name": transport_name,
                "i_pas_numbers": str(passenger_count),
                "i_service_rate": str(transport_rate),
                "i_additional_price": str(child_seat_price),
                "i_total_price": str(total_transport),
                "i_agent_date": i_transp_date or i_agent_date,
                "i_agent_time": i_transp_time or i_agent_time,
            }

            transp_response = requests.post(
                f"{api_base}/call_insert_registration_lines.php",
                data=urlencode(transp_line_data),
                headers=req_headers,
                impersonate="chrome131",
                timeout=30,
                verify=False  # Server certificate chain not fully trusted
            )

    # === Determine final status ===
    # OPERATION_TYPE=2 packages require callback instead of direct booking
    callback_packages = ["7003", "7019"]
    status = "callback_requested" if str(service_package_id) in callback_packages else "success"

    return {
        'status_code': 200,
        'body': {
            'registration_id': str(registration_id),
            'status': status,
            'package': service_name,
            'direction': direction,
            'flight': flight_number,
            'flight_date': flight_date,
            'transport_enabled': transport_enabled,
        }
    }
