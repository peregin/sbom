# SBOM Validation
SBOM utilities for validating an input file from an OCI function

## CycloneDX JSON schema repo
https://github.com/CycloneDX/specification

## Install Fn CLI
```shell
brew update && brew install fn
fn version
```

## Running the tests
```shell
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r dev-requirements.txt
pytest
```

## Deploy the application as function
```shell
# Create or update Fn context for OCI - eu-zurich-1
fn create context sbom-fn --provider oracle
fn use context sbom-fn

# Configure OCI provider settings in web-compartment
fn update context oracle.profile DEFAULT
fn update context oracle.compartment-id ocid1.compartment.oc1..aaaaaaaav4hpjodtlpnk5xkijdownucejdi7pdebnanndzzmwd6cgyev5foq
fn update context api-url https://functions.eu-zurich-1.oci.oraclecloud.com

# Get tenancy namespace
oci os ns get

# Setup OCIR
fn update context registry eu-zurich-1.ocir.io/zrtsrfizmrok/functions
fn-validate % docker login eu-zurich-1.ocir.io -u zrtsrfizmrok/lev...
fn update context registry eu-zurich-1.ocir.io/zrtsrfizmrok/functions

# Deploy with web-net
fn create app sbom-app --annotation oracle.com/oci/subnetIds='["ocid1.subnet.oc1.eu-zurich-1.aaaaaaaagakviiodxfjrqpbp7h5cgl4ychpzouxfcn2lqfzytpfsmrb6joha"]'

# Deploy the latest version once everything is configured
fn -v deploy --app sbom-app
```

## Create an API gateway connected to the function
```shell
oci api-gateway gateway create \
  --compartment-id ocid1.compartment.oc1..aaaaaaaav4hpjodtlpnk5xkijdownucejdi7pdebnanndzzmwd6cgyev5foq \
  --display-name sbom-gw \
  --endpoint-type PUBLIC \
  --subnet-id ocid1.subnet.oc1.eu-zurich-1.aaaaaaaagakviiodxfjrqpbp7h5cgl4ychpzouxfcn2lqfzytpfsmrb6joha \
  --region eu-zurich-1
  
oci api-gateway gateway list \
  --compartment-id ocid1.compartment.oc1..aaaaaaaav4hpjodtlpnk5xkijdownucejdi7pdebnanndzzmwd6cgyev5foq \
  --query "data[?\"display-name\"=='sbom-gw'].id | [0]" \
  --raw-output \
  --region eu-zurich-1
  
# w-deployment.json contains the function OCID!!!
# python
oci api-gateway deployment create \
  --compartment-id ocid1.compartment.oc1..aaaaaaaav4hpjodtlpnk5xkijdownucejdi7pdebnanndzzmwd6cgyev5foq \
  --display-name sbom-validate-deployment \
  --gateway-id ocid1.apigateway.oc1.eu-zurich-1.amaaaaaauhyoo2iardlj4oicdvjhsbsoikji3ugx7gqsbm4nmrvuzdwxffga \
  --path-prefix "/sbom" \
  --specification file://gw-deployment.json \
  --region eu-zurich-1  
# java
oci api-gateway deployment create \
  --compartment-id ocid1.compartment.oc1..aaaaaaaav4hpjodtlpnk5xkijdownucejdi7pdebnanndzzmwd6cgyev5foq \
  --display-name sbom-validate-java-deployment \
  --gateway-id ocid1.apigateway.oc1.eu-zurich-1.amaaaaaauhyoo2iardlj4oicdvjhsbsoikji3ugx7gqsbm4nmrvuzdwxffga \
  --path-prefix "/v2/sbom" \
  --specification file://gw-deployment.json \
  --region eu-zurich-1
  
oci api-gateway deployment list \
  --compartment-id ocid1.compartment.oc1..aaaaaaaav4hpjodtlpnk5xkijdownucejdi7pdebnanndzzmwd6cgyev5foq \
  --gateway-id ocid1.apigateway.oc1.eu-zurich-1.amaaaaaauhyoo2iardlj4oicdvjhsbsoikji3ugx7gqsbm4nmrvuzdwxffga \
  --query "data[?\"display-name\"=='sbom-validate-deployment'].id | [0]" \
  --raw-output \
  --region eu-zurich-1
  
oci api-gateway deployment get \
  --deployment-id ocid1.apideployment.oc1.eu-zurich-1.amaaaaaauhyoo2iahjhvwqybrxdpee3ab4wvmytuhnoxwfnp56s2gxwxwpkq \
  --region eu-zurich-1 \
  --query "data.endpoint" \
  --raw-output
  
# policies
oci iam dynamic-group create \
  --name dg-api-gw \
  --description "Dynamic group for API Gateways calling Functions" \
  --matching-rule "ALL {resource.type = 'ApiGateway', resource.compartment.id = 'ocid1.compartment.oc1..aaaaaaaav4hpjodtlpnk5xkijdownucejdi7pdebnanndzzmwd6cgyev5foq'}"
  
oci iam policy create \
  --name allow-dg-api-gw-use-functions \
  --compartment-id ocid1.compartment.oc1..aaaaaaaav4hpjodtlpnk5xkijdownucejdi7pdebnanndzzmwd6cgyev5foq \
  --description "Allow API Gateway dynamic group to invoke Functions in sbom compartment" \
  --statements '[
    "Allow dynamic-group dg-api-gw to use functions-family in compartment web-compartment"
  ]'
```

## Testing
```shell
# valid file
fn invoke sbom-app sbom-validate << 'EOF'
{
  "bomFormat": "CycloneDX",
  "specVersion": "1.5",
  "version": 1,
  "metadata": {
    "timestamp": "2024-01-01T00:00:00Z",
    "tools": [
      { "name": "sbom-validator-test" }
    ]
  }
}
EOF

# invalid file
fn invoke sbom-app sbom-validate << 'EOF'
{
  "bomFormat": "CycloneDX",
  "version": 1
}
EOF

# via API gateway
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{
    "bomFormat": "CycloneDX",
    "specVersion": "1.5",
    "version": 1,
    "metadata": {
      "timestamp": "2024-01-01T00:00:00Z",
      "tools": [{ "name": "sbom-gw-test" }]
    }
  }' \
  "https://lpicdvhygualtp6ab62aw2t6de.apigateway.eu-zurich-1.oci.customer-oci.com/sbom/validate"
  
  
curl -s -X POST \
  -H "Content-Type: application/json" \
  --data-binary @"../samples/test_small.json" \
  https://lpicdvhygualtp6ab62aw2t6de.apigateway.eu-zurich-1.oci.customer-oci.com/sbom/validate | jq .
  
# python
curl -s -X POST \
  -H "Content-Type: application/json" \
  --data-binary @"../samples/telemetry.cdx.json" \
  https://lpicdvhygualtp6ab62aw2t6de.apigateway.eu-zurich-1.oci.customer-oci.com/sbom/validate | jq .
# java
curl -s -X POST \
  -H "Content-Type: application/json" \
  --data-binary @"../samples/telemetry.cdx.json" \
  https://lpicdvhygualtp6ab62aw2t6de.apigateway.eu-zurich-1.oci.customer-oci.com/v2/sbom/validate | jq .
```

## Debugging
```shell
fn list apps
fn list functions sbom-app
fn inspect context
fn inspect app sbom-app
fn build
docker run --rm eu-zurich-1.ocir.io/zrtsrfizmrok/functions/sbom-validate:0.0.8 ls -la /function/
```
