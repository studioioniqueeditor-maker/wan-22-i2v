#!/bin/bash

# -------------------------------------------------------
# 🚀 VIVID FLOW DEPLOYMENT SCRIPT
# -------------------------------------------------------

# 1. Check if .env exists
if [ ! -f ".env" ]; then
    echo "❌ Error: I can\'t find your .env file!"
    echo "   Please make sure you have created a file named '.env' with your passwords and keys."
    exit 1
fi

echo "✅ Found .env file."

# 2. Read the project ID from the .env file
PROJECT_ID=$(grep GOOGLE_CLOUD_PROJECT .env | cut -d '=' -f2)

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Error: I couldn\'t find GOOGLE_CLOUD_PROJECT in your .env file."
    exit 1
fi

echo "✅ Using Project ID: $PROJECT_ID"

# 3. Prepare the 'secrets' (environment variables) for Google Cloud
# We read the .env file, ignore comments (#), and stick them together with commas
echo "🔮 Preparing your secrets..."
ENV_VARS=$(grep -v '^#' .env | grep -v '^$' | tr '\n' ',' | sed 's/,$//')

# 4. The Big Launch Command
echo "🚀 Launching to Google Cloud..."
echo "   (This might take a few minutes. Watch the magic happen below!)"
echo "-------------------------------------------------------"

gcloud run deploy vivid-flow \
    --source . \
    --platform managed \
    --region us-central1 \
    --allow-unauthenticated \
    --project "$PROJECT_ID" \
    --set-env-vars "$ENV_VARS"

echo "-------------------------------------------------------"
if [ $? -eq 0 ]; then
    echo "🎉 SUCCESS! Your app is live!"
else
    echo "💥 Uh oh. Something went wrong with the deployment."
fi
