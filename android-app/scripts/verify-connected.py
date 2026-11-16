"""Check the connected-mode acceptance result and that PostgreSQL holds what the phone says it sent."""
import json
import sys
from pathlib import Path

import psycopg

result = json.loads((Path(sys.argv[1]) / 'result.json').read_text())
assert result['success'], result
with psycopg.connect(sys.argv[2]) as db:
    one = lambda sql: db.execute(sql).fetchone()[0]
    assert one('SELECT count(*) FROM accounts') == 2
    assert one("SELECT count(*) FROM bank_accounts WHERE revoked_at IS NULL") == 2
    assert one("SELECT amount_cents FROM payments WHERE status = 'captured'") == 860
    assert one("SELECT amount_cents FROM payouts WHERE status = 'paid'") == 731
    assert one('SELECT sum(debit_cents) - sum(credit_cents) FROM ledger_entries') == 0
    assert one("SELECT sum(debit_cents) - sum(credit_cents) FROM ledger_entries WHERE account = 'bank:clearing'") == 129
print(result['detail'], '· PostgreSQL: 2 accounts, 1 captured payment (860), 1 payout (731), ledger balanced')
