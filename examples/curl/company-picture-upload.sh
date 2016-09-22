#!/bin/bash

# Demonstrate company picture uploading.
# The picture data is base64 encoded.

APIROOT="${APIROOT:-http://localhost:8000}"
TOKEN="${TOKEN:-test}"
COMPANY_ID="${COMPANY_ID:-1}"

curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Token ${TOKEN}" \
    -d @- \
    "$APIROOT/api/companies/${COMPANY_ID}/pictures/" <<END
{
    "image": "$(base64 -w 0 ../../media/test_images/test1.png)",
    "title": "Test",
    "num": 0
}
END
