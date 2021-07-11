#!/usr/bin/env python3

import os
import re
import sys
from pathlib import Path
from shutil import copyfile

THIS_FILE_ABS_PATH = Path(__file__).resolve(strict=True)

Z_FEEDRATE = float(os.environ['SLIC3R_MACHINE_MAX_FEEDRATE_Z'].split(',')[0]) * 60
XY_TRAVEL_SPEED = float(os.environ['SLIC3R_TRAVEL_SPEED']) * 60

LINE_REGEX = re.compile(r'(?P<gcode>[;:\s]*(\s*\b[GMXYZFE]\d+(\.\d+)?\b)*)(?P<comment>\s*;.*)*', re.ASCII)
G1_REGEX = re.compile(r'[;:\s]*\bG1\b', re.ASCII)
F_REGEX = re.compile(r'\s*F\d+(\.\d+)?\b', re.ASCII)
Z_REGEX = re.compile(r'\s*Z\d+(\.\d+)?\b', re.ASCII)


def fix_max_z_speed(input_gcode_file_path: Path) -> Path:
    output_gcode_file_path = input_gcode_file_path.parent / (
            input_gcode_file_path.stem + "_fix-max-z-speed" + input_gcode_file_path.suffix)
    with open(output_gcode_file_path, mode='wt') as gcode_output:
        gcode_output.write(
            f'This file has been post-processed by {THIS_FILE_ABS_PATH}\n' + f'Original File Location: {input_gcode_file_path}\n\n\n')

        with open(input_gcode_file_path, mode='rt') as gcode_input:

            last_travel_speed = " F" + str(XY_TRAVEL_SPEED)
            for line in gcode_input:
                output_line_modified = False

                valid_gcode_match = LINE_REGEX.match(line)
                gcode = valid_gcode_match.group('gcode')
                if G1_match := G1_REGEX.match(gcode):
                    if F_match := F_REGEX.search(gcode):
                        last_travel_speed = F_match.group(0)

                    if Z_match := Z_REGEX.search(gcode):
                        output_line_modified = True

                        gcode_comment = valid_gcode_match.group('comment')
                        if gcode_comment is None:
                            gcode_comment = ''

                        z_line = G1_match.group(0) + Z_match.group(0) + f' F{Z_FEEDRATE}{gcode_comment}\n'
                        gcode_output.write(z_line)

                        reset_F_line = G1_match.group(
                            0) + last_travel_speed + ' ; reset to previous feedrate before z-move\n'
                        gcode_output.write(reset_F_line)

                        # TODO: handle if there's X/Y/E command too

                if not output_line_modified:
                    gcode_output.write(line)

    return output_gcode_file_path

# todo strip out heating code if one side doesn't have any extrude commands

def validate_and_convert(input_gcode_file_path: Path):
    copyfile(src=input_gcode_file_path, dst=input_gcode_file_path.with_suffix('.g'))
    # TODO: Shorten name when longer than allowed by flashprint for "send gcode to printer"(35 bytes?)


def main(input_gcode_file_path: Path):
    output_gcode_file_path = fix_max_z_speed(input_gcode_file_path)
    validate_and_convert(output_gcode_file_path)


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(strict=True))
