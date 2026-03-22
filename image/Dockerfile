FROM public.ecr.aws/lambda/python:3.11

# --- install terraform ---
ARG TERRAFORM_VERSION=1.8.5
ARG AWS_PROVIDER_VERSION=5.100.0
ARG RANDOM_PROVIDER_VERSION=3.8.1
RUN yum -y install unzip curl && \
    curl -fsSL -o /tmp/terraform.zip https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip /tmp/terraform.zip -d /usr/local/bin && \
    rm -f /tmp/terraform.zip && \
    terraform version

# --- prepare provider mirror ---
# Terraform runtime uses /opt/tf-plugin-cache as a filesystem mirror, so populate it
# with `terraform providers mirror` during image build.
RUN mkdir -p /opt/tf-plugin-cache /tmp/tfinit
ENV TF_IN_AUTOMATION=1 TF_INPUT=0

RUN cat > /tmp/tfinit/backend.tf <<EOF
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "${AWS_PROVIDER_VERSION}"
    }
    random = {
      source  = "hashicorp/random"
      version = "${RANDOM_PROVIDER_VERSION}"
    }
  }
}
EOF

RUN cd /tmp/tfinit \
 && terraform providers mirror /opt/tf-plugin-cache \
 && rm -rf /tmp/tfinit

COPY image/terraformrc /opt/terraformrc
ENV TF_CLI_CONFIG_FILE=/opt/terraformrc

# --- app code ---
COPY app/app.py ${LAMBDA_TASK_ROOT}/app.py

# boto3 is included in Lambda base image; no extra deps needed.
CMD ["app.handler"]
