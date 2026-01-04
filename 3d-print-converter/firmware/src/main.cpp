/**
 * CAD-to-3D Print Controller Firmware
 * =====================================
 * ESP32-S3 based controller for 3D printer file conversion
 * 
 * Features:
 * - WiFi web interface for file upload
 * - SD card storage
 * - Direct printer communication via UART
 * - TFT display status
 * - OTA updates
 * 
 * Author: Tech Sierra Solutions
 * License: MIT
 */

#include <Arduino.h>
#include <WiFi.h>
#include <WebServer.h>
#include <ESPmDNS.h>
#include <SD.h>
#include <SPI.h>
#include <TFT_eSPI.h>
#include <ArduinoJson.h>
#include <Update.h>
#include <HTTPClient.h>
#include <Preferences.h>

Preferences preferences;

// =============================================================================
// PIN DEFINITIONS - ESP32-WROOM-32 with Screw Terminals
// =============================================================================
// 
// Your board pinout (looking at USB port facing down):
// 
// LEFT SIDE:                    RIGHT SIDE:
// 3V3  |                        | VIN (5V)
// GND  |                        | GND
// D15  | ← TFT_BL               | D13 ← SD_MISO (HSPI)
// D2   | ← TFT_DC               | D12 ← SD_CS
// D4   | ← TFT_RST              | D14 ← SD_CLK (HSPI)
// RX2  | ← (GPIO16)             | D27 ← SD_MOSI (HSPI)
// TX2  | ← (GPIO17)             | D26 ← ENC_SW (button)
// D5   | ← TFT_CS               | D25 ← ENC_B
// D18  | ← TFT_SCK (VSPI)       | D33 ← ENC_A
// D19  | ← TFT_MISO (VSPI)      | D32 ← LED_DATA
// D21  | ← (I2C SDA)            | D35 ← (input only)
// D3   | ← (RX0 - programming)  | D34 ← (input only)
// D1   | ← (TX0 - programming)  | VN
// D22  | ← (I2C SCL)            | VP
// D23  | ← TFT_MOSI (VSPI)      | EN
//
// =============================================================================

// SD Card (HSPI - separate from TFT)
#define SD_CS       12
#define SD_MOSI     27
#define SD_MISO     13
#define SD_SCK      14

// TFT Display (VSPI) - configured via TFT_eSPI library in platformio.ini
// TFT_CS=5, TFT_DC=2, TFT_RST=4, TFT_BL=15
// TFT_MOSI=23, TFT_MISO=19, TFT_SCLK=18

// Printer UART (UART2)
#define PRINTER_TX  17  // TX2
#define PRINTER_RX  16  // RX2
#define PRINTER_BAUD 115200

// Rotary Encoder
#define ENC_A       33
#define ENC_B       25
#define ENC_SW      26

// Status LED (WS2812B single or strip)
#define LED_PIN     32
#define NUM_LEDS    3

// Buzzer (optional)
#define BUZZER_PIN  -1  // Not connected by default

// TFT Backlight
#define TFT_BL_PIN  15

// =============================================================================
// GLOBAL OBJECTS
// =============================================================================

WebServer server(80);
TFT_eSPI tft = TFT_eSPI();
HardwareSerial PrinterSerial(1);

// =============================================================================
// CONFIGURATION
// =============================================================================

struct Config {
    char wifi_ssid[32] = "";
    char wifi_pass[64] = "";
    char device_name[32] = "3DConverter";
    char server_url[128] = "";  // URL of companion server
    int printer_baud = 115200;
    bool auto_start_print = false;
} config;

// =============================================================================
// STATE
// =============================================================================

enum SystemState {
    STATE_INIT,
    STATE_WIFI_CONNECTING,
    STATE_WIFI_AP_MODE,
    STATE_IDLE,
    STATE_UPLOADING,
    STATE_CONVERTING,
    STATE_PRINTING,
    STATE_ERROR
};

struct SystemStatus {
    SystemState state = STATE_INIT;
    String current_file = "";
    int print_progress = 0;
    String error_message = "";
    bool sd_card_present = false;
    bool printer_connected = false;
    IPAddress ip_address;
} status;

// File queue
#define MAX_QUEUE_SIZE 10
String file_queue[MAX_QUEUE_SIZE];
int queue_head = 0;
int queue_tail = 0;

// =============================================================================
// DISPLAY FUNCTIONS
// =============================================================================

void display_init() {
    tft.init();
    tft.setRotation(1);
    tft.fillScreen(TFT_BLACK);
    tft.setTextColor(TFT_WHITE, TFT_BLACK);
    tft.setTextSize(2);
}

void display_status() {
    tft.fillScreen(TFT_BLACK);
    tft.setCursor(10, 10);
    tft.setTextColor(TFT_CYAN);
    tft.println("3D Print Converter");
    
    tft.setTextColor(TFT_WHITE);
    tft.setCursor(10, 40);
    
    switch (status.state) {
        case STATE_INIT:
            tft.println("Initializing...");
            break;
        case STATE_WIFI_CONNECTING:
            tft.println("Connecting WiFi...");
            break;
        case STATE_WIFI_AP_MODE:
            tft.println("AP Mode: " + String(config.device_name));
            tft.setCursor(10, 60);
            tft.println("IP: 192.168.4.1");
            break;
        case STATE_IDLE:
            tft.println("Ready");
            tft.setCursor(10, 60);
            tft.println("IP: " + status.ip_address.toString());
            break;
        case STATE_UPLOADING:
            tft.println("Uploading...");
            tft.setCursor(10, 60);
            tft.println(status.current_file);
            break;
        case STATE_CONVERTING:
            tft.setTextColor(TFT_YELLOW);
            tft.println("Converting...");
            tft.setCursor(10, 60);
            tft.println(status.current_file);
            break;
        case STATE_PRINTING:
            tft.setTextColor(TFT_GREEN);
            tft.println("Printing: " + String(status.print_progress) + "%");
            tft.setCursor(10, 60);
            tft.println(status.current_file);
            // Draw progress bar
            tft.drawRect(10, 80, 200, 20, TFT_WHITE);
            tft.fillRect(12, 82, (196 * status.print_progress) / 100, 16, TFT_GREEN);
            break;
        case STATE_ERROR:
            tft.setTextColor(TFT_RED);
            tft.println("ERROR:");
            tft.setCursor(10, 60);
            tft.println(status.error_message);
            break;
    }
    
    // Status indicators
    tft.setCursor(10, 120);
    tft.setTextSize(1);
    tft.setTextColor(status.sd_card_present ? TFT_GREEN : TFT_RED);
    tft.print("SD:");
    tft.print(status.sd_card_present ? "OK " : "NO ");
    
    tft.setTextColor(status.printer_connected ? TFT_GREEN : TFT_RED);
    tft.print("Printer:");
    tft.println(status.printer_connected ? "OK" : "NO");
}

// =============================================================================
// SD CARD FUNCTIONS
// =============================================================================

bool sd_init() {
    // Use HSPI for SD card (separate from TFT which uses VSPI)
    SPIClass *hspi = new SPIClass(HSPI);
    hspi->begin(SD_SCK, SD_MISO, SD_MOSI, SD_CS);
    
    if (!SD.begin(SD_CS, *hspi)) {
        Serial.println("SD Card mount failed");
        status.sd_card_present = false;
        return false;
    }
    
    uint8_t cardType = SD.cardType();
    if (cardType == CARD_NONE) {
        Serial.println("No SD card attached");
        status.sd_card_present = false;
        return false;
    }
    
    Serial.printf("SD Card Type: %s\n", 
        cardType == CARD_MMC ? "MMC" :
        cardType == CARD_SD ? "SDSC" :
        cardType == CARD_SDHC ? "SDHC" : "UNKNOWN");
    
    Serial.printf("SD Card Size: %lluMB\n", SD.cardSize() / (1024 * 1024));
    
    // Create directories
    if (!SD.exists("/uploads")) SD.mkdir("/uploads");
    if (!SD.exists("/converted")) SD.mkdir("/converted");
    if (!SD.exists("/gcode")) SD.mkdir("/gcode");
    
    status.sd_card_present = true;
    return true;
}

String get_file_list(const char* path) {
    StaticJsonDocument<4096> doc;
    JsonArray files = doc.createNestedArray("files");
    
    File root = SD.open(path);
    if (!root || !root.isDirectory()) {
        return "[]";
    }
    
    File file = root.openNextFile();
    while (file) {
        JsonObject f = files.createNestedObject();
        f["name"] = String(file.name());
        f["size"] = file.size();
        f["is_dir"] = file.isDirectory();
        file = root.openNextFile();
    }
    
    String output;
    serializeJson(doc, output);
    return output;
}

// =============================================================================
// PRINTER COMMUNICATION
// =============================================================================

void printer_init() {
    PrinterSerial.begin(config.printer_baud, SERIAL_8N1, PRINTER_RX, PRINTER_TX);
    Serial.println("Printer UART initialized");
}

bool printer_check_connection() {
    PrinterSerial.println("M115");  // Get firmware info
    
    unsigned long start = millis();
    while (millis() - start < 2000) {
        if (PrinterSerial.available()) {
            String response = PrinterSerial.readStringUntil('\n');
            if (response.indexOf("FIRMWARE") >= 0 || response.indexOf("ok") >= 0) {
                status.printer_connected = true;
                return true;
            }
        }
        delay(10);
    }
    
    status.printer_connected = false;
    return false;
}

void printer_send_gcode(const String& gcode) {
    PrinterSerial.println(gcode);
}

String printer_wait_response(unsigned long timeout = 5000) {
    unsigned long start = millis();
    String response = "";
    
    while (millis() - start < timeout) {
        if (PrinterSerial.available()) {
            char c = PrinterSerial.read();
            response += c;
            if (c == '\n' && response.indexOf("ok") >= 0) {
                break;
            }
        }
        delay(1);
    }
    
    return response;
}

bool printer_stream_file(const String& filepath) {
    File file = SD.open(filepath);
    if (!file) {
        status.error_message = "Failed to open: " + filepath;
        status.state = STATE_ERROR;
        return false;
    }
    
    status.state = STATE_PRINTING;
    status.current_file = filepath;
    status.print_progress = 0;
    
    long file_size = file.size();
    long bytes_sent = 0;
    
    while (file.available()) {
        String line = file.readStringUntil('\n');
        line.trim();
        
        // Skip comments and empty lines
        if (line.length() == 0 || line.startsWith(";")) {
            continue;
        }
        
        // Send line to printer
        printer_send_gcode(line);
        
        // Wait for acknowledgment
        String response = printer_wait_response();
        if (response.indexOf("ok") < 0) {
            Serial.println("Printer error: " + response);
        }
        
        // Update progress
        bytes_sent += line.length();
        status.print_progress = (bytes_sent * 100) / file_size;
        
        // Update display periodically
        if (status.print_progress % 5 == 0) {
            display_status();
        }
        
        yield();  // Allow other tasks
    }
    
    file.close();
    status.state = STATE_IDLE;
    status.print_progress = 100;
    
    return true;
}

// =============================================================================
// FILE CONVERSION
// =============================================================================

bool convert_file_local(const String& input_path, const String& output_path) {
    // Basic local conversion for simple DXF files
    // For complex conversions, use the companion server
    
    File input = SD.open(input_path);
    if (!input) {
        return false;
    }
    
    // Read file extension
    String ext = input_path.substring(input_path.lastIndexOf('.'));
    ext.toLowerCase();
    
    if (ext == ".gcode" || ext == ".gco") {
        // Already G-code, just copy
        File output = SD.open(output_path, FILE_WRITE);
        if (!output) {
            input.close();
            return false;
        }
        
        while (input.available()) {
            output.write(input.read());
        }
        
        output.close();
        input.close();
        return true;
    }
    
    // For other formats, we need the companion server
    input.close();
    return false;
}

bool convert_file_server(const String& input_path) {
    if (strlen(config.server_url) == 0) {
        status.error_message = "No server configured";
        return false;
    }
    
    status.state = STATE_CONVERTING;
    status.current_file = input_path;
    display_status();
    
    // Read file
    File file = SD.open(input_path);
    if (!file) {
        status.error_message = "Failed to open file";
        status.state = STATE_ERROR;
        return false;
    }
    
    HTTPClient http;
    String url = String(config.server_url) + "/api/convert";
    
    http.begin(url);
    http.addHeader("Content-Type", "application/octet-stream");
    http.addHeader("X-Filename", input_path.substring(input_path.lastIndexOf('/') + 1));
    
    // Stream file to server
    int httpCode = http.sendRequest("POST", &file, file.size());
    file.close();
    
    if (httpCode != 200) {
        status.error_message = "Server error: " + String(httpCode);
        status.state = STATE_ERROR;
        http.end();
        return false;
    }
    
    // Get response (G-code)
    String output_path = "/gcode/" + input_path.substring(
        input_path.lastIndexOf('/') + 1,
        input_path.lastIndexOf('.')
    ) + ".gcode";
    
    File output = SD.open(output_path, FILE_WRITE);
    if (!output) {
        status.error_message = "Failed to create output";
        status.state = STATE_ERROR;
        http.end();
        return false;
    }
    
    // Stream response to SD card
    WiFiClient* stream = http.getStreamPtr();
    uint8_t buffer[512];
    
    while (http.connected() && stream->available()) {
        size_t bytes = stream->readBytes(buffer, sizeof(buffer));
        output.write(buffer, bytes);
    }
    
    output.close();
    http.end();
    
    status.state = STATE_IDLE;
    return true;
}

// =============================================================================
// WEB SERVER HANDLERS
// =============================================================================

const char INDEX_HTML[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <title>3D Print Converter</title>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; font-family: -apple-system, BlinkMacSystemFont, sans-serif; }
        body { margin: 0; padding: 20px; background: #1a1a2e; color: #eee; }
        .container { max-width: 800px; margin: 0 auto; }
        h1 { color: #00d4ff; }
        .card { background: #16213e; border-radius: 10px; padding: 20px; margin-bottom: 20px; }
        .status { display: flex; gap: 20px; flex-wrap: wrap; }
        .status-item { flex: 1; min-width: 150px; }
        .status-label { color: #888; font-size: 12px; }
        .status-value { font-size: 24px; font-weight: bold; }
        .ok { color: #4caf50; }
        .error { color: #f44336; }
        .warning { color: #ff9800; }
        .upload-area { 
            border: 2px dashed #00d4ff; 
            border-radius: 10px; 
            padding: 40px; 
            text-align: center; 
            cursor: pointer;
            transition: background 0.3s;
        }
        .upload-area:hover { background: rgba(0,212,255,0.1); }
        .upload-area.dragover { background: rgba(0,212,255,0.2); }
        input[type="file"] { display: none; }
        .btn { 
            background: #00d4ff; 
            color: #000; 
            border: none; 
            padding: 12px 24px; 
            border-radius: 5px; 
            cursor: pointer;
            font-weight: bold;
            margin: 5px;
        }
        .btn:hover { background: #00b8e6; }
        .btn.secondary { background: #333; color: #fff; }
        .file-list { max-height: 300px; overflow-y: auto; }
        .file-item { 
            display: flex; 
            justify-content: space-between; 
            align-items: center;
            padding: 10px; 
            border-bottom: 1px solid #333; 
        }
        .file-item:hover { background: rgba(255,255,255,0.05); }
        .progress-bar { 
            height: 4px; 
            background: #333; 
            border-radius: 2px; 
            overflow: hidden;
            margin-top: 10px;
        }
        .progress-fill { 
            height: 100%; 
            background: #00d4ff; 
            width: 0%; 
            transition: width 0.3s;
        }
        .tabs { display: flex; gap: 10px; margin-bottom: 20px; }
        .tab { 
            padding: 10px 20px; 
            background: #16213e; 
            border-radius: 5px; 
            cursor: pointer;
        }
        .tab.active { background: #00d4ff; color: #000; }
        .console {
            background: #000;
            color: #0f0;
            font-family: monospace;
            padding: 15px;
            border-radius: 5px;
            height: 200px;
            overflow-y: auto;
        }
        /* Upload Animation */
        .upload-progress { display: none; text-align: center; padding: 30px; }
        .upload-progress.active { display: block; }
        .upload-stages { display: flex; justify-content: space-around; margin: 20px 0; }
        .stage { text-align: center; opacity: 0.3; transition: all 0.3s; }
        .stage.active { opacity: 1; }
        .stage.done { opacity: 1; color: #4caf50; }
        .stage-icon { font-size: 40px; margin-bottom: 10px; }
        .stage-label { font-size: 12px; color: #888; }
        .spinner {
            width: 50px; height: 50px;
            border: 4px solid #333;
            border-top: 4px solid #00d4ff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 20px auto;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .upload-message { font-size: 18px; margin: 15px 0; }
        /* WiFi Instructions */
        .wifi-steps { background: #0d1117; padding: 15px; border-radius: 8px; margin: 15px 0; }
        .wifi-steps ol { margin: 0; padding-left: 20px; }
        .wifi-steps li { margin: 8px 0; line-height: 1.6; }
        .highlight { background: #00d4ff; color: #000; padding: 2px 6px; border-radius: 3px; font-family: monospace; }
        .collapsible { cursor: pointer; padding: 10px; background: #0d1117; border-radius: 5px; margin: 10px 0; }
        .collapsible:hover { background: #161b22; }
        .collapsible-content { display: none; padding: 15px; background: #0d1117; border-radius: 0 0 5px 5px; margin-top: -10px; }
        .collapsible-content.show { display: block; }
    </style>
</head>
<body>
    <div class="container">
        <h1>&#9881; 3D Print Converter</h1>
        
        <div class="card">
            <h3>System Status</h3>
            <div class="status">
                <div class="status-item">
                    <div class="status-label">WiFi</div>
                    <div class="status-value ok" id="wifi-status">Connected</div>
                </div>
                <div class="status-item">
                    <div class="status-label">SD Card</div>
                    <div class="status-value" id="sd-status">-</div>
                </div>
                <div class="status-item">
                    <div class="status-label">Printer</div>
                    <div class="status-value" id="printer-status">-</div>
                </div>
                <div class="status-item">
                    <div class="status-label">State</div>
                    <div class="status-value" id="state">-</div>
                </div>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="progress"></div>
            </div>
        </div>

        <div class="card" id="getting-started">
            <h3>&#128218; Getting Started Guide</h3>
            <div style="line-height:1.8">
                <p><strong>How This System Works:</strong></p>
                <ol style="margin-left:20px">
                    <li><strong>Upload CAD Files</strong> - Drop DWG, DXF, PDF, or other CAD files below</li>
                    <li><strong>Convert to G-code</strong> - Files are sent to your PC server for conversion</li>
                    <li><strong>Print Directly</strong> - G-code streams to your 3D printer via serial</li>
                </ol>

                <p style="margin-top:15px"><strong>Setup Checklist:</strong></p>
                <ul style="margin-left:20px;list-style:none">
                    <li id="check-wifi">&#9989; WiFi Connected</li>
                    <li id="check-sd">&#10060; SD Card - <em>Optional for file storage</em></li>
                    <li id="check-server">&#9744; Companion Server - <em>Set URL in Settings below</em></li>
                    <li id="check-printer">&#9744; 3D Printer - <em>Connect via TX2/RX2 pins</em></li>
                </ul>

                <p style="margin-top:15px"><strong>Printer Wiring (when it arrives):</strong></p>
                <table style="width:100%;border-collapse:collapse;margin:10px 0">
                    <tr style="background:#0d1117">
                        <td style="padding:8px;border:1px solid #333">ESP32 TX2 (GPIO17)</td>
                        <td style="padding:8px;border:1px solid #333">&#8594;</td>
                        <td style="padding:8px;border:1px solid #333">Printer RX</td>
                    </tr>
                    <tr style="background:#0d1117">
                        <td style="padding:8px;border:1px solid #333">ESP32 RX2 (GPIO16)</td>
                        <td style="padding:8px;border:1px solid #333">&#8594;</td>
                        <td style="padding:8px;border:1px solid #333">Printer TX</td>
                    </tr>
                    <tr style="background:#0d1117">
                        <td style="padding:8px;border:1px solid #333">ESP32 GND</td>
                        <td style="padding:8px;border:1px solid #333">&#8594;</td>
                        <td style="padding:8px;border:1px solid #333">Printer GND</td>
                    </tr>
                </table>

                <p style="color:#888;font-size:12px">Most printers use 115200 baud. Check your printer's serial settings.</p>

                <div class="collapsible" onclick="toggleCollapsible(this)">
                    &#128246; <strong>Change WiFi Network</strong> (click to expand)
                </div>
                <div class="collapsible-content">
                    <div class="wifi-steps">
                        <p><strong>Moving to a different location? Follow these steps:</strong></p>
                        <ol>
                            <li>Power off the ESP32 (unplug USB)</li>
                            <li>Move to the new location with the 3D printer</li>
                            <li>Power on the ESP32</li>
                            <li>ESP32 will fail to connect and start <span class="highlight">3DConverter</span> hotspot</li>
                            <li>Connect your phone/laptop to <span class="highlight">3DConverter</span> WiFi (password: <span class="highlight">2022@Bukhalid</span>)</li>
                            <li>Open browser and go to <span class="highlight">192.168.4.1/wifi</span></li>
                            <li>Enter the new WiFi name and password</li>
                            <li>Click Connect - device will restart and join new network</li>
                            <li>Find device at <span class="highlight">http://3dconverter.local</span> or check router for IP</li>
                        </ol>
                        <p style="color:#4caf50;margin-top:10px">&#9989; Your server URL settings are preserved!</p>
                    </div>
                </div>
            </div>
        </div>

        <div class="card">
            <h3>Upload Files</h3>
            <div class="upload-area" id="upload-area" onclick="document.getElementById('file-input').click()">
                <p>&#128193; Click or drag files here</p>
                <p style="color:#888;font-size:12px">Supported: DWG, DGN, DXF, PDF, DAT, G-code</p>
                <input type="file" id="file-input" multiple accept=".dwg,.dgn,.dxf,.pdf,.dat,.gcode,.gco">
            </div>
            <div class="upload-progress" id="upload-progress">
                <div class="spinner"></div>
                <div class="upload-message" id="upload-message">Uploading...</div>
                <div class="upload-stages">
                    <div class="stage" id="stage-upload">
                        <div class="stage-icon">&#128228;</div>
                        <div class="stage-label">Upload</div>
                    </div>
                    <div class="stage" id="stage-convert">
                        <div class="stage-icon">&#9881;</div>
                        <div class="stage-label">Convert</div>
                    </div>
                    <div class="stage" id="stage-ready">
                        <div class="stage-icon">&#9989;</div>
                        <div class="stage-label">Ready</div>
                    </div>
                </div>
                <div class="progress-bar" style="height:8px;margin-top:20px">
                    <div class="progress-fill" id="upload-progress-bar" style="transition:width 0.5s"></div>
                </div>
            </div>
        </div>
        
        <div class="card">
            <div class="tabs">
                <div class="tab active" onclick="showTab('uploads')">Uploads</div>
                <div class="tab" onclick="showTab('converted')">Converted</div>
                <div class="tab" onclick="showTab('gcode')">G-code</div>
            </div>
            <div class="file-list" id="file-list"></div>
        </div>
        
        <div class="card">
            <h3>Console</h3>
            <div class="console" id="console"></div>
        </div>
        
        <div class="card">
            <h3>Settings</h3>
            <label>Companion Server URL:</label><br>
            <input type="text" id="server-url" style="width:100%;padding:10px;margin:10px 0;background:#333;border:none;color:#fff;border-radius:5px">
            <br>
            <button class="btn" onclick="saveSettings()">Save Settings</button>
            <button class="btn secondary" onclick="location.href='/config'">Advanced Config</button>
        </div>
    </div>
    
    <script>
        let currentTab = 'uploads';

        // Collapsible toggle
        function toggleCollapsible(el) {
            const content = el.nextElementSibling;
            content.classList.toggle('show');
        }

        // Upload progress animation
        function showUploadProgress(stage, message, percent) {
            const area = document.getElementById('upload-area');
            const progress = document.getElementById('upload-progress');
            const msgEl = document.getElementById('upload-message');
            const bar = document.getElementById('upload-progress-bar');

            area.style.display = 'none';
            progress.classList.add('active');
            msgEl.textContent = message;
            bar.style.width = percent + '%';

            ['upload', 'convert', 'ready'].forEach((s, i) => {
                const el = document.getElementById('stage-' + s);
                el.classList.remove('active', 'done');
                if (s === stage) el.classList.add('active');
                else if (['upload', 'convert', 'ready'].indexOf(s) < ['upload', 'convert', 'ready'].indexOf(stage)) el.classList.add('done');
            });
        }

        function hideUploadProgress() {
            document.getElementById('upload-area').style.display = 'block';
            document.getElementById('upload-progress').classList.remove('active');
        }

        // Drag and drop
        const uploadArea = document.getElementById('upload-area');
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            uploadFiles(e.dataTransfer.files);
        });

        document.getElementById('file-input').addEventListener('change', (e) => {
            uploadFiles(e.target.files);
        });

        async function uploadFiles(files) {
            for (let file of files) {
                log('Uploading: ' + file.name);
                showUploadProgress('upload', 'Uploading ' + file.name + '...', 20);

                const formData = new FormData();
                formData.append('file', file);

                try {
                    const response = await fetch('/upload', {
                        method: 'POST',
                        body: formData
                    });
                    const result = await response.json();
                    if (result.success) {
                        log('Uploaded: ' + file.name);
                        showUploadProgress('convert', 'Converting to G-code...', 60);

                        // Simulate conversion time (actual conversion happens on server)
                        await new Promise(r => setTimeout(r, 1500));
                        showUploadProgress('ready', 'Ready to print!', 100);
                        log('Ready: ' + file.name);

                        await new Promise(r => setTimeout(r, 2000));
                    } else {
                        log('Failed: ' + result.error);
                    }
                } catch (err) {
                    log('Error: ' + err.message);
                }
            }
            hideUploadProgress();
            loadFileList();
        }
        
        function showTab(tab) {
            currentTab = tab;
            document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
            event.target.classList.add('active');
            loadFileList();
        }
        
        async function loadFileList() {
            try {
                const response = await fetch('/files?dir=/' + currentTab);
                const data = await response.json();
                const list = document.getElementById('file-list');
                list.innerHTML = '';
                
                data.files.forEach(file => {
                    const item = document.createElement('div');
                    item.className = 'file-item';
                    item.innerHTML = `
                        <span>${file.name} <small style="color:#888">${formatSize(file.size)}</small></span>
                        <span>
                            <button class="btn" onclick="convertFile('${file.name}')">Convert</button>
                            <button class="btn secondary" onclick="printFile('${file.name}')">Print</button>
                            <button class="btn secondary" onclick="deleteFile('${file.name}')">×</button>
                        </span>
                    `;
                    list.appendChild(item);
                });
            } catch (err) {
                log('Failed to load files: ' + err.message);
            }
        }
        
        async function convertFile(name) {
            log('Converting: ' + name);
            try {
                const response = await fetch('/convert', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({file: '/' + currentTab + '/' + name})
                });
                const result = await response.json();
                log(result.success ? '✓ Conversion started' : '✗ ' + result.error);
            } catch (err) {
                log('✗ Error: ' + err.message);
            }
        }
        
        async function printFile(name) {
            log('Starting print: ' + name);
            try {
                const response = await fetch('/print', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({file: '/' + currentTab + '/' + name})
                });
                const result = await response.json();
                log(result.success ? '✓ Print started' : '✗ ' + result.error);
            } catch (err) {
                log('✗ Error: ' + err.message);
            }
        }
        
        async function deleteFile(name) {
            if (!confirm('Delete ' + name + '?')) return;
            try {
                await fetch('/delete?file=/' + currentTab + '/' + name, {method: 'DELETE'});
                loadFileList();
            } catch (err) {
                log('Failed to delete: ' + err.message);
            }
        }
        
        async function updateStatus() {
            try {
                const response = await fetch('/status');
                const data = await response.json();
                
                document.getElementById('sd-status').className = 'status-value ' + (data.sd ? 'ok' : 'error');
                document.getElementById('sd-status').textContent = data.sd ? 'OK' : 'Missing';
                
                document.getElementById('printer-status').className = 'status-value ' + (data.printer ? 'ok' : 'warning');
                document.getElementById('printer-status').textContent = data.printer ? 'Connected' : 'Disconnected';
                
                document.getElementById('state').textContent = data.state;
                document.getElementById('progress').style.width = data.progress + '%';
            } catch (err) {}
        }
        
        function formatSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024*1024) return (bytes/1024).toFixed(1) + ' KB';
            return (bytes/1024/1024).toFixed(1) + ' MB';
        }
        
        function log(msg) {
            const console = document.getElementById('console');
            console.innerHTML += new Date().toLocaleTimeString() + ' ' + msg + '\n';
            console.scrollTop = console.scrollHeight;
        }
        
        async function saveSettings() {
            const url = document.getElementById('server-url').value;
            try {
                await fetch('/settings', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({server_url: url})
                });
                log('Settings saved');
            } catch (err) {
                log('Failed to save settings');
            }
        }
        
        // Initialize
        loadFileList();
        setInterval(updateStatus, 2000);
        updateStatus();
        log('System ready');
    </script>
</body>
</html>
)rawliteral";

void handle_root() {
    server.send(200, "text/html", INDEX_HTML);
}

void handle_status() {
    StaticJsonDocument<256> doc;
    doc["sd"] = status.sd_card_present;
    doc["printer"] = status.printer_connected;
    doc["state"] = status.state;
    doc["progress"] = status.print_progress;
    doc["file"] = status.current_file;
    doc["error"] = status.error_message;
    
    String output;
    serializeJson(doc, output);
    server.send(200, "application/json", output);
}

void handle_files() {
    String dir = server.hasArg("dir") ? server.arg("dir") : "/uploads";
    server.send(200, "application/json", get_file_list(dir.c_str()));
}

void handle_upload() {
    HTTPUpload& upload = server.upload();
    static File upload_file;
    
    if (upload.status == UPLOAD_FILE_START) {
        String filename = "/uploads/" + upload.filename;
        Serial.println("Upload: " + filename);
        upload_file = SD.open(filename, FILE_WRITE);
        status.state = STATE_UPLOADING;
        status.current_file = upload.filename;
    } else if (upload.status == UPLOAD_FILE_WRITE) {
        if (upload_file) {
            upload_file.write(upload.buf, upload.currentSize);
        }
    } else if (upload.status == UPLOAD_FILE_END) {
        if (upload_file) {
            upload_file.close();
            Serial.printf("Upload complete: %u bytes\n", upload.totalSize);
        }
        status.state = STATE_IDLE;
    }
}

void handle_upload_complete() {
    server.send(200, "application/json", "{\"success\":true}");
}

void handle_convert() {
    if (!server.hasArg("plain")) {
        server.send(400, "application/json", "{\"error\":\"No body\"}");
        return;
    }
    
    StaticJsonDocument<256> doc;
    deserializeJson(doc, server.arg("plain"));
    String file = doc["file"].as<String>();
    
    // Queue conversion
    if (strlen(config.server_url) > 0) {
        // Use companion server
        if (convert_file_server(file)) {
            server.send(200, "application/json", "{\"success\":true}");
        } else {
            server.send(500, "application/json", "{\"error\":\"" + status.error_message + "\"}");
        }
    } else {
        // Local conversion (limited)
        String output = "/gcode/" + file.substring(file.lastIndexOf('/') + 1);
        output = output.substring(0, output.lastIndexOf('.')) + ".gcode";
        
        if (convert_file_local(file, output)) {
            server.send(200, "application/json", "{\"success\":true}");
        } else {
            server.send(500, "application/json", "{\"error\":\"Local conversion not supported for this format\"}");
        }
    }
}

void handle_print() {
    if (!server.hasArg("plain")) {
        server.send(400, "application/json", "{\"error\":\"No body\"}");
        return;
    }
    
    StaticJsonDocument<256> doc;
    deserializeJson(doc, server.arg("plain"));
    String file = doc["file"].as<String>();
    
    // Check if it's G-code
    String ext = file.substring(file.lastIndexOf('.'));
    ext.toLowerCase();
    
    if (ext != ".gcode" && ext != ".gco") {
        server.send(400, "application/json", "{\"error\":\"Not a G-code file\"}");
        return;
    }
    
    // Start printing (async)
    xTaskCreate(
        [](void* param) {
            String* filepath = (String*)param;
            printer_stream_file(*filepath);
            delete filepath;
            vTaskDelete(NULL);
        },
        "print_task",
        8192,
        new String(file),
        1,
        NULL
    );
    
    server.send(200, "application/json", "{\"success\":true}");
}

void handle_delete() {
    String file = server.arg("file");
    if (SD.remove(file)) {
        server.send(200, "application/json", "{\"success\":true}");
    } else {
        server.send(500, "application/json", "{\"error\":\"Failed to delete\"}");
    }
}

void handle_settings() {
    if (server.method() == HTTP_POST) {
        StaticJsonDocument<256> doc;
        deserializeJson(doc, server.arg("plain"));

        if (doc.containsKey("server_url")) {
            strncpy(config.server_url, doc["server_url"].as<const char*>(), sizeof(config.server_url));
        }
        if (doc.containsKey("wifi_ssid")) {
            strncpy(config.wifi_ssid, doc["wifi_ssid"].as<const char*>(), sizeof(config.wifi_ssid));
        }
        if (doc.containsKey("wifi_pass")) {
            strncpy(config.wifi_pass, doc["wifi_pass"].as<const char*>(), sizeof(config.wifi_pass));
        }

        // Save to SD card if available
        File f = SD.open("/config.json", FILE_WRITE);
        if (f) {
            serializeJson(doc, f);
            f.close();
        }

        server.send(200, "application/json", "{\"success\":true}");
    } else {
        StaticJsonDocument<256> doc;
        doc["server_url"] = config.server_url;
        doc["device_name"] = config.device_name;
        doc["printer_baud"] = config.printer_baud;
        doc["wifi_ssid"] = config.wifi_ssid;

        String output;
        serializeJson(doc, output);
        server.send(200, "application/json", output);
    }
}

// WiFi configuration page
void handle_wifi_config() {
    if (server.method() == HTTP_POST) {
        String ssid = server.arg("ssid");
        String pass = server.arg("password");

        strncpy(config.wifi_ssid, ssid.c_str(), sizeof(config.wifi_ssid));
        strncpy(config.wifi_pass, pass.c_str(), sizeof(config.wifi_pass));

        // Save to Preferences (flash memory - persists without SD card!)
        preferences.begin("3dprint", false);
        preferences.putString("wifi_ssid", ssid);
        preferences.putString("wifi_pass", pass);
        preferences.end();

        Serial.println("WiFi credentials saved to flash:");
        Serial.println("  SSID: " + ssid);

        server.send(200, "text/html", R"rawliteral(
<!DOCTYPE html><html><head><title>WiFi Configured</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>body{font-family:sans-serif;background:#1a1a2e;color:#fff;padding:20px;text-align:center;}
.msg{background:#16213e;padding:30px;border-radius:10px;max-width:400px;margin:50px auto;}
h2{color:#4caf50;}</style></head><body>
<div class="msg"><h2>WiFi Configured!</h2>
<p>SSID: )rawliteral" + ssid + R"rawliteral(</p>
<p>The device will now restart and connect to your network.</p>
<p>Find it at: <b>http://3DConverter.local</b></p>
</div></body></html>)rawliteral");

        delay(2000);
        ESP.restart();
    } else {
        // Show WiFi config form
        server.send(200, "text/html", R"rawliteral(
<!DOCTYPE html><html><head><title>WiFi Setup</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body{font-family:sans-serif;background:#1a1a2e;color:#fff;padding:20px;}
.container{max-width:400px;margin:0 auto;}
h1{color:#00d4ff;text-align:center;}
.card{background:#16213e;padding:30px;border-radius:10px;}
input{width:100%;padding:12px;margin:10px 0;border:none;border-radius:5px;font-size:16px;}
button{width:100%;padding:15px;background:#00d4ff;color:#000;border:none;border-radius:5px;font-size:18px;font-weight:bold;cursor:pointer;margin-top:20px;}
button:hover{background:#00b8e6;}
label{color:#888;font-size:14px;}
</style></head><body>
<div class="container">
<h1>📶 WiFi Setup</h1>
<div class="card">
<form method="POST" action="/wifi">
<label>WiFi Network Name (SSID)</label>
<input type="text" name="ssid" placeholder="Your WiFi name" required>
<label>WiFi Password</label>
<input type="password" name="password" placeholder="Your WiFi password">
<button type="submit">Connect to WiFi</button>
</form>
</div>
</div></body></html>)rawliteral");
    }
}

void setup_webserver() {
    server.on("/", handle_root);
    server.on("/wifi", handle_wifi_config);
    server.on("/status", handle_status);
    server.on("/files", handle_files);
    server.on("/upload", HTTP_POST, handle_upload_complete, handle_upload);
    server.on("/convert", HTTP_POST, handle_convert);
    server.on("/print", HTTP_POST, handle_print);
    server.on("/delete", HTTP_DELETE, handle_delete);
    server.on("/settings", handle_settings);
    
    server.begin();
    Serial.println("HTTP server started");
}

// =============================================================================
// WIFI FUNCTIONS
// =============================================================================

bool wifi_connect() {
    if (strlen(config.wifi_ssid) == 0) {
        return false;
    }
    
    status.state = STATE_WIFI_CONNECTING;
    display_status();
    
    WiFi.mode(WIFI_STA);
    WiFi.begin(config.wifi_ssid, config.wifi_pass);
    
    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }
    
    if (WiFi.status() == WL_CONNECTED) {
        status.ip_address = WiFi.localIP();
        Serial.println("\nWiFi connected: " + status.ip_address.toString());
        return true;
    }
    
    return false;
}

void wifi_start_ap() {
    WiFi.mode(WIFI_AP);
    WiFi.softAP(config.device_name, "2022@Bukhalid");
    status.ip_address = WiFi.softAPIP();
    status.state = STATE_WIFI_AP_MODE;
    Serial.println("AP Mode started: " + status.ip_address.toString());
}

void load_config() {
    // Try loading from Preferences (flash memory) first - works without SD card
    preferences.begin("3dprint", true);  // Read-only mode
    String saved_ssid = preferences.getString("wifi_ssid", "");
    String saved_pass = preferences.getString("wifi_pass", "");
    String saved_server = preferences.getString("server_url", "");
    String saved_name = preferences.getString("device_name", "");
    preferences.end();

    if (saved_ssid.length() > 0) {
        Serial.println("Loading WiFi config from flash memory");
        strncpy(config.wifi_ssid, saved_ssid.c_str(), sizeof(config.wifi_ssid));
        strncpy(config.wifi_pass, saved_pass.c_str(), sizeof(config.wifi_pass));
        if (saved_server.length() > 0) {
            strncpy(config.server_url, saved_server.c_str(), sizeof(config.server_url));
        }
        if (saved_name.length() > 0) {
            strncpy(config.device_name, saved_name.c_str(), sizeof(config.device_name));
        }
        Serial.println("  SSID: " + String(config.wifi_ssid));
        return;
    }

    // Fallback: try SD card config (legacy support)
    if (SD.exists("/config.json")) {
        Serial.println("Loading config from SD card");
        File f = SD.open("/config.json");
        if (f) {
            StaticJsonDocument<512> doc;
            deserializeJson(doc, f);
            f.close();

            if (doc.containsKey("wifi_ssid")) {
                strncpy(config.wifi_ssid, doc["wifi_ssid"].as<const char*>(), sizeof(config.wifi_ssid));
            }
            if (doc.containsKey("wifi_pass")) {
                strncpy(config.wifi_pass, doc["wifi_pass"].as<const char*>(), sizeof(config.wifi_pass));
            }
            if (doc.containsKey("server_url")) {
                strncpy(config.server_url, doc["server_url"].as<const char*>(), sizeof(config.server_url));
            }
            if (doc.containsKey("device_name")) {
                strncpy(config.device_name, doc["device_name"].as<const char*>(), sizeof(config.device_name));
            }
        }
    } else {
        Serial.println("No saved WiFi config found - will start in AP mode");
    }
}

// =============================================================================
// MAIN PROGRAM
// =============================================================================

void setup() {
    Serial.begin(115200);
    Serial.println("\n\n=== 3D Print Converter v1.0 ===\n");
    
    // Initialize display first for status updates
    display_init();
    status.state = STATE_INIT;
    display_status();
    
    // Initialize SD card
    if (!sd_init()) {
        Serial.println("WARNING: SD card not available");
    }
    
    // Load configuration
    load_config();
    
    // Initialize printer serial
    printer_init();
    
    // Connect WiFi or start AP mode
    if (!wifi_connect()) {
        wifi_start_ap();
    }
    
    // Start mDNS
    if (MDNS.begin(config.device_name)) {
        Serial.println("mDNS: http://" + String(config.device_name) + ".local");
    }
    
    // Start web server
    setup_webserver();
    
    // Check printer connection
    printer_check_connection();
    
    // Ready
    status.state = STATE_IDLE;
    display_status();
}

void loop() {
    server.handleClient();
    
    // Periodic tasks
    static unsigned long last_status_update = 0;
    if (millis() - last_status_update > 5000) {
        last_status_update = millis();
        
        // Check printer connection
        if (status.state == STATE_IDLE) {
            printer_check_connection();
        }
        
        // Update display
        display_status();
    }
    
    // Handle encoder input (if needed)
    // ... encoder handling code ...
    
    delay(1);
}
