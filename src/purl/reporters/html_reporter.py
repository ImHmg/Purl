"""HTML report generator for purl suite execution."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


class SuiteHtmlReporter:
    """Generates HTML reports for suite execution results."""

    def __init__(self, suite_name: str, working_dir: Path):
        """
        Initialize the HTML reporter.
        
        Args:
            suite_name: Name of the suite being executed
            working_dir: Working directory for relative path resolution
        """
        self.suite_name = suite_name
        self.working_dir = working_dir
        self.generated_time = datetime.now()

    def generate(self, aggregated_results: List[Dict[str, Any]], report_path: str = None) -> str:
        """
        Generate HTML report from aggregated results.
        
        Args:
            aggregated_results: List of results from suite execution
            report_path: Optional custom report path from suite file
            
        Returns:
            Path to the generated report file
        """
        # Determine report file path
        if report_path:
            output_path = Path(report_path)
            if not output_path.is_absolute():
                output_path = self.working_dir / output_path
        else:
            # Default: .purl/reports/{suite_name}_{timestamp}.html
            purl_dir = self.working_dir / ".purl" / "reports"
            purl_dir.mkdir(parents=True, exist_ok=True)
            timestamp = self.generated_time.strftime("%Y%m%d_%H%M%S")
            output_path = purl_dir / f"{self.suite_name}_{timestamp}.html"

        # Ensure parent directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Calculate statistics
        stats = self._calculate_statistics(aggregated_results)

        # Generate HTML content
        html_content = self._generate_html(aggregated_results, stats)

        # Write to file
        output_path.write_text(html_content, encoding='utf-8')

        return str(output_path)

    def _calculate_statistics(self, aggregated_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate summary statistics from results."""
        total_asserts = 0
        success_asserts = 0
        failed_asserts = 0
        total_requests = 0
        failed_requests = 0

        for row_result in aggregated_results:
            requests = row_result.get("requests", [])
            for request in requests:
                total_requests += 1
                
                # Check if request has error status
                if request.get("status") == "error":
                    failed_requests += 1
                    continue

                # Count asserts
                asserts = request.get("asserts", {})
                for assert_name, assert_result in asserts.items():
                    total_asserts += 1
                    if assert_result.get("pass"):
                        success_asserts += 1
                    else:
                        failed_asserts += 1

        failure_rate = (failed_asserts / total_asserts * 100) if total_asserts > 0 else 0

        return {
            "total_asserts": total_asserts,
            "success_asserts": success_asserts,
            "failed_asserts": failed_asserts,
            "failure_rate": failure_rate,
            "total_requests": total_requests,
            "failed_requests": failed_requests,
            "total_rows": len(aggregated_results)
        }

    def _generate_html(self, aggregated_results: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """Generate complete HTML report."""
        
        # Read Bootstrap CSS and JS from assets
        assets_dir = Path(__file__).parent.parent / "assets"
        bootstrap_css = (assets_dir / "bootstrap.css").read_text(encoding='utf-8')
        bootstrap_js = (assets_dir / "bootstrap.js").read_text(encoding='utf-8')

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Purl Suite Report - {self._escape_html(self.suite_name)}</title>
    <style>
        {bootstrap_css}
    </style>
    <style>
        body {{
            background-color: #f8f9fa;
            padding: 20px;
        }}
        .report-container {{
            max-width: 1400px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        .report-header {{
            border-bottom: 2px solid #dee2e6;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        .report-title {{
            font-size: 28px;
            font-weight: 600;
            color: #212529;
            margin-bottom: 10px;
        }}
        .report-meta {{
            color: #6c757d;
            font-size: 14px;
        }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: #f8f9fa;
            border-radius: 6px;
            padding: 15px;
            border-left: 4px solid #0d6efd;
        }}
        .stat-card.success {{
            border-left-color: #198754;
        }}
        .stat-card.danger {{
            border-left-color: #dc3545;
        }}
        .stat-card.warning {{
            border-left-color: #ffc107;
        }}
        .stat-label {{
            font-size: 12px;
            color: #6c757d;
            text-transform: uppercase;
            font-weight: 600;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 24px;
            font-weight: 700;
            color: #212529;
        }}
        .row-section {{
            margin-bottom: 30px;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            overflow: hidden;
        }}
        .row-header {{
            background: #e9ecef;
            padding: 12px 20px;
            font-weight: 600;
            color: #495057;
            border-bottom: 1px solid #dee2e6;
        }}
        .request-item {{
            border-bottom: 1px solid #dee2e6;
            padding: 20px;
        }}
        .request-item:last-child {{
            border-bottom: none;
        }}
        .request-header {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
        }}
        .request-title {{
            font-weight: 600;
            color: #212529;
            font-size: 16px;
        }}
        .badge {{
            padding: 4px 10px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }}
        .badge-success {{
            background: #d1e7dd;
            color: #0a3622;
        }}
        .badge-danger {{
            background: #f8d7da;
            color: #58151c;
        }}
        .badge-info {{
            background: #cff4fc;
            color: #055160;
        }}
        .section-title {{
            font-size: 13px;
            font-weight: 600;
            color: #495057;
            margin-top: 15px;
            margin-bottom: 8px;
            text-transform: uppercase;
        }}
        .code-block {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 12px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .assert-item {{
            padding: 8px 12px;
            margin-bottom: 6px;
            border-radius: 4px;
            font-size: 13px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .assert-item.success {{
            background: #d1e7dd;
            border-left: 3px solid #198754;
        }}
        .assert-item.failed {{
            background: #f8d7da;
            border-left: 3px solid #dc3545;
        }}
        .assert-icon {{
            font-weight: 700;
        }}
        .capture-item {{
            padding: 8px 12px;
            margin-bottom: 6px;
            background: #cff4fc;
            border-radius: 4px;
            font-size: 13px;
            border-left: 3px solid #0dcaf0;
        }}
        .variable-item {{
            padding: 8px 12px;
            margin-bottom: 6px;
            background: #fff3cd;
            border-radius: 4px;
            font-size: 13px;
            border-left: 3px solid #ffc107;
        }}
        .error-message {{
            background: #f8d7da;
            color: #58151c;
            padding: 12px;
            border-radius: 4px;
            border-left: 4px solid #dc3545;
            margin-top: 10px;
        }}
        .http-method {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 3px;
            font-size: 11px;
            font-weight: 700;
            margin-right: 8px;
        }}
        .method-get {{ background: #d1e7dd; color: #0a3622; }}
        .method-post {{ background: #cff4fc; color: #055160; }}
        .method-put {{ background: #fff3cd; color: #664d03; }}
        .method-delete {{ background: #f8d7da; color: #58151c; }}
        .method-patch {{ background: #e2e3e5; color: #2b2f32; }}
        .collapsible {{
            cursor: pointer;
            user-select: none;
        }}
        .collapsible:hover {{
            background: #f8f9fa;
        }}
        .collapse-content {{
            max-height: 0;
            overflow: hidden;
            transition: max-height 0.3s ease;
        }}
        .collapse-content.show {{
            max-height: 5000px;
        }}
    </style>
</head>
<body>
    <div class="report-container">
        <div class="report-header">
            <div class="report-title">🧪 Purl Suite Report</div>
            <div class="report-meta">
                <strong>Suite:</strong> {self._escape_html(self.suite_name)} | 
                <strong>Generated:</strong> {self.generated_time.strftime("%Y-%m-%d %H:%M:%S")}
            </div>
        </div>

        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-label">Total Rows</div>
                <div class="stat-value">{stats['total_rows']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Requests</div>
                <div class="stat-value">{stats['total_requests']}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Total Asserts</div>
                <div class="stat-value">{stats['total_asserts']}</div>
            </div>
            <div class="stat-card success">
                <div class="stat-label">Success Asserts</div>
                <div class="stat-value">{stats['success_asserts']}</div>
            </div>
            <div class="stat-card danger">
                <div class="stat-label">Failed Asserts</div>
                <div class="stat-value">{stats['failed_asserts']}</div>
            </div>
            <div class="stat-card warning">
                <div class="stat-label">Failure Rate</div>
                <div class="stat-value">{stats['failure_rate']:.1f}%</div>
            </div>
        </div>

        {self._generate_results_html(aggregated_results)}
    </div>

    <script>
        {bootstrap_js}
    </script>
    <script>
        // Toggle collapse functionality
        document.querySelectorAll('.collapsible').forEach(item => {{
            item.addEventListener('click', function() {{
                const content = this.nextElementSibling;
                content.classList.toggle('show');
            }});
        }});
    </script>
</body>
</html>"""
        return html

    def _generate_results_html(self, aggregated_results: List[Dict[str, Any]]) -> str:
        """Generate HTML for all row results."""
        html_parts = []

        for row_result in aggregated_results:
            row_index = row_result.get("row_index", 0)
            variables = row_result.get("variables", {})
            requests = row_result.get("requests", [])

            html_parts.append(f"""
        <div class="row-section">
            <div class="row-header">
                📋 Row {row_index}
                {f' - {len(variables)} variable(s)' if variables else ''}
            </div>
            """)

            # Show row variables if present
            if variables:
                html_parts.append('<div style="padding: 15px 20px; background: #fffbf0; border-bottom: 1px solid #dee2e6;">')
                html_parts.append('<div class="section-title">Row Variables</div>')
                for key, value in variables.items():
                    html_parts.append(f'<div class="variable-item"><strong>{self._escape_html(str(key))}:</strong> {self._escape_html(str(value))}</div>')
                html_parts.append('</div>')

            # Show each request
            for req_index, request in enumerate(requests, start=1):
                html_parts.append(self._generate_request_html(request, req_index))

            html_parts.append('</div>')

        return '\n'.join(html_parts)

    def _generate_request_html(self, request: Dict[str, Any], req_index: int) -> str:
        """Generate HTML for a single request result."""
        html_parts = []
        
        html_parts.append('<div class="request-item">')
        
        # Request header
        file_name = request.get("file", "Unknown")
        status = request.get("status", "unknown")
        
        # Check if this is an error request
        is_error = status == "error"
        
        html_parts.append('<div class="request-header">')
        html_parts.append(f'<div class="request-title">Request #{req_index}: {self._escape_html(Path(file_name).name)}</div>')
        
        if is_error:
            html_parts.append('<span class="badge badge-danger">ERROR</span>')
        else:
            # Count assert status
            asserts = request.get("asserts", {})
            failed_count = sum(1 for result in asserts.values() if not result.get("pass"))
            if failed_count > 0:
                html_parts.append(f'<span class="badge badge-danger">{failed_count} Failed</span>')
            else:
                html_parts.append('<span class="badge badge-success">All Passed</span>')
        
        html_parts.append('</div>')

        # Show error message if present
        if is_error:
            error_msg = request.get("message", "Unknown error")
            html_parts.append(f'<div class="error-message"><strong>Error:</strong> {self._escape_html(str(error_msg))}</div>')
            html_parts.append('</div>')
            return '\n'.join(html_parts)

        # Request details
        req_data = request.get("request", {})
        if req_data:
            method = req_data.get("url", "").split("://")[0] if "://" in str(req_data.get("url", "")) else "GET"
            # Try to extract method from request_spec
            request_spec = request.get("request_spec", {})
            method = request_spec.get("Method", "GET").upper()
            url = req_data.get("url", "")
            
            html_parts.append('<div class="section-title">Request</div>')
            html_parts.append(f'<div style="margin-bottom: 10px;">')
            html_parts.append(f'<span class="http-method method-{method.lower()}">{method}</span>')
            html_parts.append(f'<code>{self._escape_html(url)}</code>')
            html_parts.append('</div>')
            
            # Request headers
            headers = req_data.get("headers", {})
            if headers:
                html_parts.append('<div class="collapsible" style="padding: 8px; background: #f8f9fa; border-radius: 4px; margin-bottom: 5px;"><strong>▶ Headers</strong></div>')
                html_parts.append('<div class="collapse-content">')
                html_parts.append(f'<div class="code-block">{self._escape_html(json.dumps(headers, indent=2))}</div>')
                html_parts.append('</div>')
            
            # Request body
            body_data = req_data.get("json") or req_data.get("data")
            if body_data:
                html_parts.append('<div class="collapsible" style="padding: 8px; background: #f8f9fa; border-radius: 4px; margin-bottom: 5px;"><strong>▶ Request Body</strong></div>')
                html_parts.append('<div class="collapse-content">')
                if isinstance(body_data, (dict, list)):
                    html_parts.append(f'<div class="code-block">{self._escape_html(json.dumps(body_data, indent=2))}</div>')
                else:
                    html_parts.append(f'<div class="code-block">{self._escape_html(str(body_data))}</div>')
                html_parts.append('</div>')

        # Response details
        response = request.get("response")
        if response:
            html_parts.append('<div class="section-title">Response</div>')
            status_code = getattr(response, 'status_code', 'N/A')
            elapsed = getattr(response, 'elapsed', None)
            elapsed_ms = elapsed.total_seconds() * 1000 if elapsed else 0
            
            html_parts.append(f'<div style="margin-bottom: 10px;">')
            html_parts.append(f'<span class="badge badge-info">Status: {status_code}</span> ')
            html_parts.append(f'<span class="badge badge-info">Time: {elapsed_ms:.0f}ms</span>')
            html_parts.append('</div>')
            
            # Response headers
            response_headers = dict(getattr(response, 'headers', {}))
            if response_headers:
                html_parts.append('<div class="collapsible" style="padding: 8px; background: #f8f9fa; border-radius: 4px; margin-bottom: 5px;"><strong>▶ Response Headers</strong></div>')
                html_parts.append('<div class="collapse-content">')
                html_parts.append(f'<div class="code-block">{self._escape_html(json.dumps(response_headers, indent=2))}</div>')
                html_parts.append('</div>')
            
            # Response body
            try:
                response_body = response.json()
                html_parts.append('<div class="collapsible" style="padding: 8px; background: #f8f9fa; border-radius: 4px; margin-bottom: 5px;"><strong>▶ Response Body</strong></div>')
                html_parts.append('<div class="collapse-content">')
                html_parts.append(f'<div class="code-block">{self._escape_html(json.dumps(response_body, indent=2))}</div>')
                html_parts.append('</div>')
            except:
                response_text = getattr(response, 'text', '')
                if response_text:
                    html_parts.append('<div class="collapsible" style="padding: 8px; background: #f8f9fa; border-radius: 4px; margin-bottom: 5px;"><strong>▶ Response Body</strong></div>')
                    html_parts.append('<div class="collapse-content">')
                    html_parts.append(f'<div class="code-block">{self._escape_html(response_text[:1000])}</div>')
                    html_parts.append('</div>')

        # Asserts
        asserts = request.get("asserts", {})
        if asserts:
            html_parts.append('<div class="section-title">Assertions</div>')
            for assert_name, assert_result in asserts.items():
                assert_passed = assert_result.get("pass", False)
                actual = assert_result.get("actual")
                expected = assert_result.get("expected")
                op = assert_result.get("op")
                
                status_class = "success" if assert_passed else "failed"
                icon = "✓" if assert_passed else "✗"
                
                html_parts.append(f'<div class="assert-item {status_class}">')
                html_parts.append(f'<span class="assert-icon">{icon}</span>')
                html_parts.append(f'<div><strong>{self._escape_html(assert_name)}</strong>')
                
                # Show details for failed assertions
                if not assert_passed:
                    details = []
                    if op:
                        details.append(f"op: {self._escape_html(str(op))}")
                    if actual is not None:
                        details.append(f"actual: {self._escape_html(str(actual))}")
                    if expected is not None:
                        details.append(f"expected: {self._escape_html(str(expected))}")
                    if details:
                        html_parts.append(f'<br><small>{" | ".join(details)}</small>')
                
                html_parts.append('</div></div>')

        # Captures
        captures = request.get("captures", {})
        if captures:
            html_parts.append('<div class="section-title">Captures</div>')
            for capture_name, capture_value in captures.items():
                html_parts.append(f'<div class="capture-item">')
                html_parts.append(f'<strong>{self._escape_html(capture_name)}:</strong> {self._escape_html(str(capture_value))}')
                html_parts.append('</div>')

        html_parts.append('</div>')
        return '\n'.join(html_parts)

    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if text is None:
            return ""
        return (str(text)
                .replace("&", "&amp;")
                .replace("<", "&lt;")
                .replace(">", "&gt;")
                .replace('"', "&quot;")
                .replace("'", "&#39;"))
