def run(headers, user_input):
    """
    List available VIP service packages at Fattal Terminal.

    Returns the VIP lounge/room packages with their IDs, descriptions, and prices.
    Prices may vary based on passenger count.
    """
    passenger_count = user_input.get("passenger_count", 1)

    try:
        data = _fetch_packages(headers, passenger_count)
    except Exception as e:
        error_msg = str(e)
        if 'Session expired' in error_msg:
            return {'status_code': 401, 'body': {'error': 'Session expired'}}
        return {'status_code': 500, 'body': {'error': error_msg}}

    # Parse the response - format: [{"TotalRows": N, "Rows": [...]}]
    if not data or not isinstance(data, list) or len(data) == 0:
        return {'status_code': 200, 'body': {'packages': []}}

    rows = data[0].get("Rows", [])

    packages = []
    for row in rows:
        package = {
            "id": row.get("PACKAGE_ID"),
            "name": row.get("PROD_DESC_EN"),
            "name_hebrew": row.get("PROD_DESC_HE"),
            "price_usd": float(row.get("PROD_PRICE", 0)),
            "operation_type": row.get("OPERATION_TYPE"),
            "requires_callback": row.get("OPERATION_TYPE") == "2",
        }
        packages.append(package)

    return {
        'status_code': 200,
        'body': {
            'passenger_count': passenger_count,
            'packages': packages,
            'note': 'Packages with operation_type=2 require callback instead of direct online booking'
        }
    }