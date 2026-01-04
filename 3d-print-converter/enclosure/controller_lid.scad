/*
 * 3D Blueprint Controller - LID
 * Salahuddin Softech Solution
 *
 * Print this file for the enclosure lid.
 * Export as STL: File > Export > Export as STL
 *
 * PRINT ORIENTATION: Print upside down (as exported)
 */

// ==========================================
// PARAMETERS - Must match main file
// ==========================================

box_length = 100;
box_width = 60;
box_height = 30;
wall_thickness = 2.5;
corner_radius = 3;
base_height = 22;
lid_height = 8;
led_diameter = 5;
led_spacing = 12;
led_count = 4;
screw_diameter = 3;
screw_head_diameter = 6;
text_depth = 0.8;
tolerance = 0.3;

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

module led_holder(diameter, depth) {
    union() {
        cylinder(d=diameter, h=depth+1, $fn=24);
        translate([0, 0, depth-1])
            cylinder(d=diameter+2, h=2, $fn=24);
    }
}

// ==========================================
// LID - Flipped for printing
// ==========================================

translate([0, 0, lid_height])
rotate([180, 0, 0])
difference() {
    union() {
        rounded_box(box_length, box_width, lid_height, corner_radius);

        translate([wall_thickness + tolerance, wall_thickness + tolerance, -3])
            rounded_box(
                box_length - 2*(wall_thickness + tolerance),
                box_width - 2*(wall_thickness + tolerance),
                3,
                corner_radius - wall_thickness
            );
    }

    // LED holes
    led_start_x = (box_length - (led_count-1) * led_spacing) / 2;
    led_y = 15;

    for (i = [0:led_count-1]) {
        translate([led_start_x + i * led_spacing, led_y, -1])
            led_holder(led_diameter, lid_height + 2);
    }

    // Reset button hole
    translate([box_length - 15, box_width - 15, -1])
        cylinder(d=6, h=lid_height + 2, $fn=24);

    // Screw holes
    lid_post_positions = [
        [wall_thickness + 3, wall_thickness + 3],
        [box_length - wall_thickness - 3, wall_thickness + 3],
        [wall_thickness + 3, box_width - wall_thickness - 3],
        [box_length - wall_thickness - 3, box_width - wall_thickness - 3]
    ];

    for (pos = lid_post_positions) {
        translate([pos[0], pos[1], -1])
            cylinder(d=screw_diameter + 0.5, h=lid_height + 5, $fn=24);
        translate([pos[0], pos[1], lid_height - 2])
            cylinder(d=screw_head_diameter, h=3, $fn=24);
    }

    // Branding text
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
