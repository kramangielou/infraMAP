import pytest
from app.services.geo import validate_geometry

def test_valid_point(): validate_geometry({'type':'Point','coordinates':[121,14]})
def test_invalid_polygon():
    with pytest.raises(ValueError): validate_geometry({'type':'Polygon','coordinates':[[[121,14],[122,14],[122,15]]]})
