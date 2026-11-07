.PHONY: dev check seed demo ui ui-mock install clean
SHELL := /bin/sh

# Development secrets come from engine/.env when it exists, otherwise engine/.env.example.
# The engine refuses to start without them, which is deliberate: a missing secret must not
# silently default in production.
ENVFILE = $(CURDIR)/$(firstword $(notdir $(wildcard engine/.env)) .env.example)
ENVPATH = $(CURDIR)/engine/$(firstword $(notdir $(wildcard engine/.env)) .env.example)
LOADENV = set -a; . $(ENVPATH); set +a;

install:    ## python deps and UI deps, from a clean clone
	pip install -r engine/requirements.txt
	cd ui && if [ -f package-lock.json ]; then npm ci; else npm install; fi

dev:        ## run the API on :18000 (serves the built UI at / when ui/dist exists)
	cd engine && $(LOADENV) python -m uvicorn engine.api:app --port 18000 --reload

seed:       ## synthetic experts, panel, pulse and one sealed round; prints the magic links
	cd engine && $(LOADENV) python -m scripts.seed

demo:       ## full loop on R1043 with the synthetic panel, offline, < 60 s
	cd engine && $(LOADENV) SEED_ON_START=false python -X utf8 -m scripts.demo_replay

check:      ## everything a merge must pass
	cd engine && $(LOADENV) python -m pytest -q
	cd ui && if [ ! -d node_modules ]; then 		if [ -f package-lock.json ]; then npm ci; else npm install; fi; 	fi
	cd ui && npm run build
	python scripts/validate_fixtures.py

ui:         ## frontend dev server against the live engine on :18000
	cd ui && npm run dev:live

ui-mock:    ## frontend dev server on fixtures only, no engine needed
	cd ui && npm run dev:mock

clean:      ## drop build output and caches
	rm -rf ui/dist ui/node_modules engine/.pytest_cache reports
