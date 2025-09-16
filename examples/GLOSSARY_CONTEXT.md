# Glossary Context Example

This file provides instructions for AI term extraction and glossary translation.

## Term Extraction Rules

### Always Extract These
- **Character Names**: All NPCs, companions, bosses, and significant characters
- **Location Names**: Cities, dungeons, regions, landmarks, areas
- **Item Names**: Weapons, armor, consumables, key items, artifacts
- **Skill/Spell Names**: All abilities, magic spells, special attacks
- **Faction Names**: Guilds, organizations, groups, tribes
- **Currency/Resources**: In-game money, crafting materials, special resources
- **Game-Specific Terms**: Unique mechanics, lore concepts, world terminology

### Never Extract These
- **Common Gaming Terms**: level, health, mana, inventory, menu, settings
- **UI Elements**: button labels, navigation terms, system messages
- **Generic Words**: yes, no, ok, cancel, back, next, previous
- **Numbers and Quantities**: 1, 2, 100%, level 5, +10 damage
- **Common Adjectives**: good, bad, strong, weak, fast, slow
- **Articles and Prepositions**: the, a, an, in, on, at, with

### Context-Dependent (Extract if Unique)
- **Descriptive Names**: "Ancient Sword" (extract), "Iron Sword" (don't extract)
- **Modified Terms**: "Fire Magic" (extract if game-specific), "Magic" alone (don't extract)
- **Proper Nouns**: Extract if they're game-world specific

## Translation Guidelines

### Character Names
- **Main Characters**: Keep original names or use established conventions
  - Example: "Aria" → "Арія" (phonetic adaptation)
- **Fantasy NPCs**: Adapt phonetically while maintaining feel
  - Example: "Blacksmith Gorm" → "Коваль Горм"
- **Mythical Beings**: Translate titles, keep mystical names
  - Example: "Dragon Lord Pyrion" → "Володар Драконів Піріон"

### Location Names
- **Descriptive Places**: Translate the descriptive part
  - Example: "Whispering Woods" → "Шепочучі Ліси"
- **Proper Nouns**: Keep original or adapt phonetically
  - Example: "Kingdom of Valdris" → "Королівство Валдріс"
- **Geographical Features**: Translate fully
  - Example: "Crystal Lake" → "Кришталеве Озеро"

### Items and Equipment
- **Functional Items**: Translate descriptively
  - Example: "Health Potion" → "Зілля Здоров'я"
  - Example: "Steel Sword" → "Сталевий Меч"
- **Magical/Unique Items**: Keep mystical feel
  - Example: "Shadowbane" → "Погубник Тіней"
  - Example: "Amulet of Warding" → "Амулет Захисту"
- **Artifacts**: Often keep original names
  - Example: "The Worldstone" → "Світовий Камінь"

### Skills and Abilities
- **Combat Skills**: Action-oriented translation
  - Example: "Flame Strike" → "Полум'яний Удар"
  - Example: "Shadow Step" → "Тіньовий Крок"
- **Magic Spells**: Mystical and powerful sounding
  - Example: "Heal" → "Зцілення"
  - Example: "Fireball" → "Вогняна Куля"
- **Passive Abilities**: Descriptive translation
  - Example: "Iron Will" → "Залізна Воля"

### Game Mechanics
- **Resources**: Clear and descriptive
  - Example: "Soul Essence" → "Душевна Есенція"
  - Example: "Crafting Materials" → "Матеріали для Крафту"
- **Stats/Attributes**: Standard gaming terms
  - Example: "Strength" → "Сила"
  - Example: "Intelligence" → "Інтелект"

## Consistency Rules

### Maintain Throughout Game
- Use the same translation for recurring terms
- Keep character names consistent across all contexts
- Maintain established naming conventions

### Style Guidelines
- **Formal**: For ancient/mystical content
- **Modern**: For contemporary/UI content
- **Epic**: For dramatic/story content
- **Clear**: For functional/mechanical content

### Special Handling
- **Rhymes/Wordplay**: Attempt to preserve or recreate in Ukrainian
- **Cultural References**: Adapt to Ukrainian context when possible
- **Technical Terms**: Use established Ukrainian gaming terminology

## Quality Checklist

### Before Finalizing Glossary
- [ ] All character names are phonetically appropriate
- [ ] Location names maintain their atmospheric feel
- [ ] Item names are clear and evocative
- [ ] Skill names sound powerful and appropriate
- [ ] No common words are included
- [ ] Translations are consistent with Ukrainian gaming conventions
- [ ] Mystical/magical terms maintain their mysterious quality
- [ ] All terms fit the game's overall tone and style

## Examples by Game Type

### Fantasy RPG
- Extract: Wizard, Dragon, Excalibur, Fireball, Elven Forest
- Don't Extract: Attack, Defend, Menu, Level, Experience

### Sci-Fi Game
- Extract: Plasma Rifle, Starship, Quantum Drive, Nebula Station
- Don't Extract: Shoot, Jump, Inventory, Save, Load

### Horror Game
- Extract: Ancient Evil, Cursed Mansion, Holy Water, Exorcism
- Don't Extract: Run, Hide, Options, Volume, Graphics