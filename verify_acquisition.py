import os
import django
import hashlib
from django.conf import settings

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.cases.models import Case, Evidence
from apps.acquisition.models import AcquisitionTask
from apps.acquisition.physical import PhysicalImager

def create_dummy_source(path, size_mb=10):
    print(f"Creating dummy source file at {path} ({size_mb} MB)...")
    data = os.urandom(1024 * 1024) # 1MB random data
    
    md5 = hashlib.md5()
    sha256 = hashlib.sha256()
    
    with open(path, 'wb') as f:
        for _ in range(size_mb):
            f.write(data)
            md5.update(data)
            sha256.update(data)
            
    return md5.hexdigest(), sha256.hexdigest()

def verify_acquisition():
    # 1. Setup Data using default admin
    User = get_user_model()
    # Ensure admin exists or get first user
    user = User.objects.first()
    if not user:
        user = User.objects.create_superuser('admin', 'admin@example.com', 'admin')

    case = Case.objects.create(name="Verification Case", created_by=user)
    
    # 2. Prepare Source
    source_path = '/tmp/dummy_disk.raw'
    expected_md5, expected_sha256 = create_dummy_source(source_path)
    print(f"Source Hashes:\nMD5: {expected_md5}\nSHA256: {expected_sha256}")
    
    # 3. Create Task
    dest_path = '/tmp/acquired_image.dd'
    evidence = Evidence.objects.create(
        case=case, 
        name="Test Disk", 
        source_type="disk", 
        file_path=dest_path, 
        size_bytes=0, 
        acquired_by=user
    )
    
    task = AcquisitionTask.objects.create(
        evidence=evidence,
        type='disk_physical',
        source_path=source_path,
        destination_path=dest_path,
        created_by=user
    )
    
    # 4. Run Imager
    print("\nStarting PhysicalImager...")
    imager = PhysicalImager(task)
    success = imager.acquire()
    
    if not success:
        print("❌ Acquisition failed!")
        print(task.error_message)
        return
        
    # 5. Verify
    task.refresh_from_db()
    evidence.refresh_from_db()
    
    print("\nAcquisition Results:")
    print(f"Status: {task.status}")
    print(f"Calculated MD5: {task.calculated_md5}")
    print(f"Calculated SHA256: {task.calculated_sha256}")
    
    if task.calculated_md5 == expected_md5 and task.calculated_sha256 == expected_sha256:
        print("✅ SUCCESS: Hashes match!")
    else:
        print("❌ FAILURE: Hash mismatch!")

if __name__ == "__main__":
    verify_acquisition()
