import os
import django
import sys
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.cases.models import Case, Evidence, AuditLog
from apps.preservation.blockchain import BlockchainAnchorService
from apps.preservation.middleware import _thread_locals

def verify_preservation_pillar():
    User = get_user_model()
    # Mock a logged in user via thread locals
    admin_user = User.objects.first()
    _thread_locals.user = admin_user
    
    print("1. Testing Automatic Chain of Custody Logging...")
    # Create Case -> Should trigger log
    case = Case.objects.create(name="Preservation Test Case", created_by=admin_user)
    print(f"   Created Case: {case.id}")
    
    # Create Evidence -> Should trigger log
    evidence = Evidence.objects.create(
        case=case,
        name="Tampered File.txt",
        source_type="disk",
        file_path="/tmp/test.txt",
        size_bytes=123,
        acquired_by=admin_user
    )
    print(f"   Created Evidence: {evidence.id}")
    
    # Verify Logs
    logs = AuditLog.objects.filter(case=case).order_by('timestamp')
    print(f"   Found {logs.count()} Audit Logs.")
    if logs.count() >= 2:
        print("   ✅ Automatic logging working.")
    else:
        print("   ❌ Automatic logging FAILED.")
        return

    print("\n2. Testing Tamper-Evident Chaining...")
    prev_log = None
    chain_valid = True
    for log in logs:
        print(f"   Log {log.id}: {log.action}")
        print(f"     Hash: {log.hash[:16]}...")
        if prev_log:
            print(f"     Prev: {log.prev_hash[:16]}...")
            if log.prev_hash != prev_log.hash:
                chain_valid = False
                print("     ❌ BROKEN CHAIN DETECTED.")
        prev_log = log
        
    if chain_valid:
        print("   ✅ Log chain is valid.")
        
    print("\n3. Testing Blockchain Anchoring...")
    result = BlockchainAnchorService.anchor_logs()
    print(f"   {result}")
    
    # Verify Ledger
    if BlockchainAnchorService.verify_chain():
         print("   ✅ Blockchain Ledger is valid.")
    else:
         print("   ❌ Blockchain Ledger CORRUPTED.")
         
    # Check if logs are marked
    anchored_logs = AuditLog.objects.filter(case=case, blockchain_tx_id__isnull=False)
    if anchored_logs.count() == logs.count():
         print("   ✅ All logs successfully anchored.")
    else:
         print(f"   ❌ Only {anchored_logs.count()} logs anchored.")

if __name__ == "__main__":
    verify_preservation_pillar()
