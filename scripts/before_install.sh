#!/bin/bash
set -euo pipefail

# Create a fresh project directory. (This is mainly
# to ensure that these scripts work on a bare server.)
rm -Rf /home/datamade/pic
mkdir -p /home/datamade/pic

# Decrypt files encrypted with blackbox
cd /opt/codedeploy-agent/deployment-root/$DEPLOYMENT_GROUP_ID/$DEPLOYMENT_ID/deployment-archive/ && chown -R datamade.datamade . && sudo -H -u datamade blackbox_postdeploy
