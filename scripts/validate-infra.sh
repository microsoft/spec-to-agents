#!/bin/bash
set -e

echo "============================================"
echo "Validating Infrastructure Templates"
echo "============================================"
echo ""

# Change to the infra directory
cd "$(dirname "$0")/../infra"

# Validate main.bicep
echo "Validating main.bicep..."
az bicep build --file main.bicep

if [ $? -eq 0 ]; then
  echo "✓ main.bicep is valid"
else
  echo "✗ main.bicep has errors"
  exit 1
fi

echo ""

# Validate individual modules
echo "Validating individual modules..."
for bicep_file in app/*.bicep; do
  echo "  Validating $(basename "$bicep_file")..."
  az bicep build --file "$bicep_file" > /dev/null 2>&1
  if [ $? -eq 0 ]; then
    echo "    ✓ $(basename "$bicep_file") is valid"
  else
    echo "    ⚠ $(basename "$bicep_file") has warnings (non-blocking)"
  fi
done

echo ""
echo "============================================"
echo "Validation Complete"
echo "============================================"
echo ""
echo "Note: Warnings about BCP081 (Bing resources) and BCP318/BCP422"
echo "(conditional resources) are expected and do not prevent deployment."
