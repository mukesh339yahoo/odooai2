#!/bin/bash
VERSION=${1:-20.0}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Starting Postgres for Odoo $VERSION..."
docker run -d -e POSTGRES_USER=odoo -e POSTGRES_PASSWORD=odoo -e POSTGRES_DB=postgres --name db-$VERSION postgres:16
sleep 5

echo "Running tests on Odoo $VERSION..."
docker run --rm --link db-$VERSION:db -v "$SCRIPT_DIR/ridhira_ai_chat_report:/mnt/extra-addons/ridhira_ai_chat_report" -e HOST=db -e USER=odoo -e PASSWORD=odoo odoo:$VERSION odoo -i ridhira_ai_chat_report --test-enable -d test_db --stop-after-init

echo "Cleaning up..."
docker stop db-$VERSION || true
docker rm db-$VERSION || true
