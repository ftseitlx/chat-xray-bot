import os
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

from app.config import settings


@pytest.fixture
def mock_message():
    """Create a mock Telegram message with document"""
    message = AsyncMock()
    message.document = MagicMock()
    message.from_user = MagicMock()
    message.from_user.id = 12345
    message.answer = AsyncMock()
    message.bot = AsyncMock()
    return message


# Use patches to avoid importing problematic modules during tests
@pytest.mark.asyncio
@patch("app.handlers.upload.split_chat")
@patch("app.handlers.upload.process_chunks")
@patch("app.handlers.upload.generate_meta_report")
@patch("app.handlers.upload.render_to_pdf")
@patch("app.handlers.upload.log_cost")
@patch("os.unlink")
@patch("os.path.exists", return_value=False)
@patch("builtins.open", MagicMock())
async def test_valid_file_upload(
    mock_exists, mock_unlink, mock_log_cost, mock_render_pdf,
    mock_generate_report, mock_process_chunks, mock_split_chat, mock_message
):
    """Test uploading a valid text file under size limit"""
    # Import here to avoid circular import during module loading
    from app.handlers.upload import handle_document
    
    # Configure mock document
    mock_message.document.mime_type = "text/plain"
    mock_message.document.file_size = 1024 * 1024  # 1 MB
    
    # Mock file download
    mock_message.bot.download = AsyncMock()
    
    # Set up mocks to return appropriate values
    mock_split_chat.return_value = [["message1", "message2"]]
    mock_process_chunks.return_value = [{"author": "User", "sentiment": "positive"}]
    mock_generate_report.return_value = "<html>Report</html>"
    mock_render_pdf.return_value = "http://example.com/report.pdf"
    
    # Call the handler
    await handle_document(mock_message)
    
    # Verify message download was called
    mock_message.bot.download.assert_called_once()
    
    # Verify proper processing chain
    mock_split_chat.assert_called_once()
    mock_process_chunks.assert_called_once()
    mock_generate_report.assert_called_once()
    mock_render_pdf.assert_called_once()
    
    # Verify user was notified
    assert mock_message.answer.call_count >= 2  # Initial and completion messages


@pytest.mark.asyncio
async def test_invalid_file_type(mock_message):
    """Test uploading a file with incorrect mime type"""
    # Import here to avoid circular import during module loading
    from app.handlers.upload import handle_document
    
    # Configure mock document with invalid mime type
    mock_message.document.mime_type = "application/pdf"
    
    # Call the handler
    await handle_document(mock_message)
    
    # Verify error message sent
    mock_message.answer.assert_called_once()
    assert "Invalid file format" in mock_message.answer.call_args[0][0]


@pytest.mark.asyncio
async def test_file_too_large(mock_message):
    """Test uploading a file that exceeds size limit"""
    # Import here to avoid circular import during module loading
    from app.handlers.upload import handle_document
    
    # Configure mock document with excessive size
    mock_message.document.mime_type = "text/plain"
    mock_message.document.file_size = 3 * 1024 * 1024  # 3 MB
    
    # Call the handler
    await handle_document(mock_message)
    
    # Verify error message sent
    mock_message.answer.assert_called_once()
    assert "File too large" in mock_message.answer.call_args[0][0] 