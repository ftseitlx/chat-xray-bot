import os
import tempfile
import pytest
from pathlib import Path

from app.services.chunker import extract_message_parts, split_chat, count_tokens
from app.config import settings


def test_extract_message_parts():
    """Test extracting author, timestamp, and content from different chat formats"""
    
    # Standard format: [timestamp] Author: Content
    line1 = "[2023-05-01 14:30:45] John: Hello, how are you?"
    result1 = extract_message_parts(line1)
    assert result1["timestamp"] == "2023-05-01 14:30:45"
    assert result1["author"] == "John"
    assert result1["content"] == "Hello, how are you?"
    
    # Telegram/WhatsApp format: DD.MM.YYYY, HH:MM - Author: Content
    line2 = "01.05.2023, 14:30 - Jane: I'm doing well, thanks!"
    result2 = extract_message_parts(line2)
    assert result2["timestamp"] == "01.05.2023, 14:30"
    assert result2["author"] == "Jane"
    assert result2["content"] == "I'm doing well, thanks!"
    
    # No recognizable format
    line3 = "This is just plain text without any structure"
    result3 = extract_message_parts(line3)
    assert result3["timestamp"] == ""
    assert result3["author"] == ""
    assert result3["content"] == "This is just plain text without any structure"


def test_count_tokens():
    """Test token counting functionality"""
    text = "Hello, this is a test message to count tokens."
    token_count = count_tokens(text)
    assert token_count > 0
    
    # Check that longer text has more tokens
    longer_text = text * 10
    assert count_tokens(longer_text) > token_count


def test_split_chat():
    """Test splitting a chat file into chunks"""
    
    # Create a temporary chat file
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as temp_file:
        # Write test chat data
        for i in range(50):  # 50 messages
            temp_file.write(f"[2023-05-01 {i:02d}:00:00] User{i % 2 + 1}: This is message {i}\n")
            # Add some multi-line content
            if i % 5 == 0:
                temp_file.write("This is a continuation of the message.\n")
                temp_file.write("And another line.\n")
                
        temp_file_path = temp_file.name
    
    try:
        # Test with default settings
        original_max_messages = settings.MAX_MESSAGES_PER_CHUNK
        original_max_tokens = settings.MAX_TOKENS_PER_CHUNK
        
        # Set smaller limits for testing
        settings.MAX_MESSAGES_PER_CHUNK = 10
        settings.MAX_TOKENS_PER_CHUNK = 500
        
        # Run the split_chat function
        chunks = split_chat(Path(temp_file_path))
        
        # Verify the result
        assert chunks is not None
        assert len(chunks) > 0
        assert len(chunks) >= 5  # Should have at least 5 chunks (50 messages / 10 per chunk)
        
        # Check structure of first chunk
        first_chunk = chunks[0]
        assert len(first_chunk) > 0
        assert "timestamp" in first_chunk[0]
        assert "author" in first_chunk[0]
        assert "content" in first_chunk[0]
        
        # Check that no chunk exceeds the limits
        for chunk in chunks:
            assert len(chunk) <= settings.MAX_MESSAGES_PER_CHUNK
            total_tokens = sum(count_tokens(msg["raw"]) for msg in chunk)
            assert total_tokens <= settings.MAX_TOKENS_PER_CHUNK
            
    finally:
        # Clean up
        os.unlink(temp_file_path)
        # Restore original settings
        settings.MAX_MESSAGES_PER_CHUNK = original_max_messages
        settings.MAX_TOKENS_PER_CHUNK = original_max_tokens 