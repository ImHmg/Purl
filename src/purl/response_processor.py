"""
Response processor for handling captures and assertions
"""

import re
import json
from typing import Dict, Any, Optional
from jsonpath_ng import parse as jsonpath_parse
from .variables import VariableContext


class ResponseProcessor:
    """Processes HTTP response for captures and assertions"""
    
    def __init__(self, http_client):
        """
        Initialize response processor
        
        Args:
            http_client: HttpClient instance with response
        """
        self.http_client = http_client
        self.response = http_client.response
        self.elapsed_time = http_client.elapsed_time
        self.captures = {}
        self.var_context = VariableContext()
    
    def process_captures(self) -> Dict[str, Any]:
        """
        Process capture expressions and extract values from response
        
        Returns:
            Dictionary of captured values
        """
        captures_config = self.http_client.request_data.get('Captures', {})

        if not captures_config:
            return {}
        
        for capture_name, capture_expr in captures_config.items():
            value = self._extract_value(capture_expr)
            self.captures[capture_name] = value
             
            # Store in pvars
            self.var_context.put_variable(capture_name, str(value))

        return self.captures
    
    def process_asserts(self) -> Dict[str, Dict[str, Any]]:
        """
        Process assert expressions: capture left value using the first part;
        if an operator is present, compare; if not, assert value is not null.
        
        Supported operators (both pipe and bracket styles):
        ==, !=, >, <, contains, !contains
        
        Returns:
            Dict mapping assertion description to details: {
                'pass': bool,
                'actual': Any,
                'expected': Any,
                'op': Optional[str]
            }
        """
        asserts_config = self.http_client.request_data.get('Asserts', {})

        results: Dict[str, Dict[str, Any]] = {}
        if not asserts_config:
            return results

        for desc, expr in asserts_config.items():
            try:
                left_expr, op, right_raw = self._parse_assert_expr(str(expr))
                actual = self._extract_value(left_expr)

                if op is None:
                    # No operator: value should not be null/empty
                    results[desc] = {
                        'pass': (actual is not None and str(actual) != ""),
                        'actual': actual,
                        'expected': None,
                        'op': None,
                    }
                    continue

                expected = self._normalize_expected(right_raw)
                passed = self._evaluate_comparison(actual, expected, op)
                results[desc] = {
                    'pass': passed,
                    'actual': actual,
                    'expected': expected,
                    'op': op,
                }
            except Exception:
                results[desc] = {
                    'pass': False,
                    'actual': None,
                    'expected': None,
                    'op': None,
                }

        return results

    def _parse_assert_expr(self, expr: str):
        """
        Parse an assertion expression into (left_expr, operator, right_value_str)
        Accepts either pipe style: "<left> |op| <right>" or bracket style: "<left> [op] <right>".
        If no operator, returns (expr, None, None)
        """
        s = expr.strip()

        # Try pipe style first: |op|
        pipe_match = re.search(r"\|\s*(==|!=|>|<|contains|!contains)\s*\|", s)
        if pipe_match:
            op = pipe_match.group(1)
            parts = re.split(r"\|\s*(?:==|!=|>|<|contains|!contains)\s*\|", s, maxsplit=1)
            left = parts[0].strip()
            right = parts[1].strip() if len(parts) > 1 else ""
            return left, op, right

        # Try bracket style: [op]
        bracket_match = re.search(r"\[\s*(==|!=|>|<|contains|!contains)\s*\]", s)
        if bracket_match:
            op = bracket_match.group(1)
            parts = re.split(r"\[\s*(?:==|!=|>|<|contains|!contains)\s*\]", s, maxsplit=1)
            left = parts[0].strip()
            right = parts[1].strip() if len(parts) > 1 else ""
            return left, op, right

        # No operator: treat whole as capture expr
        return s, None, None

    def _normalize_expected(self, raw: Optional[str]) -> Optional[str]:
        """
        Normalize expected value string: strip quotes and whitespace.
        """
        if raw is None:
            return None
        v = raw.strip()
        # Remove surrounding quotes if present
        if (len(v) >= 2) and ((v[0] == v[-1]) and v[0] in ('"', "'")):
            v = v[1:-1]
        return v

    def _to_number(self, value: Any) -> Optional[float]:
        try:
            if isinstance(value, bool) or value is None:
                return None
            if isinstance(value, (int, float)):
                return float(value)
            return float(str(value).strip())
        except Exception:
            return None

    def _evaluate_comparison(self, actual: Any, expected: Optional[str], op: str) -> bool:
        """
        Evaluate comparison between actual and expected using operator.
        For numeric compares, attempt numeric coercion; fallback to string for ==/!=.
        contains/!contains use string containment.
        """
        if op in ("contains", "!contains"):
            actual_str = "" if actual is None else str(actual)
            expected_str = "" if expected is None else str(expected)
            res = expected_str in actual_str
            return res if op == "contains" else (not res)

        # Try numeric comparison
        a_num = self._to_number(actual)
        e_num = self._to_number(expected)

        if op in ("<", ">") and (a_num is not None) and (e_num is not None):
            return a_num < e_num if op == "<" else a_num > e_num

        if op in ("==", "!="):
            if (a_num is not None) and (e_num is not None):
                res = (a_num == e_num)
            else:
                res = str(actual) == ("" if expected is None else str(expected))
            return res if op == "==" else (not res)

        # Unsupported combination or failed coercion
        return False

    def _extract_value(self, expr: str) -> Optional[Any]:
        """
        Extract value based on capture expression
        
        Args:
            expr: Capture expression (e.g., "@headers Authorization", "@status", "@body jsonpath $.id")
            
        Returns:
            Extracted value or None
        """
        expr = expr.strip()
        
        # @status - capture status code
        if expr == "@status":
            return self.response.status_code
        
        # @time - capture elapsed time in milliseconds
        if expr == "@time":
            return self.elapsed_time
        
        # @headers <header_name> - capture specific header
        if expr.startswith("@headers "):
            header_name = expr.replace("@headers ", "").strip()
            if hasattr(self.response, 'headers'):
                return self.response.headers.get(header_name)
            return None
        
        # @body - capture entire body as string
        if expr == "@body":
            if hasattr(self.response, 'text'):
                return self.response.text
            return None
        
        # @body jsonpath <path> - extract from JSON body using JSONPath
        if expr.startswith("@body jsonpath "):
            jsonpath_expr = expr.replace("@body jsonpath ", "").strip()
            return self._extract_jsonpath(jsonpath_expr)
        
        # @body xpath <path> - extract from XML body using XPath
        if expr.startswith("@body xpath "):
            xpath_expr = expr.replace("@body xpath ", "").strip()
            return self._extract_xpath(xpath_expr)
        
        # @body regex <pattern> - extract using regex
        if expr.startswith("@body regex "):
            regex_pattern = expr.replace("@body regex ", "").strip()
            return self._extract_regex(regex_pattern)
        
        return None
    
    def _extract_jsonpath(self, jsonpath_expr: str) -> Optional[Any]:
        """
        Extract value from JSON response using JSONPath
        
        Args:
            jsonpath_expr: JSONPath expression (e.g., "$.id", "$.data.user.name")
            
        Returns:
            Extracted value or None
        """
        try:
            # Get JSON body
            if hasattr(self.response, 'json'):
                body_json = self.response.json()
            else:
                return None
            
            # Parse and execute JSONPath
            jsonpath_obj = jsonpath_parse(jsonpath_expr)
            matches = jsonpath_obj.find(body_json)
            
            if matches:
                # Return first match value
                return matches[0].value
            
            return None
        except Exception as e:
            return None
    
    def _extract_xpath(self, xpath_expr: str) -> Optional[Any]:
        """
        Extract value from XML response using XPath
        
        Args:
            xpath_expr: XPath expression (e.g., "//order/id")
            
        Returns:
            Extracted value or None
        """
        try:
            from lxml import etree
            
            # Get text body
            if hasattr(self.response, 'text'):
                xml_text = self.response.text
            else:
                return None
            
            # Parse XML
            root = etree.fromstring(xml_text.encode('utf-8'))
            
            # Execute XPath
            result = root.xpath(xpath_expr)
            
            if result:
                # If result is element, get text
                if hasattr(result[0], 'text'):
                    return result[0].text
                # Otherwise return as is
                return result[0]
            
            return None
        except Exception as e:
            return None
    
    def _extract_regex(self, pattern: str) -> Optional[str]:
        """
        Extract value from response body using regex
        
        Args:
            pattern: Regular expression pattern
            
        Returns:
            Matched value or None
        """
        try:
            # Get text body
            if hasattr(self.response, 'text'):
                body_text = self.response.text
            else:
                return None
            
            # Execute regex
            match = re.search(pattern, body_text)
            
            if match:
                # Return first group if exists, otherwise full match
                if match.groups():
                    return match.group(1)
                return match.group(0)
            
            return None
        except Exception as e:
            return None
