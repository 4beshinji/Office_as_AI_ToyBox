/**
 * Sensor Node - XIAO ESP32-S3 + BME680
 * 
 * 機能:
 * - BME680センサーからの環境データ取得（温度・湿度・気圧・ガス）
 * - Wi-Fi/MQTT接続
 * - 定期的なテレメトリ送信
 */

#include <Arduino.h>
#include <WiFi.h>
#include <Wire.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Adafruit_Sensor.h>
#include <Adafruit_BME680.h>

// ==================== 設定 ====================
// Wi-Fi設定（環境に合わせて変更）
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

// MQTT設定
const char* MQTT_SERVER = "192.168.1.100";  // MQTTブローカーのIP
const int MQTT_PORT = 1883;
const char* DEVICE_ID = "sensor_node_01";

// MQTTトピック
const char* TOPIC_TEMP = "office/meeting_room_a/sensor/sensor_node_01/temperature";
const char* TOPIC_HUM = "office/meeting_room_a/sensor/sensor_node_01/humidity";
const char* TOPIC_PRES = "office/meeting_room_a/sensor/sensor_node_01/pressure";
const char* TOPIC_GAS = "office/meeting_room_a/sensor/sensor_node_01/gas";
const char* TOPIC_STATUS = "office/sensor/sensor_node_01/status";

// I2Cピン（XIAO ESP32-S3）
#define SDA_PIN 5
#define SCL_PIN 6

// BME680 I2Cアドレス（ボードによって0x76または0x77）
#define BME680_I2C_ADDR 0x76

// 送信間隔（ミリ秒）
#define TELEMETRY_INTERVAL 10000  // 10秒ごと

// ==================== グローバル変数 ====================
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
Adafruit_BME680 bme;

unsigned long lastTelemetry = 0;

// ==================== 関数プロトタイプ ====================
void setupWiFi();
void setupMQTT();
void setupBME680();
void readAndPublishSensors();
void publishStatus();

// ==================== セットアップ ====================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=== Sensor Node Starting ===");
  
  // I2C初期化
  Wire.begin(SDA_PIN, SCL_PIN);
  
  // BME680初期化
  setupBME680();
  
  // Wi-Fi接続
  setupWiFi();
  
  // MQTT接続
  setupMQTT();
  
  Serial.println("=== Initialization Complete ===\n");
  publishStatus();
}

// ==================== メインループ ====================
void loop() {
  // MQTT接続確認
  if (!mqtt.connected()) {
    Serial.println("MQTT disconnected, reconnecting...");
    setupMQTT();
  }
  mqtt.loop();
  
  // 定期的なセンサーデータ送信
  if (millis() - lastTelemetry > TELEMETRY_INTERVAL) {
    readAndPublishSensors();
    lastTelemetry = millis();
  }
  
  delay(10);
}

// ==================== Wi-Fi接続 ====================
void setupWiFi() {
  Serial.print("Connecting to WiFi");
  WiFi.mode(WIFI_STA);
  WiFi.begin(WIFI_SSID, WIFI_PASS);
  
  int attempts = 0;
  while (WiFi.status() != WL_CONNECTED && attempts < 20) {
    delay(500);
    Serial.print(".");
    attempts++;
  }
  
  if (WiFi.status() == WL_CONNECTED) {
    Serial.println("\nWiFi connected!");
    Serial.print("IP address: ");
    Serial.println(WiFi.localIP());
  } else {
    Serial.println("\nWiFi connection failed!");
    ESP.restart();
  }
}

// ==================== MQTT接続 ====================
void setupMQTT() {
  mqtt.setServer(MQTT_SERVER, MQTT_PORT);
  mqtt.setBufferSize(1024);
  
  Serial.print("Connecting to MQTT broker...");
  
  int attempts = 0;
  while (!mqtt.connected() && attempts < 5) {
    if (mqtt.connect(DEVICE_ID)) {
      Serial.println(" connected!");
    } else {
      Serial.print(".");
      delay(2000);
      attempts++;
    }
  }
  
  if (!mqtt.connected()) {
    Serial.println("\nMQTT connection failed!");
  }
}

// ==================== BME680初期化 ====================
void setupBME680() {
  Serial.println("Initializing BME680...");
  
  if (!bme.begin(BME680_I2C_ADDR, &Wire)) {
    Serial.println("Could not find BME680 sensor!");
    Serial.println("Check wiring and I2C address (0x76 or 0x77)");
    while (1) delay(1000);  // 無限ループで停止
  }
  
  // センサー設定
  bme.setTemperatureOversampling(BME680_OS_8X);
  bme.setHumidityOversampling(BME680_OS_2X);
  bme.setPressureOversampling(BME680_OS_4X);
  bme.setIIRFilterSize(BME680_FILTER_SIZE_3);
  bme.setGasHeater(320, 150);  // 320°C for 150ms
  
  Serial.println("BME680 initialized successfully");
}

// ==================== センサー読み取りと送信 ====================
void readAndPublishSensors() {
  // センサー測定実行
  if (!bme.performReading()) {
    Serial.println("Failed to perform reading :(");
    return;
  }
  
  // データ取得
  float temperature = bme.temperature;
  float humidity = bme.humidity;
  float pressure = bme.pressure / 100.0;  // Pa to hPa
  float gas = bme.gas_resistance / 1000.0;  // Ohms to kOhms
  
  // シリアル出力
  Serial.println("=== Sensor Readings ===");
  Serial.printf("Temperature: %.2f °C\n", temperature);
  Serial.printf("Humidity: %.2f %%\n", humidity);
  Serial.printf("Pressure: %.2f hPa\n", pressure);
  Serial.printf("Gas: %.2f kOhms\n", gas);
  
  // MQTT送信（個別トピック）
  char buffer[32];
  
  snprintf(buffer, sizeof(buffer), "%.2f", temperature);
  mqtt.publish(TOPIC_TEMP, buffer);
  
  snprintf(buffer, sizeof(buffer), "%.2f", humidity);
  mqtt.publish(TOPIC_HUM, buffer);
  
  snprintf(buffer, sizeof(buffer), "%.2f", pressure);
  mqtt.publish(TOPIC_PRES, buffer);
  
  snprintf(buffer, sizeof(buffer), "%.2f", gas);
  mqtt.publish(TOPIC_GAS, buffer);
  
  // 統合JSON送信（オプション）
  JsonDocument doc;
  doc["device_id"] = DEVICE_ID;
  doc["timestamp"] = millis();
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["pressure"] = pressure;
  doc["gas_resistance"] = gas;
  
  char jsonBuffer[256];
  serializeJson(doc, jsonBuffer);
  mqtt.publish(TOPIC_STATUS, jsonBuffer);
  
  Serial.println("Telemetry published\n");
}

// ==================== ステータス送信 ====================
void publishStatus() {
  JsonDocument doc;
  doc["device_id"] = DEVICE_ID;
  doc["status"] = "online";
  doc["uptime_ms"] = millis();
  doc["free_heap"] = ESP.getFreeHeap();
  doc["wifi_rssi"] = WiFi.RSSI();
  
  char buffer[256];
  serializeJson(doc, buffer);
  
  mqtt.publish(TOPIC_STATUS, buffer);
  Serial.println("Status published");
}
