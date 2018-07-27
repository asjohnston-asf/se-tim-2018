# Setup

1. Provision a new Amazon Web Services account

1. Create an IAM user and access key

1. Install and configure the AWS CLI

1. Clone this repository

   ```
   git clone git@github.com:asjohnston-asf/se-tim-2018.git
   cd se-tim-2018
   ```

# Storage

1. Deploy the storage cloudformation template

   ```
   aws cloudformation deploy --template-file buckets.yaml --stack-name <my_stack_name>
   ```

   Note the values for your <public_bucket_name>, <private_bucket_name>, and <log_bucket_name>

1. Upload your browse images

   ```
   aws s3 cp <browse_folder> s3://<public_bucket_name> --recursive
   ```

1. Upload your product files

   ```
   aws s3 cp <product_folder> s3://<private_bucket_name> --recursive
   ```

# Distribution

1. Create an application in URS.  Note your app's <client_id> and <app_password>

1. Create a docker repository for the distribution web app

   ```
   aws ecr create-repository --repository-name distribution
   ```

   Note the value for your <docker_repo_url>

1. Build the distribution web app

   ```
   docker build -t distribution web-app/
   $(aws ecr get-login --no-include-email)
   docker tag distribution:latest <docker_repo_url>/distribution:latest
   docker push <docker_repo_url> distribution:latest
   ```

1. Deploy the cloudformation template for the distribution web app

   ```
   aws cloudformation deploy --template-file web-app.yaml --stack-name distribution --capabilities CAPABILITY_NAMED_IAM --parameter-overrides \
     VpcId=<> \
     SubnetId=<> \
     ProductBucket=<private_bucket_name> \
     ContainerImage=<docker_repo_url> \
     UrsClientId=<urs_client_id> \
     UrsAuthCode=<urs_password>
   ```

   Note the values for your <urs_redirect_url> and <app_url>

1. Add your app's redirect URL in URS

# Discovery

1. Create a new collection in CMR and make it visible in MMT

1. Run the cmr update script to populate your new collection in CMR
