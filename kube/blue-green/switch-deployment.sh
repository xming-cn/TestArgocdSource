#!/bin/bash

# Script to switch between blue and green deployments

# Function to check deployment health
check_deployment_health() {
    deployment=$1
    namespace=${2:-default}
    
    echo "Checking deployment $deployment health..."
    
    # Wait for rollout to complete
    kubectl rollout status deployment/$deployment -n $namespace
    if [ $? -ne 0 ]; then
        echo "Deployment $deployment rollout failed"
        return 1
    fi
    
    # Check if deployment is ready
    ready=$(kubectl get deployment $deployment -n $namespace -o jsonpath='{.status.readyReplicas}')
    if [ "$ready" -lt 1 ]; then
        echo "Deployment $deployment is not ready"
        return 1
    fi
    
    return 0
}

# Get current version
current_version=$(kubectl get service app-service -n default -o jsonpath='{.spec.selector.version}')
echo "Current version: $current_version"

# Determine target version
if [ "$current_version" = "blue" ]; then
    target_version="green"
    target_deployment="app-green"
else
    target_version="blue"
    target_deployment="app-blue"
fi

echo "Switching to $target_version deployment..."

# Check health of target deployment before switching
if ! check_deployment_health $target_deployment; then
    echo "Target deployment is not healthy. Aborting switch."
    exit 1
fi

# Update service selector
kubectl patch service app-service -n default -p "{\"spec\":{\"selector\":{\"version\":\"$target_version\"}}}"
if [ $? -ne 0 ]; then
    echo "Failed to update service selector"
    exit 1
fi

echo "Successfully switched to $target_version deployment"

# Verify the switch
new_version=$(kubectl get service app-service -n default -o jsonpath='{.spec.selector.version}')
if [ "$new_version" = "$target_version" ]; then
    echo "Verification successful: Service is now pointing to $target_version deployment"
else
    echo "Verification failed: Service is pointing to $new_version instead of $target_version"
    exit 1
fi
