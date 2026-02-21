#!/bin/bash
# Verify log file integrity using checksums

VAULT_PATH="${VAULT_PATH:-/vault}"
LOGS_DIR="${LOGS_DIR:-${VAULT_PATH}/Logs}"
CHECKSUM_DIR="${LOGS_DIR}/.checksums"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "Verifying log integrity..."
echo ""

VERIFIED=0
TAMPERED=0
MISSING=0

for log_file in ${LOGS_DIR}/*.json; do
  if [ ! -f "$log_file" ]; then
    continue
  fi

  filename=$(basename "$log_file")
  checksum_file="${CHECKSUM_DIR}/${filename}.sha256"

  if [ ! -f "$checksum_file" ]; then
    echo -e "${YELLOW}? $filename (no checksum)${NC}"
    MISSING=$((MISSING + 1))
    continue
  fi

  # Compute current checksum
  computed=$(sha256sum "$log_file" | awk '{print $1}')

  # Load stored checksum
  stored=$(cat "$checksum_file" | tr -d '[:space:]')

  if [ "$computed" = "$stored" ]; then
    echo -e "${GREEN}✓ $filename${NC}"
    VERIFIED=$((VERIFIED + 1))
  else
    echo -e "${RED}✗ $filename TAMPERED${NC}"
    echo "  Computed: $computed"
    echo "  Stored:   $stored"
    TAMPERED=$((TAMPERED + 1))
  fi
done

echo ""
echo "Summary:"
echo "  Verified: $VERIFIED"
echo "  Tampered: $TAMPERED"
echo "  Missing checksum: $MISSING"

if [ $TAMPERED -gt 0 ]; then
  echo ""
  echo -e "${RED}WARNING: Log tampering detected!${NC}"
  exit 1
fi

exit 0
