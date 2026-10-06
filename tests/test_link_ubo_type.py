from copy import deepcopy
from pathlib import Path

import pytest
import yaml
from openapi_schema_validator import OAS30Validator


@pytest.fixture(scope="module")
def spec():
    return yaml.safe_load((Path(__file__).parents[1] / "openapi.yaml").read_text())


def check(spec, schema):
    return OAS30Validator({**schema, "components": spec["components"]})


LINKS = "/v1.1/business-relations/{crmCode}/links"


@pytest.mark.parametrize("value,valid", [
    ("DIRECT", True), ("INDIRECT", True), ("BOTH", True), (None, True),
    ("Direct", False), ("direct", False), ("", False), ("UNKNOWN", False),
    (1, False), (True, False), (["DIRECT"], False),
])
def test_optional_ubo_type_input(spec, value, valid):
    base = spec["components"]["schemas"]["BusinessRelationLink"]
    payload = {"linkedCrmCode": "UBO001", "role": "Beneficial owner", "uboType": value}
    assert check(spec, base).is_valid(payload) == valid
    field = base["properties"]["uboType"]
    assert "uboType" not in base["required"]
    assert "default" not in field
    assert not field.get("readOnly", False)
    check(spec, base).validate({"linkedCrmCode": "UBO001", "role": "Beneficial owner"})


def test_ubo_examples_round_trip_and_omit_unset_response_type(spec):
    operations = spec["paths"][LINKS]
    request = operations["post"]["requestBody"]["content"]["application/json"]
    created = operations["post"]["responses"]["201"]["content"]["application/json"]["schema"]
    get = operations["get"]["responses"]["200"]["content"]["application/json"]
    check(spec, request["schema"]).validate(request["example"])
    check(spec, created).validate(created["example"])
    check(spec, get["schema"]).validate(get["examples"]["beneficialOwners"]["value"])
    incoming = {x["linkedCrmCode"]: x for x in request["example"]}
    for link in created["example"]["linksCreated"]:
        value = incoming[link["linkedCrmCode"]].get("uboType")
        if value is None:
            assert "uboType" not in link
        else:
            assert link["uboType"] == value
    links = get["examples"]["beneficialOwners"]["value"]["links"]
    assert {x["uboType"] for x in links if "uboType" in x} == {"DIRECT", "INDIRECT", "BOTH"}
    assert "uboType" not in links[-1]
    invalid = deepcopy(get["examples"]["beneficialOwners"]["value"])
    invalid["links"][0]["uboType"] = "Direct"
    assert not check(spec, get["schema"]).is_valid(invalid)


def test_delete_contract_does_not_add_ubo_type(spec):
    schema = spec["components"]["schemas"]["BusinessRelationLinkDeleteRequest"]
    assert set(schema["items"]["properties"]) == {"linkedCrmCode", "role"}
    assert spec["paths"][LINKS]["delete"]["requestBody"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/BusinessRelationLinkDeleteRequest"
    }
