#!/usr/bin/env python3

import io
import os
import re
import shutil
import sys
from pathlib import Path
from typing import TextIO

THIS_FILE_ABS_PATH = Path(__file__).resolve(strict=True)

DESTINATION_FILE_PATH = Path(os.environ['SLIC3R_PP_OUTPUT_NAME'])

# Commented Gcode lines need to be processed too because of FF firmware parsing
GCODE_LINE_REGEX = re.compile(
    r'\A(?P<line_prefix>[;:\s]*)(?P<gcode>(\b[GMXYZFE]\d+(\.\d+)?\b)(\s+\b[GMXYZFEST]\d+(\.\d+)?\b)*\s*)(?P<comment>;.*)?',
    re.ASCII)
M109_COMMAND_REGEX = re.compile(r'\A\bM109\b\s+(?P<temperature_param>\bS\d+(\.\d+)?\b)\s+(?P<extruder_param>\bT\d+\b)',
                                re.ASCII)

FLASHPRINT_FILE_NAME_LIMIT = 36
POST_PROCESSED_FILE_PREFIX = 'FFpp_'
FAILED_PROCESSING_PREFIX = f'{POST_PROCESSED_FILE_PREFIX}FAILED_'


def add_header(gcode: io.StringIO, input_file_path: Path) -> io.StringIO:
    new_gcode = io.StringIO()

    # add header
    new_gcode.write(f'; This file has been post-processed by {THIS_FILE_ABS_PATH}\n')
    new_gcode.write(f'; Original File Location: {input_file_path}\n')
    new_gcode.write('\n\n')

    # copy rest of file
    gcode.seek(0)
    new_gcode.write(gcode.getvalue())

    return new_gcode


def add_filament_specific_z_offset_to_starting_code(gcode: io.StringIO) -> io.StringIO:
    # TODO: extract z offset from filament specific code and add to start code
    return gcode


def replace_standard_m109_commands(gcode: io.StringIO) -> io.StringIO:
    """
    The standard M109 gcode command is to set extruder temperature and and wait until it reaches it. In FF firmware,
    M109 is used to indicate printing mode(normal, mirror, duplicate). All standard M109 commands must be converted
    to a M104 and a M6 command.
    """
    new_gcode = io.StringIO()

    gcode.seek(0)
    for line in gcode:
        if valid_gcode_line_match := GCODE_LINE_REGEX.match(line):
            gcode_str_match = valid_gcode_line_match.group('gcode')
            if M109_command_match := M109_COMMAND_REGEX.match(gcode_str_match):
                new_gcode.write(
                    f'{valid_gcode_line_match.group("line_prefix")}M104 {M109_command_match.group("temperature_param")} {M109_command_match.group("extruder_param")} ; set extruder temperature\n')
                new_gcode.write(
                    f'{valid_gcode_line_match.group("line_prefix")}M6 {M109_command_match.group("extruder_param")} ; wait for extruder temperature to be reached\n')
            else:
                new_gcode.write(line)
        else:
            new_gcode.write(line)

    return new_gcode


def disable_heating_if_extruder_unused(gcode: io.StringIO) -> io.StringIO:
    # TODO: strip out heating code if one side doesn't have any extrude commands
    return gcode


def is_processed_gcode_valid(gcode: io.StringIO) -> bool:
    # TODO: Put some validation to make sure the post processing steps actually worked
    return True


def shorten_file_name(gcode_file_path: Path) -> Path:
    new_file_path_stem = gcode_file_path.stem[
                         :FLASHPRINT_FILE_NAME_LIMIT - len(gcode_file_path.stem) - len(gcode_file_path.suffix)]
    new_file_path = gcode_file_path.parent / (new_file_path_stem + gcode_file_path.suffix)
    assert (len(new_file_path.name) <= FLASHPRINT_FILE_NAME_LIMIT)
    return new_file_path


def write_gcode_to_file(gcode: TextIO, file_path: Path) -> None:
    with open(file_path, mode='wt') as output_file:
        gcode.seek(0)
        shutil.copyfileobj(fsrc=gcode, fdst=output_file)


def main(input_file_path: Path):
    with open(input_file_path, mode='rt') as unprocessed_gcode:
        with io.StringIO() as processed_gcode:
            unprocessed_gcode.seek(0)
            shutil.copyfileobj(fsrc=unprocessed_gcode, fdst=processed_gcode)

            processed_gcode = add_header(processed_gcode, input_file_path)
            processed_gcode = add_filament_specific_z_offset_to_starting_code(processed_gcode)
            processed_gcode = replace_standard_m109_commands(processed_gcode)
            processed_gcode = disable_heating_if_extruder_unused(processed_gcode)

            if is_processed_gcode_valid(processed_gcode):
                gcode_file_path = DESTINATION_FILE_PATH.parent / (
                        POST_PROCESSED_FILE_PREFIX + DESTINATION_FILE_PATH.stem + '.g')
                if len(gcode_file_path.name) > FLASHPRINT_FILE_NAME_LIMIT:
                    gcode_file_path = shorten_file_name(gcode_file_path)
                print('Post-processing completed and gcode passed validation checks!')
            else:
                gcode_file_path = DESTINATION_FILE_PATH.parent / (
                        FAILED_PROCESSING_PREFIX + DESTINATION_FILE_PATH.stem + '.g')
                print('Post-processing failed validation checks!')

            write_gcode_to_file(processed_gcode, gcode_file_path)
            print(f'File available at: {gcode_file_path}')

    input('Press Any Key to Exit...')


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(strict=True))
