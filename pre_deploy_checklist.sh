#!/bin/bash

echo "=========================================="
echo "  Pre-Deployment Validation Checklist"
echo "=========================================="
echo ""

# Track failures
FAILS=0

# Function to check
check() {
    local name="$1"
    local cmd="$2"
    
    echo -n "Checking $name... "
    if eval "$cmd" > /dev/null 2>&1; then
        echo "✅ PASS"
        return 0
    else
        echo "❌ FAIL"
        FAILS=$((FAILS + 1))
        return 1
    fi
}

# 1. Check Python 3.8+
check "Python 3.8+" "python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)'"

# 2. Check requirements.txt exists
check "requirements.txt exists" "test -f requirements.txt"

# 3. Check google-genai version in requirements
check "google-genai>=1.56.0 in requirements" "grep -q 'google-genai>=1.56.0' requirements.txt"

# 4. Check Dockerfile exists
check "Dockerfile exists" "test -f Dockerfile"

# 5. Check Dockerfile has healthcheck
check "Dockerfile healthcheck" "grep -q 'HEALTHCHECK' Dockerfile"

# 6. Check deploy.sh exists and is executable
check "deploy.sh executable" "test -x deploy.sh"

# 7. Check .env exists
check ".env file exists" "test -f .env"

# 8. Check .env has GOOGLE_CLOUD_PROJECT
check ".env has GOOGLE_CLOUD_PROJECT" "grep -q 'GOOGLE_CLOUD_PROJECT' .env"

# 9. Check .env has required variables
check ".env has admin config" "grep -q 'ADMIN_API_KEY' .env"

# 10. Check web_app.py has health route
check "web_app.py health route" "grep -q 'def health_check' web_app.py"

# 11. Check vertex_ai_veo_client.py exists
check "vertex_ai_veo_client.py exists" "test -f vertex_ai_veo_client.py"

# 12. Check vertex_ai_veo_client.py has inspection function
check "Inspection function exists" "grep -q '_inspect_operation_failure' vertex_ai_veo_client.py"

# 13. Check job_queue.py has logging
check "Job queue logging" "grep -q 'Job:' job_queue.py"

# 14. Check diagnose.py exists
check "diagnose.py exists" "test -f diagnose.py"

# 15. Check test_veo_fix.py exists
check "test_veo_fix.py exists" "test -f test_veo_fix.py"

echo ""
echo "=========================================="
if [ $FAILS -eq 0 ]; then
    echo "✅ ALL CHECKS PASSED!"
    echo "Ready to run ./deploy.sh"
    echo ""
    echo "Next steps:"
    echo "  1. python3 diagnose.py (final verification)"
    echo "  2. python3 test_veo_fix.py (test the fix)"
    echo "  3. ./deploy.sh (deploy to Cloud Run)"
    exit 0
else
    echo "❌ $FAILS checks failed"
    echo "Please fix the issues above before deploying"
    exit 1
fi
