/*
 * 3D Blueprint Controller - BASE (Standalone)
 * Salahuddin Softech Solution
 *
 * Print this file for the enclosure base.
 * Export as STL: File > Export > Export as STL
 */

// ==========================================
// PARAMETERS
// ==========================================

box_length = 100;
box_width = 60;
box_height = 30;
wall_thickness = 2.5;
corner_radius = 3;
base_height = 22;

esp32_length = 51;
esp32_width = 28;
esp32_standoff_height = 5;
esp32_hole_diameter = 2.5;

sd_module_length = 45;
sd_module_width = 24;
sd_module_standoff_height = 5;

usb_c_width = 9;
usb_c_height = 3.5;
sd_slot_width = 15;
sd_slot_height = 3;
uart_header_width = 12;
uart_header_height = 8;

screw_diameter = 3;
screw_head_diameter = 6;

// ==========================================
// MODULES
// ==========================================

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

module screw_standoff(outer_d, inner_d, height) {
    difference() {
        cylinder(d=outer_d, h=height, $fn=24);
        cylinder(d=inner_d, h=height+1, $fn=24);
    }
}

// ==========================================
// BASE ENCLOSURE
// ==========================================

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

// ESP32 mounting standoffs
esp32_x = 10;
esp32_y = (box_width - esp32_width) / 2;

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

// Lid mounting posts
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
