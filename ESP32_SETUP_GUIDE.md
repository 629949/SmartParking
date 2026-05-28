# SmartPark ESP32-S3 Setup Guide

## Hardware Requirements
- ESP32-S3 Development Board (e.g., ESP32-S3 DevKit-C)
- 3× Stepper Motors (X-axis horizontal movement, 1 per level)
- 1× Stepper Motor (Y-axis vertical lift)
- 4× Motor Drivers (DRV8825, A4988, or TB6600)
- 24V Power Supply for motors
- 5V Power Supply for ESP32
- WiFi access point

## Software Setup

### 1. Install Arduino IDE
- Download from https://www.arduino.cc/en/software
- Install ESP32 board package:
  - Preferences → Additional Boards Manager URLs: `https://raw.githubusercontent.com/espressif/arduino-esp32/gh-pages/package_esp32_index.json`
  - Tools → Board Manager → Search "esp32" → Install by Espressif Systems

### 2. Install Required Libraries
In Arduino IDE > Sketch > Include Library > Manage Libraries, search and install:
- **PubSubClient** (Nick O'Leary) - MQTT client
- **ArduinoJson** (Benoit Blanchon) - JSON parsing
- **WiFi** (comes with ESP32 core)

### 3. Configure the Sketch
Edit `ESP32_S3_MQTT_Controller.ino` and update:

```cpp
// WiFi Configuration
const char* ssid = "YOUR_NETWORK_NAME";           // Your WiFi SSID
const char* password = "YOUR_WIFI_PASSWORD";      // Your WiFi password

// MQTT Configuration
const char* mqtt_server = "192.168.1.100";        // IP of MQTT broker (SmartPark server)
const int mqtt_port = 1883;                        // Standard MQTT port
```

### 4. Motor Pin Configuration
Default pins (adjust based on your ESP32-S3 board):
```
X-Axis Motors (3 motors):
  Motor 1: GPIO 16 (STEP), GPIO 17 (DIR)
  Motor 2: GPIO 18 (STEP), GPIO 19 (DIR)
  Motor 3: GPIO 20 (STEP), GPIO 21 (DIR)

Y-Axis Motor (vertical):
  GPIO 22 (STEP), GPIO 23 (DIR)
```

### 5. Wiring Motor Drivers
Each stepper driver needs:
- STEP pin → ESP32 GPIO (as configured)
- DIR pin → ESP32 GPIO (as configured)
- GND → Common ground (ESP32, driver, motor power supply)
- VCC → 5V (for logic, not motor power)
- Motor coils → Motor power supply (24V through driver)

### 6. Upload Firmware
1. Tools → Board → esp32 → ESP32-S3 Dev Module
2. Tools → Port → Select COM port with ESP32
3. Tools → Upload Speed → 921600
4. Sketch → Upload
5. Tools → Serial Monitor (set to 115200 baud) to view debug output

## Django Configuration

### 1. Update Settings
In `smartpark/settings.py`, configure MQTT broker:
```python
# MQTT settings (ensure accessible from ESP32)
IOT_BROKER_HOST = os.environ.get('IOT_BROKER_HOST', '192.168.1.100')  # Your server IP
IOT_BROKER_PORT = int(os.environ.get('IOT_BROKER_PORT', 1883))
```

### 2. Run MQTT Broker
You need an MQTT broker running on your server. Options:
- **Mosquitto** (Linux/Mac/Windows)
  ```bash
  # Ubuntu/Debian
  sudo apt-get install mosquitto
  sudo systemctl start mosquitto
  
  # Mac
  brew install mosquitto
  brew services start mosquitto
  
  # Windows
  Download from https://mosquitto.org/download/
  ```

### 3. Test MQTT Connection
From ESP32 side:
- Serial output should show "MQTT connected" after WiFi connects
- Check subscribing to `smartpark/commands/*/`

From Django side:
- Use test script:
  ```bash
  python manage.py shell
  >>> from parking.utils import send_iot_command
  >>> from parking.models import ParkingSession, ParkingSlot
  >>> slot = ParkingSlot.objects.first()
  >>> # Create test session manually if needed
  >>> send_iot_command(session, 'park')
  ```

## Network Topology
```
┌─────────────────────────────────────────────────────┐
│ Your Network / Router (WiFi + Ethernet)             │
│                                                     │
│  ┌─────────────────┐           ┌──────────────────┐ │
│  │ ESP32-S3        │           │ SmartPark Django │ │
│  │ (WiFi client)   │◄─MQTT────►│ (MQTT Broker)    │ │
│  │ Motors control  │           │ Port 1883        │ │
│  └─────────────────┘           └──────────────────┘ │
│                                                     │
└─────────────────────────────────────────────────────┘
```

## Testing Checklist

- [ ] ESP32 connects to WiFi (see "WiFi connected! IP: 192.168.x.x" in Serial)
- [ ] ESP32 connects to MQTT (see "MQTT connected" in Serial)
- [ ] Django sends command (check IoT Control Panel for "sent" status)
- [ ] Motors respond (hear stepper movement)
- [ ] ESP32 reports status back (IoT command shows "done" status)

## Troubleshooting

### ESP32 won't connect to WiFi
- Check SSID and password (case-sensitive)
- Ensure 2.4GHz band (not 5GHz - ESP32-S3 limitation)
- Check router allows device connections
- Restart both ESP32 and router

### MQTT connection fails
- Ping broker: `ping 192.168.1.100`
- Check broker running: `sudo systemctl status mosquitto`
- Verify firewall allows port 1883
- Test with mosquitto_sub: `mosquitto_sub -h 192.168.1.100 -t "smartpark/commands/+/+"`

### Motors not responding
- Check Serial output for motor move commands
- Verify motor driver power supply (24V)
- Use multimeter to test STEP/DIR signals
- Ensure motors are properly wired to drivers
- Check STEP_DELAY value (try slower: 2000 µs = 500 RPM)

### Commands received but no status reply
- Check if callback URL is reachable: `curl http://192.168.x.x:8000/api/iot/callback/`
- Ensure `smartpark/callback` MQTT topic is being published

## Performance Tuning

### Motor Speed
Adjust `STEP_DELAY` in the sketch (microseconds between steps):
- 500 µs = 2000 RPM (very fast, may lose steps)
- 1000 µs = 1000 RPM (medium)
- 2000 µs = 500 RPM (slow but reliable)
- 5000 µs = 200 RPM (very slow, very reliable)

### Steps Per Column
Adjust `STEPS_PER_COLUMN` based on your lead screw pitch and microstepping:
- Standard lead screw 2mm pitch + 1/16 microstepping = ~400 steps/mm
- For 300mm distance: 300 * 400 = 120,000 steps
- Divide by 3 columns = 40,000 steps per column

### Steps Per Level
Adjust `STEPS_PER_LEVEL` based on vertical lift distance:
- For 3 levels 1m apart: ~400,000 steps for 1m
- Per level: ~133,000 steps

## Security (Optional)

### Enable MQTT Authentication
In Mosquitto config (`/etc/mosquitto/mosquitto.conf`):
```conf
per_listener_settings true
listener 1883
allow_anonymous false
password_file /etc/mosquitto/passwd
```

Create password file:
```bash
mosquitto_passwd -c /etc/mosquitto/passwd smartpark
# Then enter password when prompted
```

Update Arduino sketch:
```cpp
const char* mqtt_user = "smartpark";
const char* mqtt_password = "YOUR_PASSWORD";
```

Update Django settings:
```python
MQTT_USER = "smartpark"
MQTT_PASSWORD = "YOUR_PASSWORD"
```

## Support
For issues or questions, check:
- Espressif documentation: https://docs.espressif.com/
- PubSubClient docs: https://github.com/knolleary/pubsubclient
- Mosquitto docs: https://mosquitto.org/documentation/

