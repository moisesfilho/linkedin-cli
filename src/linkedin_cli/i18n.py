from .config import SUPPORTED_LANGUAGES

_MESSAGES: dict[str, dict[str, str]] = {
    "en": {
        "config_saved": "Configuration saved.",
        "config_updated": "Set '{key}' to '{value}'.",
        "config_current": "Current configuration:",
        "config_invalid_language": "Invalid language '{value}'. Choose one of: {choices}.",
        "config_unknown_key": "Unknown setting '{key}'.",
        "config_no_client_id": "client_id is not configured. Run 'linkedin auth login' to set it up.",
        "auth_no_credentials": "No credentials found. Run 'linkedin auth login' to authenticate.",
        "auth_token_expired": "Token expired and could not be refreshed. Run 'linkedin auth login' again.",
        "auth_login_ready": "Opening the browser to authenticate with LinkedIn...",
        "auth_login_success": "Authentication successful.",
        "auth_login_cancelled": "Authentication cancelled.",
        "auth_logged_out": "Logged out. Local token removed.",
        "auth_not_authenticated": "Not authenticated.",
        "auth_authenticated": "Authenticated.",
        "auth_error": "Authentication error: {message}",
        "auth_no_urn": "Could not resolve the profile URN from the userinfo response.",
        "auth_login_guide": (
            "Missing LinkedIn app credentials. Create an app at developer.linkedin.com and "
            "configure them with: 'linkedin config set --client-id ... --client-secret ...'"
        ),
        "auth_callback_failed": "Failed to complete authorization: {reason}",
        "auth_callback_timeout": "Timed out waiting for the browser callback.",
        "queue_added": "Queued post '{id}' for {when}.",
        "queue_not_found": "Queued post '{id}' not found.",
        "queue_removed": "Removed queued post '{id}'.",
        "queue_cleared": "Queue cleared.",
        "queue_empty": "Queue is empty.",
        "queue_published": "Published queued post '{id}'.",
        "queue_failed": "Failed to publish queued post '{id}': {error}",
        "post_created": "Post created: {id}",
        "post_not_found": "Post '{id}' not found.",
        "post_deleted": "Post '{id}' deleted.",
        "post_list_empty": "No posts found.",
        "post_image_uploaded": "Image uploaded: {id}",
        "error_generic": "Error: {message}",
        "error_timeout": "Request timed out after {seconds}s.",
        "error_rate_limited": "Rate limit reached. Try again later.",
        "error_http": "HTTP {code}: {message}",
        "error_unauthorized": "Unauthorized. Run 'linkedin auth login' to refresh your session.",
        "error_permission": "Insufficient permissions. Verify the approved scopes for the app.",
        "error_not_found": "Not found: {resource}",
        "error_invalid_request": "Invalid request: {message}",
        "error_server": "LinkedIn server error (HTTP {code}). Try again.",
        "error_no_access_token": "No access token available. Run 'linkedin auth login'.",
        "error_read_image": "Could not read image file: {path}",
        "error_image_upload": "Image upload failed: {message}",
        "error_missing_id": "LinkedIn did not return a post id.",
        "error_missing_upload": "LinkedIn did not return an upload URL for the image.",
        "post_list_requires_scope": "Listing posts requires the restricted scope 'r_member_social', which is not granted. Falling back to local history.",
        "post_requires_content": "Provide the post content with -t/--text or -f/--file.",
        "post_show_url": "Post URL: {url}",
    },
    "pt": {
        "config_saved": "Configuração salva.",
        "config_updated": "'{key}' definido para '{value}'.",
        "config_current": "Configuração atual:",
        "config_invalid_language": "Idioma inválido '{value}'. Escolha um de: {choices}.",
        "config_unknown_key": "Configuração desconhecida '{key}'.",
        "config_no_client_id": "client_id não configurado. Execute 'linkedin auth login' para configurá-lo.",
        "auth_no_credentials": "Nenhuma credencial encontrada. Execute 'linkedin auth login' para autenticar.",
        "auth_token_expired": "Token expirado e não foi possível renovar. Execute 'linkedin auth login' novamente.",
        "auth_login_ready": "Abrindo o navegador para autenticar com o LinkedIn...",
        "auth_login_success": "Autenticação concluída com sucesso.",
        "auth_login_cancelled": "Autenticação cancelada.",
        "auth_logged_out": "Logout realizado. Token local removido.",
        "auth_not_authenticated": "Não autenticado.",
        "auth_authenticated": "Autenticado.",
        "auth_error": "Erro de autenticação: {message}",
        "auth_no_urn": "Não foi possível obter a URN do perfil na resposta do userinfo.",
        "auth_login_guide": (
            "Credenciais do app LinkedIn ausentes. Crie um app em developer.linkedin.com e "
            "configure com: 'linkedin config set --client-id ... --client-secret ...'"
        ),
        "auth_callback_failed": "Falha ao concluir a autorização: {reason}",
        "auth_callback_timeout": "Tempo esgotado aguardando o callback do navegador.",
        "queue_added": "Post '{id}' agendado para {when}.",
        "queue_not_found": "Post agendado '{id}' não encontrado.",
        "queue_removed": "Post agendado '{id}' removido.",
        "queue_cleared": "Fila limpa.",
        "queue_empty": "A fila está vazia.",
        "queue_published": "Post agendado '{id}' publicado.",
        "queue_failed": "Falha ao publicar o post agendado '{id}': {error}",
        "post_created": "Post criado: {id}",
        "post_not_found": "Post '{id}' não encontrado.",
        "post_deleted": "Post '{id}' excluído.",
        "post_list_empty": "Nenhum post encontrado.",
        "post_image_uploaded": "Imagem enviada: {id}",
        "error_generic": "Erro: {message}",
        "error_timeout": "Tempo de requisição esgotado após {seconds}s.",
        "error_rate_limited": "Limite de requisições atingido. Tente novamente mais tarde.",
        "error_http": "HTTP {code}: {message}",
        "error_unauthorized": "Não autorizado. Execute 'linkedin auth login' para renovar a sessão.",
        "error_permission": "Permissões insuficientes. Verifique os escopos aprovados do app.",
        "error_not_found": "Não encontrado: {resource}",
        "error_invalid_request": "Requisição inválida: {message}",
        "error_server": "Erro do servidor do LinkedIn (HTTP {code}). Tente novamente.",
        "error_no_access_token": "Nenhum token de acesso disponível. Execute 'linkedin auth login'.",
        "error_read_image": "Não foi possível ler o arquivo de imagem: {path}",
        "error_image_upload": "Falha no upload da imagem: {message}",
        "error_missing_id": "O LinkedIn não retornou um id do post.",
        "error_missing_upload": "O LinkedIn não retornou uma URL de upload para a imagem.",
        "post_list_requires_scope": "Listar posts exige o escopo restrito 'r_member_social', não concedido. Usando histórico local.",
        "post_requires_content": "Forneça o conteúdo do post com -t/--text ou -f/--file.",
        "post_show_url": "URL do post: {url}",
    },
}


def t(language: str, msg_key: str, **kwargs: object) -> str:
    catalog = _MESSAGES.get(language) or _MESSAGES["en"]
    template = catalog.get(msg_key, _MESSAGES["en"].get(msg_key, msg_key))
    return template.format(**kwargs)


def get_language(language: str | None) -> str:
    if language in SUPPORTED_LANGUAGES:
        return language
    return "en"
