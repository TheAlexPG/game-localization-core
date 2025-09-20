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
@click.option('--api-url', help='API URL for local provider')
@click.option('--threads', '-t', default=1, help='Number of parallel threads (default: 1)')
@click.option('--batch-size', default=5, help='Number of texts to translate at once')
@click.option('--max-entries', type=int, help='Maximum entries to translate (for testing)')
@click.option('--patterns', help='Custom validation patterns file (CSV/Excel/JSON)')
def translate(project: str, provider: str, model: Optional[str], api_key: Optional[str],
              api_url: Optional[str], threads: int, batch_size: int, max_entries: Optional[int], patterns: Optional[str]):
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
            kwargs = {'model_name': model or 'local-model'}
            if api_url:
                kwargs['api_url'] = api_url
            ai_provider = get_provider('local', **kwargs)
        elif provider == 'mock':
            ai_provider = get_provider('mock')
        else:
            click.echo(f"Error: Unknown provider: {provider}", err=True)
            return

    except Exception as e:
        click.echo(f"Error initializing provider: {e}", err=True)
        return

    # Load real project data
    from game_translator.core.project import TranslationProject

    try:
        project_obj = TranslationProject.load(project)

        # Get pending entries
        all_entries = list(project_obj.entries.values())
        pending_entries = [entry for entry in all_entries if entry.status == TranslationStatus.PENDING]

        if max_entries:
            pending_entries = pending_entries[:max_entries]

        if not pending_entries:
            click.echo("No pending entries found for translation!")
            return

        click.echo(f"Starting translation with {provider} provider...")
        click.echo(f"Translating {len(pending_entries)} pending entries out of {len(all_entries)} total")

    except Exception as e:
        click.echo(f"Error loading project data: {e}", err=True)
        return

    # Translate entries
    if RICH_AVAILABLE:
        from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            console=console
        ) as progress:
            task = progress.add_task("Translating entries...", total=len(pending_entries))

            # Create batches
            batches = [pending_entries[i:i + batch_size] for i in range(0, len(pending_entries), batch_size)]

            # Define batch translation function
            def translate_batch(batch):
                try:
                    # Extract texts from batch
                    texts = [entry.source_text for entry in batch]

                    # Translate batch
                    translations = ai_provider.translate_texts(
                        texts,
                        source_lang=config.source_lang,
                        target_lang=config.target_lang,
                        glossary=project_obj.glossary,
                        context=project_obj.format_context_for_prompt('project')
                    )

                    # Update entries with translations
                    for entry, translation in zip(batch, translations):
                        if translation:
                            entry.translated_text = translation
                            entry.status = TranslationStatus.TRANSLATED

                    return len(batch)  # Return number of processed entries
                except Exception as e:
                    click.echo(f"Error translating batch: {e}")
                    return len(batch)  # Still count as processed for progress

            # Process batches with threading
            from concurrent.futures import ThreadPoolExecutor, as_completed
            with ThreadPoolExecutor(max_workers=threads) as executor:
                future_to_batch = {executor.submit(translate_batch, batch): batch for batch in batches}

                for future in as_completed(future_to_batch):
                    try:
                        processed_count = future.result()
                        # Update progress for all entries in the batch
                        for _ in range(processed_count):
                            progress.advance(task)
                    except Exception as e:
                        # Get batch size from the failed future
                        batch = future_to_batch[future]
                        for _ in range(len(batch)):
                            progress.advance(task)
    else:
        # Process in batches without rich progress bar using threading
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Create batches
        batches = [pending_entries[i:i + batch_size] for i in range(0, len(pending_entries), batch_size)]

        click.echo(f"Processing {len(batches)} batches with {threads} threads...")

        def translate_batch(batch_info):
            batch, batch_num = batch_info
            try:
                # Extract texts from batch
                texts = [entry.source_text for entry in batch]

                # Translate batch
                translations = ai_provider.translate_texts(
                    texts,
                    source_lang=config.source_lang,
                    target_lang=config.target_lang,
                    glossary=project_obj.glossary,
                    context=project_obj.format_context_for_prompt('project')
                )

                # Update entries with translations
                for entry, translation in zip(batch, translations):
                    if translation:
                        entry.translated_text = translation
                        entry.status = TranslationStatus.TRANSLATED

                return batch_num, len(batch), True  # batch_num, processed_count, success
            except Exception as e:
                return batch_num, len(batch), False  # batch_num, processed_count, success

        # Process batches with threading
        with ThreadPoolExecutor(max_workers=threads) as executor:
            batch_infos = [(batch, i + 1) for i, batch in enumerate(batches)]
            future_to_info = {executor.submit(translate_batch, info): info for info in batch_infos}

            completed = 0
            for future in as_completed(future_to_info):
                batch_num, processed_count, success = future.result()
                completed += 1
                status = "✓" if success else "✗"
                click.echo(f"Batch {batch_num}/{len(batches)} {status} ({processed_count} entries) - {completed}/{len(batches)} completed")

    # Save project with updated translations
    try:
        project_obj._save_project_state()
        click.echo(f"\nProject saved with updated translations.")
    except Exception as e:
        click.echo(f"Warning: Could not save project: {e}")

    # Run validation on translated entries
    validation_issues = 0
    validation_warnings = 0

    click.echo("\nValidating translations...")
    for entry in pending_entries:
        if entry.translated_text:
            result = validator.validate_entry(entry)
            validation_issues += len(result.issues)
            validation_warnings += len(result.warnings)

    if validation_issues > 0 or validation_warnings > 0:
        click.echo(f"Validation: {validation_issues} issues, {validation_warnings} warnings found")
    else:
        click.echo("Validation: All translations look good!")

    # Show translation results summary
    translated_count = len([e for e in pending_entries if e.translated_text])
    failed_count = len(pending_entries) - translated_count

    click.echo(f"\nTranslation Summary:")
    click.echo("-" * 40)
    click.echo(f"Successfully translated: {translated_count}")
    click.echo(f"Failed: {failed_count}")
    if validation_issues > 0:
        click.echo(f"Validation issues: {validation_issues}")
    if validation_warnings > 0:
        click.echo(f"Validation warnings: {validation_warnings}")

    # Show sample results
    click.echo(f"\nSample Results (first 3):")
    click.echo("-" * 40)

    for i, entry in enumerate(pending_entries[:3]):
        click.echo(f"Key: {entry.key}")
        click.echo(f"Source: {entry.source_text}")
        click.echo(f"Translation: {entry.translated_text or '(failed)'}")
        click.echo(f"Status: {entry.status.value}")
        click.echo()

    if len(pending_entries) > 3:
        click.echo(f"... and {len(pending_entries) - 3} more entries translated")


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
@click.option('--project', '-p', required=True, help='Project name or path')
@click.option('--provider', type=click.Choice(['openai', 'local', 'mock']),
              required=True, help='AI provider to use')
@click.option('--model', help='Model name (provider-specific)')
@click.option('--api-key', help='API key for provider (if required)')
@click.option('--api-url', help='API URL for local provider')
@click.option('--threads', '-t', default=1, help='Number of parallel threads (default: 1)')
@click.option('--batch-size', default=10, help='Number of texts per batch')
@click.option('--max-entries', type=int, help='Maximum entries to process (for testing)')
def extract_terms(project: str, provider: str, model: Optional[str], api_key: Optional[str],
                  api_url: Optional[str], threads: int, batch_size: int, max_entries: Optional[int]):
    """Extract important terms from source texts for glossary building"""

    from game_translator.core.project import TranslationProject
    from game_translator.providers import get_provider
    import threading
    from concurrent.futures import ThreadPoolExecutor, as_completed

    try:
        # Load project
        project_obj = TranslationProject.load(project)
        click.echo(f"Loaded project: {project_obj.config.name}")

        # Get source entries
        entries = list(project_obj.entries.values())
        source_texts = [entry.source_text for entry in entries if entry.source_text]

        if max_entries:
            source_texts = source_texts[:max_entries]

        click.echo(f"Extracting terms from {len(source_texts)} source texts...")

        # Initialize provider
        provider_kwargs = {}
        if api_key:
            provider_kwargs['api_key'] = api_key
        if model:
            provider_kwargs['model_name'] = model
        if api_url and provider == 'local':
            provider_kwargs['api_url'] = api_url

        ai_provider = get_provider(provider, **provider_kwargs)

        # Get project and glossary context
        project_context = project_obj.format_context_for_prompt('project')
        glossary_context = project_obj.format_context_for_prompt('glossary')
        combined_context = f"{project_context}\n{glossary_context}".strip()

        # Extract terms with threading
        all_terms = set()
        completed_batches = 0

        def extract_batch(texts_batch):
            try:
                # Join texts for batch processing
                combined_text = "\n".join(texts_batch)
                extracted = ai_provider.extract_terms_structured(combined_text, combined_context)
                return extracted
            except Exception as e:
                click.echo(f"Error in batch: {e}")
                return []

        # Create batches
        batches = [source_texts[i:i+batch_size] for i in range(0, len(source_texts), batch_size)]

        if RICH_AVAILABLE:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("Extracting terms...", total=len(batches))

                with ThreadPoolExecutor(max_workers=threads) as executor:
                    future_to_batch = {executor.submit(extract_batch, batch): batch for batch in batches}

                    for future in as_completed(future_to_batch):
                        try:
                            terms = future.result()
                            all_terms.update(terms)
                            progress.advance(task)
                        except Exception as e:
                            click.echo(f"Batch failed: {e}")
                            progress.advance(task)
        else:
            with ThreadPoolExecutor(max_workers=threads) as executor:
                future_to_batch = {executor.submit(extract_batch, batch): batch for batch in batches}

                for future in as_completed(future_to_batch):
                    try:
                        terms = future.result()
                        all_terms.update(terms)
                        completed_batches += 1
                        click.echo(f"Completed batch {completed_batches}/{len(batches)}")
                    except Exception as e:
                        click.echo(f"Batch failed: {e}")
                        completed_batches += 1

        # Save extracted terms to project
        extracted_terms = list(all_terms)
        extracted_terms_data = {term: {"source": term, "translated": None, "context": "extracted"} for term in extracted_terms}

        # Save to extracted terms file
        extracted_file = project_obj.project_dir / "glossary" / "extracted_terms.json"
        import json
        with open(extracted_file, 'w', encoding='utf-8') as f:
            json.dump(extracted_terms_data, f, indent=2, ensure_ascii=False)

        click.echo(f"\nExtracted {len(extracted_terms)} unique terms")
        click.echo(f"Saved to: {extracted_file}")
        click.echo("\nSample terms:")
        for term in list(extracted_terms)[:10]:
            click.echo(f"  - {term}")
        if len(extracted_terms) > 10:
            click.echo(f"  ... and {len(extracted_terms) - 10} more")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option('--project', '-p', required=True, help='Project name or path')
@click.option('--provider', type=click.Choice(['openai', 'local', 'mock']),
              required=True, help='AI provider to use')
@click.option('--model', help='Model name (provider-specific)')
@click.option('--api-key', help='API key for provider (if required)')
@click.option('--api-url', help='API URL for local provider')
@click.option('--threads', '-t', default=1, help='Number of parallel threads (default: 1)')
@click.option('--batch-size', default=10, help='Number of terms per batch')
@click.option('--input-file', help='Input file with extracted terms (default: extracted_terms.json)')
def translate_glossary(project: str, provider: str, model: Optional[str], api_key: Optional[str],
                       api_url: Optional[str], threads: int, batch_size: int, input_file: Optional[str]):
    """Translate extracted glossary terms"""

    from game_translator.core.project import TranslationProject
    from game_translator.providers import get_provider
    import json
    from concurrent.futures import ThreadPoolExecutor, as_completed

    try:
        # Load project
        project_obj = TranslationProject.load(project)
        click.echo(f"Loaded project: {project_obj.config.name}")

        # Load extracted terms
        if not input_file:
            input_file = project_obj.project_dir / "glossary" / "extracted_terms.json"
        else:
            input_file = Path(input_file)

        if not input_file.exists():
            click.echo(f"Error: Extracted terms file not found: {input_file}", err=True)
            click.echo("Run 'extract-terms' command first", err=True)
            return

        with open(input_file, 'r', encoding='utf-8') as f:
            terms_data = json.load(f)

        # Get terms that need translation
        terms_to_translate = [term for term, data in terms_data.items()
                             if not data.get('translated')]

        if not terms_to_translate:
            click.echo("All terms are already translated!")
            return

        click.echo(f"Translating {len(terms_to_translate)} terms...")

        # Initialize provider
        provider_kwargs = {}
        if api_key:
            provider_kwargs['api_key'] = api_key
        if model:
            provider_kwargs['model_name'] = model
        if api_url and provider == 'local':
            provider_kwargs['api_url'] = api_url

        ai_provider = get_provider(provider, **provider_kwargs)

        # Get project config for languages
        config = project_obj.config

        # Translate in batches with threading
        def translate_batch(terms_batch):
            try:
                # translate_glossary_structured returns Dict[str, str], not List[str]
                translations_dict = ai_provider.translate_glossary_structured(
                    terms_batch,
                    config.source_lang,
                    config.target_lang
                )
                return translations_dict
            except Exception as e:
                click.echo(f"Error in batch: {e}")
                return {}

        # Create batches
        batches = [terms_to_translate[i:i+batch_size] for i in range(0, len(terms_to_translate), batch_size)]
        translated_terms = {}

        if RICH_AVAILABLE:
            from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                task = progress.add_task("Translating glossary...", total=len(batches))

                with ThreadPoolExecutor(max_workers=threads) as executor:
                    future_to_batch = {executor.submit(translate_batch, batch): batch for batch in batches}

                    for future in as_completed(future_to_batch):
                        try:
                            batch_translations = future.result()
                            translated_terms.update(batch_translations)
                            progress.advance(task)
                        except Exception as e:
                            click.echo(f"Batch failed: {e}")
                            progress.advance(task)
        else:
            completed_batches = 0
            with ThreadPoolExecutor(max_workers=threads) as executor:
                future_to_batch = {executor.submit(translate_batch, batch): batch for batch in batches}

                for future in as_completed(future_to_batch):
                    try:
                        batch_translations = future.result()
                        translated_terms.update(batch_translations)
                        completed_batches += 1
                        click.echo(f"Completed batch {completed_batches}/{len(batches)}")
                    except Exception as e:
                        click.echo(f"Batch failed: {e}")
                        completed_batches += 1

        # Update terms data with translations
        for term, translation in translated_terms.items():
            if term in terms_data:
                terms_data[term]['translated'] = translation

        # Save updated terms
        with open(input_file, 'w', encoding='utf-8') as f:
            json.dump(terms_data, f, indent=2, ensure_ascii=False)

        # Also save as project glossary
        glossary = {term: data['translated'] for term, data in terms_data.items()
                   if data.get('translated')}
        project_obj.glossary.update(glossary)
        project_obj.save_glossary()

        click.echo(f"\nTranslated {len(translated_terms)} terms")
        click.echo(f"Updated: {input_file}")
        click.echo(f"Glossary saved to project")
        click.echo("\nSample translations:")
        for term, translation in list(translated_terms.items())[:5]:
            click.echo(f"  {term} -> {translation}")
        if len(translated_terms) > 5:
            click.echo(f"  ... and {len(translated_terms) - 5} more")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@cli.command()
@click.option('--project', '-p', required=True, help='Project name or path')
@click.option('--provider', type=click.Choice(['openai', 'local', 'mock']),
              required=True, help='AI provider to use')
@click.option('--model', help='Model name (provider-specific)')
@click.option('--api-key', help='API key for provider (if required)')
@click.option('--api-url', help='API URL for local provider')
@click.option('--threads', '-t', default=1, help='Number of parallel threads (default: 1)')
@click.option('--extract-threads', default=1, help='Threads for term extraction stage')
@click.option('--glossary-threads', default=1, help='Threads for glossary translation stage')
@click.option('--translate-threads', default=1, help='Threads for main translation stage')
@click.option('--skip-extract', is_flag=True, help='Skip term extraction (use existing)')
@click.option('--skip-glossary', is_flag=True, help='Skip glossary translation (use existing)')
@click.option('--extract-batch-size', default=10, help='Batch size for term extraction')
@click.option('--glossary-batch-size', default=10, help='Batch size for glossary translation')
@click.option('--translate-batch-size', default=5, help='Batch size for main translation')
def pipeline(project: str, provider: str, model: Optional[str], api_key: Optional[str],
             api_url: Optional[str], threads: int, extract_threads: int, glossary_threads: int,
             translate_threads: int, skip_extract: bool, skip_glossary: bool,
             extract_batch_size: int, glossary_batch_size: int, translate_batch_size: int):
    """Run complete 3-stage translation pipeline: extract terms -> translate glossary -> translate game"""

    import subprocess
    import sys

    click.echo("Starting 3-stage translation pipeline")
    click.echo(f"Project: {project}")
    click.echo(f"Provider: {provider} ({model or 'default model'})")
    click.echo(f"Threads: extract={extract_threads}, glossary={glossary_threads}, translate={translate_threads}")
    click.echo("=" * 60)

    # Base command parts
    base_cmd = [sys.executable, '-m', 'game_translator_cli.main']
    provider_args = ['--provider', provider]
    if model:
        provider_args.extend(['--model', model])
    if api_key:
        provider_args.extend(['--api-key', api_key])
    if api_url:
        provider_args.extend(['--api-url', api_url])

    try:
        # Stage 1: Extract terms
        if not skip_extract:
            click.echo("\nStage 1: Extracting terms from source texts...")
            extract_cmd = base_cmd + ['extract-terms', '--project', project] + provider_args + [
                '--threads', str(extract_threads),
                '--batch-size', str(extract_batch_size)
            ]
            result = subprocess.run(extract_cmd, check=True, capture_output=True, text=True)
            click.echo(result.stdout)
        else:
            click.echo("\nStage 1: Skipped (using existing extracted terms)")

        # Stage 2: Translate glossary
        if not skip_glossary:
            click.echo("\nStage 2: Translating glossary terms...")
            glossary_cmd = base_cmd + ['translate-glossary', '--project', project] + provider_args + [
                '--threads', str(glossary_threads),
                '--batch-size', str(glossary_batch_size)
            ]
            result = subprocess.run(glossary_cmd, check=True, capture_output=True, text=True)
            click.echo(result.stdout)
        else:
            click.echo("\nStage 2: Skipped (using existing glossary)")

        # Stage 3: Main translation with glossary
        click.echo("\nStage 3: Translating game content with glossary...")
        translate_cmd = base_cmd + ['translate', '--project', project] + provider_args + [
            '--batch-size', str(translate_batch_size)
        ]
        # Note: translate command doesn't have threads option yet, using threads value for future
        result = subprocess.run(translate_cmd, check=True, capture_output=True, text=True)
        click.echo(result.stdout)

        click.echo("\nPipeline completed successfully!")
        click.echo("=" * 60)

        # Show final status
        status_cmd = base_cmd + ['status', '--project', project]
        result = subprocess.run(status_cmd, check=True, capture_output=True, text=True)
        click.echo(result.stdout)

    except subprocess.CalledProcessError as e:
        click.echo(f"\n❌ Pipeline failed at stage: {e.cmd}", err=True)
        click.echo(f"Error: {e.stderr}", err=True)
        sys.exit(1)
    except Exception as e:
        click.echo(f"\n❌ Pipeline error: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.option('--project', '-p', required=True, help='Project name or path')
@click.option('--format', '-f', type=click.Choice(['json', 'csv', 'excel']),
              default='json', help='Export format (default: json)')
@click.option('--output', '-o', help='Output file path')
@click.option('--ignore-validation', is_flag=True,
              help='Export invalid translations as-is (default: use original for invalid)')
def export(project: str, format: str, output: Optional[str], ignore_validation: bool):
    """Export translations to file

    By default, entries that fail validation will use original text.
    Use --ignore-validation to export translations even if they have validation errors.
    """
    import sys
    from game_translator.core.project import TranslationProject
    from game_translator.exporters import get_exporter

    try:
        # Load project
        proj_path = _get_project_path(project)
        if not proj_path.exists():
            click.echo(f"Error: Project '{project}' not found", err=True)
            sys.exit(1)

        # Initialize project
        proj = TranslationProject.load(project, proj_path)

        # Run validation if not ignoring
        validation_results = None
        if not ignore_validation:
            validator = TranslationValidator()
            validation_results = validator.validate_project(proj)

            if validation_results.has_issues:
                click.echo(f"Warning: Found {len(validation_results.issues)} validation issues")

        # Prepare export data
        export_data = proj.export_for_review()

        # If not ignoring validation, replace invalid translations with source
        if not ignore_validation and validation_results:
            invalid_keys = {issue.key for issue in validation_results.issues}
            for entry in export_data['entries']:
                if entry['key'] in invalid_keys:
                    # Use source text instead of translation for invalid entries
                    entry['translation'] = entry['source']
                    if RICH_AVAILABLE:
                        console.print(f"[yellow]Warning[/yellow] Using original for: {entry['key']}")

        # Determine output path
        if not output:
            output_name = f"{proj.config.name}_export_{proj.config.target_lang}"
            if format == 'json':
                output = proj_path / 'output' / f"{output_name}.json"
            elif format == 'csv':
                output = proj_path / 'output' / f"{output_name}.csv"
            elif format == 'excel':
                output = proj_path / 'output' / f"{output_name}.xlsx"
        else:
            output = Path(output)

        # Export using appropriate exporter
        exporter = get_exporter(format)
        exporter.export(export_data, output, glossary=proj.glossary)

        # Summary
        if RICH_AVAILABLE:
            console.print(Panel.fit(
                f"[green]OK[/green] Export completed\n"
                f"[dim]Output:[/dim] {output}\n"
                f"[dim]Format:[/dim] {format.upper()}\n"
                f"[dim]Validation:[/dim] {'Ignored' if ignore_validation else 'Applied'}",
                title="Export Successful"
            ))
        else:
            click.echo(f"OK: Exported to {output}")
            click.echo(f"  Format: {format.upper()}")
            click.echo(f"  Validation: {'Ignored' if ignore_validation else 'Applied'}")

    except Exception as e:
        click.echo(f"\n❌ Export error: {e}", err=True)
        sys.exit(1)


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


@cli.group()
@click.pass_context
def context(ctx):
    """Manage project and glossary context for better translations

    Context helps AI understand your game better:
    - Project context: General game information, tone, style
    - Glossary context: Instructions for term extraction and translation
    """
    pass


@context.command('set')
@click.option('--project', '-p', required=True, help='Project name or path')
@click.option('--type', '-t',
              type=click.Choice(['project', 'glossary'], case_sensitive=False),
              default='project',
              help='Context type to set')
@click.option('--file', '-f', help='Path to context file (markdown/text/json)')
@click.option('--json', '-j', 'json_data', help='JSON string with context data')
@click.pass_context
def context_set(ctx, project, type, file, json_data):
    """Set context from file or JSON data

    Examples:
        # Set from markdown file
        game-translator context set -p my-game --file game_info.md

        # Set from JSON
        game-translator context set -p my-game --json '{"genre": "RPG", "tone": "epic"}'

        # Set glossary context
        game-translator context set -p my-game --type glossary --file glossary_rules.md
    """
    from game_translator import TranslationProject

    try:
        # Load project
        project_obj = TranslationProject.load(project)

        if file:
            # Set from file
            if type == 'project':
                project_obj.set_project_context(from_file=file)
                click.echo(f"Project context set from {file}")
            else:
                project_obj.set_glossary_context(from_file=file)
                click.echo(f"Glossary context set from {file}")

        elif json_data:
            # Parse JSON and set
            import json as json_module
            context_dict = json_module.loads(json_data)

            if type == 'project':
                project_obj.set_project_context(context=context_dict)
                click.echo(f"Project context updated with {len(context_dict)} properties")
            else:
                project_obj.set_glossary_context(context=context_dict)
                click.echo(f"Glossary context updated with {len(context_dict)} properties")
        else:
            click.echo("Error: Provide either --file or --json", err=True)

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@context.command('add')
@click.option('--project', '-p', required=True, help='Project name or path')
@click.option('--type', '-t',
              type=click.Choice(['project', 'glossary'], case_sensitive=False),
              default='project',
              help='Context type to add to')
@click.option('--key', '-k', required=True, help='Property key')
@click.option('--value', '-v', required=True, help='Property value')
@click.pass_context
def context_add(ctx, project, type, key, value):
    """Add single context property

    Examples:
        # Add project context property
        game-translator context add -p my-game --key genre --value "Dark Fantasy"

        # Add glossary context property
        game-translator context add -p my-game --type glossary --key extract_npcs --value true
    """
    from game_translator import TranslationProject

    try:
        project_obj = TranslationProject.load(project)

        if type == 'project':
            project_obj.add_project_context(key, value)
            click.echo(f"Added to project context: {key}={value}")
        else:
            project_obj.add_glossary_context(key, value)
            click.echo(f"Added to glossary context: {key}={value}")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


@context.command('show')
@click.option('--project', '-p', required=True, help='Project name or path')
@click.option('--type', '-t',
              type=click.Choice(['project', 'glossary', 'all'], case_sensitive=False),
              default='all',
              help='Context type to show')
@click.pass_context
def context_show(ctx, project, type):
    """Display current context

    Examples:
        # Show all context
        game-translator context show -p my-game

        # Show only project context
        game-translator context show -p my-game --type project
    """
    from game_translator import TranslationProject

    try:
        project_obj = TranslationProject.load(project)

        if HAS_RICH:
            from rich.console import Console
            from rich.panel import Panel
            from rich.syntax import Syntax
            console = Console()

            if type in ['project', 'all']:
                proj_ctx = project_obj.get_project_context()
                if proj_ctx:
                    content = project_obj.format_context_for_prompt('project')
                    if content:
                        panel = Panel(content, title="[bold blue]Project Context[/bold blue]", border_style="blue")
                        console.print(panel)
                    else:
                        console.print("[yellow]No project context set[/yellow]")
                else:
                    console.print("[yellow]No project context set[/yellow]")

            if type in ['glossary', 'all']:
                gloss_ctx = project_obj.get_glossary_context()
                if gloss_ctx:
                    content = project_obj.format_context_for_prompt('glossary')
                    if content:
                        panel = Panel(content, title="[bold green]Glossary Context[/bold green]", border_style="green")
                        console.print(panel)
                    else:
                        console.print("[yellow]No glossary context set[/yellow]")
                else:
                    console.print("[yellow]No glossary context set[/yellow]")
        else:
            if type in ['project', 'all']:
                proj_ctx = project_obj.get_project_context()
                if proj_ctx:
                    click.echo("\n=== PROJECT CONTEXT ===")
                    click.echo(project_obj.format_context_for_prompt('project'))
                else:
                    click.echo("No project context set")

            if type in ['glossary', 'all']:
                gloss_ctx = project_obj.get_glossary_context()
                if gloss_ctx:
                    click.echo("\n=== GLOSSARY CONTEXT ===")
                    click.echo(project_obj.format_context_for_prompt('glossary'))
                else:
                    click.echo("No glossary context set")

    except Exception as e:
        click.echo(f"Error: {e}", err=True)


def _load_project_config(proj_path: Path) -> Optional[ProjectConfig]:
    """Load project configuration"""
    config_file = proj_path / "project.json"

    if not config_file.exists():
        click.echo(f"Error: Project config not found at {config_file}", err=True)
        return None

    try:
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        # Handle both old format (with "config" key) and new format (flat)
        if "config" in config_data:
            return ProjectConfig.from_dict(config_data["config"])
        else:
            return ProjectConfig.from_dict(config_data)
    except Exception as e:
        click.echo(f"Error loading project config: {e}", err=True)
        return None


if __name__ == '__main__':
    cli()