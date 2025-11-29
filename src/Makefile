# ===========================
# Global Variables
# ===========================
REGISTRY = evyatar213
K8S_NAMESPACE = default

# ===========================
# Generic update command
# Usage: make update micro=<service_name>
# Example: make update micro=auth
# ===========================
update:
	@if [ -z "$(micro)" ]; then \
		echo "Please specify a microservice name. Usage: make update micro=auth"; \
		exit 1; \
	fi
	@echo "Building and pushing image for $(micro)..."
	docker build -t $(REGISTRY)/$(micro):latest -f $(micro)/Dockerfile .
	docker push $(REGISTRY)/$(micro):latest
	kubectl rollout restart deployment $(micro) -n $(K8S_NAMESPACE)
	@echo "Deployment restarted successfully for $(micro)"
	@echo "Applying manifests..."
	kubectl apply -f $(micro)/manifests/
	@echo "Done updating $(micro) service!"

# ===========================
# Helpers
# ===========================
logs:
	@if [ -z "$(micro)" ]; then \
		echo "Please specify a microservice. Usage: make logs micro=gateway"; \
		exit 1; \
	fi
	kubectl logs -l app=$(micro) -f -n $(K8S_NAMESPACE)

status:
	kubectl get pods -n $(K8S_NAMESPACE)
