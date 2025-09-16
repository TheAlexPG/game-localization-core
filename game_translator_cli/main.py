#!/usr/bin/env python3
"""Game Translator CLI - Main interface"""

import click
import json
from pathlib import Path
from typing import Optional, List

# Try to import rich for better output
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich.panel import Panel
    RICH_AVAILABLE = True
    console = Console()
except ImportError:
    RICH_AVAILABLE = False
    console = None

# Core imports
from game_translator.core.models import TranslationEntry, TranslationStatus, ProjectConfig, ProgressStats
from game_translator.core.validation import TranslationValidator, QualityMetrics
from game_translator.core.custom_patterns import CustomPatternsManager
from game_translator.providers import get_provider


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """Game Translator - AI-powered game localization tool

    A comprehensive tool for translating game content with AI assistance,
    validation, and quality control features.
    """
    pass


@cli.command()
@click.option('--name', '-n', required=True, help='Project name')
@click.option('--source-lang', '-s', default='en', help='Source language code (default: en)')
@click.option('--target-lang', '-t', required=True, help='Target language code')
@click.option('--source-format', default='json', help='Source file format (default: json)')
@click.option('--output-format', default='json', help='Output file format (default: json)')
@click.option('--dir', '-d', 'project_dir', help='Project directory (default: ./projects/{name})')
def init(name: str, source_lang: str, target_lang: str, source_format: str,
         output_format: str, project_dir: Optional[str]):
    """Initialize a new translation project"""

    # Create project directory
    if project_dir:
        proj_path = Path(project_dir)
    else:
        proj_path = Path("projects") / name

    proj_path.mkdir(parents=True, exist_ok=True)

    # Create project config
    config = ProjectConfig(
        name=name,
        source_lang=source_lang,
        target_lang=target_lang,
        source_format=source_format,
        output_format=output_format
    )

    # Save config
    config_file = proj_path / "project.json"
    with open(config_file, 'w', encoding='utf-8') as f:
        json.dump(config.to_dict(), f, indent=2, ensure_ascii=False)

    # Create directory structure
    (proj_path / "source").mkdir(exist_ok=True)
    (proj_path / "translations").mkdir(exist_ok=True)
    (proj_path / "output").mkdir(exist_ok=True)
    (proj_path / "glossary").mkdir(exist_ok=True)
    (proj_path / "validation").mkdir(exist_ok=True)

    if RICH_AVAILABLE:
        console.print(Panel.fit(
            f"[green]OK[/green] Project '{name}' initialized\n"
            f"[dim]Directory:[/dim] {proj_path}\n"
            f"[dim]Source language:[/dim] {source_lang}\n"
            f"[dim]Target language:[/dim] {target_lang}",
            title="Project Created"
        ))
    else:
        print(f"OK: Project '{name}' initialized")
        print(f"  Directory: {proj_path}")
        print(f"  Source: {source_lang} -> {target_lang}")


@cli.command()
@click.option('--project', '-p', required=True, help='Project name or path')
@click.option('--provider', type=click.Choice(['openai', 'local', 'mock']),
              required=True, help='AI provider to use')
@click.option('--model', help='Model name (provider-specific)')
@click.option('--api-key', help='API key for provider (if required)')
@click.option('--batch-size', default=5, help='Number of texts to translate at once')
@click.option('--max-entries', type=int, help='Maximum entries to translate (for testing)')
@click.option('--patterns', help='Custom validation patterns file (CSV/Excel/JSON)')
def translate(project: str, provider: str, model: Optional[str], api_key: Optional[str],
              batch_size: int, max_entries: Optional[int], patterns: Optional[str]):
    """Translate pending entries using AI"""

    # Load project
    proj_path = _get_project_path(project)
    if not proj_path.exists():
        click.echo(f"Error: Project not found at {proj_path}", err=True)
        return

    config = _load_project_config(proj_path)
    if not config:
        return

    # Load custom validation patterns
    validator = None
    if patterns:
        manager = CustomPatternsManager()
        pattern_path = Path(patterns)

        if pattern_path.suffix.lower() == '.csv':
            custom_patterns = manager.load_from_csv(pattern_path)
        elif pattern_path.suffix.lower() in ['.xlsx', '.xls']:
            custom_patterns = manager.load_from_excel(pattern_path)
        elif pattern_path.suffix.lower() == '.json':
            custom_patterns = manager.load_from_json(pattern_path)
        else:
            click.echo(f"Error: Unsupported patterns file format: {pattern_path.suffix}", err=True)
            return

        validator = TranslationValidator(custom_patterns=manager.get_patterns_for_validator())
        click.echo(f"Loaded {len(custom_patterns)} custom validation patterns")
    else:
        validator = TranslationValidator()

    # Initialize provider
    try:
        if provider == 'openai':
            ai_provider = get_provider('openai', api_key=api_key, model_name=model or 'gpt-4o-mini')
        elif provider == 'local':
            ai_provider = get_provider('local', model_name=model or 'local-model')
        elif provider == 'mock':
            ai_provider = get_provider('mock')
        else:
            click.echo(f"Error: Unknown provider: {provider}", err=True)
            return

    except Exception as e:
        click.echo(f"Error initializing provider: {e}", err=True)
        return

    # For demo purposes, create some sample entries
    sample_entries = [
        TranslationEntry(
            key="welcome_message",
            source_text="Welcome to the game, {player}!",
            status=TranslationStatus.PENDING
        ),
        TranslationEntry(
            key="level_complete",
            source_text="Level {level} completed with {score} points",
            status=TranslationStatus.PENDING
        ),
        TranslationEntry(
            key="game_over",
            source_text="Game Over - Press <b>Enter</b> to restart",
            status=TranslationStatus.PENDING
        )
    ]

    if max_entries:
        sample_entries = sample_entries[:max_entries]

    click.echo(f"Starting translation with {provider} provider...")
    click.echo(f"Translating {len(sample_entries)} entries")

    # Translate entries
    if RICH_AVAILABLE:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("Translating...", total=len(sample_entries))

            for entry in sample_entries:
                try:
                    # Simulate translation (replace with real translation logic)
                    translations = ai_provider.translate_texts(
                        [entry.source_text],
                        source_lang=config.source_lang,
                        target_lang=config.target_lang
                    )

                    if translations:
                        entry.translated_text = translations[0]
                        entry.status = TranslationStatus.TRANSLATED

                        # Validate translation
                        result = validator.validate_entry(entry)
                        if result.issues:
                            click.echo(f"WARNING: Validation issues for '{entry.key}': {len(result.issues)} errors")

                    progress.advance(task)

                except Exception as e:
                    click.echo(f"Error translating '{entry.key}': {e}")
    else:
        for i, entry in enumerate(sample_entries, 1):
            click.echo(f"Translating {i}/{len(sample_entries)}: {entry.key}")

            try:
                translations = ai_provider.translate_texts(
                    [entry.source_text],
                    source_lang=config.source_lang,
                    target_lang=config.target_lang
                )

                if translations:
                    entry.translated_text = translations[0]
                    entry.status = TranslationStatus.TRANSLATED

                    # Validate translation
                    result = validator.validate_entry(entry)
                    if result.issues:
                        click.echo(f"  WARNING: Validation issues: {len(result.issues)} errors")

            except Exception as e:
                click.echo(f"  Error: {e}")

    # Save results (demo - just print them)
    click.echo("\nTranslation Results:")
    click.echo("-" * 40)

    for entry in sample_entries:
        click.echo(f"Key: {entry.key}")
        click.echo(f"Source: {entry.source_text}")
        click.echo(f"Translation: {entry.translated_text or '(failed)'}")
        click.echo(f"Status: {entry.status.value}")
        click.echo()


@cli.command()
@click.option('--project', '-p', required=True, help='Project name or path')
@click.option('--patterns', help='Custom validation patterns file')
@click.option('--strict', is_flag=True, help='Use strict validation mode')
@click.option('--output', '-o', help='Save validation report to file')
def validate(project: str, patterns: Optional[str], strict: bool, output: Optional[str]):
    """Validate translations for quality and consistency"""

    proj_path = _get_project_path(project)
    if not proj_path.exists():
        click.echo(f"Error: Project not found at {proj_path}", err=True)
        return

    # Load custom patterns if specified
    validator_kwargs = {'strict_mode': strict}

    if patterns:
        manager = CustomPatternsManager()
        pattern_path = Path(patterns)

        if pattern_path.suffix.lower() == '.csv':
            custom_patterns = manager.load_from_csv(pattern_path)
        elif pattern_path.suffix.lower() in ['.xlsx', '.xls']:
            custom_patterns = manager.load_from_excel(pattern_path)
        elif pattern_path.suffix.lower() == '.json':
            custom_patterns = manager.load_from_json(pattern_path)
        else:
            click.echo(f"Error: Unsupported patterns file format: {pattern_path.suffix}", err=True)
            return

        validator_kwargs['custom_patterns'] = manager.get_patterns_for_validator()
        click.echo(f"Loaded {len(custom_patterns)} custom validation patterns")

    validator = TranslationValidator(**validator_kwargs)

    # Create demo entries for validation
    demo_entries = [
        TranslationEntry(
            key="good_example",
            source_text="Level {level} completed",
            translated_text="Рівень {level} завершено",
            status=TranslationStatus.TRANSLATED
        ),
        TranslationEntry(
            key="missing_placeholder",
            source_text="Player {name} has {coins} coins",
            translated_text="Гравець має монети",  # Missing placeholders
            status=TranslationStatus.TRANSLATED
        ),
        TranslationEntry(
            key="html_tag_issue",
            source_text="Click <b>here</b> to continue",
            translated_text="Натисніть тут для продовження",  # Missing tags
            status=TranslationStatus.TRANSLATED
        )
    ]

    click.echo(f"Validating {len(demo_entries)} entries...")

    # Run validation
    total_issues = 0
    total_warnings = 0

    if RICH_AVAILABLE:
        table = Table(title="Validation Results")
        table.add_column("Entry", style="cyan")
        table.add_column("Status", style="magenta")
        table.add_column("Issues", style="red")
        table.add_column("Warnings", style="yellow")

        for entry in demo_entries:
            result = validator.validate_entry(entry)
            total_issues += len(result.issues)
            total_warnings += len(result.warnings)

            status = "OK" if not result.issues else "Issues"
            table.add_row(
                entry.key,
                status,
                str(len(result.issues)),
                str(len(result.warnings))
            )

        console.print(table)

        # Quality metrics
        quality_score = 85 - (total_issues * 10) - (total_warnings * 2)  # Demo calculation
        quality_grade = QualityMetrics.get_quality_grade(quality_score)

        console.print(Panel.fit(
            f"[bold]Summary[/bold]\n"
            f"Entries checked: {len(demo_entries)}\n"
            f"Issues found: {total_issues}\n"
            f"Warnings: {total_warnings}\n"
            f"Quality score: {quality_score}/100 (Grade: {quality_grade})",
            title="Validation Summary"
        ))

    else:
        click.echo("Validation Results:")
        click.echo("-" * 30)

        for entry in demo_entries:
            result = validator.validate_entry(entry)
            total_issues += len(result.issues)
            total_warnings += len(result.warnings)

            click.echo(f"Entry: {entry.key}")
            if result.issues:
                click.echo(f"  ERROR: {len(result.issues)} issues found")
                for issue in result.issues:
                    click.echo(f"    - {issue.message}")
            else:
                click.echo(f"  OK: No issues")

            if result.warnings:
                click.echo(f"  WARNING: {len(result.warnings)} warnings")
            click.echo()

        # Summary
        quality_score = 85 - (total_issues * 10) - (total_warnings * 2)
        quality_grade = QualityMetrics.get_quality_grade(quality_score)

        click.echo("Summary:")
        click.echo(f"  Entries: {len(demo_entries)}")
        click.echo(f"  Issues: {total_issues}")
        click.echo(f"  Warnings: {total_warnings}")
        click.echo(f"  Quality: {quality_score}/100 (Grade: {quality_grade})")


@cli.command()
@click.option('--project', '-p', required=True, help='Project name or path')
def status(project: str):
    """Show project status and statistics"""

    proj_path = _get_project_path(project)
    if not proj_path.exists():
        click.echo(f"Error: Project not found at {proj_path}", err=True)
        return

    config = _load_project_config(proj_path)
    if not config:
        return

    # Demo statistics
    stats = ProgressStats(
        total=150,
        pending=45,
        translated=85,
        reviewed=15,
        approved=5,
        needs_update=0,
        skipped=0
    )

    if RICH_AVAILABLE:
        table = Table(title=f"Project: {config.name}")
        table.add_column("Status", style="cyan")
        table.add_column("Count", justify="right", style="magenta")
        table.add_column("Percentage", justify="right", style="green")

        table.add_row("Total", str(stats.total), "100.0%")
        table.add_row("Pending", str(stats.pending), f"{stats.pending/stats.total*100:.1f}%")
        table.add_row("Translated", str(stats.translated), f"{stats.translated/stats.total*100:.1f}%")
        table.add_row("Reviewed", str(stats.reviewed), f"{stats.reviewed/stats.total*100:.1f}%")
        table.add_row("Approved", str(stats.approved), f"{stats.approved/stats.total*100:.1f}%")

        console.print(table)

        completion = stats.completion_rate
        console.print(f"\n[bold green]Completion: {completion:.1f}%[/bold green]")

    else:
        click.echo(f"Project: {config.name}")
        click.echo(f"Source: {config.source_lang} -> {config.target_lang}")
        click.echo()
        click.echo("Statistics:")
        click.echo(f"  Total entries: {stats.total}")
        click.echo(f"  Pending: {stats.pending} ({stats.pending/stats.total*100:.1f}%)")
        click.echo(f"  Translated: {stats.translated} ({stats.translated/stats.total*100:.1f}%)")
        click.echo(f"  Reviewed: {stats.reviewed} ({stats.reviewed/stats.total*100:.1f}%)")
        click.echo(f"  Approved: {stats.approved} ({stats.approved/stats.total*100:.1f}%)")
        click.echo()
        click.echo(f"Completion: {stats.completion_rate:.1f}%")


@cli.command()
@click.option('--template', type=click.Choice(['csv', 'excel', 'json']),
              default='excel', help='Template format to create')
@click.option('--output', '-o', help='Output file path')
def create_patterns(template: str, output: Optional[str]):
    """Create template file for custom validation patterns"""

    manager = CustomPatternsManager()

    if not output:
        if template == 'csv':
            output = "validation_patterns_template.csv"
        elif template == 'excel':
            output = "validation_patterns_template.xlsx"
        elif template == 'json':
            output = "validation_patterns_template.json"

    output_path = Path(output)

    try:
        if template == 'csv':
            manager.save_template_csv(output_path)
        elif template == 'excel':
            manager.save_template_excel(output_path)
        elif template == 'json':
            # Create JSON template (implement this method in manager if needed)
            click.echo("JSON template creation not yet implemented")
            return

        if RICH_AVAILABLE:
            console.print(Panel.fit(
                f"[green]OK[/green] Template created: [bold]{output_path}[/bold]\n"
                f"[dim]Format:[/dim] {template.upper()}\n"
                f"[dim]Edit this file to add your custom validation patterns[/dim]",
                title="Template Created"
            ))
        else:
            click.echo(f"OK: Template created: {output_path}")
            click.echo(f"  Format: {template.upper()}")
            click.echo("  Edit this file to add your custom validation patterns")

    except Exception as e:
        click.echo(f"Error creating template: {e}", err=True)


def _get_project_path(project: str) -> Path:
    """Get project path from name or path string"""
    path = Path(project)
    if path.is_absolute() or path.exists():
        return path
    else:
        # Try as project name in projects directory
        return Path("projects") / project


def _load_project_config(proj_path: Path) -> Optional[ProjectConfig]:
    """Load project configuration"""
    config_file = proj_path / "project.json"

    if not config_file.exists():
        click.echo(f"Error: Project config not found at {config_file}", err=True)
        return None

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        return ProjectConfig.from_dict(config_data)
    except Exception as e:
        click.echo(f"Error loading project config: {e}", err=True)
        return None


if __name__ == '__main__':
    cli()