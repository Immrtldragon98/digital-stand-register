"""Write outcome and its receipt commit together, scoped to the authenticated user."""
import hashlib
import json
import re
from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from app.models.command_receipt import CommandReceipt


def command_result(db, user_id, request_key):
    receipt = db.query(CommandReceipt).filter_by(user_id=user_id, request_key=request_key).first()
    if receipt is None or receipt.response is None:
        raise HTTPException(404, 'No completed command found.')
    return receipt.response


def run_command(db, user_id, request_key, scope, payload, action):
    if request_key is not None and not re.fullmatch(r'[A-Za-z0-9_-]{16,128}', request_key):
        raise HTTPException(400, 'Invalid Idempotency-Key.')
    normalized = json.dumps(jsonable_encoder({'scope': scope, 'payload': payload}), sort_keys=True, separators=(',', ':'))
    fingerprint = hashlib.sha256(normalized.encode()).hexdigest()
    try:
        if request_key:
            if db.get_bind().dialect.name == 'postgresql':
                lock = int.from_bytes(hashlib.sha256(f'{user_id}:{request_key}'.encode()).digest()[:8], 'big', signed=True)
                db.execute(text('SELECT pg_advisory_xact_lock(:key)'), {'key': lock})
            receipt = db.query(CommandReceipt).filter_by(user_id=user_id, request_key=request_key).with_for_update().first()
            if receipt:
                if receipt.request_hash != fingerprint:
                    raise HTTPException(409, 'This request key was already used for a different operation.')
                if receipt.response is None:
                    raise HTTPException(409, 'Command is processing; check its status before retrying.')
                return receipt.response
            receipt = CommandReceipt(user_id=user_id, request_key=request_key, request_hash=fingerprint, scope=scope)
            db.add(receipt); db.flush()
        result = jsonable_encoder(action())
        if request_key:
            receipt.response = result
        db.commit()
        return result
    except IntegrityError as exc:
        db.rollback()
        raise HTTPException(409, 'Operation conflicted with another update. Refresh before retrying.') from exc
    except Exception:
        db.rollback()
        raise
