lint: ## Run the code linter.
	ruff ./


style:
	black .
	ruff check ./ --fix
	@echo "The style pass! ✨ 🍰 ✨"	