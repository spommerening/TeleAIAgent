"""
Advanced Tag Processing and Quality Enhancement
Handles tag validation, filtering, categorization and enhancement
"""

import logging
import re
from typing import Dict, List, Set, Tuple
from collections import defaultdict

from config import Config

logger = logging.getLogger(__name__)


class TagProcessor:
    """Advanced tag processing with quality filtering and categorization"""
    
    def __init__(self):
        self.generic_tags = set(Config.FILTER_GENERIC_TAGS)
        self.category_keywords = self._build_category_mapping()
        self.min_length = Config.MIN_TAG_LENGTH
        self.max_length = Config.MAX_TAG_LENGTH
        self.min_count = Config.MIN_TAGS_COUNT
        self.max_count = Config.MAX_TAGS_COUNT
        
    def _build_category_mapping(self) -> Dict[str, str]:
        """Build mapping from keywords to categories"""
        mapping = {}
        for category, keywords in Config.TAG_CATEGORIES.items():
            for keyword in keywords:
                mapping[keyword] = category
        return mapping
        
    def process_tags(self, raw_tags: List[str], enable_categorization: bool = True) -> Dict:
        """
        Process and enhance raw tags from AI analysis
        
        Args:
            raw_tags: Raw tag list from AI model
            enable_categorization: Whether to categorize tags
            
        Returns:
            Dict with processed tags, categories, and quality metrics
        """
        logger.info(f"🏷️ Processing {len(raw_tags)} raw tags for quality enhancement")
        
        # Step 1: Basic cleaning and validation
        cleaned_tags = self._clean_and_validate_tags(raw_tags)
        logger.info(f"✅ After cleaning: {len(cleaned_tags)} valid tags")
        
        # Step 2: Remove generic/low-quality tags
        filtered_tags = self._filter_generic_tags(cleaned_tags)
        logger.info(f"✅ After generic filtering: {len(filtered_tags)} quality tags")
        
        # Step 3: Enhance tags with compound descriptors
        enhanced_tags = self._enhance_descriptive_tags(filtered_tags)
        logger.info(f"✅ After enhancement: {len(enhanced_tags)} enhanced tags")
        
        # Step 4: Ensure minimum count with fallback
        final_tags = self._ensure_minimum_count(enhanced_tags, cleaned_tags)
        logger.info(f"✅ Final tag count: {len(final_tags)} tags")
        
        # Step 5: Categorize tags if requested
        result = {
            'tags': final_tags[:self.max_count],  # Limit to max count
            'tag_count': len(final_tags[:self.max_count]),
            'quality_score': self._calculate_quality_score(final_tags, raw_tags),
            'processing_stats': {
                'original_count': len(raw_tags),
                'cleaned_count': len(cleaned_tags),
                'filtered_count': len(filtered_tags),
                'enhanced_count': len(enhanced_tags),
                'final_count': len(final_tags)
            }
        }
        
        if enable_categorization:
            result['categorized_tags'] = self._categorize_tags(final_tags)
            
        return result
    
    def _clean_and_validate_tags(self, raw_tags: List[str]) -> List[str]:
        """Clean and validate individual tags"""
        cleaned = []
        
        for tag in raw_tags:
            if not isinstance(tag, str):
                continue
                
            # Basic cleaning
            tag = tag.strip().lower()
            tag = re.sub(r'[^\w\-äöüß]', '', tag)  # Keep German umlauts
            tag = tag.strip('-_')
            
            # Validation checks
            if (self.min_length <= len(tag) <= self.max_length and
                tag not in cleaned and  # No duplicates
                not tag.isdigit() and  # No pure numbers
                len(re.sub(r'\d', '', tag)) > 2):  # Must have letters
                
                cleaned.append(tag)
                
        return cleaned
    
    def _filter_generic_tags(self, tags: List[str]) -> List[str]:
        """Remove generic, non-descriptive tags"""
        filtered = []
        
        for tag in tags:
            # Skip if in generic filter list
            if tag in self.generic_tags:
                continue
                
            # Skip overly generic words
            if len(tag) <= 2:
                continue
                
            # Skip tags that are too common/vague
            generic_patterns = [
                r'^(sehr|ganz|etwas|ziemlich)$',
                r'^(kleine?|große?|lange?|kurze?)$',
                r'^(neue?s?|alte?s?)$',
                r'^(gute?s?|schlechte?s?)$'
            ]
            
            is_generic = any(re.match(pattern, tag) for pattern in generic_patterns)
            if not is_generic:
                filtered.append(tag)
                
        return filtered
    
    def _enhance_descriptive_tags(self, tags: List[str]) -> List[str]:
        """Enhance tags by creating compound descriptors where appropriate"""
        enhanced = []
        
        # Create compound tags for better description
        color_words = ["rot", "blau", "grün", "gelb", "orange", "lila", "rosa", "braun", "grau", "schwarz", "weiß"]
        mood_words = ["warm", "kalt", "hell", "dunkel", "weich", "hart", "glänzend", "matt"]
        
        for tag in tags:
            enhanced.append(tag)
            
            # Try to create compound descriptors
            for color in color_words:
                if color in tag and color != tag:
                    # Create compound like "warmes-rot" instead of just "warm" and "rot"
                    continue
                    
        # Remove duplicates while preserving order
        seen = set()
        result = []
        for tag in enhanced:
            if tag not in seen:
                seen.add(tag)
                result.append(tag)
                
        return result
    
    def _ensure_minimum_count(self, enhanced_tags: List[str], cleaned_tags: List[str]) -> List[str]:
        """Ensure minimum tag count by adding back high-quality cleaned tags if needed"""
        if len(enhanced_tags) >= self.min_count:
            return enhanced_tags
            
        # Add back best cleaned tags that weren't in enhanced
        additional_needed = self.min_count - len(enhanced_tags)
        enhanced_set = set(enhanced_tags)
        
        additional_tags = [
            tag for tag in cleaned_tags 
            if tag not in enhanced_set and len(tag) > 3
        ][:additional_needed]
        
        result = enhanced_tags + additional_tags
        logger.info(f"🔧 Added {len(additional_tags)} fallback tags to meet minimum count")
        
        return result
    
    def _categorize_tags(self, tags: List[str]) -> Dict[str, List[str]]:
        """Categorize tags into semantic groups"""
        categorized = defaultdict(list)
        
        for tag in tags:
            category = self._identify_tag_category(tag)
            categorized[category].append(tag)
            
        return dict(categorized)
    
    def _identify_tag_category(self, tag: str) -> str:
        """Identify the category of a single tag"""
        # Direct keyword match
        if tag in self.category_keywords:
            return self.category_keywords[tag]
            
        # Partial keyword match (for compound tags)
        for keyword, category in self.category_keywords.items():
            if keyword in tag or tag in keyword:
                return category
                
        # Pattern-based categorization
        if re.search(r'(farbe|farbig|bunt)', tag):
            return "colors"
        elif re.search(r'(stimmung|gefühl|emotion)', tag):
            return "moods"
        elif re.search(r'(zeit|uhr|stunde|tag|nacht)', tag):
            return "time"
        elif re.search(r'(stil|art|weise|technik)', tag):
            return "style"
        elif re.search(r'(ort|platz|raum|bereich)', tag):
            return "settings"
        elif re.search(r'(aktion|bewegung|aktivität)', tag):
            return "actions"
        else:
            return "general"
    
    def _calculate_quality_score(self, final_tags: List[str], original_tags: List[str]) -> float:
        """Calculate a quality score for the tag processing"""
        if not original_tags:
            return 0.0
            
        # Factors for quality scoring
        diversity_score = len(set(final_tags)) / max(len(final_tags), 1)  # Uniqueness
        length_score = sum(1 for tag in final_tags if len(tag) > 4) / len(final_tags)  # Descriptiveness
        retention_score = len(final_tags) / len(original_tags)  # How many we kept
        
        # Combined score (0-1)
        quality_score = (diversity_score * 0.3 + length_score * 0.4 + retention_score * 0.3)
        
        return round(quality_score, 3)
    
    def merge_multi_pass_tags(self, 
                            primary_result: Dict, 
                            artistic_tags: List[str] = None, 
                            contextual_tags: List[str] = None) -> Dict:
        """
        Merge results from multiple analysis passes
        
        Args:
            primary_result: Result from primary analysis
            artistic_tags: Tags from artistic analysis
            contextual_tags: Tags from contextual analysis
            
        Returns:
            Enhanced result with merged tags
        """
        logger.info("🔀 Merging multi-pass analysis results")
        
        all_tags = primary_result['tags'].copy()
        
        # Add artistic tags if provided
        if artistic_tags:
            processed_artistic = self.process_tags(artistic_tags, enable_categorization=False)
            all_tags.extend(processed_artistic['tags'])
            
        # Add contextual tags if provided  
        if contextual_tags:
            processed_contextual = self.process_tags(contextual_tags, enable_categorization=False)
            all_tags.extend(processed_contextual['tags'])
            
        # Remove duplicates while preserving order
        seen = set()
        merged_tags = []
        for tag in all_tags:
            if tag not in seen:
                seen.add(tag)
                merged_tags.append(tag)
                
        # Limit to max count with priority to primary tags
        final_tags = merged_tags[:self.max_count]
        
        # Update result
        merged_result = primary_result.copy()
        merged_result.update({
            'tags': final_tags,
            'tag_count': len(final_tags),
            'multi_pass': True,
            'sources': {
                'primary': len(primary_result['tags']),
                'artistic': len(artistic_tags) if artistic_tags else 0,
                'contextual': len(contextual_tags) if contextual_tags else 0,
                'merged_total': len(merged_tags),
                'final_count': len(final_tags)
            }
        })
        
        # Re-categorize merged tags
        merged_result['categorized_tags'] = self._categorize_tags(final_tags)
        
        logger.info(f"✅ Multi-pass merge completed: {len(final_tags)} final tags from {len(all_tags)} total")
        
        return merged_result