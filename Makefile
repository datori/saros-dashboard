.PHONY: deploy restart logs status install screenshots

deploy:
	cd frontend && npm run build
	systemctl --user restart vacuum-dashboard

restart:
	systemctl --user restart vacuum-dashboard

logs:
	journalctl --user -u vacuum-dashboard -f

status:
	systemctl --user status vacuum-dashboard

install:
	scripts/install-service.sh

screenshots:
	node scripts/screenshots.mjs
