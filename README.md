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

# Deployment in web-net
fn create app sbom-app --annotation oracle.com/oci/subnetIds='["ocid1.subnet.oc1.eu-zurich-1.aaaaaaaagakviiodxfjrqpbp7h5cgl4ychpzouxfcn2lqfzytpfsmrb6joha"]'
fn -v deploy --app sbom-app
fn list apps
```
