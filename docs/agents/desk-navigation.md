# Desk navigation (Frappe v16)

Working Time is a **Desk-only** ERPNext extension. There is no separate SPA; the apps screen tile and dock open the **Time Tracking** workspace.

| Layer | Shipped in this app | Notes |
| ----- | ------------------- | ----- |
| **Apps screen** | `hooks.py` → `add_to_apps_screen` | `title` → `app_title` (**Working Time**); `route` → `/desk/time-tracking` |
| **Dock** | `working_time/dock/working_time/working_time.json` | Rail row **Workspace** → **Time Tracking** (display title **Working Time**) |
| **Sidebar** (module shell) | `working_time/working_time/sidebar/working_time/working_time.json` | Shell **Working Time**; **Home** → workspace **Time Tracking** |
| **Workspace** | `working_time/working_time/workspace/time_tracking/time_tracking.json` | Public home at `/desk/time-tracking` |

**Naming:** **Module Def**, apps tile, dock label, and sidebar shell use **Working Time**. The **Workspace** document stays **Time Tracking** so its slug (`/desk/time-tracking`) does not collide with the **Working Time** DocType short route (`/desk/working-time`).

## Apps screen

- **Tile label:** Working Time (`add_to_apps_screen` uses `app_title`)
- **Opens:** `/desk/time-tracking` (workspace)
- **Visibility:** `working_time.api.permission.has_app_permission` — `UserPermissions.allow_modules` for module **Working Time**.

## Changing navigation (Desk)

1. Edit in Desk (developer mode) → **Export to App** for sidebar or dock JSON so `modified` stays valid for `bench migrate`.
2. `bench --site <site> migrate`; `bench clear-cache` if boot entries look stale.
3. After renaming the workspace back from **Working Time**, remove a duplicate **Working Time** workspace row on the site layer if migrate left one behind.

## Manual smoke test

1. User with **Employee**: apps tile **Working Time** visible; opens **Time Tracking** workspace at `/desk/time-tracking`.
2. **Working Time** DocType list still reachable at `/desk/working-time` (doctype route).
3. Dock rail: opens **Time Tracking** workspace.
4. User without module DocPerm: tile hidden.

## Standalone app vs mounting on ERPNext

**Default in this app:** standalone — `add_to_apps_screen` plus a `working_time` **Dock** (`mount_on` empty). Users with DocPerm on module **Working Time** open the app from the **apps screen** and land on `/desk/time-tracking`.

**Alternative:** set `mount_on` to `erpnext` on the shipped **Dock** document. Frappe appends Working Time’s rail rows to **ERPNext’s** dock and **removes** the separate apps-screen tile.

You cannot have both a dedicated apps-screen tile and `mount_on: erpnext` on the same app.

## Pin Working Time on ERPNext’s dock (production / multi-app sites)

1. Log in as **Workspace Manager** (or **Administrator**).
2. Open **ERPNext**.
3. **Manage Dock** → **For everyone** on the **erpnext** app.
4. **Add** a row: `link_type` **Workspace**, `link_to` **Time Tracking**, title **Working Time** (or **Time Tracking**), icon e.g. `calendar-clock`.
5. Save.

Direct URLs `/desk/time-tracking` (workspace) and `/desk/working-time` (DocType list) both work.

## Programmatic dock changes (install / migrate)

See earlier table in repo history; per-site ERPNext rail pinning stays manual or customer-app scoped.

## Related

- Request Management dual-surface example: `request_management/docs/agents/desk-navigation.md` (SPA + Desk).
