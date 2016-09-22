#!/bin/bash

# Test logging in.
# If the specified user exists, this should return the authorization token.

APIROOT="${APIROOT:-http://localhost:8000}"

curl -X POST \
    -H "Content-Type: application/json" \
   -d @- \
   "$APIROOT/api/login/" <<END
{
    "email": "test@example.com",
    "password": "abcd1234"
}
END
