# APENTIS API documentation

Welcome to the **APENTIS API** documentation.

This API enables external systems — such as CRMs, onboarding tools, or custom platforms — to securely integrate with the Apentis platform to manage KYC/AML-related data and documents.

The API is designed to integrate seamlessly with the Apentis backend, using secure authentication methods.

## 🔐 Authentication

All endpoints are protected by a Bearer token. Clients must pass the token in the Authorization header:

```http
Authorization: Bearer <your_token_here>
```

## 🌍 Environments

This API is available in two environments:

| Environment | Base URL                              | Description                        |
|-------------|----------------------------------------|------------------------------------|
| Production  | `https://api.apentis.com/v1.1`         | Live API connected to production   |
| Test        | `https://test-api.apentis.com/v1.1`    | Sandbox API for safe testing       |

You can use the test environment to integrate and validate your setup without affecting live data. Contact us to receive a test token.

## 🔗 Live documentation

The interactive API documentation is available here:

[👉 View APENTIS API Documentation](https://api.apentis.com/)


---

## 📁 Main Functional Areas & Endpoints

### Business Relations
- `POST /business-relations`: Create a new business relation
- `PUT /business-relations/{crmCode}`: Update an existing business relation
- `GET /business-relations/{crmCode}`: Retrieve a business relation by its crmCode

### Documents
- `POST /business-relations/{crmCode}/documents`: Upload one or more documents with associated metadata
- `POST /business-relations/{crmCode}/documents/metadata-only`: Submit document metadata only (no file)
- `GET /business-relations/{crmCode}/documents`: Retrieve all documents for a business relation
- `DELETE /business-relations/{crmCode}/documents`: Delete all or filtered documents by type

### AML / KYC status
- `GET /business-relations/{crmCode}/aml-kyc-result`: Retrieve AML risk rating, acceptance status, KYC review info, and document completeness

### Relations between business relations
- `POST /business-relations/{crmCode}/links`: Link one business relation to others (e.g. Person → Company) with a specific role (e.g. Director, Shareholder)

### Investor commitments
- `POST /business-relations/{crmCode}/investor-commitments`: Register or update a fund commitment by an investor

### Cash transactions 
- `POST /cash-transactions`: Submit one or more client cash transactions for cashflow monitoring and suspicious activity detection


---

## 🧩 Roles supported in links between relations

The following roles are supported:
- Director
- Board member
- Trustee
- Protector
- Settlor
- Beneficiary of the trust
- Key person
- Corporate director
- President
- Treasurer
- Secretary
- General partner
- Limited partner
- Beneficial owner
- Member
- Shareholder

Not all roles are valid between all types of business relations. The allowed roles depend on the **type of each party** in the relationship (primary and secondary `crmCode`).

Each role you submit must match a valid combination of:
- **Primary entity type**
- **Linked entity type**
- **Role**

A full list of allowed role mappings is provided in this reference:
- [View role compatibility table (Markdown)](./docs/role_mapping.md)
- [Download as CSV](./docs/role_mapping.csv)


---


## 🔁 API versioning

The APENTIS API follows a versioning scheme using path prefixes (e.g. `/v1.1/`) and semantic versioning in the documentation metadata.

- **Major versions** (e.g. `/v1.0/`, `/v2.0/`) are used when introducing breaking changes. These may include removing fields, renaming paths, or changing behavior in a non-backward-compatible way.
- **Minor versions** (e.g. `/v1.1/`, `/v1.2/`) are used when adding non-breaking changes like new endpoints, fields, or optional enhancements.
- The current version is accessible via: `https://api.apentis.eu/v1.1/...`

Clients should always specify the API version in their requests and monitor changelogs before upgrading to a new major version.


---

## 🗓️ Changelog

| Version | Date       | Description                                                                 |
|---------|------------|-----------------------------------------------------------------------------|
| 1.0.0   | 2025-02-11 | Initial release with business relations, document uploads, and AML/KYC endpoints. |
| 1.1.0   | 2025-05-05 | Added support for linking business relations via roles (e.g., Director, Shareholder). |



---


## 🚀 How to use

1. Obtain your API access token from Apentis.
2. Call the available endpoints using standard HTTP methods.
3. Always include the following header in your requests:

```http
Authorization: Bearer <your_token_here>
```

---

## ⚙️ Technologies
- OpenAPI 3.0 Specification
- Swagger UI (self-hosted)
- GitHub Pages for free hosting

## 🧪 Testing

Automated tests verify that the `openapi.yaml` specification is valid. Install
the test dependencies from `requirements-dev.txt` and run `pytest`:

```bash
pip install -r requirements-dev.txt
pytest
```

---

## 📄 License
This project is intended for Apentis internal and partner use only.
Unauthorized distribution or replication is prohibited.

