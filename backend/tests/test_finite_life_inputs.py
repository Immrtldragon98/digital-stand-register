import pytest
from app.api.routes.stands import CreateStandSchema, ComponentItemInput
from app.schemas.inventory import InventoryCreate, InventoryUpdate

@pytest.mark.parametrize('value', [float('inf'), float('nan')])
def test_nonfinite_life_inputs_are_rejected(value):
    cases = [
        (CreateStandSchema, {'code':'1A','initial_life_hours':value}),
        (ComponentItemInput, {'component_type_id':1,'carried_life_hours':value}),
        (InventoryCreate, {'name':'Bearing','expected_life_hours':value}),
        (InventoryUpdate, {'observed_avg_life_hours':value}),
    ]
    for schema, data in cases:
        with pytest.raises(ValueError):
            schema(**data)
