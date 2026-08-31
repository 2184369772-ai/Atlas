# Java Bridge Quickstart

This synthetic example generates project-local Java scaffold for the only two
capabilities supported by Java Bridge v0.1: Enterprise Intake and Operation
Outcome. The generated Java code does not use Python or Atlas at runtime.

From the repository root, with Atlas installed and JDK 17+ available:

```powershell
powershell -ExecutionPolicy Bypass -File examples/java-bridge-quickstart/run.ps1
```

Or on a shell with Bash:

```bash
bash examples/java-bridge-quickstart/run.sh
```

Both scripts refuse to overwrite an existing generated directory. Remove the
synthetic `generated` directory before running the example again.
