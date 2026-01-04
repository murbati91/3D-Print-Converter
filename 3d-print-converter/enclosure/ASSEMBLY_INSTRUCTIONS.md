# 3D Blueprint Controller - Assembly Instructions

**Salahuddin Softech Solution**

---

## Components Required

### Electronics
| Component | Quantity | Notes |
|-----------|----------|-------|
| ESP32-WROOM-32 DevKit | 1 | 30-pin version |
| MicroSD Card Module | 1 | SPI interface |
| 5mm LEDs | 4 | Colors: Green (PWR), Blue (STS), Yellow (WiFi), Red (PRT) |
| 220Ω Resistors | 4 | For LED current limiting |
| Tactile Push Button | 1 | 6x6mm, for reset |
| Dupont Wires | ~15 | Female-to-Female |
| MicroSD Card | 1 | 32GB FAT32 formatted |

### Hardware
| Item | Quantity | Notes |
|------|----------|-------|
| M3x8mm Screws | 4 | For lid attachment |
| M2x5mm Self-tapping | 8 | For PCB mounting |
| USB-C Cable | 1 | For power |
| Printer Serial Cable | 1 | USB-to-Serial or direct |

### Printed Parts
| File | Material | Settings |
|------|----------|----------|
| controller_base.stl | PLA (Black) | 0.2mm, 20% infill |
| controller_lid.stl | PLA (Black) | 0.2mm, 20% infill |

---

## Wiring Diagram

### ESP32 Pin Connections

```
                    ESP32 DevKit (30-pin)
                    ┌─────────────────────┐
                    │      [USB-C]        │
                    │   ○              ○   │
              EN ───│ ○              ○ │─── GPIO23
         GPIO36 ───│ ○              ○ │─── GPIO22
         GPIO39 ───│ ○              ○ │─── GPIO1  (TX)
         GPIO34 ───│ ○              ○ │─── GPIO3  (RX)
         GPIO35 ───│ ○              ○ │─── GPIO21
         GPIO32 ───│ ○              ○ │─── GND
         GPIO33 ───│ ○              ○ │─── GPIO19
         GPIO25 ───│ ○              ○ │─── GPIO18
         GPIO26 ───│ ○              ○ │─── GPIO5
  SD_MOSI GPIO27 ◄──│ ●              ○ │─── GPIO17 ──► PRINTER TX
  SD_CLK  GPIO14 ◄──│ ●              ○ │─── GPIO16 ──► PRINTER RX
    SD_CS GPIO12 ◄──│ ●              ○ │─── GPIO4
  SD_MISO GPIO13 ◄──│ ●              ○ │─── GPIO0
             GND ───│ ●              ○ │─── GPIO2
             VIN ───│ ○              ○ │─── GPIO15
                    │   ○              ○   │
                    └─────────────────────┘

        ● = SD Card Module connections (LEFT SIDE)
        ► = Printer Serial connections
```

### SD Card Module Wiring

```
    SD Card Module              ESP32
    ┌────────────┐
    │  ┌─────┐   │
    │  │ SD  │   │    Wire Colors (suggested):
    │  │Card │   │
    │  │ ──► │   │    Orange ─── CS (D12)
    │  └─────┘   │    Yellow ─── MOSI (D27)
    │            │    Green ──── CLK (D14)
    │ CS ●───────│────────────► GPIO12
    │ SCK●───────│────────────► GPIO14
    │MOSI●───────│────────────► GPIO27
    │MISO●───────│────────────► GPIO13
    │ VCC●───────│────────────► 3.3V
    │ GND●───────│────────────► GND
    └────────────┘
```

### LED Wiring

```
    From ESP32 GPIO pins to LEDs in lid:

    PWR LED (Green):  3.3V ──[220Ω]──► LED+ ──► LED- ──► GND
                      (Always on when powered)

    STS LED (Blue):   GPIO2 ──[220Ω]──► LED+ ──► LED- ──► GND

    WiFi LED (Yellow): GPIO15 ──[220Ω]──► LED+ ──► LED- ──► GND

    PRT LED (Red):    GPIO4 ──[220Ω]──► LED+ ──► LED- ──► GND
```

### Printer Connection

```
    ESP32                      3D Printer (Creality K1C)
    ┌───────┐                  ┌────────────┐
    │GPIO17 │────► TX ─────────│ RX (Serial)│
    │GPIO16 │◄──── RX ─────────│ TX (Serial)│
    │  GND  │──────────────────│    GND     │
    └───────┘                  └────────────┘

    Baud Rate: 115200
    Settings: 8N1 (8 data bits, no parity, 1 stop bit)
```

---

## Assembly Steps

### Step 1: Print Enclosure (60-90 minutes)

1. **Base**: Load `controller_base.stl` in slicer
   - Layer height: 0.2mm
   - Infill: 20%
   - No supports needed
   - Print time: ~45 minutes

2. **Lid**: Load `controller_lid.stl` in slicer
   - Print upside-down (as oriented in STL)
   - Layer height: 0.2mm
   - Infill: 20%
   - No supports needed
   - Print time: ~35 minutes

### Step 2: Prepare Electronics (10 minutes)

1. **Format SD Card**
   - Insert SD card into computer
   - Format as FAT32
   - Eject safely

2. **Flash ESP32**
   - Connect ESP32 via USB
   - Upload firmware using PlatformIO
   - Verify serial output shows "SD: false" (not connected yet)

### Step 3: Mount ESP32 (5 minutes)

```
    Enclosure Base (top view)
    ┌────────────────────────────────────────────────────────────────┐
    │                                                                │
    │     ┌──────────────────────────────┐                          │
    │     │         ESP32                │    ┌──────────────────┐  │
    │     │     ┌──────────────┐         │    │   SD Card        │  │
    │     │     │              │         │    │   Module         │  │
    │     │     │    USB-C     │         │    │   ┌────┐        │  │
    │     │     │              │         │    │   │ SD │        │  │
    │     │     └──────────────┘         │    │   └────┘        │  │
    │     │    (faces front port)        │    │                  │  │
    │     └──────────────────────────────┘    └──────────────────┘  │
    │           ↑                                    ↑              │
    │      Standoffs                            Standoffs           │
    │                                                                │
    │    [USB-C PORT]                              [SD SLOT]        │
    └────────────────────────────────────────────────────────────────┘
                        [PRINTER PORT]
```

1. Place ESP32 on mounting standoffs
2. USB-C port should face the front opening
3. Use M2 self-tapping screws (optional - friction fit works)

### Step 4: Mount SD Card Module (5 minutes)

1. Place SD card module on right-side standoffs
2. Card slot should align with side opening
3. Secure with M2 screws (optional)

### Step 5: Wire SD Card Module (10 minutes)

Connect using Dupont wires:

| SD Module | ESP32 | Wire Color |
|-----------|-------|------------|
| CS | GPIO12 (D12) | Orange |
| MOSI | GPIO27 (D27) | Yellow |
| MISO | GPIO13 (D13) | Green |
| SCK | GPIO14 (D14) | Blue |
| VCC | 3.3V | Red |
| GND | GND | Black |

**IMPORTANT**: Use LEFT side of ESP32 (HSPI pins)!

### Step 6: Wire LEDs (15 minutes)

1. Solder 220Ω resistor to each LED's positive (longer) leg
2. Thread LED leads through lid holes from inside
3. Connect wires:

| LED | Function | ESP32 Pin | Notes |
|-----|----------|-----------|-------|
| Green | Power | 3.3V | Direct (always on) |
| Blue | Status | GPIO2 | With resistor |
| Yellow | WiFi | GPIO15 | With resistor |
| Red | Printer | GPIO4 | With resistor |

All LED negative legs connect to GND.

### Step 7: Install Reset Button (5 minutes)

1. Insert tactile button into lid hole
2. Connect one leg to ESP32 EN pin
3. Connect opposite leg to GND

### Step 8: Final Assembly (5 minutes)

1. Insert formatted SD card into module
2. Carefully place wired lid onto base
3. Ensure no wires are pinched
4. Secure with 4x M3 screws in corners

### Step 9: Test (5 minutes)

1. Connect USB-C power
2. Verify LEDs:
   - Green (PWR): ON immediately
   - Yellow (WiFi): Flashing during connection
   - Blue (STS): Activity indicator

3. Connect to http://3dconverter.local or http://blueprint.local
4. Check status shows `{"sd": true}`

---

## Troubleshooting

### SD Card Not Detected
- Verify wiring (CS=D12, MOSI=D27, MISO=D13, CLK=D14)
- Ensure SD card is FAT32 formatted
- Check SD card is fully inserted (click sound)
- Press RST button to reinitialize

### WiFi Not Connecting
- Check if hotspot "Blueprint-Setup" appears
- Connect and configure at 192.168.4.1
- Ensure 2.4GHz network (not 5GHz)

### Printer Not Responding
- Verify TX/RX connections (GPIO16/17)
- Check baud rate is 115200
- Ensure printer is powered on

### LEDs Not Working
- Check resistor values (220Ω)
- Verify LED polarity (longer leg = positive)
- Test GPIO pins with multimeter

---

## Final Checklist

- [ ] Base printed and cleaned
- [ ] Lid printed and cleaned
- [ ] ESP32 mounted and secured
- [ ] SD card module mounted
- [ ] All wiring connected correctly
- [ ] LEDs installed in lid
- [ ] Reset button installed
- [ ] SD card inserted (FAT32)
- [ ] Lid secured with screws
- [ ] USB-C power connected
- [ ] Status page shows SD: true
- [ ] WiFi connected
- [ ] Test file conversion works

---

## Support

**Email**: support@salahuddinss.com
**Web**: www.salahuddinss.com

---

*Salahuddin Softech Solution - "From Blueprint to Model in Minutes"*
