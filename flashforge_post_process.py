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
LINE_REGEX = re.compile(r'(?P<gcode>[;:\s]*(\s*\b[GMXYZFE]\d+(\.\d+)?\b)*)(?P<comment>\s*;.*)*', re.ASCII)
M109_REGEX = re.compile(r'[;:\s]*\bM109\b', re.ASCII)

FLASHPRINT_FILE_NAME_LIMIT = 36
POST_PROCESSED_FILE_PREFIX = 'FFpp_'
FAILED_PROCESSING_PREFIX = f'{POST_PROCESSED_FILE_PREFIX}FAILED_'

END_OF_START_CODE_DELIMITER = '; **** End of Start GCode: FlashForge Creator 3 ****'


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


def remove_standard_m109_commands(gcode: io.StringIO) -> io.StringIO:
    """
    M109 in FF firmware is used to indicate printing mode(normal, mirror, duplicate) instead of the standard gcode command for "set temperature and wait"
    """
    new_gcode = io.StringIO()

    gcode.seek(0)
    after_start_code = False
    for line in gcode:
        if after_start_code:
            valid_gcode_match = LINE_REGEX.match(line)
            gcode_str_match = valid_gcode_match.group('gcode')
            if not M109_REGEX.match(gcode_str_match):
                new_gcode.write(line)
        else:
            new_gcode.write(line)
            if END_OF_START_CODE_DELIMITER in line:
                after_start_code = True

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
            processed_gcode = remove_standard_m109_commands(processed_gcode)
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
