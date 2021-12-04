#!/usr/bin/env python3

import io
import os
import re
import shutil
import sys
from pathlib import Path
from typing import TextIO, Dict, List

THIS_FILE_ABS_PATH = Path(__file__).resolve(strict=True)

DESTINATION_FILE_PATH = Path(os.environ['SLIC3R_PP_OUTPUT_NAME'])
TRAVEL_SPEED = float(os.environ['SLIC3R_TRAVEL_SPEED']) * 60
TRAVEL_SPEED_Z = float(os.environ['SLIC3R_TRAVEL_SPEED_Z']) * 60

GCODE_LINE_REGEX = re.compile(
    r'\A(?P<line_prefix>[;:\s]*)'  # Commented Gcode lines need to be processed too because of FF firmware parsing
    r'(?P<gcode>(\b[GMT]\d+(\.\d+)?\b)(\s+\b[XYZE]-?\d*\.?\d+\b)*(\s+\b[FST]\d*\.?\d+\b)*\s*)'
    r'(?P<comment>;.*)?',
    re.ASCII)
M109_COMMAND_REGEX = re.compile(
    r'\A\bM109\b\s+'
    r'(?P<temperature_param>\bS-?\d*\.?\d+\b)\s+'
    r'(?P<extruder_param>\bT\d+\b)',
    re.ASCII)
G1_COMMAND_REGEX = re.compile(
    r'\A\bG1\b\s+'
    r'(?P<xy_params>(\b[XY]-?\d*\.?\d+\b\s*)*)'
    r'(?P<z_param>(\b[Z]-?\d*\.?\d+\b\s*)*)'
    r'(?P<e_param>(\b[E]-?\d*\.?\d+\b\s*)*)'
    r'(?P<f_param>(\b[F]\d*\.?\d+\b\s*)*)'
    r'(?P<comment>;.*)?',
    re.ASCII)
T_COMMAND_REGEX = re.compile(r'\A\bT\d+\b', re.ASCII)

FFPP_PARSED_LINE_REGEX = re.compile(
    r'\A;\s*\bFFPP-'
    r'(?P<parsed_value_name>(\w*\b))'
    r':\s*'
    r'(?P<parsed_value>\b\d*.?\d*\b)'
    r'(?P<comment>\s*;.*)?',
    re.ASCII)
FFPP_SUBSTITUTION_LINE_REGEX = re.compile(
    r'(?P<line_prefix>\A;.*)'
    r'<FFPP-(?P<is_calculated_substitution>calculated-)?'
    r'(?P<substitution_value_name>(\w*\b))>'
    r'(?P<line_suffix>.*)',
    re.ASCII)
FFPP_PARSED_VALUES: Dict[str, List] = {}

FLASHPRINT_FILE_NAME_LIMIT = 36
POST_PROCESSED_FILE_PREFIX = 'FFpp_'
FAILED_PROCESSING_PREFIX = f'{POST_PROCESSED_FILE_PREFIX}FAILED_'

PRUSASLICER_CONFIG_START_LINE_REGEX = re.compile(r'\A; prusaslicer_config = begin', re.ASCII)


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


def parse_for_ffpp_values(gcode: io.StringIO) -> io.StringIO:
    gcode.seek(0)
    for line in gcode:
        if parsing_line_match := FFPP_PARSED_LINE_REGEX.match(line):
            parsed_value_name = parsing_line_match.group('parsed_value_name')
            parsed_value = parsing_line_match.group('parsed_value')
            if parsed_value_name in FFPP_PARSED_VALUES:
                FFPP_PARSED_VALUES[parsed_value_name].append(parsed_value)
            else:
                FFPP_PARSED_VALUES[parsed_value_name] = [parsed_value]
    return gcode


def substitute_ffpp_values(gcode: io.StringIO) -> io.StringIO:
    new_gcode = io.StringIO()

    gcode.seek(0)
    current_layer_num = 0
    reached_prusaslicer_config = False
    for line in gcode:
        if PRUSASLICER_CONFIG_START_LINE_REGEX.match(line):
            reached_prusaslicer_config = True

        if not reached_prusaslicer_config and (substitution_line_match := FFPP_SUBSTITUTION_LINE_REGEX.match(line)):
            substitution_value_name = substitution_line_match.group('substitution_value_name')
            if substitution_line_match.group('is_calculated_substitution'):
                match substitution_value_name:
                    case 'total_layer_count':
                        content = len(FFPP_PARSED_VALUES['layer_z_height'])
                    case 'next_layer_height':
                        prev_layer_z = 0 if current_layer_num == 0 \
                            else float(FFPP_PARSED_VALUES['layer_z_height'][current_layer_num - 1])
                        content = f'{float(FFPP_PARSED_VALUES["layer_z_height"][current_layer_num]) - prev_layer_z:.3f}'
                        current_layer_num += 1
                    case _:
                        raise NotImplementedError(f'Calculation of {substitution_value_name} is not implemented.')
            else:
                first_val = FFPP_PARSED_VALUES[substitution_value_name][0]
                for val in FFPP_PARSED_VALUES[substitution_value_name]:
                    # If a non-calculated value is parsed several times in the file, all the values must be the same
                    if val != first_val:
                        raise RuntimeError(
                            'Every instance of FFPP-{substitution_value_name} in input file do not have equivalent values.')
                    assert (val == first_val)
                content = first_val

            new_gcode.write(
                f'{substitution_line_match.group("line_prefix")}{content}{substitution_line_match.group("line_suffix")}\n')
        else:
            new_gcode.write(line)

    return new_gcode


def replace_standard_m109_commands(gcode: io.StringIO) -> io.StringIO:
    """
    The standard M109 gcode command is to set extruder temperature and and wait until it reaches it. In FF firmware,
    M109 is used to indicate printing mode(normal, mirror, duplicate). All standard M109 commands must be converted
    to a M104 and a M6 command.
    """
    new_gcode = io.StringIO()

    gcode.seek(0)
    fix_next_G1_speed = False
    for line in gcode:
        line_written = False
        if valid_gcode_line_match := GCODE_LINE_REGEX.match(line):
            gcode_match_str = valid_gcode_line_match.group('gcode')
            if M109_command_match := M109_COMMAND_REGEX.match(gcode_match_str):
                new_gcode.write(
                    f'{valid_gcode_line_match.group("line_prefix")}M104 {M109_command_match.group("temperature_param")} {M109_command_match.group("extruder_param")} ; set extruder temperature\n')
                new_gcode.write(
                    f'{valid_gcode_line_match.group("line_prefix")}M6 {M109_command_match.group("extruder_param")} ; wait for extruder temperature to be reached\n')
                line_written = True
                fix_next_G1_speed = True
            elif fix_next_G1_speed and (G1_command_match := G1_COMMAND_REGEX.match(gcode_match_str)):
                if G1_command_match.group('f_param'):
                    fix_next_G1_speed = False  # No need to fix next speed since it already has Feed Rate parameter
                elif G1_command_match.group('xy_params') or G1_command_match.group('z_param'):
                    if G1_command_match.group('xy_params'):
                        travel_speed = TRAVEL_SPEED
                    elif G1_command_match.group('z_param'):
                        travel_speed = TRAVEL_SPEED_Z
                    else:
                        raise RuntimeError(
                            'Error in G1_COMMAND_REGEX. Expected X, Y or Z command because of regex match'
                            'groups, but could not find one.')

                    if gcode_comment := valid_gcode_line_match.group("comment"):
                        gcode_comment = f' {gcode_comment}'
                    else:
                        gcode_comment = ''

                    new_gcode.write(
                        f'{valid_gcode_line_match.group("line_prefix")}{valid_gcode_line_match.group("gcode")} F{travel_speed}{gcode_comment}\n')
                    line_written = True
                    fix_next_G1_speed = False

        if not line_written:
            new_gcode.write(line)

    return new_gcode


def remove_useless_T_commands(gcode: io.StringIO) -> io.StringIO:
    """
    PrusaSlicer puts T{extruder_number} commands to switch the active extruder. These don't do anything on FF
    firmware and just bloat the generated gcode. On FF Firmware, extruder switches are handled by M108 and those are
    added by the toolchange_gcode feature of the Creator3 PrusaSlicer printer profile.
    """
    new_gcode = io.StringIO()

    gcode.seek(0)
    for line in gcode:
        if valid_gcode_line_match := GCODE_LINE_REGEX.match(line):
            gcode_match_str = valid_gcode_line_match.group('gcode')
            if not T_COMMAND_REGEX.match(gcode_match_str):
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
    if len(new_file_path.name) > FLASHPRINT_FILE_NAME_LIMIT:
        raise RuntimeError(
            f'Failed to shorten name below {FLASHPRINT_FILE_NAME_LIMIT} bytes (FLASHPRINT_FILE_NAME_LIMIT)')

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
            processed_gcode = parse_for_ffpp_values(processed_gcode)
            processed_gcode = substitute_ffpp_values(processed_gcode)
            processed_gcode = replace_standard_m109_commands(processed_gcode)
            processed_gcode = remove_useless_T_commands(processed_gcode)
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


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve(strict=True))
    input('Press Any Key to Exit...')
