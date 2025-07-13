"""Visual Plugin for NVIDIA G-Assist Platform.

This plugin provides functionality to interact with the screen trough qwen2-vl-7b-instruct,
specifically for ask things about the screen. It implements
a Windows pipe-based communication protocol for receiving commands and
sending responses.

Configuration:
    Required configuration in config.json:
    {
        "REPLICATE_KEY": "your_api_key_here"
    }

    Config location: %PROGRAMDATA%\\NVIDIA Corporation\\nvtopps\\rise\\plugins\\visual\\config.json
    Log location: %USERPROFILE%\\visual.log

Commands Supported:
    - initialize: Initialize the plugin
    - describe_screen: Describe users screen
    - shutdown: Gracefully shutdown the plugin

Dependencies:
    - pyautogui: For taking screenshots
    - requests: For making HTTP requests to Replicate API
    - ctypes: For Windows pipe communication
"""
import json
import logging
import os
import sys
from typing import Optional, Dict, Any
import requests
from ctypes import byref, windll, wintypes
import pyautogui
import requests
import base64
import io

# Type definitions
Response = Dict[str, Any]
"""Type alias for response dictionary containing 'success' and optional 'message'."""

# Constants
STD_INPUT_HANDLE = -10
"""Windows standard input handle constant."""

STD_OUTPUT_HANDLE = -11
"""Windows standard output handle constant."""

BUFFER_SIZE = 4096
"""Size of buffer for reading from pipe in bytes."""

CONFIG_FILE = os.path.join(
    os.environ.get("PROGRAMDATA", "."),
    r'NVIDIA Corporation\nvtopps\rise\plugins\visual',
    'config.json'
)

#CONFIG_FILE = "D:/visual/config.json"
"""Path to configuration file containing Replicate  Api credentials."""

LOG_FILE = os.path.join(os.environ.get("USERPROFILE", "."), 'visual.log')
"""Path to log file for plugin operations."""

# Replicate ai
REPLICATE_ENDPOINT = "https://api.replicate.com/v1/predictions"
"""Replicate api endpoint"""

REPLICATE_AI_PATH = "bf57361c75677fc33d480d0c5f02926e621b2caa2000347cb74aeae9d2ca07ee"
"""Replicate Ai for asking things about the screen"""

config: Dict[str, str] = {}
"""Loaded configuration containing Replicate API credentials."""

def setup_logging() -> None:
    """Configure logging with appropriate format and level.
    
    Sets up the logging configuration with file output, INFO level, and timestamp format.
    The log file location is determined by LOG_FILE constant.
    
    Log Format:
        %(asctime)s - %(levelname)s - %(message)s
        Example: 2024-03-14 12:34:56,789 - INFO - Plugin initialized
    """
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )

def load_config() -> Dict[str, str]:
    """Load configuration from config.json file.
    
    Expected config format:
    {
        "REPLICATE_KEY": "your_api_key_here"
    }
    
    Returns:
        Dict[str, str]: Configuration dictionary containing replicate API credentials.
                       Returns empty dict if file doesn't exist or on error.
    
    Note:
        Errors during file reading or JSON parsing are logged but not raised.
    """
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as file:
                return json.load(file)
    except Exception as e:
        logging.error(f"Error loading config: {e}")
    return {}

def save_config(config_data: Dict[str, str]) -> None:
    """Save configuration to config.json file.
    
    Args:
        config_data (Dict[str, str]): Configuration dictionary to save.
    """
    try:
        with open(CONFIG_FILE, "w") as file:
            json.dump(config_data, file, indent=4)
    except Exception as e:
        logging.error(f"Error saving config: {e}")

def generate_response(success: bool, message: Optional[str] = None) -> Response:
    """Generate a standardized response dictionary.
    
    Args:
        success (bool): Whether the operation was successful.
        message (Optional[str]): Optional message to include in response.
    
    Returns:
        Response: Dictionary containing success status and optional message.
    """
    response = {'success': success}
    if message:
        response['message'] = message
    return response

def describe_screen(params: Dict[str, str]) -> Response:
    """Describe the users screen.
    
    Args:
        params (Dict[str, str]): Dictionary containing 'prompt' key with the screen question.
    
    Returns:
        Response: Dictionary containing:
            - success: True if check was successful
            - message: Stream details if user is live, "OFFLINE" if not,
                      or error message if check failed.

    """
    global config
    prompt = params.get("prompt")
    
    if not prompt:
        return generate_response(False, "Missing required parameter: prompt")
    
    try:
        if(config.get('REPLICATE_KEY') is None):
            config = load_config()
        screenshot = pyautogui.screenshot()
        buffer = io.BytesIO()
        screenshot.save(buffer, format="PNG")
        buffer.seek(0)
        img_bytes = buffer.read()
        img_base64 = base64.b64encode(img_bytes).decode("utf-8")
        file_input = f"data:image/png;base64,{img_base64}"
        input = {
            "media": file_input,
            "prompt": prompt
        }
      
        response = requests.post(
            REPLICATE_ENDPOINT,
            headers={
                "Authorization": f"Bearer {config.get('REPLICATE_KEY')}",
                "Content-Type": "application/json",
                "Prefer": "wait"
            },
            json={
                "version": REPLICATE_AI_PATH,
                "input": input
            }
        )
        output = response.json()
        res = output['output']
        
        return generate_response(True, f"{res}")
    
    except requests.RequestException as e:
        return generate_response(False, "Failed to check Screen Description")

def read_command() -> Optional[Dict[str, Any]]:
    """Read command from stdin pipe.
    
    Reads data from Windows pipe in chunks until complete message is received.
    Expects JSON-formatted input.
    
    Returns:
        Optional[Dict[str, Any]]: Parsed command dictionary if successful,
                                 None if reading or parsing fails.
    
    Expected Command Format:
        {
            "tool_calls": [
                {
                    "func": "command_name",
                    "params": {
                        "param1": "value1",
                        ...
                    }
                }
            ]
        }
    """
    try:
        pipe = windll.kernel32.GetStdHandle(STD_INPUT_HANDLE)
        chunks = []
        
        while True:
            message_bytes = wintypes.DWORD()
            buffer = bytes(BUFFER_SIZE)
            success = windll.kernel32.ReadFile(
                pipe,
                buffer,
                BUFFER_SIZE,
                byref(message_bytes),
                None
            )

            if not success:
                logging.error('Error reading from command pipe')
                return None

            chunk = buffer.decode('utf-8')[:message_bytes.value]
            chunks.append(chunk)

            if message_bytes.value < BUFFER_SIZE:
                break

        retval = ''.join(chunks)
        logging.info(f'Raw Input: {retval}')
        return json.loads(retval)
        
    except json.JSONDecodeError:
        logging.error(f'Received invalid JSON: {retval}')
        logging.exception("JSON decoding failed:")
        return None
    except Exception as e:
        logging.error(f'Exception in read_command(): {e}')
        return None

def write_response(response: Response) -> None:
    """Write response to stdout pipe.
    
    Writes JSON-formatted response to Windows pipe with <<END>> marker.
    The marker is used by the reader to determine the end of the response.
    
    Args:
        response (Response): Response dictionary to write.
    
    Response Format:
        JSON-encoded dictionary followed by <<END>> marker.
        Example: {"success":true,"message":"Plugin initialized successfully"}<<END>>
    """
    try:
        pipe = windll.kernel32.GetStdHandle(STD_OUTPUT_HANDLE)
        json_message = json.dumps(response) + '<<END>>'
        message_bytes = json_message.encode('utf-8')
        
        bytes_written = wintypes.DWORD()
        windll.kernel32.WriteFile(
            pipe,
            message_bytes,
            len(message_bytes),
            bytes_written,
            None
        )
    except Exception as e:
        logging.error(f'Error writing response: {e}')

def initialize() -> Response:
    """Initialize the plugin.
    
    Performs any necessary setup for the plugin.
    
    Returns:
        Response: Success response with initialization status.
    """
    logging.info("Initializing plugin")
    return generate_response(True, "Plugin initialized successfully")

def shutdown() -> Response:
    """Shutdown the plugin.
    
    Performs any necessary cleanup before plugin shutdown.
    
    Returns:
        Response: Success response with shutdown status.
    """
    logging.info("Shutting down plugin")
    return generate_response(True, "Plugin shutdown successfully")

def main() -> None:
    """Main plugin loop.
    
    Sets up logging and enters main command processing loop.
    Handles incoming commands and routes them to appropriate handlers.
    Continues running until shutdown command is received.
    
    Command Processing Flow:
        1. Read command from pipe
        2. Parse command and parameters
        3. Route to appropriate handler
        4. Write response back to pipe
        5. Repeat until shutdown command
    
    Error Handling:
        - Invalid commands return error response
        - Failed command reads are logged and loop continues
        - Shutdown command exits loop gracefully
    """
    setup_logging()
    logging.info("Visual Plugin Started")
    
    while True:
        command = read_command()
        if command is None:
            logging.error('Error reading command')
            continue
        
        tool_calls = command.get("tool_calls", [])
        for tool_call in tool_calls:
            func = tool_call.get("func")
            params = tool_call.get("params", {})
            
            if func == "initialize":
                response = initialize()
            elif func == "describe_screen":
                response = describe_screen(params)
            elif func == "shutdown":
                response = shutdown()
                write_response(response)
                return
            else:
                response = generate_response(False, "Unknown function call")
            
            write_response(response)

if __name__ == "__main__":
    config = load_config()
    main()
