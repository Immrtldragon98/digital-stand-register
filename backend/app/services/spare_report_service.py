"""Read-only presentation of imported consumption and receipt evidence."""
from copy import deepcopy


def present_spare_report(payload):
    report = deepcopy(payload)
    report['available'] = True
    for plan in report.get('plans', []):
        for row in plan['rows']:
            target, received = row.get('monthly_target'), row['received']
            # Blank requirements are unknown; receipt coverage is not warehouse stock.
            row['still_to_receive'] = None if target is None else max(target - received, 0)
            row['extra_received'] = None if target is None else max(received - target, 0)
            row['stock_balance'] = None
    return report
