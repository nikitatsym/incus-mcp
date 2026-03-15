---
tags: [mcp, python, task]
domain: dev
type: task
---

# incus-mcp

MCP server for [Incus](https://linuxcontainers.org/incus/) container and VM manager.

- **MCP standard:** `/home/ari/src/obsidian_vault/specs/mcp-server.md` — follow it exactly (structure, registry, server dispatch, groups, config, client patterns)
- **API base:** `{INCUS_URL}/1.0`, auth: TLS client certificate or Bearer token (JWT signed with client cert)
- **OpenAPI spec:** https://github.com/lxc/incus/blob/main/doc/rest-api.yaml (Swagger 2.0, 282 operations)
- **Docs:** https://linuxcontainers.org/incus/docs/main/rest-api/
- **Health:** `GET /1.0` (200 = running, returns server environment)
- **Hosting:** GitHub — CI/CD from `/home/ari/src/vastai-mcp/.github/workflows/build.yml`, enable Pages (Actions source), create `docs/index.html` setup page

## Config

```
INCUS_URL          — base URL (e.g. https://incus.example.com:8443)
INCUS_CLIENT_CERT  — path to TLS client certificate
INCUS_CLIENT_KEY   — path to TLS client key
```

## Groups

incus_read      — instances, images, networks, storage, profiles, projects, cluster, certificates, operations, warnings, resources, metrics (safe, read-only)
incus_write     — create/update instances, images, networks, storage, profiles, projects, cluster, certificates (non-destructive)
incus_execute   — instance state changes (start/stop/restart/freeze), exec commands, snapshots, backups
incus_delete    — delete all resource types (destructive, irreversible)
incus_admin     — server config, cluster member state, warnings management, metadata

## Operations

### incus_read

| Operation | Endpoint | Notes |
|---|---|---|
| **Server** | | |
| `get_server()` | `GET /1.0` | Server environment and config |
| `get_resources()` | `GET /1.0/resources` | CPU, memory, GPU, storage, network, USB, PCI |
| `get_metrics()` | `GET /1.0/metrics` | Prometheus format |
| `get_metadata_config()` | `GET /1.0/metadata/configuration` | |
| **Instances** | | |
| `list_instances(project, filter, all_projects)` | `GET /1.0/instances?recursion=1` | Slim |
| `show_instance(name, project)` | `GET /1.0/instances/{name}` | Full |
| `get_instance_state(name, project)` | `GET /1.0/instances/{name}/state` | CPU, memory, disk, network |
| `get_instance_access(name)` | `GET /1.0/instances/{name}/access` | |
| `list_instance_logs(name)` | `GET /1.0/instances/{name}/logs` | |
| `get_instance_log(name, filename)` | `GET /1.0/instances/{name}/logs/{filename}` | |
| `list_exec_outputs(name)` | `GET /1.0/instances/{name}/logs/exec-output` | |
| `get_exec_output(name, filename)` | `GET /1.0/instances/{name}/logs/exec-output/{filename}` | |
| `get_console_output(name, project)` | `GET /1.0/instances/{name}/console` | |
| `get_instance_file(name, path, project)` | `GET /1.0/instances/{name}/files?path=` | |
| `get_instance_metadata(name, project)` | `GET /1.0/instances/{name}/metadata` | Image metadata |
| `list_instance_templates(name)` | `GET /1.0/instances/{name}/metadata/templates` | |
| **Instance Snapshots** | | |
| `list_snapshots(name, project)` | `GET /1.0/instances/{name}/snapshots?recursion=1` | |
| `show_snapshot(name, snapshot)` | `GET /1.0/instances/{name}/snapshots/{snapshot}` | |
| **Instance Backups** | | |
| `list_backups(name)` | `GET /1.0/instances/{name}/backups?recursion=1` | |
| `show_backup(name, backup)` | `GET /1.0/instances/{name}/backups/{backup}` | |
| **Images** | | |
| `list_images(project, filter, all_projects)` | `GET /1.0/images?recursion=1` | Slim |
| `show_image(fingerprint, project)` | `GET /1.0/images/{fingerprint}` | Full |
| `list_image_aliases(project)` | `GET /1.0/images/aliases?recursion=1` | |
| `show_image_alias(name)` | `GET /1.0/images/aliases/{name}` | |
| **Networks** | | |
| `list_networks(project, filter)` | `GET /1.0/networks?recursion=1` | Slim |
| `show_network(name, project)` | `GET /1.0/networks/{name}` | Full |
| `get_network_state(name)` | `GET /1.0/networks/{name}/state` | |
| `get_network_leases(name)` | `GET /1.0/networks/{name}/leases` | DHCP leases |
| `list_network_forwards(network)` | `GET /1.0/networks/{network}/forwards?recursion=1` | |
| `show_network_forward(network, listen_address)` | `GET /1.0/networks/{network}/forwards/{listen_address}` | |
| `list_load_balancers(network)` | `GET /1.0/networks/{network}/load-balancers?recursion=1` | |
| `show_load_balancer(network, listen_address)` | `GET /1.0/networks/{network}/load-balancers/{listen_address}` | |
| `get_load_balancer_state(network, listen_address)` | `GET /1.0/networks/{network}/load-balancers/{listen_address}/state` | |
| `list_network_peers(network)` | `GET /1.0/networks/{network}/peers?recursion=1` | |
| `show_network_peer(network, peer)` | `GET /1.0/networks/{network}/peers/{peer}` | |
| **Network ACLs** | | |
| `list_network_acls(project)` | `GET /1.0/network-acls?recursion=1` | |
| `show_network_acl(name)` | `GET /1.0/network-acls/{name}` | |
| `get_network_acl_log(name)` | `GET /1.0/network-acls/{name}/log` | |
| **Network Address Sets** | | |
| `list_network_address_sets()` | `GET /1.0/network-address-sets?recursion=1` | |
| `show_network_address_set(name)` | `GET /1.0/network-address-sets/{name}` | |
| **Network Allocations** | | |
| `get_network_allocations()` | `GET /1.0/network-allocations` | |
| **Network Integrations** | | |
| `list_network_integrations()` | `GET /1.0/network-integrations?recursion=1` | |
| `show_network_integration(name)` | `GET /1.0/network-integrations/{name}` | |
| **Network Zones** | | |
| `list_network_zones()` | `GET /1.0/network-zones?recursion=1` | |
| `show_network_zone(zone)` | `GET /1.0/network-zones/{zone}` | |
| `list_zone_records(zone)` | `GET /1.0/network-zones/{zone}/records?recursion=1` | |
| `show_zone_record(zone, name)` | `GET /1.0/network-zones/{zone}/records/{name}` | |
| **Storage Pools** | | |
| `list_storage_pools(project)` | `GET /1.0/storage-pools?recursion=1` | |
| `show_storage_pool(pool, project)` | `GET /1.0/storage-pools/{pool}` | |
| `get_pool_resources(pool)` | `GET /1.0/storage-pools/{pool}/resources` | |
| **Storage Volumes** | | |
| `list_volumes(pool, project, type)` | `GET /1.0/storage-pools/{pool}/volumes?recursion=1` | Slim |
| `show_volume(pool, type, volume, project)` | `GET /1.0/storage-pools/{pool}/volumes/{type}/{volume}` | Full |
| `get_volume_state(pool, type, volume)` | `GET /1.0/storage-pools/{pool}/volumes/{type}/{volume}/state` | |
| `list_volume_snapshots(pool, type, volume)` | `GET /1.0/storage-pools/{pool}/volumes/{type}/{volume}/snapshots?recursion=1` | |
| `show_volume_snapshot(pool, type, volume, snapshot)` | `GET ...snapshots/{snapshot}` | |
| `list_volume_backups(pool, type, volume)` | `GET .../{type}/{volume}/backups?recursion=1` | |
| `show_volume_backup(pool, type, volume, backup)` | `GET ...backups/{backup}` | |
| **Storage Buckets** | | |
| `list_buckets(pool)` | `GET /1.0/storage-pools/{pool}/buckets?recursion=1` | |
| `show_bucket(pool, bucket)` | `GET ...buckets/{bucket}` | |
| `list_bucket_keys(pool, bucket)` | `GET ...buckets/{bucket}/keys?recursion=1` | |
| `show_bucket_key(pool, bucket, key)` | `GET ...buckets/{bucket}/keys/{key}` | |
| `list_bucket_backups(pool, bucket)` | `GET ...buckets/{bucket}/backups?recursion=1` | |
| `show_bucket_backup(pool, bucket, backup)` | `GET ...buckets/{bucket}/backups/{backup}` | |
| **Profiles** | | |
| `list_profiles(project)` | `GET /1.0/profiles?recursion=1` | Slim |
| `show_profile(name, project)` | `GET /1.0/profiles/{name}` | Full |
| **Projects** | | |
| `list_projects(filter)` | `GET /1.0/projects?recursion=1` | Slim |
| `show_project(name)` | `GET /1.0/projects/{name}` | Full |
| `get_project_access(name)` | `GET /1.0/projects/{name}/access` | |
| `get_project_state(name)` | `GET /1.0/projects/{name}/state` | Resource usage |
| **Cluster** | | |
| `get_cluster()` | `GET /1.0/cluster` | |
| `list_cluster_members(filter)` | `GET /1.0/cluster/members?recursion=1` | |
| `show_cluster_member(name)` | `GET /1.0/cluster/members/{name}` | |
| `get_cluster_member_state(name)` | `GET /1.0/cluster/members/{name}/state` | |
| `list_cluster_groups()` | `GET /1.0/cluster/groups?recursion=1` | |
| `show_cluster_group(name)` | `GET /1.0/cluster/groups/{name}` | |
| **Certificates** | | |
| `list_certificates(filter)` | `GET /1.0/certificates?recursion=1` | |
| `show_certificate(fingerprint)` | `GET /1.0/certificates/{fingerprint}` | |
| **Operations** | | |
| `list_operations()` | `GET /1.0/operations?recursion=1` | |
| `show_operation(id)` | `GET /1.0/operations/{id}` | |
| `wait_operation(id)` | `GET /1.0/operations/{id}/wait` | |
| **Warnings** | | |
| `list_warnings()` | `GET /1.0/warnings?recursion=1` | |
| `show_warning(uuid)` | `GET /1.0/warnings/{uuid}` | |

Total: 83

### incus_write

| Operation | Endpoint | Notes |
|---|---|---|
| **Instances** | | |
| `create_instance(name, source, ...)` | `POST /1.0/instances` | Async. project, target |
| `update_instance(name, ...)` | `PUT /1.0/instances/{name}` | ETag support |
| `patch_instance(name, ...)` | `PATCH /1.0/instances/{name}` | Partial |
| `rename_instance(name, new_name)` | `POST /1.0/instances/{name}` | Also move/migrate |
| `update_instance_metadata(name, ...)` | `PUT /1.0/instances/{name}/metadata` | |
| `upload_instance_file(name, path, ...)` | `POST /1.0/instances/{name}/files?path=` | Headers: uid, gid, mode, type |
| `create_instance_template(name, ...)` | `POST /1.0/instances/{name}/metadata/templates` | |
| `rebuild_instance(name, source)` | `POST /1.0/instances/{name}/rebuild` | |
| **Instance Snapshots** | | |
| `create_snapshot(name, ...)` | `POST /1.0/instances/{name}/snapshots` | |
| `update_snapshot(name, snapshot, ...)` | `PUT /1.0/instances/{name}/snapshots/{snapshot}` | |
| `rename_snapshot(name, snapshot, new_name)` | `POST /1.0/instances/{name}/snapshots/{snapshot}` | |
| **Instance Backups** | | |
| `create_backup(name, ...)` | `POST /1.0/instances/{name}/backups` | |
| `rename_backup(name, backup, new_name)` | `POST /1.0/instances/{name}/backups/{backup}` | |
| **Images** | | |
| `create_image(...)` | `POST /1.0/images` | |
| `update_image(fingerprint, ...)` | `PUT /1.0/images/{fingerprint}` | |
| `patch_image(fingerprint, ...)` | `PATCH /1.0/images/{fingerprint}` | |
| `refresh_image(fingerprint)` | `POST /1.0/images/{fingerprint}/refresh` | |
| `create_image_alias(name, target)` | `POST /1.0/images/aliases` | |
| `update_image_alias(name, target)` | `PUT /1.0/images/aliases/{name}` | |
| `rename_image_alias(name, new_name)` | `POST /1.0/images/aliases/{name}` | |
| **Networks** | | |
| `create_network(name, ...)` | `POST /1.0/networks` | |
| `update_network(name, ...)` | `PUT /1.0/networks/{name}` | |
| `patch_network(name, ...)` | `PATCH /1.0/networks/{name}` | |
| `rename_network(name, new_name)` | `POST /1.0/networks/{name}` | |
| `create_network_forward(network, ...)` | `POST /1.0/networks/{network}/forwards` | |
| `update_network_forward(network, listen_address, ...)` | `PUT /1.0/networks/{network}/forwards/{listen_address}` | |
| `create_load_balancer(network, ...)` | `POST /1.0/networks/{network}/load-balancers` | |
| `update_load_balancer(network, listen_address, ...)` | `PUT /1.0/networks/{network}/load-balancers/{listen_address}` | |
| `create_network_peer(network, ...)` | `POST /1.0/networks/{network}/peers` | |
| `update_network_peer(network, peer, ...)` | `PUT /1.0/networks/{network}/peers/{peer}` | |
| **Network ACLs** | | |
| `create_network_acl(name, ...)` | `POST /1.0/network-acls` | |
| `update_network_acl(name, ...)` | `PUT /1.0/network-acls/{name}` | |
| `rename_network_acl(name, new_name)` | `POST /1.0/network-acls/{name}` | |
| **Network Address Sets** | | |
| `create_network_address_set(name, ...)` | `POST /1.0/network-address-sets` | |
| `update_network_address_set(name, ...)` | `PUT /1.0/network-address-sets/{name}` | |
| `rename_network_address_set(name, new_name)` | `POST /1.0/network-address-sets/{name}` | |
| **Network Integrations** | | |
| `create_network_integration(name, ...)` | `POST /1.0/network-integrations` | |
| `update_network_integration(name, ...)` | `PUT /1.0/network-integrations/{name}` | |
| `rename_network_integration(name, new_name)` | `POST /1.0/network-integrations/{name}` | |
| **Network Zones** | | |
| `create_network_zone(name, ...)` | `POST /1.0/network-zones` | |
| `update_network_zone(zone, ...)` | `PUT /1.0/network-zones/{zone}` | |
| `create_zone_record(zone, name, ...)` | `POST /1.0/network-zones/{zone}/records` | |
| `update_zone_record(zone, name, ...)` | `PUT /1.0/network-zones/{zone}/records/{name}` | |
| **Storage Pools** | | |
| `create_storage_pool(name, driver, ...)` | `POST /1.0/storage-pools` | |
| `update_storage_pool(pool, ...)` | `PUT /1.0/storage-pools/{pool}` | |
| **Storage Volumes** | | |
| `create_volume(pool, name, type, ...)` | `POST /1.0/storage-pools/{pool}/volumes` | |
| `update_volume(pool, type, volume, ...)` | `PUT /1.0/storage-pools/{pool}/volumes/{type}/{volume}` | |
| `rename_volume(pool, type, volume, new_name)` | `POST /1.0/storage-pools/{pool}/volumes/{type}/{volume}` | Also move/migrate |
| `create_volume_snapshot(pool, type, volume, ...)` | `POST .../{type}/{volume}/snapshots` | |
| `update_volume_snapshot(pool, type, volume, snapshot, ...)` | `PUT ...snapshots/{snapshot}` | |
| `rename_volume_snapshot(pool, type, volume, snapshot, new_name)` | `POST ...snapshots/{snapshot}` | |
| `create_volume_backup(pool, type, volume, ...)` | `POST .../{type}/{volume}/backups` | |
| `rename_volume_backup(pool, type, volume, backup, new_name)` | `POST ...backups/{backup}` | |
| **Storage Buckets** | | |
| `create_bucket(pool, name, ...)` | `POST /1.0/storage-pools/{pool}/buckets` | |
| `update_bucket(pool, bucket, ...)` | `PUT ...buckets/{bucket}` | |
| `create_bucket_key(pool, bucket, name, ...)` | `POST ...buckets/{bucket}/keys` | |
| `update_bucket_key(pool, bucket, key, ...)` | `PUT ...buckets/{bucket}/keys/{key}` | |
| `create_bucket_backup(pool, bucket, ...)` | `POST ...buckets/{bucket}/backups` | |
| `rename_bucket_backup(pool, bucket, backup, new_name)` | `POST ...buckets/{bucket}/backups/{backup}` | |
| **Profiles** | | |
| `create_profile(name, ...)` | `POST /1.0/profiles` | |
| `update_profile(name, ...)` | `PUT /1.0/profiles/{name}` | |
| `rename_profile(name, new_name)` | `POST /1.0/profiles/{name}` | |
| **Projects** | | |
| `create_project(name, ...)` | `POST /1.0/projects` | |
| `update_project(name, ...)` | `PUT /1.0/projects/{name}` | |
| `rename_project(name, new_name)` | `POST /1.0/projects/{name}` | |
| **Cluster** | | |
| `update_cluster(...)` | `PUT /1.0/cluster` | |
| `update_cluster_certificate(...)` | `PUT /1.0/cluster/certificate` | |
| `request_join_token(name)` | `POST /1.0/cluster/members` | |
| `update_cluster_member(name, ...)` | `PUT /1.0/cluster/members/{name}` | |
| `rename_cluster_member(name, new_name)` | `POST /1.0/cluster/members/{name}` | |
| `create_cluster_group(name, ...)` | `POST /1.0/cluster/groups` | |
| `update_cluster_group(name, ...)` | `PUT /1.0/cluster/groups/{name}` | |
| `rename_cluster_group(name, new_name)` | `POST /1.0/cluster/groups/{name}` | |
| **Certificates** | | |
| `add_certificate(...)` | `POST /1.0/certificates` | |
| `update_certificate(fingerprint, ...)` | `PUT /1.0/certificates/{fingerprint}` | |

Total: 74

### incus_execute

| Operation | Endpoint | Notes |
|---|---|---|
| **Instance State** | | |
| `start_instance(name, project)` | `PUT /1.0/instances/{name}/state` | action=start |
| `stop_instance(name, project, force)` | `PUT /1.0/instances/{name}/state` | action=stop |
| `restart_instance(name, project, force)` | `PUT /1.0/instances/{name}/state` | action=restart |
| `freeze_instance(name, project)` | `PUT /1.0/instances/{name}/state` | action=freeze |
| `unfreeze_instance(name, project)` | `PUT /1.0/instances/{name}/state` | action=unfreeze |
| `bulk_instance_state(action, project)` | `PUT /1.0/instances` | Bulk start/stop/restart |
| **Exec** | | |
| `exec_instance(name, command, project)` | `POST /1.0/instances/{name}/exec` | Returns operation with output |
| **Cluster Member State** | | |
| `evacuate_cluster_member(name)` | `POST /1.0/cluster/members/{name}/state` | |
| `restore_cluster_member(name)` | `POST /1.0/cluster/members/{name}/state` | |

Total: 9

### incus_delete

| Operation | Endpoint | Notes |
|---|---|---|
| **Instances** | | |
| `delete_instance(name, project)` | `DELETE /1.0/instances/{name}` | |
| `delete_snapshot(name, snapshot)` | `DELETE /1.0/instances/{name}/snapshots/{snapshot}` | |
| `delete_backup(name, backup)` | `DELETE /1.0/instances/{name}/backups/{backup}` | |
| `delete_instance_file(name, path, project)` | `DELETE /1.0/instances/{name}/files?path=` | |
| `delete_instance_log(name, filename)` | `DELETE /1.0/instances/{name}/logs/{filename}` | |
| `delete_exec_output(name, filename)` | `DELETE /1.0/instances/{name}/logs/exec-output/{filename}` | |
| `delete_instance_template(name)` | `DELETE /1.0/instances/{name}/metadata/templates` | |
| `clear_console(name, project)` | `DELETE /1.0/instances/{name}/console` | |
| **Images** | | |
| `delete_image(fingerprint, project)` | `DELETE /1.0/images/{fingerprint}` | |
| `delete_image_alias(name)` | `DELETE /1.0/images/aliases/{name}` | |
| **Networks** | | |
| `delete_network(name, project)` | `DELETE /1.0/networks/{name}` | |
| `delete_network_forward(network, listen_address)` | `DELETE /1.0/networks/{network}/forwards/{listen_address}` | |
| `delete_load_balancer(network, listen_address)` | `DELETE /1.0/networks/{network}/load-balancers/{listen_address}` | |
| `delete_network_peer(network, peer)` | `DELETE /1.0/networks/{network}/peers/{peer}` | |
| `delete_network_acl(name)` | `DELETE /1.0/network-acls/{name}` | |
| `delete_network_address_set(name)` | `DELETE /1.0/network-address-sets/{name}` | |
| `delete_network_integration(name)` | `DELETE /1.0/network-integrations/{name}` | |
| `delete_network_zone(zone)` | `DELETE /1.0/network-zones/{zone}` | |
| `delete_zone_record(zone, name)` | `DELETE /1.0/network-zones/{zone}/records/{name}` | |
| **Storage** | | |
| `delete_storage_pool(pool, project)` | `DELETE /1.0/storage-pools/{pool}` | |
| `delete_volume(pool, type, volume, project)` | `DELETE /1.0/storage-pools/{pool}/volumes/{type}/{volume}` | |
| `delete_volume_snapshot(pool, type, volume, snapshot)` | `DELETE ...snapshots/{snapshot}` | |
| `delete_volume_backup(pool, type, volume, backup)` | `DELETE ...backups/{backup}` | |
| `delete_volume_file(pool, type, volume)` | `DELETE .../{type}/{volume}/files` | |
| `delete_bucket(pool, bucket)` | `DELETE ...buckets/{bucket}` | |
| `delete_bucket_key(pool, bucket, key)` | `DELETE ...buckets/{bucket}/keys/{key}` | |
| `delete_bucket_backup(pool, bucket, backup)` | `DELETE ...buckets/{bucket}/backups/{backup}` | |
| **Profiles** | | |
| `delete_profile(name, project)` | `DELETE /1.0/profiles/{name}` | |
| **Projects** | | |
| `delete_project(name, force)` | `DELETE /1.0/projects/{name}` | |
| **Cluster** | | |
| `delete_cluster_member(name)` | `DELETE /1.0/cluster/members/{name}` | |
| `delete_cluster_group(name)` | `DELETE /1.0/cluster/groups/{name}` | |
| **Certificates** | | |
| `delete_certificate(fingerprint)` | `DELETE /1.0/certificates/{fingerprint}` | |
| **Operations** | | |
| `cancel_operation(id)` | `DELETE /1.0/operations/{id}` | |
| **Warnings** | | |
| `delete_warning(uuid)` | `DELETE /1.0/warnings/{uuid}` | |

Total: 34

### incus_admin

| Operation | Endpoint | Notes |
|---|---|---|
| `update_server_config(...)` | `PUT /1.0` | |
| `patch_server_config(...)` | `PATCH /1.0` | |
| `update_warning(uuid, ...)` | `PUT /1.0/warnings/{uuid}` | Acknowledge/dismiss |
| `patch_warning(uuid, ...)` | `PATCH /1.0/warnings/{uuid}` | |

Total: 4

## Slim fields

```
SLIM_INSTANCE = {"name", "status", "type", "architecture", "location", "project", "created_at"}
SLIM_IMAGE = {"fingerprint", "type", "architecture", "size", "created_at", "properties.description"}
SLIM_NETWORK = {"name", "type", "managed", "status"}
SLIM_VOLUME = {"name", "type", "content_type", "location"}
SLIM_PROFILE = {"name", "description"}
SLIM_PROJECT = {"name", "description"}
```

## Out of scope

- WebSocket streams (console, events, live operations) — not compatible with MCP request/response model
- SFTP endpoints — binary protocol, not JSON
- Untrusted/public image endpoints — MCP server uses authenticated access
- Export endpoints returning raw binary files — too large for MCP responses

## Deploy checklist

- [ ] CI/CD workflow
- [ ] Create repo and push
- [ ] If GitHub: enable Pages (source: GitHub Actions), create `docs/index.html` setup page
- [ ] If Gitea: PyPI registry works automatically, no Pages needed
- [ ] First push to `main` → build → tag v1.0.0 → release with wheel → index
- [ ] Verify build passes and install works: `uvx --extra-index-url INDEX_URL incus-mcp`
- [ ] README.md — install command, MCP config JSON with env vars, where to paste (Claude Desktop, Cursor, Claude Code), how to get API key/token
