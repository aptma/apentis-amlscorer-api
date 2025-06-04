import pytest

yaml = pytest.importorskip('yaml')
openapi_spec_validator = pytest.importorskip('openapi_spec_validator')
from openapi_spec_validator import validate_spec


def test_openapi_yaml_validates():
    with open('openapi.yaml', 'r') as f:
        spec = yaml.safe_load(f)
    # validate_spec raises an exception if the spec is invalid
    validate_spec(spec)
