import json
import stat

from email_ai_interface import prepare_debug_directory, write_private_json, write_private_text


def mode(path):
    return stat.S_IMODE(path.stat().st_mode)


def test_prepare_debug_directory_uses_private_mode(tmp_path):
    debug_dir = tmp_path / "debug"

    prepare_debug_directory(str(debug_dir))

    assert mode(debug_dir) == 0o700


def test_prepare_debug_directory_tightens_existing_mode(tmp_path):
    debug_dir = tmp_path / "debug"
    debug_dir.mkdir(mode=0o755)

    prepare_debug_directory(str(debug_dir))

    assert mode(debug_dir) == 0o700


def test_write_private_text_uses_private_mode(tmp_path):
    debug_file = tmp_path / "raw_email_test.eml"

    write_private_text(debug_file, "private mail")

    assert debug_file.read_text() == "private mail"
    assert mode(debug_file) == 0o600


def test_write_private_json_uses_private_mode(tmp_path):
    debug_file = tmp_path / "ai_output_test.json"
    payload = {"is_spam": "no", "confidence": 99, "reason": "test"}

    write_private_json(debug_file, payload)

    assert json.loads(debug_file.read_text()) == payload
    assert mode(debug_file) == 0o600
