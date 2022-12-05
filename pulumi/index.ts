
import * as pulumi from "@pulumi/pulumi";
import * as gcp from "@pulumi/gcp";

const version = "1.6.1";

const provider = new gcp.Provider(
    "gcp",
    {
	project: "partygate",
	region: "europe-west1",
    }
);

const enableCloudRun = new gcp.projects.Service(
    "enable-cloud-run",
    {
	service: "run.googleapis.com",
    },
    {
	provider: provider
    }
);

const enableComputeEngine = new gcp.projects.Service(
    "enable-compute-engine",
    {
	service: "compute.googleapis.com",
    },
    {
	provider: provider
    }
);

const enableCloudDns = new gcp.projects.Service(
    "enable-cloud-dns",
    {
	service: "dns.googleapis.com",
    },
    {
	provider: provider
    }
);

const repo = "europe-west1-docker.pkg.dev/partygate/partygate";

const webVersion = version;
const webImage = repo + "/web:" + webVersion;

const sparqlVersion = version;
const sparqlImage = repo + "/sparql:" + sparqlVersion;

const sparqlService = new gcp.cloudrun.Service(
    "sparql-service",
    {
	name: "sparql",
	location: "europe-west1",
	template: {
	    metadata: {
		labels: {
		    version: "v" + sparqlVersion.replace(/\./g, "-"),
		},		
		annotations: {
                    "autoscaling.knative.dev/minScale": "0",
                    "autoscaling.knative.dev/maxScale": "1",
		}
	    },
            spec: {
		containerConcurrency: 1000,
		containers: [
		    {
			image: sparqlImage,
			ports: [
                            {
				"name": "http1", // Must be http1 or h2c.
				"containerPort": 8089
                            }
			],
			resources: {
                            limits: {
				cpu: "1000m",
				memory: "256Mi",
                            }
			},
		    }
		],
            },
	},
    },
    {
	provider: provider,
	dependsOn: [enableCloudRun],
    }
);

const sparqlUrl = sparqlService.statuses[0].url;

export const sparqlResource = sparqlUrl.apply(
    x => x.replace(/^https:\/\//, "")
);

const webService = new gcp.cloudrun.Service(
    "web-service",
    {
	name: "web",
	location: "europe-west1",
	template: {
	    metadata: {
		labels: {
		    version: "v" + webVersion.replace(/\./g, "-"),
		},		
		annotations: {
                    "autoscaling.knative.dev/minScale": "0",
                    "autoscaling.knative.dev/maxScale": "1",
		}
	    },
            spec: {
		containerConcurrency: 1000,
		containers: [
		    {
			image: webImage,
			ports: [
                            {
				"name": "http1", // Must be http1 or h2c.
				"containerPort": 8080
                            }
			],
			commands: [
			    "/usr/local/bin/serve",
			    "0:8080",                // Listen
			    sparqlResource,	     // SPARQL API resource
			    "https",		     // SPARQL scheme
			    "",			     // Base
			],
			resources: {
                            limits: {
				cpu: "1000m",
				memory: "256Mi",
                            }
			},
		    }
		],
            },
	},
    },
    {
	provider: provider,
	dependsOn: [enableCloudRun],
    }
);

const allUsersPolicy = gcp.organizations.getIAMPolicy(
    {
	bindings: [{
            role: "roles/run.invoker",
            members: ["allUsers"],
	}],
    },
    {
	provider: provider,
    }
);

const webNoAuthPolicy = new gcp.cloudrun.IamPolicy(
    "web-no-auth-policy",
    {
	location: webService.location,
	project: webService.project,
	service: webService.name,
	policyData: allUsersPolicy.then(pol => pol.policyData),
    },
    {
	provider: provider,
    }
);

const sparqlNoAuthPolicy = new gcp.cloudrun.IamPolicy(
    "sparql-no-auth-policy",
    {
	location: sparqlService.location,
	project: sparqlService.project,
	service: sparqlService.name,
	policyData: allUsersPolicy.then(pol => pol.policyData),
    },
    {
	provider: provider,
    }
);

/*
const webDomainMapping = new gcp.cloudrun.DomainMapping(
    "web-domain-mapping",
    {
	"name": "thing.whatever.domain",
	location: "europe-west1",
	metadata: {
	    namespace: "partygate",
	},
	spec: {
	    routeName: webService.name,
	}
    },
    {
	provider: provider
    }
);

// Get rrdata from domain mapping.
export const webhost = webDomainMapping.statuses.apply(
    x => x[0].resourceRecords
).apply(
    x => x ? x[0] : { rrdata: "" }
).apply(
    x => x.rrdata
);

const innovateZone = new gcp.dns.ManagedZone(
    "innovate-zone",
    {
	name: "innovate",
	description: "innovate.domain",
	dnsName: "innovate.domain.",
	labels: {
	},
    },
    {
	provider: provider,
	dependsOn: [enableCloudDns],
    }
);

const recordSet = new gcp.dns.RecordSet(
    "web-record",
    {
	name: pulumi.interpolate`graph.${innovateZone.dnsName}`,
	managedZone: innovateZone.name,
	type: "CNAME",
	ttl: 300,
	rrdatas: [webhost],
    },
    {
	provider: provider,
    }
);

*/
