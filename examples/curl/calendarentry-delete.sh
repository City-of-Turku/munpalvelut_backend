#!/bin/bash

# Delete a calendar entry
# The user must be a member of the target company

APIROOT="${APIROOT:-http://localhost:8000}"
TOKEN="${TOKEN:-test}"
ID="${ID:-1}"

curl -X DELETE \
	-H "Authorization: Token $TOKEN" \
	"$APIROOT/api/calendarentries/$ID/"

