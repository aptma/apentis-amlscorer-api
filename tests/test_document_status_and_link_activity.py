from copy import deepcopy
from datetime import date
from pathlib import Path

import pytest
import yaml
from openapi_schema_validator import OAS30Validator, OAS30ReadValidator


@pytest.fixture(scope="module")
def spec():
    return yaml.safe_load((Path(__file__).parents[1] / "openapi.yaml").read_text())


def media(spec, path):
    return spec["paths"][path]["get"]["responses"]["200"]["content"]["application/json"]


def validator(spec, schema):
    return OAS30ReadValidator(
        {**schema, "components": spec["components"]},
        format_checker=OAS30Validator.FORMAT_CHECKER,
    )


DOCUMENTS = "/v1.1/business-relations/{crmCode}/documents"
LINKS = "/v1.1/business-relations/{crmCode}/links"


@pytest.mark.parametrize("path", [DOCUMENTS, DOCUMENTS + "/metadata-only"])
def test_document_response_status_contract(spec, path):
    response = media(spec, path)
    check = validator(spec, response["schema"])
    check.validate(response["example"])
    document = deepcopy(response["example"][0])
    for status in ["pending", "validated", "rejected", "archived"]:
        document["documentStatusId"] = status
        check.validate([document])
    for invalid in [None, "Validated", "unknown", True]:
        document["documentStatusId"] = invalid
        assert not check.is_valid([document])
    del document["documentStatusId"]
    assert not check.is_valid([document])
    check.validate([])
    status = spec["components"]["schemas"]["DocumentMetadataResponse"]["allOf"][1]["properties"]["documentStatusId"]
    assert status["readOnly"] is True


def test_document_post_schemas_do_not_expose_status(spec):
    metadata = spec["components"]["schemas"]["DocumentMetadata"]
    assert "documentStatusId" not in metadata["properties"]
    post = spec["paths"][DOCUMENTS + "/metadata-only"]["post"]
    request = post["requestBody"]["content"]["application/json"]
    assert request["schema"] == {"$ref": "#/components/schemas/DocumentMetadata"}
    validator(spec, request["schema"]).validate(request["example"])
    upload = spec["paths"][DOCUMENTS]["post"]["requestBody"]["content"]["multipart/form-data"]["schema"]
    assert "documentStatusId" not in upload["properties"]
    assert "DocumentMetadataResponse" not in str(upload)


def test_optional_activity_filter(spec):
    get = spec["paths"][LINKS]["get"]
    parameter = next(p for p in get["parameters"] if p["name"] == "isActive")
    assert parameter["in"] == "query"
    assert parameter["required"] is False
    assert parameter["allowEmptyValue"] is False
    assert parameter["schema"] == {"type": "boolean"}
    check = validator(spec, parameter["schema"])
    for value in [True, False]:
        check.validate(value)
    for value in ["", "true", 1, None]:
        assert not check.is_valid(value)
    assert get["responses"]["400"]["content"]["application/json"]["schema"] == {
        "$ref": "#/components/schemas/ErrorResponse"
    }


def test_link_examples_validate_and_match_documented_classification(spec):
    response = media(spec, LINKS)
    check = validator(spec, response["schema"])
    today = date(2026, 10, 5)  # Explicit reference date in the example summaries.
    for name, example in response["examples"].items():
        check.validate(example["value"])
        for link in example["value"]["links"]:
            start = date.fromisoformat(link["startDate"]) if link["startDate"] else None
            end = date.fromisoformat(link["endDate"]) if link["endDate"] else None
            active = (end is None or end > today) and (start is None or end is None or start < end)
            assert link["isActive"] == active
            if name == "activeLinks":
                assert active
            elif name == "historicalLinks":
                assert not active
    periods = response["examples"]["allLinks"]["value"]["links"]
    assert periods[0]["linkedCrmCode"] == periods[1]["linkedCrmCode"]
    assert periods[0]["role"] == periods[1]["role"]
    assert periods[0]["startDate"] != periods[1]["startDate"]


@pytest.mark.parametrize("field,value", [
    ("isActive", "true"), ("isActive", None), ("isActive", 1),
    ("startDate", "2026-13-01"), ("startDate", "2026-10-05T00:00:00Z"),
    ("endDate", "2026-02-30"), ("endDate", 20261005),
])
def test_invalid_link_response_fields(spec, field, value):
    response = media(spec, LINKS)
    payload = deepcopy(response["examples"]["allLinks"]["value"])
    payload["links"][0][field] = value
    assert not validator(spec, response["schema"]).is_valid(payload)


@pytest.mark.parametrize("field", ["isActive", "startDate", "endDate"])
def test_link_response_fields_required_and_read_only(spec, field):
    response = media(spec, LINKS)
    payload = deepcopy(response["examples"]["allLinks"]["value"])
    del payload["links"][0][field]
    assert not validator(spec, response["schema"]).is_valid(payload)
    schema = spec["components"]["schemas"]["BusinessRelationLinkResponse"]["allOf"][1]
    assert schema["properties"][field]["readOnly"] is True


def test_link_write_contracts_use_existing_schemas(spec):
    operations = spec["paths"][LINKS]
    base = spec["components"]["schemas"]["BusinessRelationLink"]
    assert set(base["properties"]) == {"linkedCrmCode", "role", "uboType"}
    assert "uboType" not in base["required"]
    assert base["properties"]["uboType"]["nullable"] is True
    assert base["properties"]["uboType"]["enum"] == ["DIRECT", "INDIRECT", "BOTH", None]
    link = {"linkedCrmCode": "QA12375", "role": "Beneficial owner"}
    check = validator(spec, base)
    check.validate(link)
    for ubo_type in ["DIRECT", "INDIRECT", "BOTH", None]:
        check.validate({**link, "uboType": ubo_type})
    for ubo_type in ["INVALID", "direct", "", True, 1]:
        assert not check.is_valid({**link, "uboType": ubo_type})
    post = operations["post"]
    request = post["requestBody"]["content"]["application/json"]
    assert request["schema"]["items"] == {"$ref": "#/components/schemas/BusinessRelationLink"}
    validator(spec, request["schema"]).validate(request["example"])
    created = post["responses"]["201"]["content"]["application/json"]["schema"]
    assert created["properties"]["linksCreated"]["items"] == request["schema"]["items"]
    validator(spec, created).validate(created["example"])
    delete = operations["delete"]["requestBody"]["content"]["application/json"]
    assert delete["schema"] == {"$ref": "#/components/schemas/BusinessRelationLinkDeleteRequest"}
    for example in delete["examples"].values():
        validator(spec, delete["schema"]).validate(example["value"])
    assert all(p["name"] != "isActive" for method in ["post", "delete"] for p in operations[method]["parameters"])
