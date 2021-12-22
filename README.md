ONLY WORKS ON PRUSASLCIAER 2.4+

Install python3
Import Config Bundle
edit path to script

Export config Bundle

## FlashForge Creator 3 GCode

### G Codes
G1 X Y Z F ; Move
G90 ; absolute positioning
G91 ; relative positioning
G92 E0 ; reset extrusion distance
G162 Z F1800 ; Go to max Z position

### M Codes
M6 T0 ; wait for extruder temp
M7 T0 ; wait for platform temp
M18 ; disable steppers
M104 S{first_layer_temperature[0]} T0 ; set right extruder temp
M104 S{first_layer_temperature[1]} T1 ; set left extruder temp
M106 ; Extruder/Heat Break fan on
M107 ; Extruder/Heat Break fan off
M108 T{initial_extruder} ; tool change
M118 X150.00 Y125.00 Z200.00 T[initial_extruder] ; todo: need to post process this
M140 S[first_layer_bed_temperature[initial_extruder]] T0; set bed temperature
M651 S[0-255]; chassis fan on
M652 ; chassis fan off
### T Values
Extruder Commands:
  * T0: Right Extruder
  * T1: Left Extruder

Bed Commands
  * T0: Bed

## FlashForge Creator 3 Reference
Here's some useful information that's not clear when operating the Creator 3:

* Z Calibration Expert Mode:
  * ZCAL: Extra distance from right nozzle to bed zero. 
    * Positive values mean the right nozzle is lower than the mechanical "zero" point and is too close to the bed.
    * Increasing to be more positive adds more gap between right nozzle and bed
  * ZDIFF: Offset of left nozzle relative to right nozzle.
    * Positive values mean the left nozzle is lower than right nozzle.
    * Increasing to be more positive adds more gap between the left nozzle and the bed when that nozzle is active.
