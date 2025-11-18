#!/usr/bin/env python3
"""
BCE Data Validation Script

Runs comprehensive validation checks on all BCE data files.
Used by CI/CD pipeline and can be run locally.
"""

import sys
from bce.validation import validate_all


def main():
    """Run all validation checks and report results."""
    print('=' * 60)
    print('BCE Data Validation')
    print('=' * 60)

    errors = validate_all()

    if errors:
        print(f'\n❌ {len(errors)} validation error(s):')
        for err in errors:
            print(f'  - {err}')
        sys.exit(1)
    else:
        print('\n✅ All validation checks passed')
        print('\nVerified:')
        print('  - Character files')
        print('  - Event files')
        print('  - Cross-references')
        sys.exit(0)


if __name__ == '__main__':
    main()
