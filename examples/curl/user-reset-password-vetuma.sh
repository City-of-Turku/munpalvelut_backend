#!/bin/bash

# Reset user's password using the VETUMA token.

APIROOT="${APIROOT:-http://localhost:8000}"
USER_ID="${USER_ID:-1}"

curl -X POST \
    -H "Content-Type: application/json" \
    -d @- \
    "${APIROOT}/api/reset-password/" <<END
{
    "email": "test@example.com",
    "vetuma": "vet321",
    "new_password": "qwerty123"
}
END

