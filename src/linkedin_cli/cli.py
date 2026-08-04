from typing import TextIO

import click

from .auth import AuthError, AuthService, CredentialsNotFoundError
from .client import LinkedInClient, LinkedInError
from .config import SUPPORTED_LANGUAGES, load_config, save_config
from .i18n import t
from .models import VISIBILITIES

_MASKED_FIELDS = {"client_secret"}


def _lang() -> str:
    return load_config().language


def _msg(msg_key: str, **kwargs: object) -> str:
    return t(_lang(), msg_key=msg_key, **kwargs)


@click.group()
def cli() -> None:
    """Publish and manage LinkedIn posts from the terminal."""


@cli.group()
def auth() -> None:
    """Authenticate with LinkedIn."""


@auth.command("login")
def auth_login() -> None:
    """Authenticate in the browser (OAuth 2.0)."""
    service = AuthService()
    try:
        click.echo(_msg("auth_login_ready"))
        service.login()
    except (AuthError, CredentialsNotFoundError) as exc:
        raise click.ClickException(str(exc))
    click.echo(_msg("auth_login_success"))


@auth.command("status")
def auth_status() -> None:
    """Check the authentication status."""
    service = AuthService()
    if service.is_authenticated():
        click.echo(_msg("auth_authenticated"))
    else:
        click.echo(_msg("auth_not_authenticated"))


@auth.command("logout")
def auth_logout() -> None:
    """Remove the local token."""
    service = AuthService()
    service.logout()
    click.echo(_msg("auth_logged_out"))


@cli.group()
def post() -> None:
    """Create and manage LinkedIn posts."""


@post.command("create")
@click.option("-t", "--text", help="Post content.")
@click.option(
    "-f", "--file", type=click.File("r", encoding="utf-8"), help="Read content from a file."
)
@click.option("-i", "--image", type=click.Path(exists=True, dir_okay=False), help="Image path.")
@click.option("--alt-text", help="Accessible alternative text for the image.")
@click.option(
    "--visibility",
    type=click.Choice(VISIBILITIES),
    default="PUBLIC",
    show_default=True,
    help="Who can see the post.",
)
def post_create(
    text: str | None,
    file: TextIO | None,
    image: str | None,
    alt_text: str | None,
    visibility: str,
) -> None:
    """Create a text or image post."""
    if text and file is not None:
        raise click.ClickException(_msg("post_requires_content"))
    if file is not None:
        text = file.read()
    if not text:
        raise click.ClickException(_msg("post_requires_content"))
    client = LinkedInClient()
    try:
        if image:
            asset = client.upload_image(image)
            post_obj = client.create_post(
                text, visibility=visibility, image_urn=asset.image_urn, alt_text=alt_text
            )
        else:
            post_obj = client.create_post(text, visibility=visibility)
    except (LinkedInError, AuthError, CredentialsNotFoundError) as exc:
        raise click.ClickException(str(exc))
    click.echo(_msg("post_created", id=post_obj.id))
    click.echo(_msg("post_show_url", url=post_obj.url))


@post.command("list")
@click.option("--max", "max_count", type=int, default=10, show_default=True, help="Max posts.")
def post_list(max_count: int) -> None:
    """List recent posts."""
    client = LinkedInClient()
    try:
        posts = client.list_posts(max_count=max_count)
    except (LinkedInError, AuthError, CredentialsNotFoundError) as exc:
        raise click.ClickException(str(exc))
    if not posts:
        click.echo(_msg("post_list_empty"))
        return
    for p in posts:
        click.echo(f"{p.id}  {p.published_at or ''}  {p.commentary[:60]}")


@post.command("show")
@click.argument("post_id")
def post_show(post_id: str) -> None:
    """Show a post by id."""
    client = LinkedInClient()
    try:
        p = client.get_post(post_id)
    except (LinkedInError, AuthError, CredentialsNotFoundError) as exc:
        raise click.ClickException(str(exc))
    click.echo(f"{p.id}  {p.visibility}")
    click.echo(p.commentary)
    click.echo(_msg("post_show_url", url=p.url))


@post.command("delete")
@click.argument("post_id")
def post_delete(post_id: str) -> None:
    """Delete a post by id."""
    client = LinkedInClient()
    try:
        client.delete_post(post_id)
    except (LinkedInError, AuthError, CredentialsNotFoundError) as exc:
        raise click.ClickException(str(exc))
    click.echo(_msg("post_deleted", id=post_id))


@cli.group()
def config() -> None:
    """Manage CLI configuration."""


@config.command("show")
def config_show() -> None:
    """Show the current configuration."""
    cfg = load_config()
    click.echo(_msg("config_current"))
    for field, val in vars(cfg).items():
        if val is None:
            continue
        display = "***" if field in _MASKED_FIELDS else val
        click.echo(f"  {field}: {display}")


@config.command("set")
@click.option("--language", type=click.Choice(SUPPORTED_LANGUAGES), help="Interface language.")
@click.option("--log-days", type=int, help="Log retention in days.")
@click.option("--request-timeout", type=int, help="Request timeout in seconds.")
@click.option("--api-version", type=str, help="LinkedIn-Version header (YYYYMM).")
@click.option("--redirect-uri", type=str, help="OAuth redirect URI.")
@click.option("--client-id", type=str, help="LinkedIn app Client ID.")
@click.option("--client-secret", type=str, help="LinkedIn app Client Secret.")
def config_set(
    language: str | None,
    log_days: int | None,
    request_timeout: int | None,
    api_version: str | None,
    redirect_uri: str | None,
    client_id: str | None,
    client_secret: str | None,
) -> None:
    """Update configuration values."""
    cfg = load_config()
    changes: dict[str, object] = {}
    if language is not None:
        cfg.language = language
        changes["language"] = language
    if log_days is not None:
        cfg.log_days = log_days
        changes["log_days"] = log_days
    if request_timeout is not None:
        cfg.request_timeout = request_timeout
        changes["request_timeout"] = request_timeout
    if api_version is not None:
        cfg.api_version = api_version
        changes["api_version"] = api_version
    if redirect_uri is not None:
        cfg.redirect_uri = redirect_uri
        changes["redirect_uri"] = redirect_uri
    if client_id is not None:
        cfg.client_id = client_id
        changes["client_id"] = client_id
    if client_secret is not None:
        cfg.client_secret = client_secret
        changes["client_secret"] = "***"

    save_config(cfg)
    for key, value in changes.items():
        click.echo(_msg("config_updated", key=key, value=value))
