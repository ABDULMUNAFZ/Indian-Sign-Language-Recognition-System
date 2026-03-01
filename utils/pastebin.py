import os
import logging
import requests
from typing import Optional
import config

logger = logging.getLogger(__name__)

PASTEBIN_POST_URL = "https://pastebin.com/api/api_post.php"

def upload_file_to_pastebin(file_path: str) -> str:
    """
    Reads a file and uploads its content to Pastebin.
    
    Args:
        file_path (str): The path to the file to be uploaded.
        
    Returns:
        str: The Pastebin URL if successful, otherwise an error message.
    """
    if not config.ENABLE_PASTEBIN:
        return "Pastebin feature is disabled"
        
    if not os.path.exists(file_path):
        logger.error(f"File not found: {file_path}")
        return "Error: File not found"
        
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            code_content = file.read()
    except Exception as e:
        logger.error(f"Failed to read file {file_path}: {e}")
        return "Error: Could not read file"
        
    payload = {
        "api_dev_key": config.PASTEBIN_API_KEY,
        "api_option": "paste",
        "api_paste_code": code_content,
        "api_paste_private": config.PASTEBIN_PRIVATE,
        "api_paste_name": os.path.basename(file_path),
        "api_paste_expire_date": "1D"  # Defaults to 1 Day expiration
    }
    
    if config.PASTEBIN_USER_KEY:
        payload["api_user_key"] = config.PASTEBIN_USER_KEY
        
    try:
        response = requests.post(PASTEBIN_POST_URL, data=payload, timeout=10)
        response.raise_for_status()
        
        result = response.text
        if "Bad API request" in result:
            logger.error(f"Pastebin API Error: {result}")
            return f"Error: {result}"
            
        return result
        
    except requests.exceptions.Timeout:
        logger.error("Pastebin request timed out.")
        return "Error: Request timed out"
    except requests.exceptions.RequestException as e:
        logger.error(f"Pastebin request failed: {e}")
        return "Error: Upload failed"


def delete_paste(paste_key: str) -> bool:
    """
    Deletes a specific paste from Pastebin (Requires User Key).
    
    Args:
        paste_key (str): The unique identifier of the paste.
        
    Returns:
        bool: True if deleted successfully, False otherwise.
    """
    if not config.PASTEBIN_USER_KEY:
        logger.error("api_user_key is required to delete pastes.")
        return False
        
    payload = {
        "api_dev_key": config.PASTEBIN_API_KEY,
        "api_user_key": config.PASTEBIN_USER_KEY,
        "api_paste_key": paste_key,
        "api_option": "delete"
    }
    
    try:
        response = requests.post(PASTEBIN_POST_URL, data=payload, timeout=10)
        response.raise_for_status()
        
        if "Paste Removed" in response.text:
            return True
            
        logger.error(f"Failed to delete paste: {response.text}")
        return False
        
    except requests.exceptions.RequestException as e:
        logger.error(f"Pastebin delete request failed: {e}")
        return False
