# NEXUS Storage Intelligence 2.0
## Technical specification and implementation roadmap

**Status:** P0 and P1 implemented; CI passed on Ubuntu and Windows runners; physical Windows validation remains outstanding  
**Target:** Windows 10/11 desktop environment  
**Branch:** `feature/storage-intelligence-2.0`  
**Release note:** source publication does not imply a completed physical-device validation. Keep the app local-only; do not expose its Flask server to the public Internet.

## 1. Product goal

Turn the current storage view into a reliable disk-usage investigation tool. The application must explain where storage is used, distinguish measured values from estimates, show scan coverage, and make cleanup suggestions without deleting files unexpectedly.

This is an original NEXUS implementation informed by common patterns in WizTree, TreeSize, WinDirStat, SpaceSniffer and Windows Storage. It must not copy their branding or interface assets.

## 2. Reference capabilities to adopt

| Reference pattern | NEXUS implementation |
|---|---|
| WizTree: fast file inventory and large-file ranking | Efficient file inventory; optional NTFS MFT backend only after a separate security/reliability review |
| TreeSize: hierarchical folder sizes and reports | Expandable folder tree, sortable size columns, CSV/PDF reports |
| WinDirStat: file-type breakdown and treemap | Extension/category summary and interactive treemap |
| SpaceSniffer: visual navigation and filters | Click-to-drill treemap, size/type/path filters |
| Windows Storage: categorized usage and cleanup guidance | Storage categories and explainable, review-first cleanup recommendations |

Feature availability in reference products varies by edition and version. These are design inspirations, not claims of identical implementation.

## 3. Required architecture

Separate the application into these layers:

1. **Volume discovery** — enumerate fixed, removable and network volumes where supported; identify the Windows system volume explicitly rather than assuming the first drive is primary.
2. **Scanner** — enumerate directories/files with configurable depth (unlimited by default), cancellation, progress callbacks and explicit error collection.
3. **Measurement** — report logical file size separately from allocated/on-disk size when available; never silently treat one as the other.
4. **Analysis** — aggregate directory totals, file-type categories, large-file rankings and duplicate candidates.
5. **Job manager** — run scans outside request/response handlers; expose job status, progress, pause/cancel where technically safe, and partial results.
6. **Local API** — validate parameters and return typed, predictable responses.
7. **UI** — display coverage, progress, results, filters, drill-down and safe actions.
8. **Cleanup service** — preview candidates, require explicit confirmation, log outcomes and verify actual reclaimed space.

Keep scanning and cleanup operations local. Do not upload file names, paths, hashes or disk inventories to external services.

## 4. Scanner correctness requirements

- Discover volumes dynamically; include drive type, filesystem, total/free capacity and system-volume flag.
- Support selecting a volume or a specific folder.
- Do not impose a fixed four-level depth on full scans.
- Make exclusions visible and configurable. Exclusions must not silently hide common large folders such as development dependencies or caches.
- Use filesystem error callbacks and collect inaccessible paths, permission errors and I/O failures.
- Do not follow directory symlinks/junctions by default; detect and report skipped reparse points to avoid loops and double counting.
- Handle files disappearing or changing during a scan without crashing.
- Normalize and validate paths before any cleanup operation.
- Keep partial results available and mark the scan as partial when errors or exclusions exist.
- Expose thresholds for large-file search; do not hard-code a 1 GiB minimum.
- Avoid claiming a scan is complete when errors, timeouts or exclusions affected coverage.

## 5. Job API contract (proposed)

- `POST /api/storage/scans` — start scan with selected volume/path and options; return `scan_id`.
- `GET /api/storage/scans/{scan_id}` — status, phase, files/directories processed, bytes observed, progress estimate, elapsed time and error counts.
- `POST /api/storage/scans/{scan_id}/cancel` — request cancellation.
- `GET /api/storage/scans/{scan_id}/summary` — volume totals, category totals and coverage.
- `GET /api/storage/scans/{scan_id}/folders` — paginated/sortable folder tree.
- `GET /api/storage/scans/{scan_id}/large-files` — configurable size threshold and filters.
- `GET /api/storage/scans/{scan_id}/duplicates` — duplicate candidates, with staged hashing (size first, then hash).
- `POST /api/storage/cleanup/preview` — produce a preview only; never delete.
- `POST /api/storage/cleanup/execute` — execute only an explicitly confirmed preview token and revalidate every target.

Use consistent states: `queued`, `running`, `cancelling`, `cancelled`, `completed`, `completed_with_warnings`, `failed`.

Progress must be based on actual work counters. If total work is unknown, show an indeterminate progress indicator instead of inventing a percentage.

## 6. UI requirements

### Storage overview
- One card per detected volume.
- Capacity, used, free, filesystem and drive type.
- Clearly identify the Windows system volume.
- Show the timestamp and status of the last scan.

### Scan workspace
- Volume/folder selector and scan options.
- Real progress, elapsed time, processed items and warning count.
- Pause only if the scanner can safely support it; always support cancellation.
- Partial results and clear access-denied / skipped-path reporting.

### Results
- Folder tree sorted by size.
- Large files with configurable threshold and path.
- File-type/category breakdown.
- Interactive treemap with folder drill-down.
- Filters by extension, size, path and modified date.
- Duplicate candidates with hash method and verification status.
- Export CSV and JSON; PDF can follow after core results are stable.

### Cleanup
- Explain why an item is proposed.
- Show exact path, type, estimated reclaimable space and risk category.
- Preview and confirmation required.
- Protected/system/application data excluded by default.
- Show deleted, skipped and failed counts plus measured free-space change.
- No bulk destructive action without a clear review step.

## 7. Data integrity and safety rules

- Read-only scanning by default.
- No automatic deletion, registry edits, service changes or system-file modification.
- Cleanup must use an allowlist of supported temporary locations and validate paths against traversal and symlink/reparse-point attacks.
- Never trust a stale scan result as permission to delete; re-check file identity, location and eligibility at execution time.
- Use least privilege. Do not require administrator rights for ordinary user-folder scans.
- Do not elevate automatically.
- Keep an auditable local operation log without collecting unrelated personal data.

## 8. Test strategy and acceptance criteria

### Unit tests
- Recursive aggregation at depths greater than four.
- Empty folders, hidden files, large files and mixed extensions.
- Permission-denied and disappearing-file scenarios.
- Symlinks/reparse points and loop prevention.
- Size threshold boundaries.
- Duplicate detection: same size but different content, same content with different names.
- Path traversal and cleanup allowlist validation.
- Logical size vs allocated size labeling.

### Integration tests
- API starts a job and returns a stable scan ID.
- Polling reports changing counters and terminal state.
- Cancellation is acknowledged and stops further traversal.
- Partial scans include errors and never report clean completion.
- Cleanup preview has no side effects.
- Execution revalidates targets and returns per-item outcomes.

### Windows validation (mandatory before merge)
- Windows 10 and Windows 11.
- NTFS system drive and a secondary volume.
- Removable drive where available.
- User profile with OneDrive/redirected folders where available.
- Restricted folders and access-denied cases.
- Large directory tree and many small files.
- Compare reported volume totals with Windows Storage / File Explorer; document expected differences such as metadata, hard links, compression and reserved space.

### Release gates
- Existing tests continue to pass.
- New tests pass on Windows CI or a documented Windows test machine.
- UI remains responsive during a long scan.
- No scan claims complete coverage when errors or exclusions exist.
- Cleanup preview is non-destructive and execution is confirmed.
- `main` remains unchanged until review and approval.

## 9. Delivery phases

1. **P0 — correctness foundation:** volume discovery, recursive scanner, error accounting, path safety and tests.
2. **P1 — background scan jobs:** implemented on the feature branch: bounded in-process job manager, threaded scans, real file/directory/byte counters, indeterminate progress UI, polling, cooperative cancellation, partial results and job API. Pause is intentionally deferred because the current filesystem walker has no safe pause boundary. Added unit and API tests; CI and physical Windows validation remain release gates.
3. **P2 — analysis views:** folder tree, large files, categories and exports.
4. **P3 — visual storage map:** interactive treemap and filters.
5. **P4 — duplicate analysis:** staged hashing and duplicate review.
6. **P5 — safe cleanup:** preview, confirmation, revalidation and operation log.
7. **P6 — Windows validation and release review.**

## 10. Definition of done

A scan is trustworthy only when it reports the selected scope, scan timestamp, exclusions, inaccessible paths, errors and completion state. A cleanup is successful only when per-item outcomes and the observed free-space change are reported. Visual polish is secondary to accurate measurement and safe behavior.
