#!/usr/bin/env python3

import io
import os
import shutil
import sys
from pathlib import Path
from typing import TextIO

THIS_FILE_ABS_PATH = Path(__file__).resolve(strict=True)

DESTINATION_FILE_PATH = Path(os.environ['SLIC3R_PP_OUTPUT_NAME'])
print(DESTINATION_FILE_PATH)

FLASHPRINT_FILE_NAME_LIMIT = 36
POST_PROCESSED_FILE_PREFIX = 'FFpp_'
FAILED_PROCESSING_PREFIX = f'{POST_PROCESSED_FILE_PREFIX}FAILED_'


def add_header(gcode: io.StringIO, input_file_path: Path) -> None:
    with io.StringIO() as input_gcode:
        gcode.seek(0)
        shutil.copyfileobj(fsrc=gcode, fdst=input_gcode)

        # add header
        gcode.seek(0)
        gcode.write(f'; This file has been post-processed by {THIS_FILE_ABS_PATH}\n')
        gcode.write(f'; Original File Location: {input_file_path}\n')
        gcode.write('\n\n')

        # copy rest of file
        gcode.write(input_gcode.getvalue())


def add_filament_specific_z_offset_to_starting_code(gcode: io.StringIO) -> None:
    # TODO: extract z offset from filament specific code and add to start code
    pass


def remove_standard_m109_commands(gcode: io.StringIO) -> None:
    """
    M109 in FF firmware is used to indicate printing mode(normal, mirror, duplicate) instead of the standard gcode command for "set temperature and wait"
    """
    pass


def disable_heating_if_extruder_unused(gcode: io.StringIO) -> None:
    # TODO: strip out heating code if one side doesn't have any extrude commands
    pass


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

            add_header(processed_gcode, input_file_path)
            add_filament_specific_z_offset_to_starting_code(processed_gcode)
            remove_standard_m109_commands(processed_gcode)
            disable_heating_if_extruder_unused(processed_gcode)

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
