run_format:
	SECRET_KEY=123 poetry run sh run_format.sh

freeze:
	poetry run pip freeze > requirements.txt
