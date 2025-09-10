"""
Glossary management utilities
"""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from ..core.models import ProjectConfig


class GlossaryManager:
    """Manages glossary files and operations"""
    
    def __init__(self, config: ProjectConfig):
        self.config = config
        self.glossary_dir = Path(config.get_glossary_dir())
    
    def save_extracted_terms(self, terms_data: Dict[str, Any]) -> Path:
        """Save extracted terms to file"""
        self.glossary_dir.mkdir(parents=True, exist_ok=True)
        
        output_file = self.glossary_dir / "extracted_terms.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(terms_data, f, indent=2, ensure_ascii=False)
        
        return output_file
    
    def load_extracted_terms(self) -> List[str]:
        """Load extracted terms"""
        terms_file = self.glossary_dir / "extracted_terms.json"
        
        if not terms_file.exists():
            return []
        
        with open(terms_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('terms', [])
    
    def save_translated_glossary(self, terms: List[str], translations: Dict[str, str]) -> Path:
        """Save translated glossary"""
        self.glossary_dir.mkdir(parents=True, exist_ok=True)
        
        # Create intermediate file for manual validation
        translated_terms_file = self.glossary_dir / "translated_terms.json"
        translated_data = {
            'project': self.config.name,
            'source_lang': self.config.source_lang,
            'target_lang': 'Ukrainian',
            'translations': translations,
            'note': 'This file is for manual validation. Review translations and then copy to final_glossary.json'
        }
        
        with open(translated_terms_file, 'w', encoding='utf-8') as f:
            json.dump(translated_data, f, indent=2, ensure_ascii=False)
        
        print(f"Saved translated terms to: {translated_terms_file}")
        print(f"Please review translations and copy to final_glossary.json when ready")
        
        return translated_terms_file
    
    def create_final_glossary(self, validated_translations: Dict[str, str]) -> Path:
        """Create final glossary after manual validation"""
        final_glossary_file = self.glossary_dir / "final_glossary.json"
        
        # Merge with base glossary from config
        final_translations = {}
        if self.config.glossary_terms:
            final_translations.update(self.config.glossary_terms)
        final_translations.update(validated_translations)
        
        final_data = {
            'project': self.config.name,
            'source_lang': self.config.source_lang,
            'target_lang': 'Ukrainian',
            'target_lang_code': self.config.target_lang_code,
            'translations': final_translations,
            'terms_count': len(final_translations)
        }
        
        with open(final_glossary_file, 'w', encoding='utf-8') as f:
            json.dump(final_data, f, indent=2, ensure_ascii=False)
        
        return final_glossary_file
    
    def load_final_glossary(self) -> Dict[str, str]:
        """Load final glossary for translation"""
        final_glossary_file = self.glossary_dir / "final_glossary.json"
        
        if not final_glossary_file.exists():
            # Fallback to base glossary from config
            return self.config.glossary_terms or {}
        
        with open(final_glossary_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('translations', {})
    
    def export_glossary_for_validation(self) -> Path:
        """Export glossary in human-readable format for validation"""
        translated_file = self.glossary_dir / "translated_terms.json"
        
        if not translated_file.exists():
            raise FileNotFoundError(f"No translated terms found at: {translated_file}")
        
        with open(translated_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Create readable format
        readable_file = self.glossary_dir / "glossary_for_review.txt"
        with open(readable_file, 'w', encoding='utf-8') as f:
            f.write(f"Glossary for {self.config.name} - Please review translations\n")
            f.write("=" * 60 + "\n\n")
            
            translations = data.get('translations', {})
            for en_term, ua_term in sorted(translations.items()):
                f.write(f"{en_term:<20} → {ua_term}\n")
            
            f.write(f"\n\nTotal terms: {len(translations)}")
            f.write("\n\nAfter review, update final_glossary.json with approved translations.")
        
        return readable_file
    
    def get_glossary_stats(self) -> Dict[str, Any]:
        """Get glossary statistics"""
        stats = {
            'extracted_terms': 0,
            'translated_terms': 0,
            'final_glossary_terms': 0,
            'files': []
        }
        
        # Check extracted terms
        extracted_file = self.glossary_dir / "extracted_terms.json"
        if extracted_file.exists():
            with open(extracted_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stats['extracted_terms'] = len(data.get('terms', []))
                stats['files'].append('extracted_terms.json')
        
        # Check translated terms
        translated_file = self.glossary_dir / "translated_terms.json"
        if translated_file.exists():
            with open(translated_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stats['translated_terms'] = len(data.get('translations', {}))
                stats['files'].append('translated_terms.json')
        
        # Check final glossary
        final_file = self.glossary_dir / "final_glossary.json"
        if final_file.exists():
            with open(final_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                stats['final_glossary_terms'] = len(data.get('translations', {}))
                stats['files'].append('final_glossary.json')
        
        return stats