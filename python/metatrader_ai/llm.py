OPENAI = 0
DEEPSEEK = 1
ANTHROPIC = 2
LOCAL = 3

PROVIDER_NAMES = {
    "OpenAI": OPENAI,
    "DeepSeek": DEEPSEEK,
    "Anthropic": ANTHROPIC,
    "Local": LOCAL,
}


def normalize_url(url: str, provider_id: int = OPENAI) -> str:
    """Normalize any custom endpoint URL (base path, router URL, or full endpoint)."""
    clean_url = url.strip()
    if not clean_url:
        return ""
    clean_url = clean_url.rstrip("/")

    if provider_id == ANTHROPIC:
        if clean_url.endswith("/messages"):
            return clean_url
        if clean_url.endswith("/v1"):
            return f"{clean_url}/messages"
        return f"{clean_url}/v1/messages"
    else:
        # OpenAI, DeepSeek, Local, Custom Router (e.g. https://omniroute.ai.ntk.ir/v1)
        if clean_url.endswith("/chat/completions"):
            return clean_url
        if clean_url.endswith("/v1"):
            return f"{clean_url}/chat/completions"
        return f"{clean_url}/v1/chat/completions"


class LLM:
    """LLM provider config with endpoint URL, model name, and API key."""
    __slots__ = ["provider_id", "id", "label", "model", "url"]

    def __init__(self, provider_id: int = DEEPSEEK, custom_model: str = "", custom_url: str = ""):
        self.provider_id = provider_id
        self.id = ""
        self.label = ""
        self.model = ""
        self.url = ""

        if provider_id == OPENAI:
            self.id = "openai"
            self.label = "OpenAI"
            self.model = custom_model.strip() if custom_model.strip() else "gpt-4o-mini"
            self.url = normalize_url(custom_url, OPENAI) if custom_url.strip() else "https://api.openai.com/v1/chat/completions"
        elif provider_id == DEEPSEEK:
            self.id = "deepseek"
            self.label = "DeepSeek"
            self.model = custom_model.strip() if custom_model.strip() else "deepseek-chat"
            self.url = normalize_url(custom_url, DEEPSEEK) if custom_url.strip() else "https://api.deepseek.com/chat/completions"
        elif provider_id == ANTHROPIC:
            self.id = "anthropic"
            self.label = "Anthropic"
            self.model = custom_model.strip() if custom_model.strip() else "claude-3-5-sonnet-20241022"
            self.url = normalize_url(custom_url, ANTHROPIC) if custom_url.strip() else "https://api.anthropic.com/v1/messages"
        elif provider_id == LOCAL:
            self.id = "local"
            self.label = "Local"
            self.model = custom_model.strip() if custom_model.strip() else "local-model"
            self.url = normalize_url(custom_url, LOCAL) if custom_url.strip() else "http://127.0.0.1:11434/v1/chat/completions"
        else:
            self.id = "custom"
            self.label = "Custom"
            self.model = custom_model.strip() if custom_model.strip() else "default"
            self.url = normalize_url(custom_url, OPENAI) if custom_url.strip() else "http://127.0.0.1:11434/v1/chat/completions"
