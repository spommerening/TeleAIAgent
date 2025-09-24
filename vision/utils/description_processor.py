"""
Description Processor for Image Analysis
Simple processor to handle image descriptions from AI analysis
"""

import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)


class DescriptionProcessor:
    """Simple processor for image descriptions"""
    
    def __init__(self):
        self.min_description_length = 10
        self.max_description_length = 1000
        
    def process_description(self, raw_description: str) -> Dict:
        """
        Process and validate raw description from AI analysis
        
        Args:
            raw_description: Raw description text from AI model
            
        Returns:
            Dict with processed description and metadata
        """
        logger.info(f"📝 Processing image description (length: {len(raw_description)})")
        
        # Clean and validate description
        cleaned_description = self._clean_description(raw_description)
        
        # Validate description quality
        is_valid = self._validate_description(cleaned_description)
        
        result = {
            'description': cleaned_description,
            'length': len(cleaned_description),
            'is_valid': is_valid,
            'processed_at': time.strftime('%Y-%m-%d %H:%M:%S'),
            'processing_stats': {
                'original_length': len(raw_description),
                'cleaned_length': len(cleaned_description),
                'quality_score': self._calculate_quality_score(cleaned_description)
            }
        }
        
        logger.info(f"✅ Description processed: valid={is_valid}, length={len(cleaned_description)}")
        
        return result
    
    def _clean_description(self, raw_description: str) -> str:
        """Clean and format the description"""
        if not isinstance(raw_description, str):
            return ""
            
        # Basic cleaning
        description = raw_description.strip()
        
        # Remove common AI response prefixes (German)
        prefixes_to_remove = [
            "Dieses Bild zeigt",
            "Das Bild zeigt",
            "Das Bild stellt dar",
            "Ich kann sehen",
            "Auf diesem Bild",
            "In diesem Bild",
            "Das Foto zeigt",
            "Die Aufnahme zeigt",
            "Zu sehen ist",
            "Man sieht",
            "Es ist zu sehen"
        ]
        
        for prefix in prefixes_to_remove:
            if description.startswith(prefix):
                description = description[len(prefix):].strip()
                if description.startswith(","):
                    description = description[1:].strip()
                break
        
        # Ensure proper capitalization
        if description and description[0].islower():
            description = description[0].upper() + description[1:]
        
        # Ensure it ends with punctuation
        if description and description[-1] not in '.!?':
            description += '.'
        
        return description
    
    def _validate_description(self, description: str) -> bool:
        """Validate that the description meets quality criteria"""
        if not description:
            return False
            
        # Check length constraints
        if len(description) < self.min_description_length:
            logger.warning(f"Description too short: {len(description)} < {self.min_description_length}")
            return False
            
        if len(description) > self.max_description_length:
            logger.warning(f"Description too long: {len(description)} > {self.max_description_length}")
            return False
        
        # Check for meaningful content (not just punctuation or numbers)
        meaningful_chars = sum(1 for c in description if c.isalpha())
        if meaningful_chars < 5:
            logger.warning("Description lacks meaningful content")
            return False
        
        return True
    
    def _calculate_quality_score(self, description: str) -> float:
        """Calculate a quality score for the description"""
        if not description:
            return 0.0
        
        # Factors for quality scoring
        length_factor = min(len(description) / 100, 1.0)  # Optimal around 100 chars
        word_count = len(description.split())
        word_factor = min(word_count / 15, 1.0)  # Optimal around 15 words
        
        # Bonus for descriptive words (German)
        descriptive_words = [
            'farbe', 'farbig', 'hell', 'dunkel', 'licht', 'lebhaft', 'schön', 'detailliert',
            'zeigt', 'zeigen', 'enthält', 'beinhaltet', 'präsentiert', 'darstellt',
            'sichtbar', 'erkennbar', 'atmosphäre', 'stimmung', 'komposition', 'perspektive',
            'beleuchtung', 'schatten', 'kontrast', 'textur', 'struktur', 'muster'
        ]
        descriptive_bonus = sum(0.1 for word in descriptive_words if word in description.lower())
        
        # Combined score (0-1)
        quality_score = (length_factor * 0.4 + word_factor * 0.4 + min(descriptive_bonus, 0.2))
        
        return round(quality_score, 3)