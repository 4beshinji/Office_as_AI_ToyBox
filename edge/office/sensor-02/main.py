import machine
import time
import json
from mcp_device import MCPDevice
from bme680_driver import BME680
from mhz19_driver import MHZ19C

# --- Configuration ---
DEVICE_ID = "sensor-node-02"
WIFI_SSID = "YOUR_WIFI_SSID"      # User should change this
WIFI_PASS = "YOUR_WIFI_PASSWORD"  # User should change this
MQTT_BROKER = "192.168.128.161"      # SOMS Server Static IP

# Pin Definitions (ESP32-C6)
I2C_SDA_PIN = 6
I2C_SCL_PIN = 7
UART_RX_PIN = 4
UART_TX_PIN = 5

# --- Hardware Initialization ---
i2c = machine.I2C(0, sda=machine.Pin(I2C_SDA_PIN), scl=machine.Pin(I2C_SCL_PIN))
bme = BME680(i2c)

# MH-Z19C needs UART. Using UART1
mhz = MHZ19C(1, rx_pin=UART_RX_PIN, tx_pin=UART_TX_PIN)

# --- MCP Tool Handlers ---
def get_sensor_data():
    """Reads all sensors and returns the data."""
    bme_data = bme.read_sensor()
    co2 = mhz.read_co2()
    
    data = {
        "temperature": bme_data.get("temperature"),
        "humidity": bme_data.get("humidity"),
        "pressure": bme_data.get("pressure"),
        "gas_resistance": bme_data.get("gas_resistance"),
        "co2": co2
    }
    return data

def restart_device():
    """Restarts the ESP32."""
    machine.reset()
    return {"status": "restarting"}

# --- Device Setup ---
device = MCPDevice(
    device_id=DEVICE_ID,
    ssid=WIFI_SSID,
    password=WIFI_PASS,
    broker=MQTT_BROKER,
    topic_prefix=f"office/meeting_room_a/sensor/{DEVICE_ID}"
)

# Register Tools
device.register_tool("get_status", get_sensor_data)
device.register_tool("restart", restart_device)

def main():
    try:
        device.connect()
    except Exception as e:
        print(f"Failed to connect: {e}")
        time.sleep(10)
        machine.reset()

    last_report = 0
    REPORT_INTERVAL = 30 # seconds

    while True:
        try:
            device.loop()
            
            # Periodic Telemetry
            if time.time() - last_report > REPORT_INTERVAL:
                sensor_data = get_sensor_data()
                
                # Publish individual topics for backward compatibility or direct access
                device.publish_telemetry("temperature", {"value": sensor_data["temperature"], "unit": "C"})
                device.publish_telemetry("humidity", {"value": sensor_data["humidity"], "unit": "%"})
                device.publish_telemetry("co2", {"value": sensor_data["co2"], "unit": "ppm"})
                
                # Publish summary status
                device.publish_telemetry("status", sensor_data)
                
                last_report = time.time()
                
        except Exception as e:
            print(f"Error in main loop: {e}")
            time.sleep(1)

if __name__ == "__main__":
    main()
