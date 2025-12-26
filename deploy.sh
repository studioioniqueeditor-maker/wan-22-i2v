#!/bin/bash

# -------------------------------------------------------
# 🚀 VIVID FLOW DEPLOYMENT SCRIPT
# -------------------------------------------------------

set -e  # Exit on error

# 1. Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: I can't find your .env file!"
    echo "   Please make sure you have created a file named '.env' with your passwords and keys."
    exit 1
fi

echo "✅ Found .env file."

# 2. Read the project ID from the .env file
PROJECT_ID=$(grep GOOGLE_CLOUD_PROJECT .env | cut -d '=' -f2)

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: I couldn't find GOOGLE_CLOUD_PROJECT in your .env file."
    exit 1
fi

echo "✅ Using Project ID: $PROJECT_ID"

# 3. Verify requirements.txt has correct google-genai version
echo "🔍 Checking dependencies..."
if grep -q "google-genai>=1.56.0" requirements.txt; then
    echo "✅ google-genai version 1.56.0+ configured"
else
    echo "⚠️  Warning: google-genai version not pinned. Updating requirements.txt..."
    # Update to use >=1.56.0
    sed -i.bak 's/google-genai$/google-genai>=1.56.0/' requirements.txt
fi

# 4. Check for service account key
if [ ! -f "service_account.json" ] && [ -z "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
    echo "⚠️  Warning: No service_account.json found."
    echo "   Make sure gcloud is authenticated or set GOOGLE_APPLICATION_CREDENTIALS"
    echo "   Checking gcloud authentication..."
    gcloud auth list --filter=status:ACTIVE --format="value(account)" | head -1
fi

# 5. Prepare the 'secrets' (environment variables) for Google Cloud
echo "🔮 Preparing your secrets..."
# Filter out comments, empty lines, and join with commas
ENV_VARS=$(grep -v '^#' .env | grep -v '^$' | grep '=' | tr '\n' ',' | sed 's/,$//')

if [ -z "$ENV_VARS" ]; then
    echo "❌ Error: No environment variables found in .env file"
    exit 1
fi

echo "✅ Found $(echo $ENV_VARS | tr ',' '\n' | wc -l) environment variables"

# 6. Check if Dockerfile exists
if [ ! -f "Dockerfile" ]; then
    echo "❌ Error: Dockerfile not found"
    exit 1
fi
echo "✅ Dockerfile found"

# 7. The Big Launch Command
echo ""
echo "🚀 Launching to Google Cloud Run..."
echo "   Platform: managed"
echo "   Region: us-central1"
echo "   Service: vivid-flow"
echo "   Project: $PROJECT_ID"
echo ""
echo "   (This might take 5-10 minutes...)"

echo "-------------------------------------------------------"

gcloud run deploy vivid-flow \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --project "$PROJECT_ID" \
    --set-env-vars "$ENV_VARS" \
    --memory 2Gi \
    --cpu 1 \
    --timeout 3600 \
    --max-instances 5

DEPLOY_STATUS=$?

echo "-------------------------------------------------------"

if [ $DEPLOY_STATUS -eq 0 ]; then
    echo "🎉 SUCCESS! Your app is live!"
    echo ""
    echo "To view your deployed app:"
    echo "  gcloud run services describe vivid-flow --region us-central1 --project $PROJECT_ID"
    echo ""
    echo "To test the API:"
    echo "  curl -H 'X-API-Key: YOUR_KEY' https://YOUR_URL/api/v1/admin/stats"
    exit 0
else
    echo "💥 DEPLOYMENT FAILED!"
    echo ""
    echo "Common issues:"
    echo "  1. Quota limits exceeded - check Google Cloud Console"
    echo "  2. Missing permissions - ensure service account has Cloud Run Admin, Storage Admin"
    echo "  3. Invalid .env variables - run: python3 diagnose.py"
    echo ""
    echo "Run 'python3 diagnose.py' locally to verify configuration first."
    exit 1
fi
