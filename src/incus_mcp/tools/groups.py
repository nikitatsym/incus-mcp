from ..registry import Group

incus_read = Group(
    "incus_read",
    "Query Incus data (safe, read-only).\n\n"
    "Call with operation=\"help\" to list all available read operations.\n"
    "Otherwise pass the operation name and a JSON object with parameters.\n\n"
    "Example: incus_read(operation=\"ListInstances\")",
)

incus_write = Group(
    "incus_write",
    "Create or update Incus resources (non-destructive).\n\n"
    "Call with operation=\"help\" to list all available write operations.\n"
    "Otherwise pass the operation name and a JSON object with parameters.\n\n"
    "Example: incus_write(operation=\"CreateInstance\", params={\"name\": \"my-vm\", ...})",
)

incus_execute = Group(
    "incus_execute",
    "Execute actions on Incus instances: start, stop, restart, freeze, exec commands.\n\n"
    "Call with operation=\"help\" to list all available execute operations.\n"
    "Otherwise pass the operation name and a JSON object with parameters.\n\n"
    "Example: incus_execute(operation=\"StartInstance\", params={\"name\": \"my-vm\"})",
)

incus_delete = Group(
    "incus_delete",
    "Delete Incus resources (destructive, irreversible).\n\n"
    "Call with operation=\"help\" to list all available delete operations.\n"
    "Otherwise pass the operation name and a JSON object with parameters.\n\n"
    "Example: incus_delete(operation=\"DeleteInstance\", params={\"name\": \"my-vm\"})",
)

incus_admin = Group(
    "incus_admin",
    "Manage Incus server config and warnings.\n\n"
    "Call with operation=\"help\" to list all available admin operations.\n"
    "Otherwise pass the operation name and a JSON object with parameters.\n\n"
    "Example: incus_admin(operation=\"UpdateServerConfig\", params={...})",
)
