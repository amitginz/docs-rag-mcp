# REST API design

## Resources and verbs
Model the API around nouns such as `/orders` and `/orders/42`. Use GET to read, POST to create, PUT to replace, PATCH to update part of a resource and DELETE to remove it. GET must be safe and must not change data.

## Status codes
Return 200 for success, 201 after creating a resource, 204 when there is no body, 400 for invalid input, 401 when authentication is missing, 403 when access is forbidden, 404 when the resource does not exist and 409 for conflicts. Use 500 only for real server errors.

## Idempotency
PUT and DELETE are idempotent: repeating the request gives the same result. For POST requests that must not be duplicated, such as payments, accept an `Idempotency-Key` header and store the first result.

## Pagination and errors
Never return an unbounded list. Use `limit` and `cursor` parameters, and return a consistent JSON error object with a code and a human-readable message.
