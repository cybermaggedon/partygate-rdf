
VERSION=$(shell git describe | sed 's/^v//')

all:

curate:
	rm -f data.db
	make turtle
	rdfproc -n -s sqlite -t synchronous=off data.db parse data.ttl turtle

# RDFlib doesn't seem to output prefix for rdf: namespace?!
turtle:
	./process/curate data schema > data.ttl.tmp
	( \
	  echo '@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .';\
	  cat data.ttl.tmp; \
	) > data.ttl
	rm -f data.ttl.tmp

REPO=europe-west1-docker.pkg.dev/cyberapocalypse/ukraine
WEB_CONTAINER=${REPO}/web:${VERSION}
SPARQL_CONTAINER=${REPO}/sparql:${VERSION}

images: curate
	docker build -f Containerfile.web -t web .
	docker build -f Containerfile.sparql -t sparql .
	docker tag web ${WEB_CONTAINER}
	docker tag sparql ${SPARQL_CONTAINER}

push:
	docker push ${WEB_CONTAINER}
	docker push ${SPARQL_CONTAINER}

clean:
	-rm -f ${PROJECT}.db

	podman run -d --name web \
		-p 8080/tcp --expose=8080 \
		${WEB_CONTAINER}
	podman run -d --name sparql -p 8089/tcp \
		${SPARQL_CONTAINER}

stop:
	podman rm -f web sparql

