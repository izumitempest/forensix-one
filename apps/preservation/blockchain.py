import hashlib
import json
import os
import time
from django.conf import settings
from apps.cases.models import AuditLog

class BlockchainAnchorService:
    """
    Pillar 2: Blockchain Anchoring (Mock)
    Simulates anchoring forensic audit logs to a public blockchain.
    """
    
    LEDGER_FILE = os.path.join(settings.BASE_DIR, 'blockchain_ledger.json')

    @staticmethod
    def get_latest_block():
        if not os.path.exists(BlockchainAnchorService.LEDGER_FILE):
            return None
        
        try:
            with open(BlockchainAnchorService.LEDGER_FILE, 'r') as f:
                chain = json.load(f)
                return chain[-1] if chain else None
        except Exception:
            return None

    @staticmethod
    def anchor_logs():
        """
        Gathers all unanchored audit logs and commits them to a new block.
        """
        unanchored_logs = AuditLog.objects.filter(blockchain_tx_id__isnull=True).order_by('timestamp')
        
        if not unanchored_logs.exists():
            return "No logs to anchor"

        latest_block = BlockchainAnchorService.get_latest_block()
        prev_hash = latest_block['hash'] if latest_block else "0" * 64
        
        # Merkle Tree Root Simulation
        # Just hashing all log hashes together for simplicity
        combined_hash = hashlib.sha256()
        log_ids = []
        
        for log in unanchored_logs:
            combined_hash.update(log.hash.encode())
            log_ids.append(str(log.id))
            
        merkle_root = combined_hash.hexdigest()
        
        # Create Block
        block = {
            'index': (latest_block['index'] + 1) if latest_block else 0,
            'timestamp': time.time(),
            'prev_hash': prev_hash,
            'merkle_root': merkle_root,
            'log_count': len(log_ids)
        }
        
        # Compute Block Hash
        block_content = f"{block['index']}{block['timestamp']}{block['prev_hash']}{block['merkle_root']}"
        block['hash'] = hashlib.sha256(block_content.encode()).hexdigest()
        
        # Save to Ledger
        BlockchainAnchorService._append_to_chain(block)
        
        # Update Logs with "Transaction ID" (the block hash)
        unanchored_logs.update(blockchain_tx_id=block['hash'])
        
        return f"Anchored {len(log_ids)} logs to block {block['index']} (Hash: {block['hash']})"

    @staticmethod
    def _append_to_chain(block):
        chain = []
        if os.path.exists(BlockchainAnchorService.LEDGER_FILE):
            try:
                with open(BlockchainAnchorService.LEDGER_FILE, 'r') as f:
                    chain = json.load(f)
            except:
                pass
                
        chain.append(block)
        
        with open(BlockchainAnchorService.LEDGER_FILE, 'w') as f:
            json.dump(chain, f, indent=2)

    @staticmethod
    def verify_chain():
        """Verifies the integrity of the local blockchain ledger"""
        if not os.path.exists(BlockchainAnchorService.LEDGER_FILE):
            return True # Empty is valid
            
        with open(BlockchainAnchorService.LEDGER_FILE, 'r') as f:
            chain = json.load(f)
            
        for i in range(1, len(chain)):
            current = chain[i]
            previous = chain[i-1]
            
            if current['prev_hash'] != previous['hash']:
                return False
                
            # Recompute hash check
            content = f"{current['index']}{current['timestamp']}{current['prev_hash']}{current['merkle_root']}"
            if hashlib.sha256(content.encode()).hexdigest() != current['hash']:
                return False
                
        return True
