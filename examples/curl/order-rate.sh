#!/bin/bash

# Create a new order

APIROOT="${APIROOT:-http://localhost:8000}"
TOKEN="${TOKEN:-test}"
USER_ID="${USER_ID:-1}"
ORDER_ID="${ORDER_ID:-1}"

curl -X PUT \
    -H "Content-Type: application/json" \
    -H "Authorization: Token $TOKEN" \
    -d @- \
    "${APIROOT}/api/users/${USER_ID}/rate-order/${ORDER_ID}/" <<END
{
    "rating": 2
}
END
