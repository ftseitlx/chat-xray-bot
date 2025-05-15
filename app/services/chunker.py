import logging
import re
import os
from pathlib import Path
from typing import List, Dict, Any
from bs4 import BeautifulSoup
import time  # added for timing logs

from app.config import settings

logger = logging.getLogger(__name__)

# Adjust to a smaller chunk size to avoid rate limits
MAX_MESSAGES_PER_CHUNK = 25  # Reduced from previous value

def extract_message_parts(line: str) -> Dict[str, str]:
    """
    Extract author, timestamp, and content from a single line of chat.
    
    Args:
        line: A single line from the chat log
        
    Returns:
        Dictionary with timestamp, author, and content
    """
    # Initialize empty parts
    parts = {
        "timestamp": "",
        "author": "",
        "content": line  # Default to whole line if no pattern matches
    }
    
    # Try WhatsApp/standard format: [timestamp] Author: Content
    # or DD.MM.YYYY, HH:MM - Author: Content
    whatsapp_patterns = [
        r'^\[(?P<timestamp>.*?)\] (?P<author>.*?): (?P<content>.*)$',
        r'^(?P<timestamp>\d{2}\.\d{2}\.\d{4}, \d{2}:\d{2}) - (?P<author>.*?): (?P<content>.*)$',
        r'^(?P<timestamp>\d{2}/\d{2}/\d{4}, \d{2}:\d{2}) - (?P<author>.*?): (?P<content>.*)$'
    ]
    
    for pattern in whatsapp_patterns:
        match = re.match(pattern, line)
        if match:
            parts.update(match.groupdict())
            return parts
    
    # Try other common patterns
    other_patterns = [
        # Discord-like: Author [timestamp]: Content
        r'^(?P<author>.*?) \[(?P<timestamp>.*?)\]: (?P<content>.*)$',
        
        # Simple format: Author: Content
        r'^(?P<author>.*?): (?P<content>.*)$'
    ]
    
    for pattern in other_patterns:
        match = re.match(pattern, line)
        if match:
            parts.update(match.groupdict())
            return parts
    
    # No pattern matched, return the original line as content
    return parts

def extract_messages_from_html(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extract messages from a WhatsApp HTML export.
    
    Args:
        file_path: Path to the HTML chat file
        
    Returns:
        List of message dictionaries
    """
    try:
        messages = []
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # WhatsApp HTML export format
        msg_divs = soup.find_all('div', class_='message')
        if msg_divs:
            logger.info(f"Found {len(msg_divs)} WhatsApp message divs in HTML file")
            
            for msg_div in msg_divs:
                try:
                    # Extract the message info
                    header = msg_div.find('div', class_='message-header')
                    if not header:
                        continue
                    
                    # Extract author and timestamp
                    author = header.find('span', class_='message-author')
                    author = author.text.strip() if author else "Unknown"
                    
                    timestamp = header.find('span', class_='message-timestamp')
                    timestamp = timestamp.text.strip() if timestamp else ""
                    
                    # Extract message content
                    content_div = msg_div.find('div', class_='message-content')
                    content = content_div.text.strip() if content_div else ""
                    
                    # Create message dictionary
                    raw_msg = f"[{timestamp}] {author}: {content}"
                    message = {
                        "raw": raw_msg,
                        "author": author,
                        "message": content,
                        "timestamp": timestamp
                    }
                    
                    messages.append(message)
                    
                except Exception as e:
                    logger.warning(f"Error parsing message div: {e}")
        
        # --- NEW: Telegram Desktop HTML export support ---
        if not messages:
            telegram_divs = soup.find_all('div', class_=lambda c: c and 'message' in c.split())
            if telegram_divs:
                logger.info(f"Detected Telegram export with {len(telegram_divs)} message divs")
                for td in telegram_divs:
                    try:
                        author_tag = td.find('div', class_='from_name')
                        content_tag = td.find('div', class_='text')
                        date_tag = td.find('div', class_=lambda c: c and 'date' in c.split())

                        if not author_tag or not content_tag:
                            continue  # Skip system/service messages

                        author = author_tag.text.strip()
                        content = content_tag.text.strip()

                        # Telegram stores timestamp in title attribute of date div
                        timestamp = ''
                        if date_tag:
                            timestamp = date_tag.get('title', date_tag.text.strip())

                        raw_msg = f"[{timestamp}] {author}: {content}"
                        messages.append({
                            "raw": raw_msg,
                            "author": author,
                            "message": content,
                            "timestamp": timestamp
                        })
                    except Exception as te:
                        logger.warning(f"Error parsing Telegram message div: {te}")
        
        # If still no messages found, fall back to generic parsing
        if not messages:
            # Generic approach: find any message-like patterns in the HTML
            logger.info("No WhatsApp/Telegram format messages found, trying generic HTML parsing")
            
            # Remove scripts and styles to avoid parsing their content
            for script in soup(["script", "style"]):
                script.extract()
                
            # Get text content
            text_content = soup.get_text(separator="\n")
            
            # Try to extract messages using regex patterns
            lines = text_content.split("\n")
            for line in lines:
                line = line.strip()
                if line and ":" in line:  # Basic check for a message-like line
                    parts = extract_message_parts(line)
                    
                    if parts["author"]:  # Only include if we could extract an author
                        message = {
                            "raw": line,
                            "author": parts["author"],
                            "message": parts["content"],
                            "timestamp": parts["timestamp"]
                        }
                        messages.append(message)
        
        logger.info(f"Extracted {len(messages)} messages from HTML file")
        return messages
        
    except Exception as e:
        logger.error(f"Error extracting messages from HTML: {e}")
        raise

def extract_messages_from_text(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extract messages from a plain text chat file.
    
    Added extra timing / diagnostic logging because this step was
    suspected to hang in production.  The new logs clearly mark the
    start, end and message count as well as elapsed seconds.
    """

    logger.info(f"→ START extract_messages_from_text ({file_path})")
    _ts_start = time.time()

    try:
        # --- Fast line-by-line parsing first to avoid catastrophic regex backtracking ---
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        messages: List[Dict[str, Any]] = []

        lines = content.split("\n")
        for line in lines:
            line = line.strip()
            if not line or ":" not in line:
                continue
            parts = extract_message_parts(line)
            if parts["author"]:
                messages.append({
                    "raw": line,
                    "author": parts["author"],
                    "message": parts["content"],
                    "timestamp": parts["timestamp"]
                })

        # If we got a reasonable number, accept and skip heavy regex
        if len(messages) >= 50:
            logger.info(f"Fast line parser captured {len(messages)} msgs – skipping heavy regex stage")
        else:
            # Fallback to regex patterns for more precise capture (may be slower)
            logger.info("Fast line parser insufficient; falling back to regex patterns")

            # Common patterns for chat exports (can be extended)
            patterns = [
                # WhatsApp pattern: "[DATE, TIME] AUTHOR: MESSAGE"
                r'\[(?P<date>[^\]]+), (?P<time>[^\]]+)\] (?P<author>[^:]+?): (?P<message>.*?)\n',
                # WhatsApp pattern: "DATE, TIME - AUTHOR: MESSAGE"
                r'(?P<date>\d{2}[./]\d{2}[./]\d{4}), (?P<time>\d{2}:\d{2}) - (?P<author>[^:]+?): (?P<message>.*?)(?=\n\d{2}[./]\d{2}|$)',
                # Discord pattern: "AUTHOR [DATE TIME] MESSAGE"
                r'(?P<author>[^\[]+?) \[(?P<date>[^\]]+?) (?P<time>[^\]]+?)\] (?P<message>.*?)(?=\n[^\[]|$)',
            ]

            messages = []  # reset
            for pattern in patterns:
                try:
                    matches = re.finditer(pattern, content, re.MULTILINE)
                except re.error as re_err:
                    logger.warning(f"Regex compile error: {re_err} – skipping pattern")
                    continue

                for match in matches:
                    groups = match.groupdict()
                    raw_msg = match.group(0).strip()
                    messages.append({
                        "raw": raw_msg,
                        "author": groups.get("author", "Unknown"),
                        "message": groups.get("message", ""),
                        "timestamp": f"{groups.get('date', '')} {groups.get('time', '')}".strip(),
                    })

                if messages:
                    break  # Found using current pattern

            if not messages:
                logger.error("Failed to extract any messages even after regex stage.")
                raise ValueError("Could not parse chat format")

        # ensure we have messages (line parser might still be empty for rare formats)
        if not messages:
            logger.error("Failed to extract any messages from the chat file.")
            raise ValueError("Could not parse chat format")

        logger.info(
            f"← END extract_messages_from_text — {len(messages)} msgs, elapsed {time.time() - _ts_start:.1f}s"
        )
        return messages
        
    except Exception as e:
        logger.exception("extract_messages_from_text FAILED")
        raise

def extract_messages(file_path: Path) -> List[Dict[str, Any]]:
    """
    Extract messages from a chat file (text or HTML).
    
    Args:
        file_path: Path to the chat file
        
    Returns:
        List of message dictionaries
    """
    # Determine file type based on extension
    file_extension = file_path.suffix.lower()
    
    if file_extension == '.html' or file_extension == '.htm':
        logger.info(f"Processing HTML file: {file_path}")
        return extract_messages_from_html(file_path)
    else:
        logger.info(f"Processing plain text file: {file_path}")
        return extract_messages_from_text(file_path)

def count_tokens(text: str) -> int:
    """
    Very rough estimation of token count.
    
    Args:
        text: Input text
        
    Returns:
        Estimated token count
    """
    # Roughly 1.3 tokens per word for English, might be different for other languages
    return int(len(text.split()) * 1.3)

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
        # Get token estimate
        msg_token_estimate = count_tokens(message["raw"])
        
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