#!/bin/bash
# ForensixOne - Long-Term Privileged Access Setup
# This script configures the host for secure hardware imaging.

set -e

echo "🛡️ Starting ForensixOne Privileged Environment Setup..."

# 1. Create Forensics group (if not uses 'disk')
# For simplicity with existing setups, we'll ensure the user is in 'disk'
# but 'forensics' is more granular for production.
GROUP_NAME="forensics"

if ! getent group $GROUP_NAME > /dev/null; then
    echo "Creating group: $GROUP_NAME"
    sudo groupadd $GROUP_NAME
fi

echo "Adding current user ($USER) to $GROUP_NAME and disk groups..."
sudo usermod -aG $GROUP_NAME $USER
sudo usermod -aG disk $USER

# 2. Deploy Udev Rules
RULES_FILE="scripts/99-forensics-disks.rules"
DEST_RULES="/etc/udev/rules.d/99-forensics-disks.rules"

if [ -f "$RULES_FILE" ]; then
    echo "Installing udev rules to $DEST_RULES..."
    sudo cp "$RULES_FILE" "$DEST_RULES"
    sudo udevadm control --reload-rules && sudo udevadm trigger
else
    echo "❌ Error: $RULES_FILE not found."
    exit 1
fi

echo "✅ Environment configured!"
echo ""
echo "🚀 NEXT STEPS:"
echo "1. LOG OUT and LOG BACK IN to apply group changes."
echo "2. Start your dedicated acquisition worker with:"
echo "   celery -A config worker -l info -Q privileged"
echo ""
echo "The platform will now be able to image disks securely. 🕵️‍♂️🏛️"
