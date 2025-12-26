# CAD-to-3D Print Converter System
## Complete Open-Source Solution

### System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                        CAD-to-3D Print Converter                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────────────────┐   │
│  │ INPUT FILES  │    │  CONVERSION      │    │  OUTPUT                  │   │
│  │              │    │  PIPELINE        │    │                          │   │
│  │ • .dwg       │───►│                  │───►│ • .stl (mesh)            │   │
│  │ • .dgn       │    │ Python + FreeCAD │    │ • .gcode (printer ready) │   │
│  │ • .dxf       │    │ + ODA Converter  │    │ • .3mf (modern format)   │   │
│  │ • .pdf       │    │                  │    │                          │   │
│  │ • .dat       │    └────────┬─────────┘    └──────────────────────────┘   │
│  └──────────────┘             │                                              │
│                               │                                              │
│  ┌────────────────────────────▼─────────────────────────────────────────┐   │
│  │                     HARDWARE CONTROLLER                               │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │   │
│  │  │   ESP32-S3  │  │  SD Card    │  │  OLED/TFT   │  │  3D Printer │  │   │
│  │  │   Main MCU  │──│  Storage    │──│  Display    │──│  Interface  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Part 1: Software Components (All Open Source)

### Required Software Stack

| Component | Purpose | License |
|-----------|---------|---------|
| **Python 3.10+** | Main scripting | PSF |
| **FreeCAD** | CAD operations, 3D modeling | LGPL |
| **ODA File Converter** | DWG/DGN to DXF | Free (proprietary but free) |
| **Inkscape** | PDF to SVG/DXF | GPL |
| **OpenSCAD** | Parametric 3D from scripts | GPL |
| **PrusaSlicer/Cura** | STL to G-code | AGPL/LGPL |
| **ezdxf** | Python DXF library | MIT |
| **trimesh** | Python 3D mesh library | MIT |
| **numpy-stl** | STL file handling | BSD |

### Conversion Flow

```
                    ┌─────────────────────────────────────────┐
                    │         FILE TYPE DETECTION              │
                    └──────────────────┬──────────────────────┘
                                       │
          ┌────────────────┬───────────┼───────────┬────────────────┐
          ▼                ▼           ▼           ▼                ▼
    ┌──────────┐    ┌──────────┐ ┌──────────┐ ┌──────────┐   ┌──────────┐
    │   DWG    │    │   DGN    │ │   DXF    │ │   PDF    │   │   DAT    │
    └────┬─────┘    └────┬─────┘ └────┬─────┘ └────┬─────┘   └────┬─────┘
         │               │            │            │              │
         ▼               ▼            │            ▼              ▼
    ┌──────────┐    ┌──────────┐     │      ┌──────────┐   ┌──────────┐
    │   ODA    │    │   ODA    │     │      │ Inkscape │   │  Parser  │
    │Converter │    │Converter │     │      │ PDF→SVG  │   │ (custom) │
    └────┬─────┘    └────┬─────┘     │      └────┬─────┘   └────┬─────┘
         │               │            │            │              │
         └───────────────┴────────────┼────────────┴──────────────┘
                                      │
                                      ▼
                              ┌──────────────┐
                              │   DXF/SVG    │
                              │  Normalized  │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │   FreeCAD    │
                              │  Processing  │
                              │              │
                              │ • 2D → 3D    │
                              │ • Extrusion  │
                              │ • Healing    │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │  STL/STEP    │
                              │   Output     │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │  PrusaSlicer │
                              │  STL→G-code  │
                              └──────┬───────┘
                                     │
                                     ▼
                              ┌──────────────┐
                              │   G-CODE     │
                              │  (Print)     │
                              └──────────────┘
```

---

## Part 2: Hardware Design

### ESP32-S3 Controller Board Features

- **MCU**: ESP32-S3-WROOM-1 (dual-core, 240MHz, WiFi, BLE)
- **Display**: 2.4" TFT or 1.3" OLED
- **Storage**: MicroSD card slot
- **Connectivity**: 
  - USB-C (file upload + power)
  - WiFi (web interface)
  - UART (3D printer serial)
- **Controls**: Rotary encoder + buttons
- **Power**: 5V USB or 12V from printer PSU

### PCB Block Diagram

```
                          ┌─────────────────────────────────────┐
                          │         3D Print Controller         │
                          │              PCB v1.0               │
                          └─────────────────────────────────────┘
                                           │
    ┌──────────────────────────────────────┼──────────────────────────────────┐
    │                                      │                                   │
    │  ┌─────────────┐              ┌──────┴──────┐              ┌──────────┐ │
    │  │   USB-C     │              │             │              │  SD Card │ │
    │  │  Connector  │──────────────│  ESP32-S3   │──────────────│   Slot   │ │
    │  │  (CH340C)   │              │  WROOM-1    │              │          │ │
    │  └─────────────┘              │             │              └──────────┘ │
    │                               │  ┌───────┐  │                           │
    │  ┌─────────────┐              │  │ PSRAM │  │              ┌──────────┐ │
    │  │   5V/3.3V   │              │  │  8MB  │  │              │  TFT/    │ │
    │  │  Regulator  │──────────────│  └───────┘  │──────────────│  OLED    │ │
    │  │  (AMS1117)  │              │             │   SPI        │ Display  │ │
    │  └─────────────┘              └──────┬──────┘              └──────────┘ │
    │                                      │                                   │
    │  ┌─────────────┐              ┌──────┴──────┐              ┌──────────┐ │
    │  │   Rotary    │              │    UART     │              │  Status  │ │
    │  │   Encoder   │──────────────│   Header    │──────────────│   LEDs   │ │
    │  │  + Button   │   GPIO       │ (to Printer)│    GPIO      │  RGB x3  │ │
    │  └─────────────┘              └─────────────┘              └──────────┘ │
    │                                                                          │
    └──────────────────────────────────────────────────────────────────────────┘
```

### Pin Assignments

| Function | ESP32-S3 Pin | Notes |
|----------|--------------|-------|
| USB D+ | GPIO19 | Native USB |
| USB D- | GPIO20 | Native USB |
| SD_CMD | GPIO35 | SD Card |
| SD_CLK | GPIO36 | SD Card |
| SD_D0 | GPIO37 | SD Card |
| TFT_CS | GPIO10 | Display |
| TFT_DC | GPIO9 | Display |
| TFT_RST | GPIO8 | Display |
| TFT_MOSI | GPIO11 | SPI |
| TFT_SCLK | GPIO12 | SPI |
| UART_TX | GPIO43 | To Printer |
| UART_RX | GPIO44 | From Printer |
| ENC_A | GPIO4 | Rotary Encoder |
| ENC_B | GPIO5 | Rotary Encoder |
| ENC_SW | GPIO6 | Encoder Button |
| LED_R | GPIO38 | Status LED |
| LED_G | GPIO39 | Status LED |
| LED_B | GPIO40 | Status LED |

---

## Part 3: System Modes

### Mode 1: Standalone (ESP32 Only)
- Upload files via WiFi web interface
- Basic conversion (DXF → STL extrusion)
- Send G-code directly to printer

### Mode 2: With Companion Server (Raspberry Pi / PC)
- Full conversion pipeline
- Complex 3D operations
- Web dashboard
- Queue management

### Mode 3: Cloud Hybrid
- Heavy conversion on cloud/server
- ESP32 handles file transfer + printer control
- Perfect for your ICC integration

---

## Bill of Materials (BOM)

| Component | Qty | Est. Cost | Source |
|-----------|-----|-----------|--------|
| ESP32-S3-WROOM-1-N8R8 | 1 | $4.50 | AliExpress/LCSC |
| 2.4" TFT ILI9341 | 1 | $3.00 | AliExpress |
| MicroSD Card Slot | 1 | $0.30 | LCSC |
| USB-C Connector | 1 | $0.20 | LCSC |
| AMS1117-3.3V | 1 | $0.10 | LCSC |
| CH340C (USB-UART) | 1 | $0.50 | LCSC |
| Rotary Encoder | 1 | $0.50 | AliExpress |
| RGB LEDs (WS2812B) | 3 | $0.30 | LCSC |
| Capacitors/Resistors | Kit | $1.00 | LCSC |
| PCB (JLCPCB) | 5 | $2.00 | JLCPCB |
| **Total** | | **~$12.50** | |

---

## Getting Started

1. Install software dependencies (see `software/requirements.txt`)
2. Run the conversion server
3. Flash ESP32 firmware
4. Connect to WiFi and access web interface
5. Upload files and print!

---

## License

MIT License - Use freely for personal and commercial projects.
