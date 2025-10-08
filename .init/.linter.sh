#!/bin/bash
cd /home/kavia/workspace/code-generation/palestine-youth-employment-platform-147458-147468/job_matching_backend
source venv/bin/activate
flake8 .
LINT_EXIT_CODE=$?
if [ $LINT_EXIT_CODE -ne 0 ]; then
  exit 1
fi

