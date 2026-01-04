#!/usr/bin/env python3
"""
Claude AI Auto-Deploy System
Automatically detects, encodes, and deploys artifacts from Claude AI to GitHub

Author: Ariel Shapira / BidDeed.AI
Created: 2025-01-03
Version: 1.0.0
"""

import os
import json
import base64
import hashlib
import mimetypes
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re

# Configuration
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN', 'YOUR_GITHUB_TOKEN_HERE')
GITHUB_API = 'https://api.github.com'
GITHUB_USER = 'breverdbidder'
OUTPUTS_DIR = Path('/mnt/user-data/outputs')

# Deployment routing rules
ROUTING_RULES = {
    # Workflows
    r'.*\.yml$': {
        'repo': 'life-os',
        'path': '.github/workflows/',
        'description': 'GitHub Actions workflow'
    },
    # Python modules
    r'.*_node.*\.py$': {
        'repo': 'life-os',
        'path': 'src/nodes/',
        'description': 'LangGraph node module'
    },
    r'.*_agent.*\.py$': {
        'repo': 'life-os',
        'path': 'src/agents/',
        'description': 'Agent module'
    },
    r'.*_scraper.*\.py$': {
        'repo': 'brevard-bidder-scraper',
        'path': 'src/scrapers/',
        'description': 'Scraper module'
    },
    r'.*\.py$': {
        'repo': 'life-os',
        'path': 'src/',
        'description': 'Python module'
    },
    # Web artifacts
    r'.*\.(html|css|js)$': {
        'repo': 'biddeed-conversational-ai',
        'path': 'public/',
        'description': 'Web artifact'
    },
    # Documentation
    r'.*\.md$': {
        'repo': 'life-os',
        'path': 'docs/',
        'description': 'Documentation'
    },
    # Reports
    r'.*\.docx$': {
        'repo': 'life-os',
        'path': 'reports/',
        'description': 'Document report'
    },
    r'.*\.pdf$': {
        'repo': 'life-os',
        'path': 'reports/',
        'description': 'PDF report'
    },
    # Skills
    r'SKILL\.md$': {
        'repo': 'life-os',
        'path': 'skills/',
        'description': 'Skill documentation'
    }
}


class ClaudeAIDeployer:
    """Main deployment orchestrator"""
    
    def __init__(self, outputs_dir: Path = OUTPUTS_DIR):
        self.outputs_dir = outputs_dir
        self.github_token = GITHUB_TOKEN
        self.github_api = GITHUB_API
        self.github_user = GITHUB_USER
        self.deployment_log = []
        
    def scan_outputs(self) -> List[Path]:
        """Scan outputs directory for deployable files"""
        if not self.outputs_dir.exists():
            print(f"⚠️  Outputs directory not found: {self.outputs_dir}")
            return []
        
        files = []
        for item in self.outputs_dir.rglob('*'):
            if item.is_file() and not item.name.startswith('.'):
                files.append(item)
        
        return files
    
    def route_file(self, filepath: Path) -> Optional[Dict]:
        """Determine deployment target for file"""
        filename = filepath.name
        
        for pattern, target in ROUTING_RULES.items():
            if re.match(pattern, filename, re.IGNORECASE):
                return {
                    'repo': target['repo'],
                    'path': target['path'],
                    'description': target['description'],
                    'filename': filename
                }
        
        # Default fallback
        return {
            'repo': 'life-os',
            'path': 'artifacts/',
            'description': 'Unclassified artifact',
            'filename': filename
        }
    
    def encode_file(self, filepath: Path) -> Tuple[str, bool]:
        """Encode file content (Base64 for binary, UTF-8 for text)"""
        try:
            # Try to read as text first
            content = filepath.read_text(encoding='utf-8')
            return content, False  # Not binary
        except UnicodeDecodeError:
            # Binary file - use Base64
            content = filepath.read_bytes()
            encoded = base64.b64encode(content).decode('utf-8')
            return encoded, True  # Is binary
    
    def calculate_checksum(self, filepath: Path) -> str:
        """Calculate SHA256 checksum"""
        sha256 = hashlib.sha256()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b''):
                sha256.update(chunk)
        return sha256.hexdigest()
    
    def create_deployment_manifest(self, filepath: Path, route: Dict, 
                                   content: str, is_binary: bool) -> Dict:
        """Create deployment metadata"""
        checksum = self.calculate_checksum(filepath)
        
        return {
            'source_file': str(filepath),
            'filename': filepath.name,
            'target_repo': route['repo'],
            'target_path': route['path'] + filepath.name,
            'description': route['description'],
            'is_binary': is_binary,
            'checksum': checksum,
            'size_bytes': filepath.stat().st_size,
            'created_at': datetime.utcnow().isoformat() + 'Z',
            'deployed_by': 'claude-ai-deployer',
            'version': '1.0.0'
        }
    
    def push_to_github(self, manifest: Dict, content: str) -> Dict:
        """Push file to GitHub using REST API"""
        repo = manifest['target_repo']
        path = manifest['target_path']
        
        # For now, create the deployment script that will use curl
        # (GitHub REST API via Python requires requests library)
        
        deployment_cmd = self._generate_curl_command(manifest, content)
        
        return {
            'status': 'prepared',
            'repo': repo,
            'path': path,
            'command': deployment_cmd,
            'manifest': manifest
        }
    
    def _generate_curl_command(self, manifest: Dict, content: str) -> str:
        """Generate curl command for GitHub deployment"""
        repo = manifest['target_repo']
        path = manifest['target_path']
        message = f"Deploy: {manifest['filename']} - {manifest['description']}"
        
        # Escape content for JSON
        content_escaped = content.replace('\\', '\\\\').replace('"', '\\"').replace('\n', '\\n')
        
        cmd = f'''curl -X PUT \\
  -H "Authorization: token {self.github_token}" \\
  -H "Accept: application/vnd.github.v3+json" \\
  "{self.github_api}/repos/{self.github_user}/{repo}/contents/{path}" \\
  -d '{{"message": "{message}", "content": "{base64.b64encode(content.encode()).decode()}", "branch": "main"}}'
'''
        
        return cmd
    
    def deploy_file(self, filepath: Path) -> Dict:
        """Complete deployment pipeline for single file"""
        print(f"\n📦 Processing: {filepath.name}")
        
        # Route file
        route = self.route_file(filepath)
        print(f"   → Target: {route['repo']}/{route['path']}")
        
        # Encode content
        content, is_binary = self.encode_file(filepath)
        print(f"   → Encoded: {'Binary (Base64)' if is_binary else 'Text (UTF-8)'}")
        
        # Create manifest
        manifest = self.create_deployment_manifest(filepath, route, content, is_binary)
        print(f"   → Checksum: {manifest['checksum'][:8]}...")
        
        # Push to GitHub
        result = self.push_to_github(manifest, content)
        print(f"   → Status: {result['status'].upper()}")
        
        self.deployment_log.append({
            'filepath': str(filepath),
            'manifest': manifest,
            'result': result,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        })
        
        return result
    
    def deploy_all(self) -> List[Dict]:
        """Deploy all files in outputs directory"""
        files = self.scan_outputs()
        
        if not files:
            print("✅ No files to deploy")
            return []
        
        print(f"\n🚀 Claude AI Auto-Deploy System v1.0.0")
        print(f"📁 Found {len(files)} file(s) to deploy\n")
        
        results = []
        for filepath in files:
            try:
                result = self.deploy_file(filepath)
                results.append(result)
            except Exception as e:
                print(f"❌ Failed to deploy {filepath.name}: {str(e)}")
                results.append({
                    'status': 'failed',
                    'error': str(e),
                    'filepath': str(filepath)
                })
        
        return results
    
    def generate_deployment_report(self) -> str:
        """Generate deployment summary report"""
        total = len(self.deployment_log)
        prepared = sum(1 for log in self.deployment_log 
                      if log['result']['status'] == 'prepared')
        failed = sum(1 for log in self.deployment_log 
                    if log['result']['status'] == 'failed')
        
        report = f"""
╔══════════════════════════════════════════════════════════════╗
║            CLAUDE AI AUTO-DEPLOY REPORT                      ║
╚══════════════════════════════════════════════════════════════╝

Timestamp: {datetime.utcnow().isoformat()}Z
Total Files: {total}
Prepared: {prepared}
Failed: {failed}

Deployments:
"""
        
        for log in self.deployment_log:
            manifest = log['manifest']
            result = log['result']
            status_icon = "✅" if result['status'] == 'prepared' else "❌"
            
            report += f"""
{status_icon} {manifest['filename']}
   Repo: {manifest['target_repo']}
   Path: {manifest['target_path']}
   Size: {manifest['size_bytes']:,} bytes
   Checksum: {manifest['checksum'][:16]}...
"""
        
        return report
    
    def save_deployment_log(self, output_path: Path):
        """Save deployment log to JSON file"""
        log_data = {
            'version': '1.0.0',
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'total_deployments': len(self.deployment_log),
            'deployments': self.deployment_log
        }
        
        output_path.write_text(json.dumps(log_data, indent=2))
        print(f"\n💾 Deployment log saved: {output_path}")


def main():
    """Main execution"""
    deployer = ClaudeAIDeployer()
    
    # Deploy all files
    results = deployer.deploy_all()
    
    # Generate report
    report = deployer.generate_deployment_report()
    print(report)
    
    # Save log
    log_path = Path('/home/claude/deployment_log.json')
    deployer.save_deployment_log(log_path)
    
    # Save deployment commands script
    commands_path = Path('/home/claude/deploy_commands.sh')
    with open(commands_path, 'w') as f:
        f.write("#!/bin/bash\n\n")
        f.write("# Claude AI Auto-Deploy Commands\n")
        f.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n\n")
        
        for log in deployer.deployment_log:
            if log['result']['status'] == 'prepared':
                f.write(log['result']['command'])
                f.write("\n\n")
    
    commands_path.chmod(0o755)
    print(f"📜 Deployment commands saved: {commands_path}")
    
    return results


if __name__ == '__main__':
    main()
