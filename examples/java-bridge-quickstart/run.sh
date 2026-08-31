#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
target="${1:-$script_dir/generated}"

if [[ -e "$target" ]]; then
  echo "Refusing to overwrite existing Java quickstart target: $target" >&2
  exit 1
fi

mkdir -p "$target"
atlas adapter init enterprise-intake --target "$target" --language java
atlas adapter init operation-outcome --target "$target" --language java

source_root="$target/atlas-adapters-java/src"
classes="$target/classes"
mkdir -p "$classes"
mapfile -t java_files < <(find "$source_root" -type f -name '*.java' -print)
javac -d "$classes" "${java_files[@]}"
java -cp "$classes" com.atlas.adoption.enterpriseintake.EnterpriseIntakeScaffoldSmoke
java -cp "$classes" com.atlas.adoption.operationoutcome.OperationOutcomeScaffoldSmoke
echo "Java Bridge quickstart passed: ${#java_files[@]} sources compiled; both synthetic smoke programs passed."
