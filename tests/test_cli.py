import json

from click.testing import CliRunner

from linkedin_cli.auth import AuthError
from linkedin_cli.cli import cli
from linkedin_cli.config import load_config
from linkedin_cli.models import Post


def run(*args, **kwargs):
    return CliRunner().invoke(cli, args, **kwargs)


def test_config_show_defaults(data_dir):
    result = run("config", "show")

    assert result.exit_code == 0
    assert "language: en" in result.output
    assert "log_days: 120" in result.output
    assert "api_version: 202604" in result.output


def test_config_show_masks_secret(data_dir):
    (data_dir / "config.json").write_text(json.dumps({"client_secret": "hunter2"}))

    result = run("config", "show")

    assert result.exit_code == 0
    assert "client_secret: ***" in result.output
    assert "hunter2" not in result.output


def test_config_show_hides_none_values(data_dir):
    result = run("config", "show")

    assert result.exit_code == 0
    assert "client_id: None" not in result.output


def test_config_set_language(data_dir):
    result = run("config", "set", "--language", "pt")

    assert result.exit_code == 0
    assert "pt" in result.output
    assert load_config().language == "pt"


def test_config_set_multiple(data_dir):
    result = run(
        "config", "set", "--log-days", "30", "--api-version", "202601", "--request-timeout", "15"
    )

    assert result.exit_code == 0
    cfg = load_config()
    assert cfg.log_days == 30
    assert cfg.api_version == "202601"
    assert cfg.request_timeout == 15


def test_config_set_after_language_uses_pt_messages(data_dir):
    run("config", "set", "--language", "pt")

    result = run("config", "set", "--log-days", "45")

    assert result.exit_code == 0
    assert "definido para" in result.output


def test_config_set_client_secret_masked(data_dir):
    result = run("config", "set", "--client-secret", "hunter2")

    assert result.exit_code == 0
    assert "hunter2" not in result.output
    assert load_config().client_secret == "hunter2"


def test_config_set_redirect_uri_and_client_id(data_dir):
    result = run(
        "config",
        "set",
        "--redirect-uri",
        "http://localhost:9999",
        "--client-id",
        "my-client-id",
    )

    assert result.exit_code == 0
    cfg = load_config()
    assert cfg.redirect_uri == "http://localhost:9999"
    assert cfg.client_id == "my-client-id"


def test_config_set_invalid_language(data_dir):
    result = run("config", "set", "--language", "fr")

    assert result.exit_code == 2
    assert "Invalid value" in result.output


def test_config_set_no_options_keeps_defaults(data_dir):
    result = run("config", "set")

    assert result.exit_code == 0
    assert load_config().language == "en"


def test_cli_help():
    result = run("--help")

    assert result.exit_code == 0
    assert "Publish and manage LinkedIn posts" in result.output


def test_auth_login_success(data_dir, mocker):
    service = mocker.patch("linkedin_cli.cli.AuthService")
    service.return_value.login.return_value = None

    result = run("auth", "login")

    assert result.exit_code == 0
    assert "Authentication successful." in result.output


def test_auth_login_pt_messages(data_dir, mocker):
    run("config", "set", "--language", "pt")
    mocker.patch("linkedin_cli.cli.AuthService")

    result = run("auth", "login")

    assert result.exit_code == 0
    assert "Autenticação concluída" in result.output


def test_auth_login_error(data_dir, mocker):
    mocker.patch("linkedin_cli.cli.AuthService").return_value.login.side_effect = AuthError("boom")

    result = run("auth", "login")

    assert result.exit_code == 1
    assert "boom" in result.output


def test_auth_status_not_authenticated(data_dir, mocker):
    mocker.patch("linkedin_cli.cli.AuthService").return_value.is_authenticated.return_value = False

    result = run("auth", "status")

    assert result.exit_code == 0
    assert "Not authenticated." in result.output


def test_auth_status_authenticated(data_dir, mocker):
    mocker.patch("linkedin_cli.cli.AuthService").return_value.is_authenticated.return_value = True

    result = run("auth", "status")

    assert result.exit_code == 0
    assert "Authenticated." in result.output


def test_auth_logout(data_dir, mocker):
    service = mocker.patch("linkedin_cli.cli.AuthService")

    result = run("auth", "logout")

    assert result.exit_code == 0
    assert "Logged out." in result.output
    service.return_value.logout.assert_called_once()


def test_post_create_text(data_dir, mocker):
    client = mocker.patch("linkedin_cli.cli.LinkedInClient").return_value
    client.create_post.return_value = Post(id="urn:li:share:1", commentary="hello")

    result = run("post", "create", "-t", "hello")

    assert result.exit_code == 0
    assert "Post created: urn:li:share:1" in result.output
    assert "https://www.linkedin.com/feed/update/urn:li:share:1/" in result.output
    client.create_post.assert_called_once_with("hello", visibility="PUBLIC")


def test_post_create_from_file(data_dir, tmp_path, mocker):
    content = tmp_path / "post.md"
    content.write_text("Markdown **content**")
    client = mocker.patch("linkedin_cli.cli.LinkedInClient").return_value
    client.create_post.return_value = Post(id="urn:li:share:2", commentary="Markdown **content**")

    result = run("post", "create", "-f", str(content))

    assert result.exit_code == 0
    assert "urn:li:share:2" in result.output
    client.create_post.assert_called_once_with("Markdown **content**", visibility="PUBLIC")


def test_post_create_image(data_dir, tmp_path, mocker):
    image = tmp_path / "img.png"
    image.write_bytes(b"x")
    client = mocker.patch("linkedin_cli.cli.LinkedInClient").return_value
    client.upload_image.return_value.image_urn = "urn:li:image:IMG"
    client.create_post.return_value = Post(id="urn:li:share:3", commentary="pic")

    result = run("post", "create", "-t", "pic", "-i", str(image), "--alt-text", "alt")

    assert result.exit_code == 0
    client.upload_image.assert_called_once_with(str(image))
    client.create_post.assert_called_once_with(
        "pic", visibility="PUBLIC", image_urn="urn:li:image:IMG", alt_text="alt"
    )


def test_post_create_requires_content(data_dir, mocker):
    result = run("post", "create")

    assert result.exit_code == 1
    assert "Provide the post content" in result.output


def test_post_create_rejects_text_and_file(data_dir, tmp_path, mocker):
    content = tmp_path / "post.md"
    content.write_text("file content")

    result = run("post", "create", "-t", "hello", "-f", str(content))

    assert result.exit_code == 1
    assert "Provide the post content" in result.output


def test_post_show_error(data_dir, mocker):
    client = mocker.patch("linkedin_cli.cli.LinkedInClient").return_value
    client.get_post.side_effect = AuthError("not found")

    result = run("post", "show", "urn:li:share:9")

    assert result.exit_code == 1
    assert "not found" in result.output


def test_post_delete_error(data_dir, mocker):
    client = mocker.patch("linkedin_cli.cli.LinkedInClient").return_value
    client.delete_post.side_effect = AuthError("denied")

    result = run("post", "delete", "urn:li:share:9")

    assert result.exit_code == 1
    assert "denied" in result.output


def test_post_create_error(data_dir, mocker):
    client = mocker.patch("linkedin_cli.cli.LinkedInClient").return_value
    client.create_post.side_effect = AuthError("bad auth")

    result = run("post", "create", "-t", "hi")

    assert result.exit_code == 1
    assert "bad auth" in result.output


def test_post_list(data_dir, mocker):
    client = mocker.patch("linkedin_cli.cli.LinkedInClient").return_value
    client.list_posts.return_value = [
        Post(id="urn:li:share:1", commentary="hello", published_at=123),
        Post(id="urn:li:share:2", commentary="world"),
    ]

    result = run("post", "list", "--max", "5")

    assert result.exit_code == 0
    assert "urn:li:share:1" in result.output
    assert "urn:li:share:2" in result.output
    client.list_posts.assert_called_once_with(max_count=5)


def test_post_list_empty(data_dir, mocker):
    mocker.patch("linkedin_cli.cli.LinkedInClient").return_value.list_posts.return_value = []

    result = run("post", "list")

    assert result.exit_code == 0
    assert "No posts found." in result.output


def test_post_show(data_dir, mocker):
    client = mocker.patch("linkedin_cli.cli.LinkedInClient").return_value
    client.get_post.return_value = Post(id="urn:li:share:1", commentary="hello")

    result = run("post", "show", "urn:li:share:1")

    assert result.exit_code == 0
    assert "hello" in result.output
    client.get_post.assert_called_once_with("urn:li:share:1")


def test_post_delete(data_dir, mocker):
    client = mocker.patch("linkedin_cli.cli.LinkedInClient").return_value

    result = run("post", "delete", "urn:li:share:1")

    assert result.exit_code == 0
    assert "Post 'urn:li:share:1' deleted." in result.output
    client.delete_post.assert_called_once_with("urn:li:share:1")


def test_post_error_handling(data_dir, mocker):
    client = mocker.patch("linkedin_cli.cli.LinkedInClient").return_value
    client.list_posts.side_effect = AuthError("denied")

    result = run("post", "list")

    assert result.exit_code == 1
    assert "denied" in result.output


def test_auth_pt_message_in_post_flow(data_dir, mocker):
    run("config", "set", "--language", "pt")
    client = mocker.patch("linkedin_cli.cli.LinkedInClient").return_value
    client.list_posts.side_effect = AuthError("negado")

    result = run("post", "list")

    assert result.exit_code == 1
    assert "negado" in result.output
