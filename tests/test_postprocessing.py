import pytest
import os
import difflib
import sys

from pathlib import Path


def test_postprocess_gcode_snippets(test_data_path):
    from flashforge_post_process import main, POST_PROCESSED_FILE_PREFIX
    input_file_path = test_data_path / 'test_input.gcode'
    main(input_file_path)

    expected_generated_output_file_path = (test_data_path / 'test_expected_output.g').resolve(strict=True)
    slicer_output_path = Path(os.environ['SLIC3R_PP_OUTPUT_NAME']).resolve()
    generated_output_file_path = (
            slicer_output_path.parent / f'{POST_PROCESSED_FILE_PREFIX}{slicer_output_path.stem}{slicer_output_path.suffix}').resolve(
        strict=True)
    with open(file=expected_generated_output_file_path, mode='rt') as expected_generated_output_file:
        with open(file=generated_output_file_path, mode='rt') as generated_output_file:
            diff_lines = list(difflib.unified_diff(a=expected_generated_output_file.readlines(),
                                                   b=generated_output_file.readlines()[4:],
                                                   fromfile=str(expected_generated_output_file_path),
                                                   tofile=str(generated_output_file_path)))

    sys.stdout.writelines(diff_lines)
    assert (len(diff_lines) == 0)  # expect no difference between generated output and expected output
