# Fattal Booking Unofficial API

Unofficial Python integrations for Fattal Booking VIP and transport booking flows.

## Integrations

- `fattal_booking_list_vip_packages.py` - list available VIP service packages.
- `fattal_booking_list_transport_options.py` - list transportation options by city, direction, and passenger count.
- `fattal_booking_upload_lead.py` - submit a booking lead with passenger, flight, contact, package, and optional transport details.

## Usage

Each file exposes a `run(input, context)` entrypoint. The runtime is expected to provide:

- `input`: integration-specific request fields.
- `context["headers"]`: authenticated request headers when required.
- `context["base_url"]`: the platform base URL when overriding the default.

Install dependencies:

```bash
pip install -r requirements.txt
```

## Info

This unofficial API is built by [Integuru.ai](https://integuru.ai/).

For custom requests or hosted authentication, contact richard@taiki.online.

See the [complete list of APIs by Integuru](https://github.com/Integuru-AI/APIs-by-Integuru).
