.PHONY: inspect plan run check

inspect:
	python3 linter.py inspect fixture --out inspection.json

plan:
	python3 linter.py plan fixture --out plan.json

run:
	python3 linter.py run fixture --out diagnostics.json --log acquisition.log

check:
	python3 check.py
