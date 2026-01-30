"""
Download Kaggle Customer Support Ticket Dataset
"""
import kagglehub
import shutil
from pathlib import Path


def download_dataset():
    """Download the customer support ticket dataset from Kaggle."""
    print("📥 Downloading Kaggle customer support ticket dataset...")
    
    try:
        # Download latest version
        path = kagglehub.dataset_download("suraj520/customer-support-ticket-dataset")
        print(f"✓ Downloaded to: {path}")
        
        # Setup target directory
        dataset_path = Path(path)
        target_path = Path("data/kaggle")
        target_path.mkdir(parents=True, exist_ok=True)
        
        # Copy CSV files to project directory
        csv_files = list(dataset_path.glob("*.csv"))
        
        if not csv_files:
            print("⚠️  No CSV files found in downloaded dataset")
            return None
        
        for csv_file in csv_files:
            target_file = target_path / csv_file.name
            shutil.copy(csv_file, target_file)
            print(f"✓ Copied: {csv_file.name}")
        
        print(f"\n✅ Dataset ready at: {target_path.absolute()}")
        return target_path
        
    except Exception as e:
        print(f"\n❌ Error downloading dataset: {e}")
        print("\nMake sure you have:")
        print("1. Kaggle API credentials configured (~/.kaggle/kaggle.json)")
        print("2. Internet connection")
        print("3. Accepted the dataset terms on Kaggle website")
        return None


if __name__ == "__main__":
    download_dataset()
