"""An AWS Python Pulumi program"""
import base64

import pulumi
import pulumi_aws as aws
import pulumi_kubernetes as k8s
import pulumi_docker as docker
from TraefikRoute import TraefikRoute, TraefikRouteArgs

config = pulumi.Config()
basestack = pulumi.StackReference(config.require('baseStackName'))

provider = k8s.Provider('Provider', kubeconfig=basestack.require_output("kubeconfig"))

# Create repository

repo = aws.ecr.Repository("ml-segment")



# Get registry info (Cred and endpoint)
def get_registry_info(rid):
    creds = aws.ecr.get_credentials(registry_id=rid)
    decoded = base64.b64decode(creds.authorization_token).decode()
    parts = decoded.split(':')
    if len(parts) != 2:
        raise Exception("Invalid credentials")

    username = parts[0]
    password = parts[1]
    return docker.ImageRegistry(creds.proxy_endpoint, username=username, password=password)


image_name = repo.repository_url

registry_info = repo.registry_id.apply(get_registry_info)

image = docker.Image("ml-segment",
                     image_name=image_name,
                     build="../",
                     skip_push=False,
                     registry=registry_info
                     )

app_labels = {"app": "ml-segment"}

ml = k8s.apps.v1.Deployment(
    "ml-segment-serve",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        labels=app_labels,
    ),
    spec=k8s.apps.v1.DeploymentSpecArgs(
        replicas=1,
        selector=k8s.meta.v1.LabelSelectorArgs(
            match_labels=app_labels,
        ),
        template=k8s.core.v1.PodTemplateSpecArgs(
            metadata=k8s.meta.v1.ObjectMetaArgs(
                labels=app_labels,
            ),
            spec=k8s.core.v1.PodSpecArgs(
                containers=[k8s.core.v1.ContainerArgs(
                    name='ml-segment-container',
                    image=image.image_name,
                    ports=[k8s.core.v1.ContainerPortArgs(
                        name='http',
                        container_port=80,
                    )],
                    env=[k8s.core.v1.EnvVarArgs(
                        name="LISTEN_PORT",
                        value='80',
                    )],
                )],
                service_account_name=basestack.require_output("modelsServiceAccountName")
            ),
        ),
    ),
    opts=pulumi.ResourceOptions(provider=provider))

mlsegment_service = k8s.core.v1.Service(
    "ml-segment-service",
    metadata=k8s.meta.v1.ObjectMetaArgs(
        name="ml-segment-service",
        labels=app_labels,
    ),
    spec=k8s.core.v1.ServiceSpecArgs(
        ports=[k8s.core.v1.ServicePortArgs(
            port=80,
        )],
        selector=app_labels,
    ),
    opts=pulumi.ResourceOptions(provider=provider)
)

mlsegment_traefik_route = TraefikRoute('ml-segment-route',
                                       TraefikRouteArgs(
                                           prefix='/models/ml-segment',
                                           service=mlsegment_service,
                                           namespace='default',
                                       ), opts=pulumi.ResourceOptions(provider=provider, depends_on=[mlsegment_service])
                                       )