.PHONY: test demo benchmark

test:
	PYTHONPATH=src python -m unittest discover -s tests -v

demo:
	PYTHONPATH=src python -m candidate_finality.demo

benchmark:
	PYTHONPATH=src python -m candidate_finality.benchmark --iterations 1000 --warmup 100

