FROM public.ecr.aws/lambda/python:3.11

# --- install terraform ---
ARG TERRAFORM_VERSION=1.8.5
RUN yum -y install unzip curl && \
    curl -fsSL -o /tmp/terraform.zip https://releases.hashicorp.com/terraform/${TERRAFORM_VERSION}/terraform_${TERRAFORM_VERSION}_linux_amd64.zip && \
    unzip /tmp/terraform.zip -d /usr/local/bin && \
    rm -f /tmp/terraform.zip && \
    terraform version

# --- prepare provider cache (aws) ---
# We'll run a minimal init that downloads the pinned provider, then copy it into /opt/tf-plugin-cache
# Pin provider version via required_providers in backend.tf; Terraform will cache it.
RUN mkdir -p /opt/tf-plugin-cache /tmp/tfinit
COPY terraformrc /opt/terraformrc
ENV TF_CLI_CONFIG_FILE=/opt/terraformrc
ENV TF_PLUGIN_CACHE_DIR=/opt/tf-plugin-cache
ENV TF_IN_AUTOMATION=1 TF_INPUT=0

RUN cat > /tmp/tfinit/backend.tf <<'EOF'
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
EOF

RUN cd /tmp/tfinit \
 && terraform init -input=false \
 && rm -rf /tmp/tfinit/.terraform \
 && rm -rf /tmp/tfinit

# --- app code ---
COPY app/app.py ${LAMBDA_TASK_ROOT}/app.py

# boto3 is included in Lambda base image; no extra deps needed.
CMD ["app.handler"]
