"""
Colored output utilities using termcolor
"""

from termcolor import colored, cprint
import json
from typing import Any, Dict


class ColoredOutput:
    """Utility class for colored console output"""
    
    @staticmethod
    def success(message: str) -> None:
        """Print success message in green"""
        cprint(message, 'green', attrs=['bold'])
    
    @staticmethod
    def error(message: str) -> None:
        """Print error message in red"""
        cprint(message, 'red', attrs=['bold'])
    
    @staticmethod
    def warning(message: str) -> None:
        """Print warning message in yellow"""
        cprint(message, 'yellow', attrs=['bold'])
    
    @staticmethod
    def info(message: str) -> None:
        """Print info message in cyan"""
        cprint(message, 'cyan')
    
    @staticmethod
    def header(message: str) -> None:
        """Print header message in magenta with bold"""
        cprint(message, 'magenta', attrs=['bold'])
    
    @staticmethod
    def separator(char: str = "=", length: int = 80, color: str = 'cyan') -> None:
        """Print a colored separator line"""
        cprint(char * length, color)
    
    @staticmethod
    def key_value(key: str, value: str, indent: int = 0) -> None:
        """Print key-value pair with colors"""
        spaces = "  " * indent
        key_colored = colored(f"{key}:", 'blue', attrs=['bold'])
        value_colored = colored(str(value), 'white')
        print(f"{spaces}{key_colored} {value_colored}")
    
    @staticmethod
    def method_colored(method: str) -> str:
        """Get colored method string"""
        method_upper = method.upper()
        # Use a uniform style so every method looks consistent
        return colored(' ' + method_upper + ' ', 'white', 'on_magenta', attrs=['bold'])
    
    @staticmethod
    def section_header(title: str) -> None:
        """Print a section header"""
        print()
        cprint(f"{title}:", 'magenta', attrs=['bold'])
    
    @staticmethod
    def file_processing(filename: str, index: int = None, total: int = None) -> None:
        """Print file processing message"""
        print()
        if index is not None and total is not None:
            prefix = colored(f"[{index}/{total}]", 'cyan', attrs=['bold'])
            label = colored("Processing:", 'cyan', attrs=['bold'])
            file_colored = colored(filename, 'white', attrs=['bold'])
            print(f"{prefix} {label} {file_colored}")
        else:
            label = colored("Processing:", 'cyan', attrs=['bold'])
            file_colored = colored(filename, 'white', attrs=['bold'])
            print(f"{label} {file_colored}")
    
    @staticmethod
    def env_config(env_names: list) -> None:
        """Print environment configuration message"""
        env_str = ", ".join(env_names)
        label = colored("Environment configs:", 'cyan')
        value = colored(env_str, 'white', attrs=['bold'])
        print(f"{label} {value}")
    
    @staticmethod
    def print_colored(text: str, color: str = 'white', on_color: str = None, attrs: list = None) -> None:
        """Print text with specified colors and attributes"""
        cprint(text, color, on_color, attrs)


def format_json_colored(data: dict, indent: int = 2) -> str:
    """
    Format JSON data with colors
    
    Args:
        data: Dictionary to format
        indent: Indentation spaces
        
    Returns:
        Colored JSON string
    """
    # Convert to pretty JSON string
    json_str = json.dumps(data, indent=indent)
    
    # Color the JSON output
    lines = []
    for line in json_str.split('\n'):
        stripped = line.strip()
        
        # Detect line type and color accordingly
        if stripped.startswith('"') and '":' in line:
            # This is a key line
            key_part = line.split(':', 1)[0]
            value_part = ':' + line.split(':', 1)[1] if ':' in line else ''
            colored_line = colored(key_part, 'blue', attrs=['bold']) + colored(value_part, 'white')
            lines.append(colored_line)
        elif stripped in ['{', '}', '[', ']']:
            # Brackets
            lines.append(colored(line, 'yellow'))
        else:
            # Regular values
            lines.append(colored(line, 'white'))
    
    return '\n'.join(lines)


def format_dict_colored(data: Dict[str, Any], indent: int = 0) -> None:
    """
    Print dictionary with colored key-value pairs
    
    Args:
        data: Dictionary to print
        indent: Indentation level
    """
    for key, value in data.items():
        ColoredOutput.key_value(key, value, indent)


HTTP_STATUS_CODES = {
    "100": "Continue", "101": "Switching Protocols", "102": "Processing",
    "200": "OK", "201": "Created", "202": "Accepted", "203": "Non-Authoritative Information",
    "204": "No Content", "205": "Reset Content", "206": "Partial Content", "207": "Multi-Status",
    "226": "IM Used", "300": "Multiple Choices", "301": "Moved Permanently", "302": "Found",
    "303": "See Other", "304": "Not Modified", "305": "Use Proxy", "307": "Temporary Redirect",
    "308": "Permanent Redirect", "400": "Bad Request", "401": "Unauthorized",
    "402": "Payment Required", "403": "Forbidden", "404": "Not Found", "405": "Method Not Allowed",
    "406": "Not Acceptable", "407": "Proxy Authentication Required", "408": "Request Timeout",
    "409": "Conflict", "410": "Gone", "411": "Length Required", "412": "Precondition Failed",
    "413": "Payload Too Large", "414": "URI Too Long", "415": "Unsupported Media Type",
    "416": "Range Not Satisfiable", "417": "Expectation Failed", "418": "I'm a teapot",
    "422": "Unprocessable Entity", "423": "Locked", "424": "Failed Dependency",
    "426": "Upgrade Required", "428": "Precondition Required", "429": "Too Many Requests",
    "431": "Request Header Fields Too Large", "451": "Unavailable For Legal Reasons",
    "500": "Internal Server Error", "501": "Not Implemented", "502": "Bad Gateway",
    "503": "Service Unavailable", "504": "Gateway Time-out", "505": "HTTP Version Not Supported",
    "506": "Variant Also Negotiates", "507": "Insufficient Storage",
    "511": "Network Authentication Required"
}


def get_status_color(status_code: int) -> str:
    """Get color for status code based on category"""
    if 100 <= status_code < 200:
        return 'cyan'
    elif 200 <= status_code < 300:
        return 'green'
    elif 300 <= status_code < 400:
        return 'yellow'
    elif 400 <= status_code < 500:
        return 'red'
    elif 500 <= status_code < 600:
        return 'magenta'
    else:
        return 'white'


def print_http_request(http_client) -> None:
    """
    Print HTTP request details before execution
    
    Args:
        http_client: HttpClient instance
    """
    from .http_client import HttpClient
    
    ColoredOutput.separator("-", 80, 'red')
    http_header = colored("  ", 'white', 'on_blue', attrs=['bold']) + colored(" REQUEST ", 'black', 'on_white', attrs=['bold'])
    
    # Print method and URL
    method = colored(' ' + http_client.get_method().upper() + ' ', 'white', 'on_magenta', attrs=['bold']) 
    url = colored(http_client.get_url(), 'white', attrs=['bold'])

    print(f"{http_header}{method} {url}")
    
    # Print query parameters
    query_params = http_client.get_query_params()
    if query_params:
        ColoredOutput.section_header("Query Parameters")
        for key, value in query_params.items():
            ColoredOutput.key_value(key, value, indent=1)
    
    # Print headers
    headers = http_client.get_headers()
    if headers:
        ColoredOutput.section_header("Headers")
        for key, value in headers.items():
            ColoredOutput.key_value(key, value, indent=1)
    
    # Print body
    body_type, body = http_client.get_body() if http_client.get_body() else (None, None)
    if http_client.get_body_type() == 'TextBody':
        ColoredOutput.section_header("TextBody")
        print(colored(str(body), 'white'))
    elif http_client.get_body_type() == 'JsonBody':
        ColoredOutput.section_header("JsonBody")
        if isinstance(body, str):
            try:
                body_dict = json.loads(body)
                print(format_json_colored(body_dict, indent=2))
            except json.JSONDecodeError:
                print(colored(body, 'white'))
        elif isinstance(body, dict):
            print(format_json_colored(body, indent=2))
        else:
            print(colored(str(body), 'white'))
    elif http_client.get_body_type() == 'FormBody':
        ColoredOutput.section_header("FormBody")
        for key, value in body.items():
            ColoredOutput.key_value(key, value, indent=1)
    elif http_client.get_body_type() == 'MultipartBody':
        ColoredOutput.section_header("MultipartBody")
        for key, value in body.items():
            ColoredOutput.key_value(key, value, indent=1)
    elif http_client.get_body_type() == 'Body':
        ColoredOutput.section_header("Body")
        if isinstance(body, dict):
            for key, value in body.items():
                ColoredOutput.key_value(key, value, indent=1)
        else:
            print(colored(str(body), 'white'))
    print()


def print_http_response(http_client) -> None:
    """
    Print HTTP response details after execution
    
    Args:
        http_client: HttpClient instance with response and elapsed_time
    """
    from .http_client import HttpClient
    
    # Get response from http_client
    response = http_client.response
    
    # Print status code with description
    status_code = response.status_code
    status_text = HTTP_STATUS_CODES.get(str(status_code), "Unknown")
    status_line = f" {status_code} {status_text} "
    
    # Build the response header line with timing
    response_header = colored("  ", 'black', 'on_green', attrs=['bold']) + colored(" RESPONSE ", 'black', 'on_white', attrs=['bold'])
    time_info = colored(f"[{http_client.elapsed_time:.2f} ms] ", 'white', 'on_dark_grey')

    
    # Print status code below
    status_colored = colored(status_line, 'white', 'on_dark_grey', attrs=['bold'])
    print( response_header + status_colored + time_info)
    
    # Print response body
    ColoredOutput.section_header("Response Body")
    try:
        # Try to parse as JSON
        if hasattr(response, 'json'):
            try:
                body_json = response.json()
                print(format_json_colored(body_json, indent=2))
            except:
                # Fallback to text
                if hasattr(response, 'text'):
                    print(colored(response.text, 'white'))
        elif hasattr(response, 'text'):
            print(colored(response.text, 'white'))
        else:
            print(colored("No response body", 'yellow'))
    except Exception as e:
        print(colored(f"Error reading response: {str(e)}", 'red'))
    
    # Print response headers
    if hasattr(response, 'headers') and response.headers:
        ColoredOutput.section_header("Response Headers")
        for key, value in response.headers.items():
            ColoredOutput.key_value(key, value, indent=1)

    print()


def print_captures(captures: Dict[str, Any]) -> None:
    """
    Print captured values from response
    
    Args:
        captures: Dictionary of captured values
    """
    if not captures:
        return
    
    ColoredOutput.section_header("Captures")
    for key, value in captures.items():
        ColoredOutput.key_value(key, str(value), indent=1)
    print()


def print_asserts(asserts: Dict[str, Dict[str, Any]]) -> None:
    """
    Print assertion results with colors.
    - Passed assertions in green
    - Failed assertions in red, include actual/expected
    
    Args:
        asserts: Dict mapping description -> { pass, actual, expected, op }
    """
    if not asserts:
        return
    
    ColoredOutput.section_header("Asserts")
    for desc, result in asserts.items():
        passed = bool(result.get('pass', False))
        actual = result.get('actual')
        expected = result.get('expected')
        op = result.get('op')

        status_text = 'PASS' if passed else 'FAIL'
        status_color = 'green' if passed else 'red'
        
        # Header line for each assertion
        cprint(f"  {desc}: {status_text}", status_color, attrs=['bold'])
        
        # Details line(s)
        if op is not None:
            ColoredOutput.key_value('op', op, indent=2)
        ColoredOutput.key_value('actual', str(actual), indent=2)
        if expected is not None:
            ColoredOutput.key_value('expected', str(expected), indent=2)
    print()
