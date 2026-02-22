#!/usr/bin/env bash
set -e

# Change directory to project root
cd "$(dirname "$0")/.."

echo "Starting GiniCast Phase 1 Pipeline: All Configured Metrics"
ginicast-data pull --all

echo "Running Audit..."
ginicast-data audit

echo "Pipeline complete."
