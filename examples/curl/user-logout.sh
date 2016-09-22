#!/bin/bash

# Test logging out.
# This should return {"status": "token invalidated"}

APIROOT="${APIROOT:-http://localhost:8000}"
TOKEN="${TOKEN:-test}"

curl -X POST \
	-H "Authorization: Token $TOKEN" \
	"$APIROOT/api/logout/"

