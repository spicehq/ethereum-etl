docker:
	docker build -f Dockerfile.compactor . -t ghcr.io/spicehq/etl-compactor:local

DIR=/Users/phillip/code/spicehq/data-platform

docker-run:
	docker run --rm -it -v ${DIR}/output:/app/output ghcr.io/spicehq/etl-compactor:local /bin/bash

docker-dev:
	docker run --rm -it -v ${DIR}/output:/app/output -v ${PWD}:/app/dev ghcr.io/spicehq/etl-compactor:local /bin/bash