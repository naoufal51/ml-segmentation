import pulumi
from pulumi import Output
import pulumi_kubernetes as kubernetes
import json


class TraefikRouteArgs:
    def __init__(
            self,
            namespace: pulumi.Input[str],
            prefix: pulumi.Input[str],
            service: kubernetes.core.v1.Service,
            stripprefix: pulumi.Input[bool],
    ):
        self.namespace = namespace
        self.prefix = prefix
        self.service = service
        self.stripprefix = stripprefix


class TraefikRoute(pulumi.ComponentResource):
    def __init__(self, name: str, args: TraefikRouteArgs, opts: pulumi.ResourceOptions = None):
        super().__init__("pkg:index:TraefikRoute", name, {}, opts)

        middlewares = []

        # Remove trailing /
        trailing_slash_middleware = kubernetes.apiextensions.CustomResource(
            f'{name}-trailing-slash',
            api_version='traefik.containo.us/v1alpha1',
            kind='Middleware',
            metadata=kubernetes.meta.v1.ObjectMetaArgs(
                # annotations={"pulumi.com/autonamed": "true"},
                name=f'{name}-trailing-slash-test',
                namespace=args.namespace
            ),
            spec={
                "redirectRegex": {
                    "regex": f"^.*\\{args.prefix}$",
                    # "regex": '(^.*\/mlflow$$)',
                    "replacement": args.prefix + '/',
                    "permanent": False
                }
            },
            opts=pulumi.ResourceOptions(provider=opts.provider),
        )

        #       middlewares.append({"name": f'{name}-trailing-slash-test'})
        #

        # Strip prefix
        if args.stripprefix:
            strip_prefix_middleware = kubernetes.apiextensions.CustomResource(
                resource_name=f'{name}-strip-prefix',
                api_version='traefik.containo.us/v1alpha1',
                kind='Middleware',
                metadata=kubernetes.meta.v1.ObjectMetaArgs(
                    # annotations= {"pulumi.com/autonamed": "true" },
                    name=f'{name}-strip-prefix-test',
                    namespace=args.namespace
                ),
                spec={
                    "stripPrefix": {
                        "prefixes": [
                            args.prefix  # args.prefix
                        ],  # [args.prefix]
                        "forceslash": True
                    },
                },
                opts=pulumi.ResourceOptions(provider=opts.provider)
            )

        kubernetes.apiextensions.CustomResource(
            f'{name}-ingress-route',
            api_version='traefik.containo.us/v1alpha1',
            kind='IngressRoute',
            metadata=kubernetes.meta.v1.ObjectMetaArgs(
                namespace=args.namespace
            ),
            spec={
                "entryPoints": ["web"],
                "routes": [{
                    # "match": f'PathPrefix(`{args.prefix}`)',  # 'PathPrefix(`'+args.prefix+'`)',
                    "match": 'PathPrefix(`'+args.prefix+'`)',
                    # "match": 'PathPrefix(`/`)',
                    "kind": "Rule",
                    "middlewares": [
                        {
                            "name": f'{name}-trailing-slash-test',
                            "namespace": args.namespace,
                        },
                        {
                            "name": f'{name}-strip-prefix-test',
                            "namespace": args.namespace,
                        }
                    ],
                    "services": [{
                        "name": args.service if isinstance(args.service, str) else args.service.metadata.name,
                        "port": 80 if isinstance(args.service, str) else args.service.spec.ports[0].port,
                    }],
                }]
            }, opts=pulumi.ResourceOptions(provider=opts.provider
                                           )
        )

        self.register_outputs({})

