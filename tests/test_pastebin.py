import pytest
from unittest.mock import patch, MagicMock
import config
from utils.pastebin import upload_file_to_pastebin

@pytest.fixture
def temp_file(tmp_path):
    """Creates a temporary file for testing."""
    file_path = tmp_path / "test_script.py"
    file_path.write_text("print('Hello Pastebin API!')")
    return str(file_path)

def test_upload_disabled(temp_file):
    """Test behavior when ENABLE_PASTEBIN is False."""
    config.ENABLE_PASTEBIN = False
    result = upload_file_to_pastebin(temp_file)
    assert result == "Pastebin feature is disabled"

def test_invalid_file_path():
    """Test behavior when the file path does not exist."""
    config.ENABLE_PASTEBIN = True
    result = upload_file_to_pastebin("nonexistent_file_123.txt")
    assert result == "Error: File not found"

@patch("utils.pastebin.requests.post")
def test_successful_upload(mock_post, temp_file):
    """Test a valid, successful Pastebin upload."""
    config.ENABLE_PASTEBIN = True
    
    # Mock successful Pastebin API response
    mock_response = MagicMock()
    mock_response.text = "https://pastebin.com/xyz123"
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    
    result = upload_file_to_pastebin(temp_file)
    
    assert result == "https://pastebin.com/xyz123"
    mock_post.assert_called_once()
