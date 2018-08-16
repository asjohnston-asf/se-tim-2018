# Requirements

- docker (tested with 18.03.1)
- pip 3.6 (tested with 9.0.3)
- aws cli (tested with 1.14.9)

# Setup

1. Provision a new Amazon Web Services account.

   - [How do I create and activate a new Amazon Web Services account?](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/)

1. Create an IAM user and access key.

   - [Creating Your First IAM Admin User and Group](https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started_create-admin-group.html)
   - [Managing Access Keys for IAM Users](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)

1. Install the AWS Command Line Interface and configure your default region and access keys.

   - [Installing the AWS Command Line Interface](https://docs.aws.amazon.com/cli/latest/userguide/installing.html)
   - [Configuring the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)

1. [optional] Register a new application in Earthdata Login.  Note your new app's <urs_client_id> and <urs_app_password>.  Use any placeholder URL for the Redirect URL field; we'll update that later.

   - [How To Register An Application](https://wiki.earthdata.nasa.gov/display/EL/How+To+Register+An+Application)

   Alternatively, you can re-use the client id and password for an existing application.

1. Generate your <urs_auth_code> from your <urs_client_id> and <urs_app_password>.

   ```
   echo -n "<urs_client_id>:<urs_app_password>" | base64
   ```

   See the "UrsAuthCode" parameter of the [Apache URS Authentication Module](https://developer.earthdata.nasa.gov/urs/urs-integration/apache-urs-authentication-module) for more details.


1. Create a new docker repository for the distribution web app.

   ```
   aws ecr create-repository --repository-name distribution
   ```

   Note the value for your <docker_repository_uri>.

1. Create a new S3 bucket to hold cloudformation artifacts.

   ```
   aws s3api create-bucket --bucket <artifact_bucket_name>
   ```

1. Clone this repository and cd to the root directory.

   ```
   git clone git@github.com:asjohnston-asf/se-tim-2018.git
   cd se-tim-2018
   ```

# Build and Deploy

1. Build the distribution web app and upload the docker image to your docker repository.

   ```
   docker build -t distribution distribution/
   $(aws ecr get-login --no-include-email)
   docker tag distribution <docker_repository_uri>
   docker push <docker_repository_uri>
   ```

1. Install python requirements for the logging lambda function.  **Use pip 3.6!**

   ```
   pip install -r logging/requirements.txt -t logging/src/
   ```

1. Package the cloudformation template.

   ```
   aws cloudformation package --template-file cloudformation.yaml --s3-bucket <artifact_bucket_name> --output-template-file cloudformation-packaged.yaml
   ```

1. Deploy the packaged cloudformation template.  This step can take 15-25 minutes.

   ```
   aws cloudformation deploy \
     --stack-name <stack_name> \
     --template-file cloudformation-packaged.yaml \
     --capabilities CAPABILITY_NAMED_IAM \
     --parameter-overrides \
         VpcId=<vpc_id> \
         SubnetIds=<subnet_id_1>,<subnet_id_2> \
         ContainerImage=<docker_repository_uri> \
         UrsServer=https://urs.earthdata.nasa.gov \
         UrsClientId=<urs_client_id> \
         UrsAuthCode=<urs_auth_code> \
         LoadBalancerCidrIp=0.0.0.0/0 \
         ElasticSearchCidrIp=<local_ip>
   ```

   Note the stack output values for your:
   - <product_url>
   - <browse_url>
   - <urs_redirect_url>
   - <kibana_url>
   - <public_bucket_name>
   - <private_bucket_name>

1. Add your app's <urs_redirect_url> in URS.

   - [Manage Redirect URIs](https://developer.earthdata.nasa.gov/urs/urs-integration/how-to-register-an-application/manage-redirect-uris)

# Upload Data

1. Upload your browse images to your public bucket.

   ```
   aws s3 cp <browse_folder> s3://<public_bucket_name> --recursive
   ```

1. Upload your product files to your private bucket.

   ```
   aws s3 cp <product_folder> s3://<private_bucket_name> --recursive
   ```

# Update CMR

1. Clone your collection in the Common Metadata Repository using the Metadata Management Tool.  Note your new collection's <collection_concept_id>.

   - [Metadata Management Tool (MMT) User's Guide](https://wiki.earthdata.nasa.gov/display/CMR/Metadata+Management+Tool+%28MMT%29+User%27s+Guide)
     - [Clone and edit a collection record in the CMR for my provider](https://wiki.earthdata.nasa.gov/display/CMR/Metadata+Management+Tool+%28MMT%29+User%27s+Guide#MetadataManagementTool(MMT)User'sGuide-CloneandeditacollectionrecordintheCMRformyprovider)

1. Run the cmr update script to populate your new collection in CMR.
