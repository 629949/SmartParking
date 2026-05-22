# SmartPark — IoT Automated Parking System
Django web application for the SmartPark automated parking system.

## Stack
- Python 3 / Django 4.x
- Django Channels (WebSocket live slot updates)
- SQLite (dev) → PostgreSQL (production)
- ReportLab (PDF receipts)
- MQTT via paho-mqtt (IoT communication)
- Bootstrap 5 + dark theme UI

## Quick Start

```bash
pip install -r requirements.txt
python manage.py migrate
python manage.py setup_slots    # Creates the 9 parking slots
python manage.py createsuperuser
python manage.py runserver
```

Visit: http://127.0.0.1:8000

## Default Admin
- URL: /admin/
- Username: admin / Password: admin123 (change immediately)

## IoT Integration

### MQTT Topics
- Subscribe: `smartpark/commands/<level>/<column>`
- Payload: `{"cmd_id":42, "action":"park", "level":2, "column":1, "slot":"L2-A", "plate":"UAA123B"}`

### Callback Endpoint (Arduino → Server)
```
POST /api/iot/callback/
{
  "command_id": 42,
  "status": "done",
  "slot_id": 5,
  "slot_status": "occupied"
}
```

### Settings to configure (settings.py)
```python
IOT_BROKER_HOST = '192.168.x.x'   # Your MQTT broker IP
IOT_BROKER_PORT = 1883
PARKING_RATE_UGX = 2000            # Fee per hour in UGX
```

### Install paho-mqtt for real MQTT
```bash
pip install paho-mqtt
```

## Payment Integration
`parking/utils.py` → `simulate_payment()` — replace with:
- **MTN MoMo API** (Uganda): https://momodeveloper.mtn.com
- **Airtel Money API**: https://developers.airtel.africa
- **Flutterwave**: supports UGX, mobile money

## Features
- Live dashboard with slot grid (auto-refreshes every 5s)
- Vehicle parking request with slot selection
- IoT command dispatch (MQTT) to Arduino controller
- Time-based billing (UGX 2,000/hr)
- Mobile Money / Cash / Card payment
- PDF receipt generation
- Session history
- Admin IoT control panel (staff only)
- WebSocket support via Django Channels
# SmartParking
