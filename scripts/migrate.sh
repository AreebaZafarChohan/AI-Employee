#!/bin/bash
# Run database migrations
# Usage: ./migrate.sh [upgrade|downgrade|current|history]

set -e

COMMAND="${1:-upgrade}"

echo "Running database migration: $COMMAND..."

cd "$(dirname "$0")/.."

# Check if alembic is initialized
if [ ! -d "alembic" ]; then
    echo "Alembic not initialized. Initializing..."
    alembic init alembic
fi

# Run the migration command
case "$COMMAND" in
    upgrade)
        alembic upgrade head
        echo "Database upgraded to latest version."
        ;;
    downgrade)
        alembic downgrade -1
        echo "Database downgraded by one version."
        ;;
    current)
        alembic current
        ;;
    history)
        alembic history
        ;;
    migrate)
        # Generate new migration
        MESSAGE="${2:-auto migration}"
        alembic revision --autogenerate -m "$MESSAGE"
        echo "Migration generated: $MESSAGE"
        ;;
    *)
        echo "Unknown command: $COMMAND"
        echo "Usage: ./migrate.sh [upgrade|downgrade|current|history|migrate]"
        exit 1
        ;;
esac
