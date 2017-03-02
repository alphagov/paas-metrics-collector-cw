.DEFAULT_GOAL := help
SHELL := /bin/bash

CF_USE_SERVICE ?= 1

.PHONY: help
help:
	@cat $(MAKEFILE_LIST) | grep -E '^[a-zA-Z_-]+:.*?## .*$$' | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

generate-manifest:
	@erb manifest.yml.erb

cf-push:
	$(if ${CF_ORG},,$(error Must specify CF_ORG))
	$(if ${CF_SPACE},,$(error Must specify CF_SPACE))
	cf target -s ${CF_SPACE}
	cf push -f <(make generate-manifest)
