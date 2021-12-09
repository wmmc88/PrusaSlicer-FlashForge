import pytest
import os
import difflib
import sys

from pathlib import Path
from importlib import reload


@pytest.mark.parametrize('test_env', ['gcode_snippets', 'soluble_cube', 'benchy_PETG', 'left_benchy', 'right_benchy', 'nozzle_switch_rod'], indirect=True)
def test_postprocess_file(test_data_path, test_env):
    import flashforge_post_process
    reload(flashforge_post_process)

    input_file_path = test_data_path / f'{test_env["test_name"]}_input.gcode'
    flashforge_post_process.main(input_file_path)

    expected_generated_output_file_path = (test_data_path / f'{test_env["test_name"]}_expected_output.g').resolve(
        strict=True)
    slicer_output_path = Path(os.environ['SLIC3R_PP_OUTPUT_NAME']).resolve()
    generated_output_file_path = (
            slicer_output_path.parent / f'{flashforge_post_process.POST_PROCESSED_FILE_PREFIX}{slicer_output_path.stem}.g').resolve(
        strict=True)
    with open(file=expected_generated_output_file_path, mode='rt') as expected_generated_output_file:
        with open(file=generated_output_file_path, mode='rt') as generated_output_file:
            diff_lines = list(difflib.unified_diff(a=expected_generated_output_file.readlines(),
                                                   b=generated_output_file.readlines()[4:],
                                                   fromfile=str(expected_generated_output_file_path),
                                                   tofile=str(generated_output_file_path)))

    sys.stdout.writelines(diff_lines)
    assert (len(diff_lines) == 0)  # expect no difference between generated output and expected output
