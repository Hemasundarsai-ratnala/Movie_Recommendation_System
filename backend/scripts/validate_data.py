import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(BASE_DIR))

from backend.app.config import settings
from backend.app.utils.validation import validate_datasets, format_validation_report

def main():
    print("Starting data validation checks...")
    report = validate_datasets(settings.MOVIES_CSV, settings.RATINGS_CSV)
    print(format_validation_report(report))
    print("Data validation completed successfully.")

if __name__ == "__main__":
    main()
