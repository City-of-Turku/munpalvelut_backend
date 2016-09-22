#!/bin/bash

# Change a user's password.
# Admin users can change anyone's password without providing
# the old password (except their own.)

APIROOT="${APIROOT:-http://localhost:8000}"
USER_ID="${USER_ID:-1}"
TOKEN="${TOKEN:-test}"

curl -X PUT \
    -H "Content-Type: application/json" \
    -H "Authorization: Token $TOKEN" \
    -d @- \
    "${APIROOT}/api/users/${USER_ID}/change_password/" <<END
{
	"old_password": "abcd1234",
    "new_password": "qwerty123"
}
END

