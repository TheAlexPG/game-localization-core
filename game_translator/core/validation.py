"""Translation validation system for quality control"""

import re
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from .models import TranslationEntry, TranslationStatus


@dataclass
class ValidationIssue:
    """Single validation issue"""
    key: str
    issue_type: str
    message: str
    severity: str = "error"  # error, warning, info
    suggestion: Optional[str] = None


@dataclass
class ValidationResult:
    """Result of validation check"""
    issues: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    checked_count: int = 0

    def add_issue(self, entry_key: str, issue_type: str, message: str,
                 suggestion: Optional[str] = None):
        """Add validation error"""
        issue = ValidationIssue(
            key=entry_key,
            issue_type=issue_type,
            message=message,
            severity="error",
            suggestion=suggestion
        )
        self.issues.append(issue)

    def add_warning(self, entry_key: str, warning_type: str, message: str,
                   suggestion: Optional[str] = None):
        """Add validation warning"""
        issue = ValidationIssue(
            key=entry_key,
            issue_type=warning_type,
            message=message,
            severity="warning",
            suggestion=suggestion
        )
        self.warnings.append(issue)

    def add_info(self, entry_key: str, info_type: str, message: str):
        """Add validation info"""
        issue = ValidationIssue(
            key=entry_key,
            issue_type=info_type,
            message=message,
            severity="info"
        )
        self.info.append(issue)

    @property
    def has_issues(self) -> bool:
        """Check if there are any issues"""
        return len(self.issues) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings"""
        return len(self.warnings) > 0

    @property
    def total_problems(self) -> int:
        """Total number of problems found"""
        return len(self.issues) + len(self.warnings)

    def get_summary(self) -> str:
        """Get validation summary"""
        return f"Checked {self.checked_count} entries: {len(self.issues)} errors, {len(self.warnings)} warnings"


class TranslationValidator:
    """Validates translation quality and consistency"""

    def __init__(self, strict_mode: bool = False):
        """
        Initialize validator

        Args:
            strict_mode: If True, more checks are performed as errors instead of warnings
        """
        self.strict_mode = strict_mode

        # Patterns for validation
        # Regular placeholders: {placeholder}
        self.placeholder_pattern = re.compile(r'\{[^}]+\}')

        # Game-specific placeholders: {20204,5101}
        self.game_id_pattern = re.compile(r'\{\d+,\d+\}')

        # System variables: $anything$ (flexible content)
        self.system_var_pattern = re.compile(r'\$[^$]+\$')

        # HTML/XML tags: <tag> and <tag attr="value">
        self.html_tag_pattern = re.compile(r'<[^>]+>')

        # HTML entities: &lt; &gt; &#8217; &amp;
        self.html_entity_pattern = re.compile(r'&[a-zA-Z0-9#]+;')

    def validate_entry(self, entry: TranslationEntry) -> ValidationResult:
        """Validate single translation entry"""
        result = ValidationResult()
        result.checked_count = 1

        # Skip validation for skipped entries
        if entry.status == TranslationStatus.SKIPPED:
            return result

        # 1. Check if translation exists (empty translation)
        if not entry.translated_text or not entry.translated_text.strip():
            if entry.status != TranslationStatus.PENDING:
                result.add_issue(entry.key, "empty_translation",
                               "Translation is empty but status is not pending")
            return result

        # 2. Check for unchanged translation (text matches original)
        self._check_unchanged_translation(entry, result)

        # 3. Check placeholders consistency
        self._check_placeholders(entry, result)

        # 4. Check HTML/XML tags consistency
        self._check_tags(entry, result)


        return result

    def _check_unchanged_translation(self, entry: TranslationEntry, result: ValidationResult):
        """Check if translation is identical to source (by hash or direct comparison)"""
        # Option 1: Direct string comparison
        if entry.translated_text.strip() == entry.source_text.strip():
            if entry.is_technical():
                result.add_info(entry.key, "technical_unchanged",
                              "Technical text unchanged (expected for technical terms)")
            else:
                severity = "error" if self.strict_mode else "warning"
                if severity == "error":
                    result.add_issue(entry.key, "unchanged_text",
                                   "Translation identical to source text")
                else:
                    result.add_warning(entry.key, "unchanged_text",
                                     "Translation identical to source text")

        # Option 2: Hash comparison (more flexible for whitespace differences)
        elif entry._calculate_hash(entry.translated_text) == entry.source_hash:
            result.add_info(entry.key, "content_unchanged",
                          "Translation content is the same as source (ignoring formatting)")

    def _check_placeholders(self, entry: TranslationEntry, result: ValidationResult):
        """Check all types of placeholders and variables consistency"""

        # 1. Regular placeholders: {placeholder}
        self._check_placeholder_type(entry, result, self.placeholder_pattern,
                                   "placeholder", "Regular placeholders")

        # 2. System variables: $INPUT_ACTION$
        self._check_placeholder_type(entry, result, self.system_var_pattern,
                                   "system_variable", "System variables")

        # 3. HTML entities: &lt; &gt; &#8217;
        self._check_placeholder_type(entry, result, self.html_entity_pattern,
                                   "html_entity", "HTML entities")

    def _check_placeholder_type(self, entry: TranslationEntry, result: ValidationResult,
                              pattern: re.Pattern, error_type: str, description: str):
        """Check specific type of placeholders"""
        source_items = pattern.findall(entry.source_text)
        trans_items = pattern.findall(entry.translated_text)

        source_set = set(source_items)
        trans_set = set(trans_items)

        if source_set != trans_set:
            missing = source_set - trans_set
            extra = trans_set - source_set

            message_parts = []
            if missing:
                message_parts.append(f"Missing: {', '.join(missing)}")
            if extra:
                message_parts.append(f"Extra: {', '.join(extra)}")

            message = f"{description} mismatch. " + "; ".join(message_parts)
            suggestion = f"Expected {description.lower()}: {', '.join(sorted(source_set))}" if source_set else None

            result.add_issue(entry.key, f"{error_type}_mismatch", message, suggestion)

    def _check_tags(self, entry: TranslationEntry, result: ValidationResult):
        """Check HTML/XML tag consistency"""
        source_tags = self.html_tag_pattern.findall(entry.source_text)
        trans_tags = self.html_tag_pattern.findall(entry.translated_text)

        # Normalize tags for comparison (remove attributes, focus on tag names)
        def normalize_tag(tag):
            return re.sub(r'<(\w+)[^>]*>', r'<\1>', tag)

        source_normalized = [normalize_tag(tag) for tag in source_tags]
        trans_normalized = [normalize_tag(tag) for tag in trans_tags]

        if source_normalized != trans_normalized:
            result.add_issue(entry.key, "tag_mismatch",
                           f"HTML/XML tags don't match. Source: {source_tags}, Translation: {trans_tags}",
                           f"Expected tags: {', '.join(source_tags)}")


    def validate_project(self, project) -> ValidationResult:
        """Validate entire translation project"""
        result = ValidationResult()

        for entry in project.entries.values():
            entry_result = self.validate_entry(entry)

            # Merge results
            result.issues.extend(entry_result.issues)
            result.warnings.extend(entry_result.warnings)
            result.info.extend(entry_result.info)
            result.checked_count += entry_result.checked_count

        return result


class QualityMetrics:
    """Calculate quality metrics for translations"""

    @staticmethod
    def calculate_completion_rate(entries: List[TranslationEntry]) -> float:
        """Calculate completion percentage"""
        if not entries:
            return 0.0

        completed = sum(1 for e in entries
                       if e.status in [TranslationStatus.TRANSLATED,
                                     TranslationStatus.REVIEWED,
                                     TranslationStatus.APPROVED])
        return (completed / len(entries)) * 100.0

    @staticmethod
    def calculate_quality_score(validation_result: ValidationResult) -> float:
        """Calculate quality score (0-100) based on validation results"""
        if validation_result.checked_count == 0:
            return 0.0

        # Weight different issue types
        error_weight = -10
        warning_weight = -2

        total_score = 100
        error_penalty = len(validation_result.issues) * error_weight
        warning_penalty = len(validation_result.warnings) * warning_weight

        final_score = max(0, total_score + error_penalty + warning_penalty)
        return min(100.0, final_score)

    @staticmethod
    def get_quality_grade(score: float) -> str:
        """Get letter grade for quality score"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"