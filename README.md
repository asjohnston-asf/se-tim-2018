# Setup

1. Provision a new Amazon Web Services account.

   - [How do I create and activate a new Amazon Web Services account?](https://aws.amazon.com/premiumsupport/knowledge-center/create-and-activate-aws-account/)

1. Create an IAM user and access key.

   - [Creating Your First IAM Admin User and Group](https://docs.aws.amazon.com/IAM/latest/UserGuide/getting-started_create-admin-group.html)
   - [Managing Access Keys for IAM Users](https://docs.aws.amazon.com/IAM/latest/UserGuide/id_credentials_access-keys.html)

1. Install the AWS Command Line Interface and configure your default region and access keys.

   - [Installing the AWS Command Line Interface](https://docs.aws.amazon.com/cli/latest/userguide/installing.html)
   - [Configuring the AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-getting-started.html)

1. Clone this repository.

   ```
   git clone git@github.com:asjohnston-asf/se-tim-2018.git
   cd se-tim-2018
   ```

1. Register a new application in Earthdata Login.  Note your new app's <client_id> and <app_password>.

   - [How To Register An Application](https://wiki.earthdata.nasa.gov/display/EL/How+To+Register+An+Application)

1. Create a docker repository for the distribution web app.

   ```
   aws ecr create-repository --repository-name distribution
   ```

   Note the value for your <docker_repo_url>

1. Create a new S3 bucket to hold cloudformation artifacts.

   ```
   aws s3api create-bucket --bucket <artifact_bucket_name>
   ```

# Build and Deploy

1. Build the distribution web app and upload the docker image to your docker repository.

   ```
   docker build -t distribution distribution/
   $(aws ecr get-login --no-include-email)
   docker tag distribution:latest <docker_repo_url>:latest
   docker push <docker_repo_url>:latest
   ```

1. Install python requirements for the logging lambda function.

   ```
   pip install -r logging/requirements.txt -t logging/src/
   ```

1. Package the cloudformation template.

   ```
   aws cloudformation package --template-file cloudformation.yaml --s3-bucket <artifact_bucket_name> --output-template-file cloudformation-packaged.yaml
   ```

1. Deploy the packaged cloudformation template.  This step can take 10-20 minutes.

   ```
   aws cloudformation deploy --template-file cloudformation-packaged.yaml --stack-name <stack_name> --capabilities CAPABILITY_NAMED_IAM --parameter-overrides \
     VpcId=<> \
     SubnetId=<> \
     ContainerImage=<docker_repo_url> \
     UrsClientId=<urs_client_id> \
     UrsAuthCode=<urs_password>
     ElasticSearchCidrIp=<local ip>
   ```

   Note the stack output values for your:
     <app_url>
     <urs_redirect_url>
     <private_bucket_name>
     <public_bucket_name>
     <kibana_url>

1. Add your app's <urs_redirect_url> in URS.

   - [Manage Redirect URIs](https://developer.earthdata.nasa.gov/urs/urs-integration/how-to-register-an-application/manage-redirect-uris)

# Upload data

1. Upload your browse images to your public bucket

   ```
   aws s3 cp <browse_folder> s3://<public_bucket_name> --recursive
   ```

1. Upload your product files to your private bucket

   ```
   aws s3 cp <product_folder> s3://<private_bucket_name> --recursive
   ```

# Update CMR

1. Clone your collection in the Common Metadata Repository using the Metadata Management Tool.  Note your new collection's <collection_concept_id>.

   - [Metadata Management Tool (MMT) User's Guide](https://wiki.earthdata.nasa.gov/display/CMR/Metadata+Management+Tool+%28MMT%29+User%27s+Guide)
     - [Clone and edit a collection record in the CMR for my provider](https://wiki.earthdata.nasa.gov/display/CMR/Metadata+Management+Tool+%28MMT%29+User%27s+Guide#MetadataManagementTool(MMT)User'sGuide-CloneandeditacollectionrecordintheCMRformyprovider)

1. Run the cmr update script to populate your new collection in CMR.
