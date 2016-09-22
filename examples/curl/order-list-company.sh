#!/bin/bash

# Create a new order

APIROOT="${APIROOT:-http://localhost:8000}"
TOKEN="${TOKEN:-test}"
COMPANY_ID="${COMPANY_ID:-1}"

curl -X GET \
    -H "Content-Type: application/json" \
    -H "Authorization: Token $TOKEN" \
    -d @- \
    "${APIROOT}/api/companies/${COMPANY_ID}/orders/" <<END
{}
END
