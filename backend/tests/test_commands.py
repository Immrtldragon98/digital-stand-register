import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from fastapi import HTTPException
import app.models
from app.database.session import Base
from app.models.user import User
from app.models.inventory_item import InventoryItem
from app.models.command_receipt import CommandReceipt
from app.services.command_service import run_command,command_result


def test_atomic_receipt_replay_and_rollback():
    engine=create_engine('sqlite:///:memory:');Base.metadata.create_all(engine)
    with Session(engine) as db:
        db.add(User(id=1,username='admin',hashed_password='test',role_id=1));db.commit()
        calls=[]
        def save():
            calls.append(1);db.add(InventoryItem(name='Bearing',quantity=2));return {'ok':True}
        key='change-test-00000001'
        assert run_command(db,1,key,'CHANGE',{},save)=={'ok':True}
        assert run_command(db,1,key,'CHANGE',{},save)=={'ok':True}
        assert len(calls)==1
        with pytest.raises(HTTPException):run_command(db,1,key,'CHANGE',{'different':True},save)
        with pytest.raises(HTTPException):command_result(db,2,key)
        def fail():
            db.add(InventoryItem(name='Seal',quantity=1));db.flush();raise HTTPException(400,'Invalid')
        with pytest.raises(HTTPException):run_command(db,1,'change-test-00000002','CHANGE',{},fail)
        assert db.query(InventoryItem).count()==1
        assert db.query(CommandReceipt).count()==1
