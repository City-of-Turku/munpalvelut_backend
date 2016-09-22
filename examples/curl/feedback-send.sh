#!/bin/bash

# Send feedback

APIROOT="${APIROOT:-http://localhost:8000}"
TOKEN="${TOKEN:-test}"

curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Token $TOKEN" \
    -d @- \
    "${APIROOT}/api/feedback/" <<END
{
    "subject": "Hello",
    "message": "World"
}
END

