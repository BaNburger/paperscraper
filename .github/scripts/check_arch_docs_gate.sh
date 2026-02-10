#!/usr/bin/env bash
set -euo pipefail

required_docs=(
  "01_TECHNISCHE_ARCHITEKTUR.md"
  "04_ARCHITECTURE_DECISIONS.md"
  "05_IMPLEMENTATION_PLAN.md"
)

architecture_prefixes=(
  "alembic/versions/"
  "paper_scraper/api/v1/"
  "paper_scraper/core/database.py"
  "paper_scraper/core/permissions.py"
  "paper_scraper/jobs/"
  "paper_scraper/mcp/"
  "paper_scraper/modules/ingestion/"
  "paper_scraper/modules/integrations/"
  "paper_scraper/modules/papers/"
  "paper_scraper/modules/scoring/"
  "paper_scraper/modules/search/"
)

event_name="${GITHUB_EVENT_NAME:-}"
head_sha="${GITHUB_HEAD_SHA:-$(git rev-parse HEAD)}"
base_sha="${GITHUB_BASE_SHA:-}"

if [[ -z "${base_sha}" ]]; then
  if git rev-parse HEAD^ >/dev/null 2>&1; then
    base_sha="$(git rev-parse HEAD^)"
  else
    base_sha="$(git rev-list --max-parents=0 HEAD)"
  fi
fi

if ! git cat-file -e "${base_sha}^{commit}" 2>/dev/null; then
  echo "Base commit ${base_sha} not present locally. Fetching main for merge-base fallback."
  git fetch --no-tags --depth=1 origin main
  base_sha="$(git merge-base HEAD origin/main)"
fi

changed_files="$(git diff --name-only "${base_sha}" "${head_sha}")"

if [[ -z "${changed_files}" ]]; then
  echo "No changed files detected between ${base_sha} and ${head_sha}. Skipping documentation gate."
  exit 0
fi

architecture_changed=0
while IFS= read -r file; do
  for prefix in "${architecture_prefixes[@]}"; do
    if [[ "${file}" == "${prefix}"* ]]; then
      architecture_changed=1
      break 2
    fi
  done
done <<< "${changed_files}"

if [[ "${architecture_changed}" -eq 0 ]]; then
  echo "No architecture-impacting files changed. Documentation gate passed."
  exit 0
fi

missing_docs=()
for doc in "${required_docs[@]}"; do
  if ! grep -Fxq "${doc}" <<< "${changed_files}"; then
    missing_docs+=("${doc}")
  fi
done

if [[ "${#missing_docs[@]}" -gt 0 ]]; then
  echo "Architecture-impacting changes detected for event: ${event_name:-unknown}."
  echo "Changed files:"
  while IFS= read -r file; do
    echo "- ${file}"
  done <<< "${changed_files}"
  echo "Missing required documentation updates:"
  for doc in "${missing_docs[@]}"; do
    echo "- ${doc}"
  done
  echo "Please update all mandatory architecture docs in the same change."
  exit 1
fi

echo "Architecture documentation gate passed."
