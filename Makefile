
VERSION=1.5

all:
	rapper -i turtle -o ntriples partygate.ttl > partygate.ntriples
	rapper -i turtle -o rdfxml partygate.ttl > partygate.rdf
	rapper -i turtle -o json partygate.ttl > partygate.json
	rdfproc -n -s sqlite partygate.db parse partygate.ttl turtle

serve:
	go build proxy/serve.go

lodlive:
	git clone http://github.com/cybermaggedon/lodlive
	(cd lodlive; git checkout default-local)
	cp query.html lodlive/
	cp lodlive.profile.js lodlive/js/

CONTAINER=partygate/web
CONTAINER2=partygate/sparql

WEB_CONTAINER=docker.io/cybermaggedon/partygate-web:${VERSION}
SPARQL_CONTAINER=docker.io/cybermaggedon/partygate-sparql:${VERSION}

containers: lodlive serve Dockerfile.web Dockerfile.sparql
	docker build -t partygate-web -f Dockerfile.web .
	docker tag partygate-web ${WEB_CONTAINER}
	docker build -t partygate-sparql -f Dockerfile.web .
	docker tag partygate-sparql ${SPARQL_CONTAINER}

push:
	sudo buildah push docker.io/cybermaggedon/partygate-web:${VERSION}
	sudo buildah push docker.io/cybermaggedon/partygate-web:latest
	sudo buildah push docker.io/cybermaggedon/partygate-sparql:${VERSION}
	sudo buildah push docker.io/cybermaggedon/partygate-sparql:latest

run:
	sudo podman run -d --name web \
		-p 8080/tcp --expose=8080 \
		--ip=10.88.1.1 --add-host sparql:10.88.1.2 \
		docker.io/cybermaggedon/partygate-web:${VERSION}
	sudo podman run -d --name sparql -p 8089/tcp --ip=10.88.1.2 \
		docker.io/cybermaggedon/partygate-sparql:${VERSION}

stop:
	sudo podman rm -f web sparql

