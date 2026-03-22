#!/usr/bin/env python3
"""
Gold Tier Test Runner

Runs all tests for Gold Tier implementation including:
- Watcher files (odoo_watcher.py, social_watcher.py, filesystem_watcher.py, gmail_watcher.py)
- MCP servers (syntax and structure validation)
- Unit tests
"""

import subprocess
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent
RESULTS_FILE = ROOT / "gold_tier_test_report.md"

def run_command(cmd, description, timeout=60):
    """Run a command and capture output."""
    print(f"\n{'='*80}")
    print(f"Running: {description}")
    print(f"Command: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
    print('='*80)
    
    try:
        result = subprocess.run(
            cmd if isinstance(cmd, list) else cmd.split(),
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(ROOT)
        )
        return {
            'success': result.returncode == 0,
            'stdout': result.stdout,
            'stderr': result.stderr,
            'returncode': result.returncode
        }
    except subprocess.TimeoutExpired:
        return {
            'success': False,
            'stdout': '',
            'stderr': f'Timeout after {timeout}s',
            'returncode': -1,
            'timeout': True
        }
    except Exception as e:
        return {
            'success': False,
            'stdout': '',
            'stderr': str(e),
            'returncode': -1,
            'exception': True
        }

def test_python_syntax(filepath):
    """Test Python file syntax."""
    result = run_command(
        ['python3', '-m', 'py_compile', str(filepath)],
        f"Syntax check: {filepath.name}",
        timeout=30
    )
    return result

def test_node_syntax(filepath):
    """Test Node.js file syntax."""
    result = run_command(
        ['node', '--check', str(filepath)],
        f"Syntax check: {filepath.name}",
        timeout=30
    )
    return result

def run_pytest_tests():
    """Run pytest unit tests."""
    result = run_command(
        ['python3', '-m', 'pytest', 'tests/', '-v', '--tb=short'],
        "Pytest unit tests",
        timeout=300
    )
    return result

def test_watcher_files():
    """Test watcher files."""
    results = {}
    watchers = [
        'odoo_watcher.py',
        'social_watcher.py',
        'filesystem_watcher.py',
        'gmail_watcher.py'
    ]
    
    for watcher in watchers:
        filepath = ROOT / watcher
        if filepath.exists():
            results[watcher] = test_python_syntax(filepath)
        else:
            results[watcher] = {
                'success': False,
                'stderr': 'File not found',
                'returncode': -1
            }
    
    return results

def test_mcp_servers():
    """Test MCP server files."""
    results = {}
    mcp_servers = [
        ('odoo-server', 'src/index.js'),
        ('facebook-server', 'src/index.js'),
        ('instagram-server', 'src/index.js'),
        ('twitter-server', 'src/index.js'),
    ]
    
    for server, main_file in mcp_servers:
        filepath = ROOT / 'mcp' / server / main_file
        if filepath.exists():
            results[f"{server}/index.js"] = test_node_syntax(filepath)
        else:
            results[f"{server}/index.js"] = {
                'success': False,
                'stderr': 'File not found',
                'returncode': -1
            }
    
    return results

def test_odoo_connection():
    """Test Odoo connection."""
    filepath = ROOT / 'test_odoo_connection.py'
    if filepath.exists():
        return run_command(
            ['python3', str(filepath)],
            "Odoo connection test",
            timeout=60
        )
    return {
        'success': False,
        'stderr': 'test_odoo_connection.py not found',
        'returncode': -1
    }

def generate_report(results):
    """Generate test report."""
    report = []
    report.append("# Gold Tier Implementation Test Report")
    report.append(f"\nGenerated: {datetime.now().isoformat()}")
    report.append("\n---\n")
    
    # Summary
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    # Watcher tests
    report.append("## Watcher Files Tests\n")
    if 'watchers' in results:
        for name, result in results['watchers'].items():
            total_tests += 1
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            if result['success']:
                passed_tests += 1
            else:
                failed_tests += 1
            report.append(f"- {name}: {status}")
            if not result['success'] and result.get('stderr'):
                report.append(f"  - Error: {result['stderr'][:200]}")
    
    # MCP server tests
    report.append("\n## MCP Server Tests\n")
    if 'mcp_servers' in results:
        for name, result in results['mcp_servers'].items():
            total_tests += 1
            status = "✅ PASS" if result['success'] else "❌ FAIL"
            if result['success']:
                passed_tests += 1
            else:
                failed_tests += 1
            report.append(f"- {name}: {status}")
            if not result['success'] and result.get('stderr'):
                report.append(f"  - Error: {result['stderr'][:200]}")
    
    # Pytest tests
    report.append("\n## Pytest Unit Tests\n")
    if 'pytest' in results:
        result = results['pytest']
        total_tests += 1
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        if result['success']:
            passed_tests += 1
        else:
            failed_tests += 1
        report.append(f"- Unit tests: {status}")
        if result.get('stdout'):
            # Extract summary line
            for line in result['stdout'].split('\n'):
                if 'passed' in line or 'failed' in line or 'error' in line:
                    report.append(f"  - {line.strip()}")
        if result.get('stderr'):
            report.append(f"  - Errors: {result['stderr'][:500]}")
    
    # Odoo connection test
    report.append("\n## Odoo Connection Test\n")
    if 'odoo_connection' in results:
        result = results['odoo_connection']
        total_tests += 1
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        if result['success']:
            passed_tests += 1
        else:
            failed_tests += 1
        report.append(f"- Odoo connection: {status}")
        if result.get('stdout'):
            report.append(f"  - Output: {result['stdout'][:500]}")
        if result.get('stderr'):
            report.append(f"  - Error: {result['stderr'][:500]}")
    
    # Overall summary
    report.append("\n---\n")
    report.append("## Overall Summary\n")
    report.append(f"- **Total Tests:** {total_tests}")
    report.append(f"- **Passed:** {passed_tests}")
    report.append(f"- **Failed:** {failed_tests}")
    report.append(f"- **Success Rate:** {(passed_tests/total_tests*100) if total_tests > 0 else 0:.1f}%")
    
    return '\n'.join(report)

def main():
    """Main test runner."""
    print("Starting Gold Tier Test Suite...")
    print(f"Root directory: {ROOT}")
    
    results = {}
    
    # Test watcher files
    print("\n[1/4] Testing watcher files...")
    results['watchers'] = test_watcher_files()
    
    # Test MCP servers
    print("\n[2/4] Testing MCP servers...")
    results['mcp_servers'] = test_mcp_servers()
    
    # Run pytest tests
    print("\n[3/4] Running pytest unit tests...")
    results['pytest'] = run_pytest_tests()
    
    # Test Odoo connection
    print("\n[4/4] Testing Odoo connection...")
    results['odoo_connection'] = test_odoo_connection()
    
    # Generate report
    print("\nGenerating test report...")
    report = generate_report(results)
    
    # Save report
    RESULTS_FILE.write_text(report, encoding='utf-8')
    print(f"\nTest report saved to: {RESULTS_FILE}")
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    print(report)
    
    return 0 if 'failed' not in report.lower() or '❌ FAIL' not in report else 1

if __name__ == "__main__":
    sys.exit(main())
