"""Smart Glossary Filtering for optimized translation prompts"""

import re
from typing import Dict, List, Set
from collections import defaultdict


class SmartGlossaryMatcher:
    """Intelligent glossary matcher that finds only relevant terms for given texts"""

    def __init__(self, glossary: Dict[str, str]):
        """Initialize with full glossary

        Args:
            glossary: Full glossary dictionary {source_term: translated_term}
        """
        self.glossary = glossary
        self.terms_lowercase = {term.lower(): term for term in glossary.keys()}

        # Pre-compile regex patterns for better performance
        self._word_patterns = {}
        for term in glossary.keys():
            # Create word boundary pattern for each term
            pattern = r'\b' + re.escape(term) + r'\b'
            self._word_patterns[term] = re.compile(pattern, re.IGNORECASE)

    def find_relevant_terms(self, text: str) -> Dict[str, str]:
        """Find only glossary terms that appear in the given text

        Args:
            text: Source text to analyze

        Returns:
            Dictionary with only relevant glossary terms
        """
        if not text or not self.glossary:
            return {}

        relevant = {}
        text_lower = text.lower()

        # Method 1: Exact case-sensitive match (highest priority)
        for term in self.glossary:
            if term in text:
                relevant[term] = self.glossary[term]

        # Method 2: Case-insensitive match for terms not found yet
        for term_lower, original_term in self.terms_lowercase.items():
            if original_term not in relevant and term_lower in text_lower:
                relevant[original_term] = self.glossary[original_term]

        # Method 3: Word boundary match for more precision
        for term in self.glossary:
            if term not in relevant:
                if self._word_patterns[term].search(text):
                    relevant[term] = self.glossary[term]

        return relevant

    def find_batch_relevant_terms(self, texts: List[str]) -> Dict[str, str]:
        """Find all relevant terms for a batch of texts

        Args:
            texts: List of source texts to analyze

        Returns:
            Dictionary with all relevant glossary terms from the batch
        """
        if not texts:
            return {}

        all_relevant = {}

        for text in texts:
            if text:  # Skip empty texts
                relevant = self.find_relevant_terms(text)
                all_relevant.update(relevant)

        return all_relevant

    def get_coverage_stats(self, texts: List[str]) -> Dict[str, any]:
        """Get statistics about glossary coverage for given texts

        Args:
            texts: List of source texts to analyze

        Returns:
            Statistics dictionary
        """
        batch_relevant = self.find_batch_relevant_terms(texts)

        total_terms = len(self.glossary)
        used_terms = len(batch_relevant)
        coverage_percent = (used_terms / total_terms * 100) if total_terms > 0 else 0

        return {
            "total_glossary_terms": total_terms,
            "relevant_terms_found": used_terms,
            "coverage_percentage": round(coverage_percent, 2),
            "optimization_ratio": round((1 - used_terms / total_terms) * 100, 2) if total_terms > 0 else 0,
            "relevant_terms": list(batch_relevant.keys())
        }

    def format_relevant_glossary_for_prompt(self, texts: List[str],
                                          max_terms: int = None) -> str:
        """Format relevant glossary terms for inclusion in AI prompt

        Args:
            texts: Source texts to find relevant terms for
            max_terms: Maximum number of terms to include (most frequent first)

        Returns:
            Formatted glossary string for prompt
        """
        relevant_terms = self.find_batch_relevant_terms(texts)

        if not relevant_terms:
            return ""

        # Limit terms if specified
        if max_terms and len(relevant_terms) > max_terms:
            # For now, just take first N terms
            # Could be improved to prioritize by frequency or importance
            relevant_terms = dict(list(relevant_terms.items())[:max_terms])

        # Format as simple key-value pairs
        glossary_lines = []
        for source_term, translated_term in relevant_terms.items():
            glossary_lines.append(f"{source_term} = {translated_term}")

        if glossary_lines:
            return "Relevant glossary terms:\n" + "\n".join(glossary_lines)
        return ""


def create_smart_glossary_matcher(glossary: Dict[str, str]) -> SmartGlossaryMatcher:
    """Factory function to create SmartGlossaryMatcher instance

    Args:
        glossary: Full glossary dictionary

    Returns:
        SmartGlossaryMatcher instance
    """
    return SmartGlossaryMatcher(glossary)


# Utility functions for backward compatibility
def get_batch_relevant_glossary(texts: List[str], glossary: Dict[str, str]) -> Dict[str, str]:
    """Get relevant glossary terms for a batch of texts

    Args:
        texts: List of source texts
        glossary: Full glossary dictionary

    Returns:
        Dictionary with only relevant terms
    """
    if not glossary:
        return {}

    matcher = SmartGlossaryMatcher(glossary)
    return matcher.find_batch_relevant_terms(texts)


def format_glossary_for_prompt(glossary_terms: Dict[str, str]) -> str:
    """Format glossary terms for AI prompt

    Args:
        glossary_terms: Dictionary of glossary terms to format

    Returns:
        Formatted string for prompt inclusion
    """
    if not glossary_terms:
        return ""

    glossary_lines = [f"{source} = {target}" for source, target in glossary_terms.items()]
    return "Glossary terms:\n" + "\n".join(glossary_lines)