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
  schema = specification["components"]["schemas"]["BusinessRelation"]
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
  validator = validator_for(specification, media["schema"])
  for name, example in media["examples"].items():
    errors = list(validator.iter_errors(example["value"]))
    assert not errors, (name, [error.message for error in errors])


def test_update_examples_validate_complete_operation_contract(specification):
  media = request_media(specification, "/v1.1/business-relations/{crmCode}", "put")
  validator = validator_for(specification, media["schema"])
  for name, example in media["examples"].items():
    errors = list(validator.iter_errors(example["value"]))
    assert not errors, (name, [error.message for error in errors])
  validator.validate({})


@pytest.mark.parametrize("payload,is_valid", [
  ({"type": "Person", "relationshipManager": "user-active"}, True),
  ({"type": "Company", "clientGroups": ["group-active"]}, True),
  ({"type": "Trust", "clientGroups": None}, True),
  ({"type": "Unknown"}, False),
  ({"firstName": "Updated"}, True),
  ({"firstName": []}, False),
  ({"name": "Updated company"}, True),
  ({"name": []}, False),
  ({"incorporationDate": []}, False),
  ({"relationshipManager": []}, False),
  ({"relationshipManager": " "}, False),
  ({"clientGroups": "group-active"}, False),
  ({"clientGroups": [None]}, False),
  ({"clientGroups": [""]}, False),
])
def test_partial_update_preserves_field_validation(specification, payload, is_valid):
  media = request_media(specification, "/v1.1/business-relations/{crmCode}", "put")
  assert validator_for(specification, media["schema"]).is_valid(payload) == is_valid


@pytest.mark.parametrize("schema_name", ["PersonBusinessRelation", "CompanyBusinessRelation"])
def test_create_schema_still_requires_identity_fields(specification, schema_name):
  schema = specification["components"]["schemas"][schema_name]
  assert not validator_for(specification, schema).is_valid({"clientGroups": []})


def test_discriminator_covers_existing_business_relation_types(specification):
  schemas = specification["components"]["schemas"]
  request_validator = validator_for(specification, schemas["BusinessRelation"])
  response_validator = validator_for(specification, schemas["BusinessRelationResponse"])
  for schema_name in ["PersonBusinessRelation", "CompanyBusinessRelation"]:
    for relation_type in schemas[schema_name]["properties"]["type"]["enum"]:
      relation = {"type": relation_type, "crmCode": "EXAMPLE", "name": "Example"}
      if schema_name == "PersonBusinessRelation":
        relation.update(firstName="Example", lastName="Person")
      request_validator.validate(relation)
      response_validator.validate(relation)


@pytest.mark.parametrize("relation_type", ["Person", "Company"])
@pytest.mark.parametrize("field,value,is_valid", [
  ("relationshipManager", "user-active", True),
  ("relationshipManager", None, False),
  ("clientGroups", [], True),
  ("clientGroups", ["group-active", "group-inactive"], True),
  ("clientGroups", None, False),
  ("clientGroups", [None], False),
])
def test_response_assignments_exclude_request_only_nulls(
    specification, relation_type, field, value, is_valid):
  relation = {"type": relation_type, "crmCode": "EXAMPLE", "name": "Example company"}
  if relation_type == "Person":
    relation.update(firstName="Example", lastName="Person")
  single = response_media(specification, "/v1.1/business-relations/{crmCode}")
  listed = response_media(specification, "/v1.1/business-relations")
  single_validator = validator_for(specification, single["schema"])
  list_validator = validator_for(specification, listed["schema"])
  single_validator.validate(relation)
  relation[field] = value
  assert single_validator.is_valid(relation) == is_valid
  assert list_validator.is_valid([relation]) == is_valid
  assert list_validator.is_valid({"businessRelations": [relation]}) == is_valid


def test_get_examples_validate_complete_operation_contract(specification):
  for path in ["/v1.1/business-relations", "/v1.1/business-relations/{crmCode}"]:
    media = response_media(specification, path)
    validator = validator_for(specification, media["schema"])
    for name, example in media["examples"].items():
      errors = list(validator.iter_errors(example["value"]))
      assert not errors, (path, name, [error.message for error in errors])


def test_unpaginated_request_does_not_inject_page_size(specification):
  parameters = specification["paths"]["/v1.1/business-relations"]["get"]["parameters"]
  page_size = next(parameter for parameter in parameters if parameter["name"] == "pageSize")
  assert not page_size.get("required", False)
  assert "default" not in page_size["schema"]


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
