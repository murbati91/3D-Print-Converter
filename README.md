# 3D Print Converter

Convert CAD files directly to G-code and stream to your 3D printer via WiFi.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Platform](https://img.shields.io/badge/platform-ESP32--S3-green.svg)
![Python](https://img.shields.io/badge/python-3.10+-yellow.svg)

## Overview

3D Print Converter is an open-source solution that bridges the gap between CAD design and 3D printing. Upload DWG, DXF, PDF, or SVG files through a web interface, and the system automatically converts them to G-code and streams directly to your 3D printer.

### Key Features

- **Web-Based Interface** - Access via `http://3dconverter.local` from any device
- **Multiple Input Formats** - DWG, DGN, DXF, PDF, SVG, DAT
- **Multiple Output Formats** - STL, OBJ, STEP, G-code, 3MF
- **Direct Printer Control** - Stream G-code via UART with real-time progress
- **Standalone Operation** - ESP32 controller with TFT display
- **Low Cost** - ~$12 BOM for the controller hardware

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Web Browser   │────▶│  ESP32-S3       │────▶│   3D Printer    │
│   (Any Device)  │     │  Controller     │     │   (UART)        │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                                 ▼
                        ┌─────────────────┐
                        │  Python Server  │
                        │  (Conversion)   │
                        └─────────────────┘
```

## Components

| Component | Description |
|-----------|-------------|
| **Firmware** | ESP32-S3 Arduino code with web server, SD card, TFT display |
| **Server** | Python FastAPI conversion engine |
| **Portable App** | Standalone Windows application |
| **Enclosure** | 3D printable case (OpenSCAD + STL) |

## Quick Start

### 1. Hardware Setup

**Required Components:**
- ESP32-S3-WROOM-1 module
- 2.4" TFT ILI9341 or 1.3" ST7789 display
- MicroSD card slot
- 5V power supply

**Wiring:**
| Function | GPIO |
|----------|------|
| TFT CS | 5 |
| TFT DC | 2 |
| TFT RST | 4 |
| SD CS | 12 |
| Printer TX | 17 |
| Printer RX | 16 |

### 2. Flash Firmware

```bash
# Install PlatformIO
pip install platformio

# Build and upload
cd 3d-print-converter/firmware
pio run -t upload
```

### 3. Run Conversion Server

```bash
# Install dependencies
cd 3d-print-converter/software
pip install -r requirements.txt

# Start server
python server.py --host 0.0.0.0 --port 8000
```

### 4. Connect and Print

1. Connect to ESP32 WiFi AP (`3DConverter`) or configure your network
2. Open `http://3dconverter.local` in your browser
3. Upload a CAD file
4. Click Convert → Print

## Conversion Pipeline

```
Input File (DWG/PDF/DXF/SVG)
    │
    ▼
┌───────────────────────────────┐
│  Stage 1: Format Detection    │
└───────────────────────────────┘
    │
    ▼
┌───────────────────────────────┐
│  Stage 2: DXF Normalization   │
│  - ODA Converter (DWG/DGN)    │
│  - Inkscape (PDF→SVG→DXF)     │
│  - ezdxf (native DXF)         │
└───────────────────────────────┘
    │
    ▼
┌───────────────────────────────┐
│  Stage 3: 2D→3D Conversion    │
│  - Profile extrusion          │
│  - Polygon generation         │
└───────────────────────────────┘
    │
    ▼
┌───────────────────────────────┐
│  Stage 4: Mesh Processing     │
│  - Repair & validation        │
│  - Scale & center             │
└───────────────────────────────┘
    │
    ▼
┌───────────────────────────────┐
│  Stage 5: G-code Generation   │
│  - PrusaSlicer (primary)      │
│  - Built-in slicer (fallback) │
└───────────────────────────────┘
    │
    ▼
Output (G-code) → Printer
```

## API Reference

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/status` | System health and tool availability |
| POST | `/api/convert` | Synchronous conversion (streaming response) |
| POST | `/api/convert/async` | Async conversion (returns job ID) |
| GET | `/api/jobs/{id}` | Check job status |
| GET | `/api/jobs/{id}/download` | Download converted file |
| GET | `/api/formats` | List supported formats |

### Example Request

```bash
curl -X POST http://localhost:8000/api/convert \
  -F "file=@drawing.dxf" \
  -F "output_format=gcode" \
  -F "extrusion_height=10" \
  -F "layer_height=0.2"
```

## Configuration

### Conversion Settings

| Parameter | Default | Description |
|-----------|---------|-------------|
| `extrusion_height` | 10.0 mm | Height for 2D→3D extrusion |
| `scale_factor` | 1.0 | Model scaling |
| `layer_height` | 0.2 mm | Slicer layer height |
| `nozzle_diameter` | 0.4 mm | Printer nozzle size |
| `print_speed` | 50 mm/s | Print movement speed |
| `infill_percentage` | 20% | Interior fill density |
| `bed_size` | 220x220x250 | Print volume (mm) |

### External Tools

For full format support, install these optional tools:

| Tool | Purpose | Required For |
|------|---------|--------------|
| [ODA File Converter](https://www.opendesign.com/guestfiles/oda_file_converter) | DWG/DGN support | .dwg, .dgn files |
| [Inkscape](https://inkscape.org/) | PDF conversion | .pdf files |
| [FreeCAD](https://www.freecad.org/) | STEP export | .step output |
| [PrusaSlicer](https://www.prusa3d.com/prusaslicer/) | G-code generation | Better slicing quality |

## Hardware BOM

| Part | Quantity | Est. Cost |
|------|----------|-----------|
| ESP32-S3-WROOM-1 | 1 | $4.00 |
| 2.4" TFT ILI9341 | 1 | $4.00 |
| MicroSD Module | 1 | $1.00 |
| AMS1117 3.3V Regulator | 1 | $0.50 |
| USB-C Connector | 1 | $0.50 |
| PCB + Misc | 1 | $2.50 |
| **Total** | | **~$12.50** |

## Project Structure

```
3d-print-converter/
├── firmware/
│   ├── src/main.cpp          # ESP32 firmware (1300+ lines)
│   └── platformio.ini        # Build configuration
│
├── software/
│   ├── converter_engine.py   # Conversion pipeline
│   ├── server.py             # FastAPI REST server
│   └── requirements.txt      # Python dependencies
│
├── enclosure/
│   ├── *.scad                # OpenSCAD source files
│   └── stl/                  # Ready-to-print STL files
│
├── portable-app/             # Standalone Windows app
│
└── build-exe/                # Windows executable
    └── dist/3D-Print-Converter.exe
```

## Troubleshooting

### ESP32 not connecting to WiFi
- Check credentials in web config portal
- Try AP mode: connect to `3DConverter` network, access `192.168.4.1`

### Conversion fails
- Verify Python server is running on port 8000
- Check server logs for missing tools (ODA, Inkscape)
- Ensure input file is valid (try opening in original CAD software)

### Printer not responding
- Verify UART wiring (TX→RX, RX→TX)
- Check baud rate matches printer (default: 115200)
- Ensure printer firmware supports standard G-code (Marlin compatible)

## Contributing

Contributions are welcome! Please feel free to submit issues and pull requests.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [ezdxf](https://github.com/mozman/ezdxf) - DXF file handling
- [trimesh](https://github.com/mikedh/trimesh) - 3D mesh processing
- [PrusaSlicer](https://github.com/prusa3d/PrusaSlicer) - G-code generation
- [TFT_eSPI](https://github.com/Bodmer/TFT_eSPI) - ESP32 display driver

---

Made with :gear: by [murbati91](https://github.com/murbati91)
