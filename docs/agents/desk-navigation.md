# Desk navigation (Frappe v16)

Working Time is a **Desk-only** ERPNext extension. There is no separate SPA; the apps screen tile and dock open the **Working Time** workspace.

| Layer | Shipped in this app | Notes |
| ----- | ------------------- | ----- |
| **Apps screen** | `hooks.py` → `add_to_apps_screen` | `title` → `app_title` (**Working Time**); `route` → `/desk/working-time` |
| **Dock** | `working_time/dock/working_time/working_time.json` | One rail row: **Workspace** → **Working Time** |
| **Sidebar** (module shell) | `working_time/working_time/sidebar/working_time/working_time.json` | Shipped **Sidebar** for shell **Working Time** |
| **Workspace** | `working_time/working_time/workspace/working_time/working_time.json` | Public home at `/desk/working-time` |

**Naming:** **Module Def**, apps tile, dock, sidebar shell, and workspace all use **Working Time** (matches `app_title` in `hooks.py`).

## Apps screen

- **Tile label:** Working Time (`add_to_apps_screen` uses `app_title`)
- **Opens:** `/desk/working-time`
- **Visibility:** `working_time.api.permission.has_app_permission` — the session user’s `UserPermissions.allow_modules` (same list as `Workspace.get_allowed_modules` / `frappe.boot.user.allow_modules` after boot). Any **DocPerm**-granted read, write, or create on a DocType in module **Working Time** shows the tile (including **Freelancer Time** without a separate **Working Time** DocType check).

## Changing navigation (Desk)

1. Edit in Desk (developer mode) → **Export to App** for sidebar or dock JSON so `modified` stays valid for `bench migrate`.
2. `bench --site <site> migrate`; `bench clear-cache` if boot entries look stale.
3. Sites upgraded from an older **Time Tracking** workspace name: remove duplicate workspace/sidebar rows on the site layer (**Manage Sidebar** → **For everyone**) or reset to standard after migrate imports the renamed fixtures.

## Manual smoke test

1. User with **Employee**: apps tile visible; opens **Working Time** workspace.
2. Dock rail: single icon → same workspace.
3. User without module DocPerm: tile hidden (routes not offered).
4. Sidebar links: **Working Time**, **Freelancer Time**, reports, setup DocTypes.

## Standalone app vs mounting on ERPNext

**Default in this app:** standalone — `add_to_apps_screen` plus a `working_time` **Dock** (`mount_on` empty). Users with DocPerm on module **Working Time** open **Working Time** from the **apps screen** and land on `/desk/working-time` in one click, without opening ERPNext first.

**Alternative:** set `mount_on` to `erpnext` on the shipped `working_time` **Dock** document. Frappe appends Working Time’s rail rows to **ERPNext’s** dock and **removes** the separate apps-screen tile (`on_apps_screen` is false when the app is mounted). Use when time tracking should live only inside the ERPNext shell (companion-app pattern, e.g. India Compliance).

You cannot have both a dedicated apps-screen tile and `mount_on: erpnext` on the same app; Frappe treats mounting as winning over `add_to_apps_screen`.

## Pin Working Time on ERPNext’s dock (production / multi-app sites)

For users who work mainly in **ERPNext** but should also reach time tracking from ERPNext’s left rail **in addition** to the apps screen:

1. Log in as **Workspace Manager** (or **Administrator**).
2. Open **ERPNext** (apps screen or existing session).
3. **Manage Dock** → layer **For everyone** (site arrangement on the **erpnext** app).
4. **Add** a row: `link_type` **Workspace**, `link_to` **Working Time**, icon e.g. `calendar-clock`, title **Working Time**.
5. Save. No `bench migrate` in the Working Time app is required; this is a **site** dock layer, not shipped JSON.

Direct URL `/desk/working-time` and the Awesome Bar always work regardless of dock layout.

## Programmatic dock changes (install / migrate)

| Approach | What it does | Fit for `working_time` |
| -------- | ------------ | ---------------------- |
| **`mount_on: erpnext`** on the app’s standard **Dock** (JSON or patch that sets the field on the `working_time` Dock row) | Companion mount; rows on ERPNext rail; **no** apps-screen tile | Possible in a patch, same as shipping JSON — but changes product default away from standalone |
| **Patch calling `save_site_dock("erpnext", items)`** | Writes the **site** arrangement layer for ERPNext’s dock | Technically possible (`ignore_permissions` in migrate), but `_save_layer` **replaces** the whole site layer — the patch must send the full desired arrangement, it is site-specific, and it runs on every site that installs the app unless gated (e.g. only in a customer app like `uea`) |
| **Patch editing ERPNext’s shipped standard Dock** | Would modify `erpnext` app JSON or DB row owned by ERPNext | **Out of scope** for `working_time`; would fight ERPNext upgrades |
| **`after_install` in `working_time`** | Same as site-layer dock save | Same drawbacks; wrong default for OSS sites that only want the apps-screen entry |

**Conclusion:** keep standalone navigation in `working_time`. Per-site ERPNext rail pinning belongs in **Desk** (or a **customer app** patch with an explicit site/product gate), not in generic `working_time` install/migrate.

## Related

- Request Management dual-surface example: `request_management/docs/agents/desk-navigation.md` (SPA + Desk).
