"""
Silksong project configuration
"""
from ..core.models import ProjectConfig

# Silksong-specific configuration
SILKSONG_CONFIG = ProjectConfig(
    name="silksong",
    source_lang="EN",
    target_lang_code="DE",  # Replace German with Ukrainian
    source_dir="./SILKSONG_EN/._Decrypted",
    # preserve_terms=[
    #     "Hornet", "Pharloom", "Silksong", "Citadel",
    #     "Garmond", "Lace", "Shakra", "Coral", "Nuu"
    # ],
    # glossary_terms={
    #     # Base glossary terms that can be extended
    #     "Weaver": "Ткач",
    #     "Needle": "Голка",
    #     "Thread": "Нитка",
    #     "Silk": "Шовк",
    #     "Hunter": "Мисливець",
    #     "Knight": "Лицар",
    #     "Crest": "Герб",
    #     "Wilds": "Пустка",
    #     "Forge": "Кузня",
    #     "Peak": "Пік",
    #     "Void": "Порожнеча",
    #     "Soul": "Душа",
    #     "Mask": "Маска",
    #     "Charm": "Оберіг",
    #     "Spool": "Котушка",
    #     "Fragment": "Фрагмент"
    # }
)