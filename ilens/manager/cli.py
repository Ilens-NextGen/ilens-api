from os import system
import click


@click.group("manager")
def cli():
    """Manager CLI"""


@cli.group("deploy")
def deploy():
    """Deploy App / Load Balancer"""


@cli.group("start")
def start():
    """Start App / Load Balancer"""


@cli.group("stop")
def stop():
    """Stop App / Load Balancer"""


@cli.group("logs")
def logs():
    """Get App / Load Balancer Logs"""


@deploy.command("app")
@click.option("--host", "-h", help="The host to deploy the app to", default="backend")
@click.option(
    "--quiet", "-q", help="Do not output anything", is_flag=True, default=False
)
def deploy_app(host: str, quiet: bool):
    click.echo("Deploying app")
    args = ["pyinfra", "--limit", host]
    if quiet:
        args.append("--quiet")
    args.extend(["ilens/manager/hosts.py", "ilens/manager/deploy_web.py"])
    return system(" ".join(args))


@deploy.command("haproxy")
@click.option(
    "--host", "-h", help="The host to deploy HAProxy to", default="loadbalancer"
)
@click.option(
    "--quiet", "-q", help="Do not output anything", is_flag=True, default=False
)
def deploy_haproxy(host: str, quiet: bool):
    click.echo("Deploying HAProxy")
    args = ["pyinfra", "--limit", host]
    if quiet:
        args.append("--quiet")
    args.extend(["ilens/manager/hosts.py", "ilens/manager/deploy_haproxy.py"])
    return system(" ".join(args))


@deploy.command("health-check")
@click.option("--host", "-h", help="The host to run the health check on")
@click.option(
    "--quiet", "-q", help="Do not output anything", is_flag=True, default=False
)
def health_check(host: str, quiet: bool):
    click.echo("Running health check")
    args = ["pyinfra"]
    if quiet:
        args.append("--quiet")
    if host:
        args.extend(["--limit", host])
    args.extend(["ilens/manager/hosts.py", "ilens/manager/health_check.py"])
    return system(" ".join(args))


@start.command("app")
@click.option("--host", "-h", help="The host to start the app on", default="backend")
@click.option(
    "--quiet", "-q", help="Do not output anything", is_flag=True, default=False
)
def start_app(host: str, quiet: bool):
    click.echo("Starting app")
    args = ["pyinfra", "--limit", host]
    if quiet:
        args.append("--quiet")
    args.extend(["ilens/manager/hosts.py", "exec", "--", "service", "ilens", "start"])
    return system(" ".join(args))


@stop.command("app")
@click.option("--host", "-h", help="The host to stop the app on", default="backend")
@click.option(
    "--quiet", "-q", help="Do not output anything", is_flag=True, default=False
)
def stop_app(host: str, quiet: bool):
    click.echo("Stopping app")
    args = ["pyinfra", "--limit", host]
    if quiet:
        args.append("--quiet")
    args.extend(["ilens/manager/hosts.py", "exec", "--", "service", "ilens", "stop"])
    return system(" ".join(args))


@start.command("haproxy")
@click.option(
    "--host", "-h", help="The host to start HAProxy on", default="loadbalancer"
)
@click.option(
    "--quiet", "-q", help="Do not output anything", is_flag=True, default=False
)
def start_haproxy(host: str, quiet: bool):
    click.echo("Starting HAProxy")
    args = ["pyinfra", "--limit", host]
    if quiet:
        args.append("--quiet")
    args.extend(["ilens/manager/hosts.py", "exec", "--", "service", "haproxy", "start"])
    return system(" ".join(args))


@stop.command("haproxy")
@click.option(
    "--host", "-h", help="The host to stop HAProxy on", default="loadbalancer"
)
@click.option(
    "--quiet", "-q", help="Do not output anything", is_flag=True, default=False
)
def stop_haproxy(host: str, quiet: bool):
    click.echo("Stopping HAProxy")
    args = ["pyinfra", "--limit", host]
    if quiet:
        args.append("--quiet")
    args.extend(["ilens/manager/hosts.py", "exec", "--", "service", "haproxy", "stop"])
    return system(" ".join(args))


@logs.command("app")
@click.option(
    "--host", "-h", help="The host to get the app logs from", default="backend"
)
@click.option(
    "--quiet", "-q", help="Do not output anything", is_flag=True, default=False
)
@click.option("--follow", "-f", help="Follow the logs", is_flag=True, default=False)
@click.option("--lines", "-n", help="Number of lines to show", default=10)
def app_logs(host: str, quiet: bool, follow: bool, lines: int):
    click.echo("Getting app logs")
    args = ["pyinfra", "--limit", host]
    if quiet:
        args.append("--quiet")
    args.extend(["ilens/manager/hosts.py", "exec", "--", "tail"])
    if follow:
        args.append("-f")
    args.extend(["-n", str(lines), "~/projects/ilens-api/ilens_server.log"])
    return system(" ".join(args))
