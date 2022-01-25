
VERSION=1.4

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

sparql:
	-rm -rf sparql-service
	git clone http://github.com/cybermaggedon/sparql-service
	(cd sparql-service; make)
	cp sparql-service/sparql sparql

CONTAINER=partygate/web
CONTAINER2=partygate/sparql

containers: build-base build-web build-sparql
	sudo ./build-base docker.io/cybermaggedon/partygate-base
	sudo ./build-web docker.io/cybermaggedon/partygate-web:${VERSION}
	sudo ./build-sparql docker.io/cybermaggedon/partygate-sparql:${VERSION}
	sudo buildah tag docker.io/cybermaggedon/partygate-web:${VERSION} \
		docker.io/cybermaggedon/partygate-web:latest
	sudo buildah tag docker.io/cybermaggedon/partygate-sparql:${VERSION} \
		docker.io/cybermaggedon/partygate-sparql:latest

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

