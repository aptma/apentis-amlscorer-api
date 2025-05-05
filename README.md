# AMLscorer API documentation

Welcome to the **AMLscorer API** documentation.

This API enables external systems — such as CRMs, onboarding tools, or custom platforms — to securely integrate with the Apentis AMLscorer platform to manage KYC/AML-related data and documents.

The API is designed to integrate seamlessly with the Apentis AMLscorer backend, using secure authentication methods.

## 🔐 Authentication

All endpoints are protected by a Bearer Token. Clients must pass the token in the Authorization header:

```http
Authorization: Bearer <your_token_here>
```

## 🔗 Live documentation

The interactive API documentation is available here:

[👉 View AMLscorer API Documentation](https://aptma.github.io/amlscorer-api/)



---

## 📁 Main Functional Areas & Endpoints

### 🧑‍💼 Business Relations
- `POST /business-relations`: Create a new business relation
- `PUT /business-relations/{crmCode}`: Update an existing business relation
- `GET /business-relations/{crmCode}`: Retrieve a business relation by its crmCode

### 📄 Documents
- `POST /business-relations/{crmCode}/documents`: Upload a document with its metadata
- `POST /business-relations/{crmCode}/documents/metadata`: Submit document metadata only (no file)
- `POST /business-relations/{crmCode}/documents/multiple`: Upload multiple documents and their metadata
- `GET /business-relations/{crmCode}/documents`: Retrieve all documents for a business relation
- `DELETE /business-relations/{crmCode}/documents`: Delete all or filtered documents by type

### 🔍 AML / KYC Status
- `GET /business-relations/{crmCode}/aml-kyc-result`: Retrieve AML risk rating, acceptance status, KYC review info, and document completeness

### 🔗 Relations Between Business Relations
- `POST /business-relations/{crmCode}/links`: Link one business relation to others (e.g. Person → Company) with a specific role (e.g. Director, Shareholder)

---

## 🧩 Roles Supported in Links Between Relations

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

---

## 📄 License
This project is intended for Apentis internal and partner use only.
Unauthorized distribution or replication is prohibited.

