#!/bin/bash
set -e

# If the first argument looks like a flag (starts with -), prepend 'angie'
# Example: 'docker run ... -g "daemon off;"' becomes 'angie -g "daemon off;"'
if [ "${1#-}" != "$1" ]; then
    set -- angie "$@"
fi

if [ "$#" -eq 0 ]; then
    set -- angie -g daemon off;
fi

# Execute the command
exec "$@"