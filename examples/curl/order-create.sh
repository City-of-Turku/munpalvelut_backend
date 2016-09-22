#!/bin/bash

# Create a new order

APIROOT="${APIROOT:-http://localhost:8000}"
TOKEN="${TOKEN:-test}"
USER_ID="${USER_ID:-1}"
COMPANY_ID="${COMPANY_ID:-1}"
SERVICE_PACKAGE_ID="${SERVICE_PACKAGE_ID:-1}"

curl -X POST \
    -H "Content-Type: application/json" \
    -H "Authorization: Token $TOKEN" \
    -d @- \
    "${APIROOT}/api/users/${USER_ID}/orders/" <<END
{
    "user_first_name": "Test",
    "user_last_name": "User",
    "user_email": "test@example.com",
    "user_phone": "+12345678",

    "site_address_street": "Ääkköskatu 3",
    "site_address_street2": "",
    "site_address_postalcode": "12345",
    "site_address_city": "Helsinki",
    "site_room_count": 4,
    "site_sanitary_count": 1,
    "site_floor_count": 1,
    "site_floor_area": 80.4,

    "duration": 3,
    "price": 400,
    "timeslot_start": "2016-10-10T07:00:00Z",
    "timeslot_end": "2016-10-10T11:00:00Z",
    "extra_info": "",

    "company": ${COMPANY_ID},
    "service_package": ${SERVICE_PACKAGE_ID},
    "service_package_shortname": "palvelu-paketti"
}
END
