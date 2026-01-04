# 3D Blueprint Controller Enclosure

**Salahuddin Softech Solution**

Professional 3D printable enclosure for ESP32 + SD Card Module assembly.

## Files

### STL Files (Ready to Print)
- `stl/controller_base.stl` - Enclosure base (461 KB)
- `stl/controller_lid.stl` - Enclosure lid with branding (1.5 MB)

### OpenSCAD Source Files
- `controller_enclosure.scad` - Main design with all modules
- `controller_base_standalone.scad` - Base only (for modification)
- `controller_lid.scad` - Lid only (for modification)

### Documentation
- `ASSEMBLY_INSTRUCTIONS.md` - Complete assembly guide with wiring diagrams

### Utilities
- `export_stl.bat` - Batch script to regenerate STL files

## Quick Print Settings

| Parameter | Value |
|-----------|-------|
| Material | PLA (Black/Dark Gray) |
| Layer Height | 0.2mm |
| Infill | 20% |
| Supports | Not required |
| Walls | 3 perimeters |
| Print Time | ~80 min total |

## Dimensions

- **Overall**: 100mm x 60mm x 30mm
- **Wall Thickness**: 2.5mm
- **Weight**: ~35g (both parts)

## Features

- 4 LED indicator holes (5mm)
- USB-C power port
- SD card access slot
- UART printer port
- Reset button access
- Ventilation slots
- Professional branding embossed

## Print Order

1. Print `controller_base.stl` upright
2. Print `controller_lid.stl` upside-down (as exported)
3. No supports needed for either part

---

*Salahuddin Softech Solution*
