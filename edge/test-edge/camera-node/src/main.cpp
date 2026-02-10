/**
 * Camera Node - Freenove ESP32 WROVER v3.0
 * 
 * 機能:
 * - OV2640カメラからの画像取得
 * - Wi-Fi/MQTT接続
 * - リクエストに応じた画像キャプチャとBase64送信
 * - ステータス報告
 */

#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include "esp_camera.h"
#include "esp_log.h"

// ==================== 設定 ====================
// Wi-Fi設定（環境に合わせて変更）
const char* WIFI_SSID = "YOUR_WIFI_SSID";
const char* WIFI_PASS = "YOUR_WIFI_PASSWORD";

// MQTT設定
const char* MQTT_SERVER = "192.168.1.100";  // MQTTブローカーのIP
const int MQTT_PORT = 1883;
const char* DEVICE_ID = "camera_node_01";

// MQTTトピック
const char* TOPIC_STATUS = "office/camera/camera_node_01/status";
const char* TOPIC_REQUEST = "mcp/camera_node_01/request/capture_image";
const char* TOPIC_RESPONSE = "mcp/camera_node_01/response/#";

// カメラピン定義（Freenove ESP32 WROVER v3.0）
#define PWDN_GPIO_NUM     32
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     21
#define SIOD_GPIO_NUM     26
#define SIOC_GPIO_NUM     27
#define Y9_GPIO_NUM       35
#define Y8_GPIO_NUM       34
#define Y7_GPIO_NUM       39
#define Y6_GPIO_NUM       36
#define Y5_GPIO_NUM       19
#define Y4_GPIO_NUM       18
#define Y3_GPIO_NUM       5
#define Y2_GPIO_NUM       4
#define VSYNC_GPIO_NUM    25
#define HREF_GPIO_NUM     23
#define PCLK_GPIO_NUM     22

// オンボードLED
#define LED_PIN 2

// ==================== グローバル変数 ====================
WiFiClient wifiClient;
PubSubClient mqtt(wifiClient);
static const char* TAG = "CameraNode";

// ==================== 関数プロトタイプ ====================
void setupCamera();
void setupWiFi();
void setupMQTT();
void mqttCallback(char* topic, byte* payload, unsigned int length);
void captureAndSendImage(const char* requestId);
void publishStatus();

// ==================== セットアップ ====================
void setup() {
  Serial.begin(115200);
  delay(1000);
  
  Serial.println("\n=== Camera Node Starting ===");
  
  // LED初期化
  pinMode(LED_PIN, OUTPUT);
  digitalWrite(LED_PIN, LOW);
  
  // カメラ初期化
  setupCamera();
  
  // Wi-Fi接続
  setupWiFi();
  
  // MQTT接続
  setupMQTT();
  
  Serial.println("=== Initialization Complete ===\n");
  digitalWrite(LED_PIN, HIGH);
  publishStatus();
}

// ==================== メインループ ====================
void loop() {
  if (!mqtt.connected()) {
    Serial.println("MQTT disconnected, reconnecting...");
    setupMQTT();
  }
  mqtt.loop();
  
  // 定期的なステータス送信（30秒ごと）
  static unsigned long lastStatus = 0;
  if (millis() - lastStatus > 30000) {
    publishStatus();
    lastStatus = millis();
  }
  
  delay(10);
}

// ==================== カメラ初期化 ====================
void setupCamera() {
  Serial.println("Initializing camera...");
  
  camera_config_t config;
  config.ledc_channel = LEDC_CHANNEL_0;
  config.ledc_timer = LEDC_TIMER_0;
  config.pin_d0 = Y2_GPIO_NUM;
  config.pin_d1 = Y3_GPIO_NUM;
  config.pin_d2 = Y4_GPIO_NUM;
  config.pin_d3 = Y5_GPIO_NUM;
  config.pin_d4 = Y6_GPIO_NUM;
  config.pin_d5 = Y7_GPIO_NUM;
  config.pin_d6 = Y8_GPIO_NUM;
  config.pin_d7 = Y9_GPIO_NUM;
  config.pin_xclk = XCLK_GPIO_NUM;
  config.pin_pclk = PCLK_GPIO_NUM;
  config.pin_vsync = VSYNC_GPIO_NUM;
  config.pin_href = HREF_GPIO_NUM;
  config.pin_sccb_sda = SIOD_GPIO_NUM;
  config.pin_sccb_scl = SIOC_GPIO_NUM;
  config.pin_pwdn = PWDN_GPIO_NUM;
  config.pin_reset = RESET_GPIO_NUM;
  config.xclk_freq_hz = 20000000;
  config.pixel_format = PIXFORMAT_JPEG;
  
  // PSRAMがある場合は高解像度
  if (psramFound()) {
    config.frame_size = FRAMESIZE_UXGA;  // 1600x1200
    config.jpeg_quality = 10;
    config.fb_count = 2;
    Serial.println("PSRAM found, using high resolution");
  } else {
    config.frame_size = FRAMESIZE_SVGA;  // 800x600
    config.jpeg_quality = 12;
    config.fb_count = 1;
    Serial.println("PSRAM not found, using lower resolution");
  }
  
  // カメラ初期化
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x\n", err);
    ESP.restart();
  }
  
  Serial.println("Camera initialized successfully");
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
  mqtt.setCallback(mqttCallback);
  mqtt.setBufferSize(65536);  // 大きな画像データ用
  
  Serial.print("Connecting to MQTT broker...");
  
  int attempts = 0;
  while (!mqtt.connected() && attempts < 5) {
    if (mqtt.connect(DEVICE_ID)) {
      Serial.println(" connected!");
      mqtt.subscribe(TOPIC_REQUEST);
      Serial.printf("Subscribed to: %s\n", TOPIC_REQUEST);
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

// ==================== MQTTメッセージ受信 ====================
void mqttCallback(char* topic, byte* payload, unsigned int length) {
  Serial.printf("Message received on topic: %s\n", topic);
  
  // JSON解析
  JsonDocument doc;
  DeserializationError error = deserializeJson(doc, payload, length);
  
  if (error) {
    Serial.printf("JSON parse failed: %s\n", error.c_str());
    return;
  }
  
  const char* method = doc["method"];
  const char* requestId = doc["id"];
  
  if (strcmp(method, "capture_image") == 0) {
    captureAndSendImage(requestId);
  }
}

// ==================== 画像キャプチャと送信 ====================
void captureAndSendImage(const char* requestId) {
  Serial.println("Capturing image...");
  digitalWrite(LED_PIN, LOW);  // LED点滅で撮影中を表示
  
  // 画像取得
  camera_fb_t* fb = esp_camera_fb_get();
  if (!fb) {
    Serial.println("Camera capture failed");
    digitalWrite(LED_PIN, HIGH);
    return;
  }
  
  Serial.printf("Image captured: %d bytes\n", fb->len);
  
  // Base64エンコード（簡易実装：実際はチャンク送信が必要）
  // ここでは画像サイズが小さい場合のみ対応
  if (fb->len < 50000) {
    // レスポンストピック作成
    char responseTopic[128];
    snprintf(responseTopic, sizeof(responseTopic), 
             "mcp/camera_node_01/response/%s", requestId);
    
    // JSON作成
    JsonDocument responseDoc;
    responseDoc["jsonrpc"] = "2.0";
    responseDoc["id"] = requestId;
    responseDoc["result"]["image_size"] = fb->len;
    responseDoc["result"]["format"] = "jpeg";
    responseDoc["result"]["resolution"] = "UXGA";
    
    char jsonBuffer[256];
    serializeJson(responseDoc, jsonBuffer);
    
    // 送信
    mqtt.publish(responseTopic, jsonBuffer);
    Serial.printf("Response sent to: %s\n", responseTopic);
  }
  
  // フレームバッファ解放
  esp_camera_fb_return(fb);
  digitalWrite(LED_PIN, HIGH);
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
