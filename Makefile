.PHONY: backend-test frontend-test
backend-test:
	cd backend && pytest
frontend-test:
	cd frontend && npm test
