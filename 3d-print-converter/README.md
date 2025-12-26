# 🖨️ CAD-to-3D Print Converter

> **Open-source solution for converting DWG, DGN, DXF, PDF to 3D printable formats**

![License](https://img.shields.io/badge/license-MIT-green)
![Platform](https://img.shields.io/badge/platform-ESP32--S3-blue)
![Python](https://img.shields.io/badge/python-3.10+-blue)

## 🎯 Features

- **Multi-format support**: DWG, DGN, DXF, PDF, DAT, SVG
- **Output formats**: STL, OBJ, STEP, G-code, 3MF
- **Hardware controller**: ESP32-S3 based PCB design
- **Web interface**: Upload files via WiFi
- **Direct printing**: Stream G-code to printer
- **100% Open Source**: MIT licensed

## 📁 Project Structure

```
3d-print-converter/
├── software/              # Python conversion engine
│   ├── converter_engine.py    # Main conversion library
│   ├── server.py             # FastAPI REST server
│   └── requirements.txt      # Python dependencies
│
├── firmware/              # ESP32-S3 firmware
│   ├── src/main.cpp          # Main firmware code
│   └── platformio.ini        # PlatformIO config
│
├── hardware/              # PCB design files
│   └── 3d_print_controller.kicad_sch
│
├── docs/                  # Documentation
│   └── ARCHITECTURE.md       # System architecture
│
├── install.sh            # Installation script
└── README.md             # This file
```

## 🚀 Quick Start

### Option 1: Software Only (PC/Server)

```bash
# Clone the repository
git clone https://github.com/your-repo/3d-print-converter.git
cd 3d-print-converter

# Run installation script
chmod +x install.sh
./install.sh

# Start the server
source venv/bin/activate
python software/server.py
```

Access the API at: `http://localhost:8000`

### Option 2: Full System (ESP32 + Server)

1. **Install software** (as above)
2. **Flash ESP32 firmware**:
   ```bash
   cd firmware
   pio run -t upload
   ```
3. **Configure WiFi** via AP mode (192.168.4.1)
4. **Set companion server URL** in web interface

## 📖 API Usage

### Convert a File

```bash
# Single file conversion
curl -X POST "http://localhost:8000/api/convert" \
  -F "file=@drawing.dwg" \
  -o output.gcode

# With parameters
curl -X POST "http://localhost:8000/api/convert?output_format=stl&extrusion_height=5" \
  -F "file=@drawing.dxf" \
  -o output.stl
```

### Python Client

```python
import requests

# Convert file
with open('drawing.dwg', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/convert',
        files={'file': f},
        params={'output_format': 'gcode'}
    )

# Save result
with open('output.gcode', 'wb') as f:
    f.write(response.content)
```

## 🔧 Hardware Build

### Bill of Materials (~$12.50)

| Component | Qty | Est. Cost |
|-----------|-----|-----------|
| ESP32-S3-WROOM-1-N8R8 | 1 | $4.50 |
| 2.4" TFT ILI9341 | 1 | $3.00 |
| MicroSD Card Slot | 1 | $0.30 |
| USB-C Connector | 1 | $0.20 |
| AMS1117-3.3V | 1 | $0.10 |
| CH340C | 1 | $0.50 |
| Rotary Encoder | 1 | $0.50 |
| Misc (caps, resistors) | - | $1.00 |
| PCB (JLCPCB x5) | 5 | $2.00 |

### PCB Manufacturing

1. Open `hardware/3d_print_controller.kicad_sch` in KiCad
2. Generate Gerber files
3. Upload to JLCPCB/PCBWay
4. Select 2-layer, 1.6mm thickness

## 🛠️ Conversion Pipeline

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│ Input File  │───►│ ODA/Inkscape │───►│  FreeCAD    │───►│ PrusaSlicer  │
│ DWG/DGN/PDF │    │  → DXF       │    │  → STL      │    │  → G-code    │
└─────────────┘    └──────────────┘    └─────────────┘    └──────────────┘
```

## 📦 Dependencies

### Required (automatically installed)

- **Python 3.10+**
- **ezdxf** - DXF file handling
- **trimesh** - 3D mesh operations
- **FastAPI** - REST API server
- **numpy-stl** - STL file handling

### External Tools

| Tool | Purpose | Installation |
|------|---------|--------------|
| FreeCAD | CAD processing | `apt install freecad` |
| ODA Converter | DWG/DGN support | [Download](https://www.opendesign.com/guestfiles/oda_file_converter) |
| Inkscape | PDF/SVG conversion | `apt install inkscape` |
| PrusaSlicer | G-code generation | [Download](https://www.prusa3d.com/prusaslicer/) |
| OpenSCAD | Parametric modeling | `apt install openscad` |

## 🌐 Integration with Your Infrastructure

### With Infrastructure Control Center (ICC)

```python
# Add to ICC monitoring
from icc_client import ICCClient

icc = ICCClient('icc.bahrain-ai.com')
icc.register_service(
    name='3d-converter',
    url='http://converter-server:8000',
    health_check='/status'
)
```

### Docker Deployment

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    freecad inkscape openscad

WORKDIR /app
COPY . .
RUN pip install -r software/requirements.txt

EXPOSE 8000
CMD ["python", "software/server.py"]
```

## 🐛 Troubleshooting

### ODA Converter not found
```bash
# Check if installed
which ODAFileConverter

# If missing, download from:
# https://www.opendesign.com/guestfiles/oda_file_converter
```

### ESP32 won't flash
```bash
# Hold BOOT button while connecting USB
# Then release and run:
pio run -t upload
```

### Conversion fails
```bash
# Check tool availability
curl http://localhost:8000/api/formats

# Review logs
tail -f /var/log/3d-converter.log
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing`)
5. Open Pull Request

## 📄 License

MIT License - see [LICENSE](LICENSE) file.

## 🙏 Acknowledgments

- [ODA (Open Design Alliance)](https://www.opendesign.com/) for DWG/DGN support
- [FreeCAD](https://www.freecad.org/) for CAD processing
- [PrusaSlicer](https://www.prusa3d.com/prusaslicer/) for G-code generation
- [ESP32](https://www.espressif.com/) community

---

**Made with ❤️ by Tech Sierra Solutions**
