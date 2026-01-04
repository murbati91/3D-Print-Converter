/*
 * 3D Blueprint Controller Enclosure
 * Salahuddin Softech Solution
 *
 * Housing for ESP32 + SD Card Module
 * Designed for FDM 3D printing (PLA/PETG)
 *
 * Print Settings:
 * - Layer Height: 0.2mm
 * - Infill: 20%
 * - Supports: Not required
 * - Walls: 3 perimeters
 */

// ==========================================
// PARAMETERS - Adjust as needed
// ==========================================

// Overall dimensions (mm)
box_length = 100;      // X dimension
box_width = 60;        // Y dimension
box_height = 30;       // Z dimension (base + lid)
wall_thickness = 2.5;
corner_radius = 3;

// Base/Lid split
base_height = 22;
lid_height = 8;

// ESP32 dimensions (ESP32-WROOM-32 DevKit)
esp32_length = 51;
esp32_width = 28;
esp32_standoff_height = 5;
esp32_hole_diameter = 2.5;

// SD Card module dimensions
sd_module_length = 45;
sd_module_width = 24;
sd_module_standoff_height = 5;

// LED hole dimensions
led_diameter = 5;  // 5mm LEDs
led_spacing = 12;
led_count = 4;

// Port dimensions
usb_c_width = 9;
usb_c_height = 3.5;
sd_slot_width = 15;
sd_slot_height = 3;
uart_header_width = 12;
uart_header_height = 8;

// Screw hole dimensions
screw_diameter = 3;
screw_head_diameter = 6;
screw_standoff_height = 3;

// Text emboss depth
text_depth = 0.8;

// Tolerance for fit
tolerance = 0.3;

// ==========================================
// MODULES
// ==========================================

// Rounded box module
module rounded_box(length, width, height, radius) {
    hull() {
        translate([radius, radius, 0])
            cylinder(r=radius, h=height, $fn=32);
        translate([length-radius, radius, 0])
            cylinder(r=radius, h=height, $fn=32);
        translate([radius, width-radius, 0])
            cylinder(r=radius, h=height, $fn=32);
        translate([length-radius, width-radius, 0])
            cylinder(r=radius, h=height, $fn=32);
    }
}

// Screw standoff
module screw_standoff(outer_d, inner_d, height) {
    difference() {
        cylinder(d=outer_d, h=height, $fn=24);
        cylinder(d=inner_d, h=height+1, $fn=24);
    }
}

// LED holder
module led_holder(diameter, depth) {
    union() {
        // Main LED hole
        cylinder(d=diameter, h=depth+1, $fn=24);
        // Flange for LED retention
        translate([0, 0, depth-1])
            cylinder(d=diameter+2, h=2, $fn=24);
    }
}

// ==========================================
// BASE ENCLOSURE
// ==========================================

module enclosure_base() {
    difference() {
        // Outer shell
        rounded_box(box_length, box_width, base_height, corner_radius);

        // Inner cavity
        translate([wall_thickness, wall_thickness, wall_thickness])
            rounded_box(
                box_length - 2*wall_thickness,
                box_width - 2*wall_thickness,
                base_height,
                corner_radius - wall_thickness/2
            );

        // USB-C port (front center)
        translate([box_length/2 - usb_c_width/2, -1, wall_thickness + 3])
            cube([usb_c_width, wall_thickness+2, usb_c_height]);

        // UART printer port (back)
        translate([box_length/2 - uart_header_width/2, box_width - wall_thickness - 1, wall_thickness + 3])
            cube([uart_header_width, wall_thickness+2, uart_header_height]);

        // SD card slot (right side)
        translate([box_length - wall_thickness - 1, box_width/2 - sd_slot_width/2, wall_thickness + esp32_standoff_height + 5])
            cube([wall_thickness+2, sd_slot_width, sd_slot_height]);

        // Ventilation slots (bottom)
        for (i = [0:4]) {
            translate([15 + i*15, wall_thickness/2, -1])
                cube([8, box_width - wall_thickness, wall_thickness+2]);
        }
    }

    // ESP32 mounting standoffs (4 corners)
    esp32_x = 10;
    esp32_y = (box_width - esp32_width) / 2;

    // Standoff positions for ESP32
    standoff_positions = [
        [esp32_x + 2, esp32_y + 2],
        [esp32_x + esp32_length - 2, esp32_y + 2],
        [esp32_x + 2, esp32_y + esp32_width - 2],
        [esp32_x + esp32_length - 2, esp32_y + esp32_width - 2]
    ];

    for (pos = standoff_positions) {
        translate([pos[0], pos[1], wall_thickness])
            screw_standoff(5, esp32_hole_diameter, esp32_standoff_height);
    }

    // SD module mounting standoffs
    sd_x = 60;
    sd_y = (box_width - sd_module_width) / 2;

    sd_standoff_positions = [
        [sd_x + 3, sd_y + 3],
        [sd_x + sd_module_length - 3, sd_y + 3],
        [sd_x + 3, sd_y + sd_module_width - 3],
        [sd_x + sd_module_length - 3, sd_y + sd_module_width - 3]
    ];

    for (pos = sd_standoff_positions) {
        translate([pos[0], pos[1], wall_thickness])
            screw_standoff(5, 2, sd_module_standoff_height);
    }

    // Lid mounting posts (4 corners)
    lid_post_positions = [
        [wall_thickness + 3, wall_thickness + 3],
        [box_length - wall_thickness - 3, wall_thickness + 3],
        [wall_thickness + 3, box_width - wall_thickness - 3],
        [box_length - wall_thickness - 3, box_width - wall_thickness - 3]
    ];

    for (pos = lid_post_positions) {
        translate([pos[0], pos[1], base_height - 5])
            screw_standoff(screw_head_diameter, screw_diameter, 5);
    }
}

// ==========================================
// LID
// ==========================================

module enclosure_lid() {
    difference() {
        union() {
            // Main lid body
            rounded_box(box_length, box_width, lid_height, corner_radius);

            // Inner lip for secure fit
            translate([wall_thickness + tolerance, wall_thickness + tolerance, -3])
                rounded_box(
                    box_length - 2*(wall_thickness + tolerance),
                    box_width - 2*(wall_thickness + tolerance),
                    3,
                    corner_radius - wall_thickness
                );
        }

        // LED holes (4 LEDs in a row)
        led_start_x = (box_length - (led_count-1) * led_spacing) / 2;
        led_y = 15;

        for (i = [0:led_count-1]) {
            translate([led_start_x + i * led_spacing, led_y, -1])
                led_holder(led_diameter, lid_height + 2);
        }

        // Reset button hole
        translate([box_length - 15, box_width - 15, -1])
            cylinder(d=6, h=lid_height + 2, $fn=24);

        // Screw holes for lid attachment
        lid_post_positions = [
            [wall_thickness + 3, wall_thickness + 3],
            [box_length - wall_thickness - 3, wall_thickness + 3],
            [wall_thickness + 3, box_width - wall_thickness - 3],
            [box_length - wall_thickness - 3, box_width - wall_thickness - 3]
        ];

        for (pos = lid_post_positions) {
            translate([pos[0], pos[1], -1])
                cylinder(d=screw_diameter + 0.5, h=lid_height + 5, $fn=24);
            // Countersink for screw head
            translate([pos[0], pos[1], lid_height - 2])
                cylinder(d=screw_head_diameter, h=3, $fn=24);
        }

        // Branding text emboss (top surface)
        translate([box_length/2, box_width/2 + 8, lid_height - text_depth])
            linear_extrude(text_depth + 1)
                text("3D BLUEPRINT CONTROLLER",
                     size=4,
                     font="Arial:style=Bold",
                     halign="center",
                     valign="center");

        translate([box_length/2, box_width/2 - 2, lid_height - text_depth])
            linear_extrude(text_depth + 1)
                text("Salahuddin Softech Solution",
                     size=3,
                     font="Arial",
                     halign="center",
                     valign="center");

        // LED labels
        led_labels = ["PWR", "STS", "WiFi", "PRT"];
        for (i = [0:led_count-1]) {
            translate([led_start_x + i * led_spacing, led_y + 8, lid_height - text_depth])
                linear_extrude(text_depth + 1)
                    text(led_labels[i],
                         size=2.5,
                         font="Arial:style=Bold",
                         halign="center",
                         valign="center");
        }

        // Reset label
        translate([box_length - 15, box_width - 22, lid_height - text_depth])
            linear_extrude(text_depth + 1)
                text("RST",
                     size=2.5,
                     font="Arial:style=Bold",
                     halign="center",
                     valign="center");
    }
}

// ==========================================
// PORT LABELS (for base)
// ==========================================

module port_labels() {
    // USB-C label
    translate([box_length/2, -0.5, base_height - 5])
        rotate([90, 0, 0])
            linear_extrude(1)
                text("USB-C", size=3, font="Arial:style=Bold", halign="center");

    // Printer port label
    translate([box_length/2, box_width + 0.5, base_height - 5])
        rotate([90, 0, 180])
            linear_extrude(1)
                text("PRINTER", size=3, font="Arial:style=Bold", halign="center");

    // SD slot label
    translate([box_length + 0.5, box_width/2, base_height - 5])
        rotate([90, 0, 90])
            linear_extrude(1)
                text("SD", size=3, font="Arial:style=Bold", halign="center");
}

// ==========================================
// RENDER OPTIONS
// ==========================================

// Uncomment one of these to render:

// Option 1: Base only (for printing)
// enclosure_base();

// Option 2: Lid only (for printing)
// translate([0, 0, lid_height]) rotate([180, 0, 0]) enclosure_lid();

// Option 3: Assembly view (for visualization)
color("DarkSlateGray") enclosure_base();
color("DarkSlateGray", 0.7) translate([0, 0, base_height]) enclosure_lid();

// Option 4: Exploded view
// color("DarkSlateGray") enclosure_base();
// color("DarkSlateGray", 0.7) translate([0, 0, base_height + 20]) enclosure_lid();

// ==========================================
// EXPORT INSTRUCTIONS
// ==========================================

/*
 * TO EXPORT STL FILES:
 *
 * 1. For BASE:
 *    - Uncomment "enclosure_base();" line above
 *    - Comment out other render options
 *    - File > Export > Export as STL
 *    - Save as "controller_base.stl"
 *
 * 2. For LID:
 *    - Uncomment the lid line with rotate
 *    - Comment out other render options
 *    - File > Export > Export as STL
 *    - Save as "controller_lid.stl"
 *
 * PRINT SETTINGS:
 * - Material: PLA (black or dark gray recommended)
 * - Layer Height: 0.2mm
 * - Infill: 20%
 * - Supports: None needed
 * - Bed Adhesion: Brim recommended for lid
 * - Orientation: Print base upright, lid upside down
 *
 * ASSEMBLY:
 * 1. Mount ESP32 on standoffs in base
 * 2. Mount SD card module on standoffs
 * 3. Connect wiring (see wiring diagram)
 * 4. Insert 5mm LEDs into lid holes
 * 5. Attach lid with M3 screws (4x)
 */
