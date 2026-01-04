#!/usr/bin/env python3
"""
Deployment Verification Script
Verifies that files were successfully deployed to GitHub

Author: Ariel Shapira / BidDeed.AI
Created: 2025-01-03
"""

import json
import sys
import time
from pathlib import Path
from typing import Dict, List
import subprocess


class DeploymentVerifier:
    """Verifies GitHub deployments"""
    
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.log_data = self._load_log()
        self.github_token = 'YOUR_GITHUB_TOKEN_HERE'
        self.github_api = 'https://api.github.com'
        self.github_user = 'breverdbidder'
    
    def _load_log(self) -> Dict:
        """Load deployment log"""
        if not self.log_path.exists():
            print(f"❌ Deployment log not found: {self.log_path}")
            sys.exit(1)
        
        return json.loads(self.log_path.read_text())
    
    def verify_file_exists(self, repo: str, path: str) -> bool:
        """Verify file exists in GitHub repo using curl"""
        url = f"{self.github_api}/repos/{self.github_user}/{repo}/contents/{path}"
        
        cmd = [
            'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
            '-H', f'Authorization: token {self.github_token}',
            '-H', 'Accept: application/vnd.github.v3+json',
            url
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            status_code = result.stdout.strip()
            return status_code == '200'
        except Exception as e:
            print(f"⚠️  Verification error: {str(e)}")
            return False
    
    def verify_all(self) -> Dict:
        """Verify all deployments"""
        print("\n🔍 Verifying Deployments...")
        print("=" * 60)
        
        deployments = self.log_data.get('deployments', [])
        total = len(deployments)
        verified = 0
        failed = 0
        
        results = []
        
        for deployment in deployments:
            manifest = deployment.get('manifest', {})
            filename = manifest.get('filename', 'unknown')
            repo = manifest.get('target_repo', '')
            path = manifest.get('target_path', '')
            
            print(f"\n📄 {filename}")
            print(f"   Repo: {repo}")
            print(f"   Path: {path}")
            
            # Wait 2 seconds between checks (rate limiting)
            time.sleep(2)
            
            exists = self.verify_file_exists(repo, path)
            
            if exists:
                print(f"   Status: ✅ VERIFIED")
                verified += 1
            else:
                print(f"   Status: ❌ NOT FOUND")
                failed += 1
            
            results.append({
                'filename': filename,
                'repo': repo,
                'path': path,
                'verified': exists
            })
        
        print("\n" + "=" * 60)
        print(f"\n📊 Verification Summary")
        print(f"   Total: {total}")
        print(f"   Verified: {verified} ({verified/total*100:.1f}%)")
        print(f"   Failed: {failed} ({failed/total*100:.1f}%)")
        
        return {
            'total': total,
            'verified': verified,
            'failed': failed,
            'success_rate': verified / total if total > 0 else 0,
            'details': results
        }
    
    def save_verification_report(self, results: Dict, output_path: Path):
        """Save verification results"""
        report_data = {
            'timestamp': self.log_data.get('timestamp'),
            'verification_results': results
        }
        
        output_path.write_text(json.dumps(report_data, indent=2))
        print(f"\n💾 Verification report saved: {output_path}")


def main():
    """Main execution"""
    log_path = Path('/home/claude/deployment_log.json')
    
    verifier = DeploymentVerifier(log_path)
    results = verifier.verify_all()
    
    # Save verification report
    report_path = Path('/home/claude/verification_report.json')
    verifier.save_verification_report(results, report_path)
    
    # Exit with error code if any verifications failed
    if results['failed'] > 0:
        sys.exit(1)
    
    print("\n✅ All deployments verified successfully")
    sys.exit(0)


if __name__ == '__main__':
    main()
