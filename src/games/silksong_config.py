"""
Silksong project configuration
"""
from ..core.models import ProjectConfig

# Silksong-specific configuration
SILKSONG_CONFIG = ProjectConfig(
    name="silksong",
    source_lang="EN",
    target_lang_code="DE",  # Replace German with Ukrainian
    source_dir="./SILKSONG_EN/._Decrypted"
)