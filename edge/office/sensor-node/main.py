from mcp_device import MCPDevice
import machine
import dht
import time

# Configuration
DEVICE_ID = "sensor_01"
BROKER = "192.168.1.100" # Central Server IP

# Hardware Setup
sensor = dht.DHT22(machine.Pin(4))
led = machine.Pin(2, machine.Pin.OUT)

def set_indicator(state="on"):
    if state == "on":
        led.value(1)
    else:
        led.value(0)
    return {"status": "ok", "led": state}

def main():
    device = MCPDevice(DEVICE_ID, "SSID", "PASS", BROKER, topic_prefix="office/env/sensor_01")
    
    # Register Tools
    device.register_tool("set_indicator", set_indicator)
    
    try:
        device.connect()
    except:
        print("Connection failed, resetting...")
        machine.reset()
        
    while True:
        device.loop()
        
        # Read Sensor
        try:
            sensor.measure()
            temp = sensor.temperature()
            hum = sensor.humidity()
            
            payload = {
                "temperature": temp,
                "humidity": hum
            }
            device.publish_telemetry("status", payload)
            
        except OSError as e:
            print("Failed to read sensor")
            
        time.sleep(10)

if __name__ == "__main__":
    main()
