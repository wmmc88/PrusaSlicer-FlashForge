G1 Z123 F1000

G1 X234.23 Y1234.53 F2400
G1 Z456.789

G1 X12.23 Y125.65 Z123.4 F2345

G1 X234.23 Y1234.53 F2400
G1 Z456.789 ; This is a comment

G1 X234.23 Y1234.53 F2400
G1 Z456.789; This is a comment

;G1 Z234.2 F1800

 ;G1 Z234.2 F1800

; G1 Z234.2 F1800

;G1 Z234.2 F1800 ; This is a comment

 ;G1 Z234.2 F1800; This is a comment

; G1 Z234.2 F1800; This is a comment

M108 T1

M108 T0
G1 X123 Y234; comment comment

M108 T0
G1 X123 Y2.34 F3240

M108 T0
G1 Z7.1 F420 ; restore layer Z

M108 T0
G1 X-18.196 Y-.437 ; move to first skirt point

M108 T0
G1 X-18.196 Y1.626  F7800.0 ; move to first skirt point

M108 T0
G1 X-18.196 Y-.437  F7800.0 ; move to first skirt point

M108 T0
G1 X4.364 Y17.76  F7800.0 ; move to first skirt point
