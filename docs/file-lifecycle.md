# File Lifecycle

Atlas File Lifecycle is a reference-level Candidate for file/source identity and lifecycle semantics.

It covers:

- file/source identity
- file metadata such as name, type, size, and checksum when available
- file reference kind and locator
- lifecycle state
- retention intent
- file-level issues
- state-transition checks
- Shadow comparison vocabulary

Project code still owns upload, download, object storage, permissions, business version rules, ImportBatch, database transactions, supplement/approval flows, and business meaning of the file.

Minimal example:

```bash
python examples/file-lifecycle-synthetic/run_example.py
```

The expected Shadow result is `MATCH` with no lost metadata or issues.
