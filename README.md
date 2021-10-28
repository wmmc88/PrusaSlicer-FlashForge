ONLY WORKS ON PRUSASLCIAER 2.4+

Install python3
Import Config Bundle
edit path to script

Export config Bundle

## FF C3 GCode

### G Codes
G90: Absolute Positioning
G1 X Y Z F: Move

### M Codes
M118 X150.00 Y125.00 Z200.00 T[initial_extruder] ; todo: need to post process this
M118 X150.00 Y125.00 Z200.00 T[initial_extruder] ; todo: need to post process this
M140 S[first_layer_bed_temperature[initial_extruder]] T0; set bed temperature
M104 S{first_layer_temperature[0]} T0; set right extruder temp
M104 S{first_layer_temperature[1]} T1; set left extruder temp
M108 T{initial_extruder} ; tool change
M106 ; Extruder/Heat Break fan on
M651 S[0-255]; chassis fan on

### T Values
T0: Right Extruder for M104, Bed for M140
T1: Left Extruder for M104




; **** Start of Start GCode: FlashForge Creator 3 ****




M7 T0 ; wait for platform
M6 T0 ; wait for temp
M6 T1 ; wait for temp

G90; absolute positioning
G92 Z-0.06 ; Adjust Z-offset to 60 microns higher for PETG
G1 Z0.500 F{machine_max_feedrate_z[0] * 60}

M108 T{initial_extruder} ; tool change
G92 E0 ; reset extrusion distance 
G1 F200 E15 ; feed 15mm of feed stock 
G92 E0 ; reset extrusion distance 

; M652 ; chassis fan off 
; M109 T1/2 only if dupe or mirror
; **** End of Start GCode: FlashForge Creator 3 ****

; **** Start of End GCode: FlashForge Creator 3 ****
G92 E0 ; reset extrusion distance
G1 E-10 F1800;
G1 Y125.0 F{travel_speed * 60};
G1 Z200.0 F{machine_max_feedrate_z[0] * 60};
G92 E0 ; reset extrusion distance 

M107 ; Extruder/Heat Break fan off
;percent
;end gcode
M104 S0 T1  ; cool down left extruder
M104 S0 T0  ; cool down right extruder
M140 S0 T0 ; cool down bed
M652 ; chassis fan OFF
G91 ; relative positioning
M18 ; disable steppers
; **** End of End GCode: FlashForge Creator 3 ****"