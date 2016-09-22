#!/bin/bash

# Create a new calendar entry
# The user must be a member of the target company

APIROOT="${APIROOT:-http://localhost:8000}"
TOKEN="${TOKEN:-test}"
COMPANY_ID="${COMPANY_ID:-1}"

curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Token $TOKEN" \
    -d @- \
    "$APIROOT/api/calendarentries/" <<END
{
    "start": "2016-10-10T12:00:00Z",
    "end": "2016-10-10T14:00:00Z",
    "company": ${COMPANY_ID}
}
END
