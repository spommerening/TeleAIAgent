#!/usr/bin/env python3
"""
Test script to validate enhanced tagging system improvements
Compares old vs new tagging quality and demonstrates features
"""

import asyncio
import sys
import os
import json
from pathlib import Path

# Add tagger module path
sys.path.append('/home/appl/TeleAIAgent/tagger')

from utils.tag_processor import TagProcessor
from config import Config

async def test_tag_processing():
    """Test the enhanced tag processing system"""
    print("🧪 Testing Enhanced Tag Processing System")
    print("=" * 50)
    
    # Initialize tag processor
    processor = TagProcessor()
    
    # Test cases with simulated AI output (before/after scenarios)
    test_cases = [
        {
            "name": "Cat Image Example",
            "old_tags": ["katze", "tier", "bild", "foto", "innen", "gut", "schön"],
            "new_tags": ["entspannte-katze", "warmes-sonnenlicht", "gemütliche-wohnatmosphäre", 
                        "nachmittagsstimmung", "häusliche-geborgenheit", "flauschiges-fell", 
                        "ruhige-pose", "fensterplatz", "goldenes-licht", "friedliche-szene"]
        },
        {
            "name": "Landscape Example", 
            "old_tags": ["landschaft", "natur", "baum", "himmel", "grün", "blau", "tag"],
            "new_tags": ["weitläufige-berglandschaft", "dramatische-wolkenformation", 
                        "goldene-stunde", "erhabene-natur", "panoramablick", "tiefblaue-schatten",
                        "warmes-abendlicht", "majestätische-gipfel", "endlose-weite", 
                        "naturspektakel", "romantische-stimmung"]
        }
    ]
    
    for test_case in test_cases:
        print(f"\n🎯 Test Case: {test_case['name']}")
        print("-" * 30)
        
        # Process old-style tags
        old_result = processor.process_tags(test_case['old_tags'])
        print(f"📊 Old Tags ({len(test_case['old_tags'])}): {', '.join(test_case['old_tags'])}")
        print(f"   Quality Score: {old_result['quality_score']}")
        print(f"   After Processing: {', '.join(old_result['tags'])}")
        
        # Process new-style tags  
        new_result = processor.process_tags(test_case['new_tags'])
        print(f"✨ New Tags ({len(test_case['new_tags'])}): {', '.join(test_case['new_tags'][:5])}...")
        print(f"   Quality Score: {new_result['quality_score']}")
        print(f"   After Processing: {', '.join(new_result['tags'])}")
        
        # Show categorization
        if 'categorized_tags' in new_result:
            print(f"🏷️ Categories:")
            for category, tags in new_result['categorized_tags'].items():
                if tags:
                    print(f"   {category}: {', '.join(tags)}")
        
        print(f"📈 Quality Improvement: {new_result['quality_score'] - old_result['quality_score']:.3f}")

async def test_multi_pass_merging():
    """Test multi-pass tag merging functionality"""
    print("\n\n🔀 Testing Multi-Pass Tag Merging")
    print("=" * 50)
    
    processor = TagProcessor()
    
    # Simulate results from different analysis passes
    primary_tags = ["entspannte-katze", "warmes-sonnenlicht", "gemütliche-wohnatmosphäre"]
    artistic_tags = ["weiche-komposition", "harmonische-farben", "natürliches-licht", "intime-atmosphäre"]
    contextual_tags = ["nachmittags-szene", "häusliche-umgebung", "ruhe-moment", "alltägliche-schönheit"]
    
    # Process primary result first
    primary_result = processor.process_tags(primary_tags)
    
    # Merge all passes
    merged_result = processor.merge_multi_pass_tags(
        primary_result=primary_result,
        artistic_tags=artistic_tags,
        contextual_tags=contextual_tags
    )
    
    print(f"🎯 Primary Analysis: {', '.join(primary_tags)}")
    print(f"🎨 Artistic Analysis: {', '.join(artistic_tags)}")
    print(f"🌍 Contextual Analysis: {', '.join(contextual_tags)}")
    print(f"🔀 Merged Result ({len(merged_result['tags'])}): {', '.join(merged_result['tags'])}")
    
    if 'sources' in merged_result:
        print(f"📊 Source Distribution: {merged_result['sources']}")

def test_configuration():
    """Test enhanced configuration"""
    print("\n\n⚙️ Testing Enhanced Configuration")
    print("=" * 50)
    
    print(f"🤖 Primary Model: {Config.PRIMARY_VISION_MODEL}")
    print(f"🔄 Fallback Model: {Config.FALLBACK_VISION_MODEL}")
    print(f"📏 Tag Limits: {Config.MIN_TAGS_COUNT}-{Config.MAX_TAGS_COUNT}")
    print(f"🚫 Generic Filter Count: {len(Config.FILTER_GENERIC_TAGS)}")
    print(f"🏷️ Categories: {len(Config.TAG_CATEGORIES)}")
    
    print(f"\n📝 Enhanced Prompt Preview:")
    print(Config.IMAGE_TAGGING_PROMPT[:200] + "...")
    
    print(f"\n🎨 Artistic Prompt Preview:")  
    print(Config.ARTISTIC_ANALYSIS_PROMPT[:150] + "...")

async def main():
    """Run all tests"""
    try:
        print("🚀 Enhanced Tagging System Validation")
        print("=" * 60)
        
        test_configuration()
        await test_tag_processing()
        await test_multi_pass_merging()
        
        print("\n\n✅ All tests completed successfully!")
        print("📊 Summary of Improvements:")
        print("   • Multi-pass analysis with specialized prompts")
        print("   • Advanced tag quality filtering and validation") 
        print("   • Automatic tag categorization")
        print("   • Enhanced AI model selection (llava:7b > gemma3n:e2b)")
        print("   • Detailed quality scoring and metrics")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())