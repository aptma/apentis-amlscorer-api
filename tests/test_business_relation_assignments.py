from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")
openapi_schema_validator = pytest.importorskip("openapi_schema_validator")
OAS30Validator = openapi_schema_validator.OAS30Validator


@pytest.fixture(scope="module")
def specification():
  return yaml.safe_load(
    (Path(__file__).parents[1] / "openapi.yaml").read_text(encoding="utf-8")
  )


def validator_for(specification, schema):
  return OAS30Validator({**schema, "components": specification["components"]})


def response_media(specification, path):
  response = specification["paths"][path]["get"]["responses"]["200"]
  return response["content"]["application/json"]


def request_media(specification, path, method):
  request = specification["paths"][path][method]["requestBody"]
  return request["content"]["application/json"]


def validate_relation_example(specification, example):
  # Validate concrete types; the existing union has no discriminator mapping for Person/Company.
  schema_name = "PersonBusinessRelation" if example["type"] == "Person" else "CompanyBusinessRelation"
  schema = specification["components"]["schemas"][schema_name]
  errors = list(validator_for(specification, schema).iter_errors(example))
  assert not errors, [error.message for error in errors]


@pytest.mark.parametrize("relation_type", ["PersonBusinessRelation", "CompanyBusinessRelation"])
@pytest.mark.parametrize(
  "field,value,is_valid",
  [
    ("relationshipManager", "user-active", True),
    ("relationshipManager", None, True),
    ("relationshipManager", "", False),
    ("relationshipManager", " \t", False),
    ("relationshipManager", ["user-active"], False),
    ("clientGroups", ["group-active"], True),
    ("clientGroups", ["group-active", "group-active"], True),
    ("clientGroups", [], True),
    ("clientGroups", None, True),
    ("clientGroups", [None], False),
    ("clientGroups", [""], False),
    ("clientGroups", [" \t"], False),
    ("clientGroups", "group-active", False),
  ],
)
def test_assignment_field_schemas(specification, relation_type, field, value, is_valid):
  schema = specification["components"]["schemas"][relation_type]["properties"][field]
  assert validator_for(specification, schema).is_valid(value) == is_valid


def test_schema_config_examples_use_id_name_values(specification):
  media = response_media(specification, "/v1.1/business-relations/schema-config")
  validator = validator_for(specification, media["schema"])
  for example in media["examples"].values():
    validator.validate(example["value"])
  invalid_metadata = {
    "fields": {"relationshipManager": {"type": "string", "values": ["user-active"]}}
  }
  assert not validator.is_valid(invalid_metadata)


def test_assignment_request_examples_validate_fields(specification):
  properties = specification["components"]["schemas"]["PersonBusinessRelation"]["properties"]
  operations = [
    ("/v1.1/business-relations", "post"),
    ("/v1.1/business-relations/{crmCode}", "put"),
  ]
  for path, method in operations:
    media = request_media(specification, path, method)
    for example in media["examples"].values():
      for field in ("relationshipManager", "clientGroups"):
        if field in example["value"]:
          validator_for(specification, properties[field]).validate(example["value"][field])


def test_new_create_examples_validate_complete_payloads(specification):
  media = request_media(specification, "/v1.1/business-relations", "post")
  for name in ("companyAssignments", "unassigned"):
    validate_relation_example(specification, media["examples"][name]["value"])


def test_new_get_examples_validate_both_list_shapes(specification):
  media = response_media(specification, "/v1.1/business-relations")
  validator = validator_for(specification, media["schema"])
  unpaginated = media["examples"]["unpaginatedAssignments"]["value"]
  for example in unpaginated:
    validate_relation_example(specification, example)
  validator.validate({"businessRelations": []})
  validator.validate({"businessRelations": [], "nextCursor": "example-cursor"})
  validator.validate([])
  assert not validator.is_valid({"nextCursor": "cursor-without-relations"})
  single_media = response_media(specification, "/v1.1/business-relations/{crmCode}")
  for name in ("unassigned", "clientGroupsDisabled"):
    validate_relation_example(specification, single_media["examples"][name]["value"])


def test_examples_distinguish_selectable_values_and_historical_assignments(specification):
  schema_examples = response_media(specification, "/v1.1/business-relations/schema-config")["examples"]
  fields = schema_examples["clientGroupsEnabled"]["value"]["fields"]
  selectable_managers = {value["id"] for value in fields["relationshipManager"]["values"]}
  selectable_groups = {value["id"] for value in fields["clientGroups"]["values"]}
  get_examples = response_media(specification, "/v1.1/business-relations/{crmCode}")["examples"]
  historical = get_examples["historicalAssignments"]["value"]
  assert historical["relationshipManager"] not in selectable_managers
  assert set(historical["clientGroups"]) - selectable_groups

  put_media = request_media(specification, "/v1.1/business-relations/{crmCode}", "put")
  retained = put_media["examples"]["retainInactiveAssignments"]["value"]
  assert retained["relationshipManager"] == historical["relationshipManager"]
  assert set(historical["clientGroups"]) < set(retained["clientGroups"])
  assert set(retained["clientGroups"]) - set(historical["clientGroups"]) <= selectable_groups

  assert "clientGroups" not in schema_examples["clientGroupsDisabled"]["value"]["fields"]
  assert "clientGroups" not in get_examples["clientGroupsDisabled"]["value"]
  assert "relationshipManager" not in get_examples["unassigned"]["value"]
  assert get_examples["unassigned"]["value"]["clientGroups"] == []
  assert schema_examples["noActiveValues"]["value"]["fields"]["clientGroups"]["values"] == []
