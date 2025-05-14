import logging
import re
from pathlib import Path
from typing import List, Dict, Any

from app.config import settings

logger = logging.getLogger(__name__)

# Adjust to a smaller chunk size to avoid rate limits
MAX_MESSAGES_PER_CHUNK = 25  # Reduced from previous value

def extract_messages(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extract messages from a chat file.
    
    Args:
        file_path: Path to the chat file
        
    Returns:
        List of message dictionaries
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
        
        # Common patterns for chat exports (can be extended)
        patterns = [
            # WhatsApp pattern: "[DATE, TIME] AUTHOR: MESSAGE"
            r'\[(?P<date>.*?), (?P<time>.*?)\] (?P<author>.*?): (?P<message>.*?)(?=\n\[|$)',
            
            # Discord pattern: "AUTHOR [DATE TIME] MESSAGE"
            r'(?P<author>.*?) \[(?P<date>.*?) (?P<time>.*?)\] (?P<message>.*?)(?=\n\w|$)',
            
            # Generic pattern: just try to extract author and message
            r'(?P<author>[^:]+): (?P<message>.+?)(?=\n\w|$)'
        ]
        
        # Try each pattern until one works
        messages = []
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.DOTALL | re.MULTILINE)
            messages = []
            
            for match in matches:
                groups = match.groupdict()
                raw_msg = match.group(0)
                
                message = {
                    "raw": raw_msg,
                    "author": groups.get("author", "Unknown"),
                    "message": groups.get("message", ""),
                    "timestamp": f"{groups.get('date', '')} {groups.get('time', '')}".strip()
                }
                
                messages.append(message)
            
            # If we found messages, break out of the loop
            if messages:
                break
        
        # If no patterns matched, try a simple line-by-line approach
        if not messages:
            logger.warning("No predefined patterns matched. Trying simple extraction.")
            lines = content.split("\n")
            
            for line in lines:
                if ":" in line:
                    # Very simple extraction
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        author = parts[0].strip()
                        message_text = parts[1].strip()
                        
                        message = {
                            "raw": line,
                            "author": author,
                            "message": message_text,
                            "timestamp": ""
                        }
                        
                        messages.append(message)
        
        if not messages:
            logger.error("Failed to extract any messages from the chat file.")
            raise ValueError("Could not parse chat format")
            
        logger.info(f"Extracted {len(messages)} messages from the chat file.")
        return messages
        
    except Exception as e:
        logger.error(f"Error extracting messages: {e}")
        raise


def split_chat(file_path: Path) -> List[List[Dict[str, Any]]]:
    """
    Split a chat file into chunks.
    
    Args:
        file_path: Path to the chat file
        
    Returns:
        List of chunks, where each chunk is a list of message dictionaries
    """
    messages = extract_messages(file_path)
    
    # Check if we need to use a more aggressive chunking strategy
    # for very large chats (over 1000 messages)
    if len(messages) > 1000:
        logger.warning(f"Very large chat detected ({len(messages)} messages). Using aggressive chunking.")
        # For large chats, use even smaller chunks
        actual_chunk_size = min(MAX_MESSAGES_PER_CHUNK, 15)
    else:
        actual_chunk_size = MAX_MESSAGES_PER_CHUNK
    
    # Split messages into chunks
    chunks = []
    current_chunk = []
    
    # Estimate tokens to avoid LLM limits
    estimated_tokens = 0
    token_limit = 3000  # Conservative estimate for token limit per chunk
    
    for message in messages:
        # Very rough token estimation (about 1.3 tokens per word)
        msg_token_estimate = len(message["raw"].split()) * 1.3
        
        # If adding this message would exceed token limit, start a new chunk
        if (estimated_tokens + msg_token_estimate > token_limit or 
            len(current_chunk) >= actual_chunk_size) and current_chunk:
            chunks.append(current_chunk)
            current_chunk = []
            estimated_tokens = 0
        
        current_chunk.append(message)
        estimated_tokens += msg_token_estimate
    
    # Add the last chunk if it's not empty
    if current_chunk:
        chunks.append(current_chunk)
    
    logger.info(f"Split chat into {len(chunks)} chunks.")
    return chunks 