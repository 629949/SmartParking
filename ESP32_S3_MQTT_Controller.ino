/*
 * SmartPark ESP32-S3 MQTT Motor Controller
 * 
 * This sketch enables an ESP32-S3 to:
 * - Connect to WiFi and MQTT broker
 * - Subscribe to parking control commands
 * - Drive X-axis (horizontal) and Y-axis (vertical) stepper motors
 * - Report status back to Django via MQTT callback
 * 
 * Requirements:
 * - ESP32-S3 board
 * - PubSubClient library (Arduino IDE > Sketch > Include Library > Manage Libraries > Search "PubSubClient")
 * - ArduinoJson library (for JSON parsing)
 * - Stepper motor driver (e.g., DRV8825, A4988, or TB6600)
 * 
 * Motor Connections:
 * - X-Axis Motors (3x lead screws): GPIO 16 (STEP), GPIO 17 (DIR) + GPIO 18, 19 + GPIO 20, 21
 * - Y-Axis Motor (vertical lift): GPIO 22 (STEP), GPIO 23 (DIR)
 * 
 * MQTT Topics:
 * - Subscribe: smartpark/commands/<level>/<column>  (e.g., smartpark/commands/2/1)
 * - Publish: smartpark/callback  (status updates)
 */

#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>

// WiFi Configuration
const char* ssid = "YOUR_SSID";
const char* password = "YOUR_PASSWORD";

// MQTT Configuration
const char* mqtt_server = "YOUR_BROKER_IP";  // e.g., "192.168.1.100" or "mqtt.smartpark.local"
const int mqtt_port = 1883;
const char* mqtt_client_id = "SmartPark-ESP32-01";
const char* mqtt_user = "";  // Leave blank if no auth
const char* mqtt_password = "";

// Motor Pins
const int X_MOTOR_PINS[3][2] = {
  {16, 17},  // Motor 1: STEP, DIR
  {18, 19},  // Motor 2: STEP, DIR
  {20, 21}   // Motor 3: STEP, DIR
};

const int Y_MOTOR_STEP = 22;
const int Y_MOTOR_DIR = 23;

// Motor Settings
const int STEPS_PER_REV = 200;  // Standard stepper: 200 steps = 1 revolution
const int STEPS_PER_LEVEL = 1000;  // Adjust based on your mechanical setup
const int STEP_DELAY = 1000;  // Microseconds between steps (500 = 2ms = 1000 RPM)

WiFiClient espClient;
PubSubClient client(espClient);

void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n\n=== SmartPark ESP32-S3 Motor Controller ===");
  
  // Initialize motor pins
  for (int i = 0; i < 3; i++) {
    pinMode(X_MOTOR_PINS[i][0], OUTPUT);  // STEP
    pinMode(X_MOTOR_PINS[i][1], OUTPUT);  // DIR
  }
  pinMode(Y_MOTOR_STEP, OUTPUT);
  pinMode(Y_MOTOR_DIR, OUTPUT);
  
  Serial.println("Motor pins initialized");
  
  // Connect to WiFi
  connectToWiFi();
  
  // Setup MQTT
  client.setServer(mqtt_server, mqtt_port);
  client.setCallback(mqttCallback);
  
  Serial.println("Setup complete. Attempting MQTT connection...");
}

void loop() {
  if (!client.connected()) {
    connectToMQTT();
  }
  client.loop();
  delay(10);
}

void connectToWiFi() {
  Serial.print("Connecting to WiFi: ");
  Serial.println(ssid);
  
  WiFi.mode(WIFI_STA);
  WiFi.begin(ssid, password);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.print("\nWiFi connected! IP: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed!");
  }
}

void connectToMQTT() {
  if (!client.connected()) {
    Serial.print("Connecting to MQTT... ");
    if (client.connect(mqtt_client_id, mqtt_user, mqtt_password)) {
      Serial.println("connected");
      
      // Subscribe to all parking commands
      client.subscribe("smartpark/commands/1/1");
      client.subscribe("smartpark/commands/1/2");
      client.subscribe("smartpark/commands/1/3");
      client.subscribe("smartpark/commands/2/1");
      client.subscribe("smartpark/commands/2/2");
      client.subscribe("smartpark/commands/2/3");
      client.subscribe("smartpark/commands/3/1");
      client.subscribe("smartpark/commands/3/2");
      client.subscribe("smartpark/commands/3/3");
      
      Serial.println("Subscribed to all parking slots");
    } else {
      Serial.print("failed, rc=");
      Serial.print(client.state());
      Serial.println(" trying again in 5 seconds");
      delay(5000);
    }
  }
}

void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.print("\nReceived MQTT: ");
  Serial.println(topic);
  
  // Parse JSON payload
  StaticJsonDocument<200> doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  
  if (error) {
    Serial.print("JSON parse error: ");
    Serial.println(error.c_str());
    return;
  }
  
  // Extract command data
  int cmd_id = doc["cmd_id"] | 0;
  const char* action = doc["action"] | "unknown";
  int target_level = doc["level"] | 1;
  int target_column = doc["column"] | 1;
  const char* slot = doc["slot"] | "L1-A";
  const char* plate = doc["plate"] | "UNKNOWN";
  
  Serial.print("Command: ");
  Serial.print(action);
  Serial.print(" | Level: ");
  Serial.print(target_level);
  Serial.print(" | Column: ");
  Serial.print(target_column);
  Serial.print(" | Plate: ");
  Serial.println(plate);
  
  // Execute command
  if (strcmp(action, "park") == 0) {
    parkVehicle(target_level, target_column);
    reportStatus(cmd_id, "done", slot);
  } else if (strcmp(action, "retrieve") == 0) {
    retrieveVehicle(target_level, target_column);
    reportStatus(cmd_id, "done", slot);
  } else if (strcmp(action, "home") == 0) {
    homePosition();
    reportStatus(cmd_id, "done", "HOME");
  } else if (strcmp(action, "status") == 0) {
    reportStatus(cmd_id, "ack", slot);
  }
}

void parkVehicle(int level, int column) {
  Serial.println(">>> PARKING VEHICLE");
  
  // Move Y-axis to target level
  moveYAxis(level);
  delay(500);
  
  // Move X-axis to target column
  moveXAxis(column);
  delay(500);
  
  Serial.println("<<< PARKING COMPLETE");
}

void retrieveVehicle(int level, int column) {
  Serial.println(">>> RETRIEVING VEHICLE");
  
  // Move X-axis to target column first
  moveXAxis(column);
  delay(500);
  
  // Move Y-axis to level 1 (ground)
  moveYAxis(1);
  delay(500);
  
  Serial.println("<<< RETRIEVAL COMPLETE");
}

void homePosition() {
  Serial.println(">>> HOMING ALL AXES");
  moveYAxis(1);
  delay(300);
  moveXAxis(1);
  Serial.println("<<< HOME POSITION SET");
}

void moveXAxis(int target_column) {
  // Column: 1 = A, 2 = B, 3 = C
  // Calculate steps needed
  int steps_per_column = 500;  // Adjust based on your mechanical setup
  int target_steps = (target_column - 1) * steps_per_column;
  
  // Select motor for this column/level
  int motor_index = (target_column - 1) % 3;
  
  Serial.print("X-Axis moving to column ");
  Serial.print(target_column);
  Serial.print(" (motor ");
  Serial.print(motor_index);
  Serial.print(", ");
  Serial.print(target_steps);
  Serial.println(" steps)");
  
  stepMotor(X_MOTOR_PINS[motor_index][0], X_MOTOR_PINS[motor_index][1], target_steps);
}

void moveYAxis(int target_level) {
  // Level 1 = ground, 2 = middle, 3 = top
  int target_steps = (target_level - 1) * STEPS_PER_LEVEL;
  
  Serial.print("Y-Axis moving to level ");
  Serial.print(target_level);
  Serial.print(" (");
  Serial.print(target_steps);
  Serial.println(" steps)");
  
  stepMotor(Y_MOTOR_STEP, Y_MOTOR_DIR, target_steps);
}

void stepMotor(int step_pin, int dir_pin, int steps) {
  // Set direction (assuming 0 = forward, 1 = backward)
  digitalWrite(dir_pin, steps > 0 ? LOW : HIGH);
  steps = abs(steps);
  
  for (long i = 0; i < steps; i++) {
    digitalWrite(step_pin, HIGH);
    delayMicroseconds(STEP_DELAY / 2);
    digitalWrite(step_pin, LOW);
    delayMicroseconds(STEP_DELAY / 2);
    
    // Allow MQTT to process periodically
    if (i % 100 == 0) {
      client.loop();
    }
  }
}

void reportStatus(int cmd_id, const char* status, const char* slot) {
  // Send callback to Django
  // POST http://YOUR_SERVER/api/iot/callback/
  // or publish to MQTT: smartpark/callback
  
  StaticJsonDocument<200> doc;
  doc["command_id"] = cmd_id;
  doc["status"] = status;
  doc["slot_id"] = slot;
  doc["device_id"] = mqtt_client_id;
  doc["timestamp"] = millis();
  
  char payload[256];
  serializeJson(doc, payload);
  
  client.publish("smartpark/callback", payload);
  Serial.print("Status reported: ");
  Serial.println(payload);
}

/*
 * TROUBLESHOOTING:
 * 
 * 1. ESP32-S3 won't connect to WiFi:
 *    - Check SSID and password
 *    - Ensure 2.4GHz band (ESP32-S3 doesn't support 5GHz)
 *    - Check antenna connection
 * 
 * 2. MQTT connection fails:
 *    - Verify broker IP and port
 *    - Check firewall allows MQTT (1883)
 *    - Try: mosquitto_pub -h YOUR_IP -t "test" -m "hello"
 * 
 * 3. Motors not moving:
 *    - Verify pin connections and GPIO numbers
 *    - Check motor driver power supply
 *    - Use oscilloscope to verify step/dir signals
 *    - Test with direct digitalWrite commands first
 * 
 * 4. Commands received but no motion:
 *    - Check STEP_DELAY (too fast = missed steps)
 *    - Verify motor current settings on driver
 *    - Ensure motor power separate from ESP32 power
 */
