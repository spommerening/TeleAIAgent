"""
Text Processing Utilities
Helper functions for text processing
"""

import logging
import re
import markdown2

logger = logging.getLogger(__name__)

class TextProcessor:
    def __init__(self):
        pass
    
    def markdown_to_telegram_html(self, markdown_text):
        """Converts Markdown to Telegram HTML"""
        logger.info("Markdown to HTML conversion started")
        
        try:
            # Debug: Output original text
            # logger.debug("Original text before code block processing:")
            # logger.debug("-" * 80)
            # logger.debug(markdown_text)
            # logger.debug("-" * 80)
            
            # Markdown direkt konvertieren
            html = markdown2.markdown(markdown_text)
            
            # Debug: HTML after merging
            # logger.debug("\nHTML after code block integration:")
            # logger.debug(html)
            
            # Debug: HTML after code block restoration
            # logger.debug("\nHTML after code block restoration:")
            # logger.debug(html)
            
            # Format links correctly
            html = self._fix_links(html)
            
            # Replace unsupported tags with supported ones
            html = self._replace_unsupported_tags(html)
            
            # Debug: HTML after code block restoration
            # logger.debug("\nHTML after code block restoration:")
            # logger.debug("-" * 80)
            # logger.debug(html)
            # logger.debug("-" * 80)
            
            # Remove all remaining HTML tags not supported by Telegram
            html = self._remove_unsupported_tags(html)
            
            # Remove excessive line breaks
            html = re.sub(r'\n{3,}', '\n\n', html.strip())
            
            # logger.debug(f"Converted HTML text: {html}")
            
        except Exception as e:
            logger.error(f"Error in Markdown conversion: {e}")
            # Fallback: Return original text with basic formatting
            html = markdown_text.replace('*', '').replace('_', '')
        
        return html
    
    def _replace_unsupported_tags(self, html):
        """Replaces unsupported HTML tags"""
        # Debug: HTML before tag replacement
        # logger.debug("\nHTML before tag replacement:")
        # logger.debug(html)
        # List of HTML tags supported by Telegram:
        # <b>, <i>, <u>, <s>, <tg-spoiler>, <a>, <code>, <pre>
        replacements = [
            # Basic HTML
            ('<p>', ''),
            ('</p>', '\n'),
            ('<br>', '\n'),
            ('<hr>', '\n—————\n'),  # Replace horizontal line with dashes
            
            # Headings
            ('<h1>', '<b>'),
            ('</h1>', '</b>\n'),
            ('<h2>', '<b>'),
            ('</h2>', '</b>\n'),
            ('<h3>', '<b>'),
            ('</h3>', '</b>\n'),
            
            # Lists
            ('<ul>', '\n'),
            ('</ul>', '\n'),
            ('<ol>', '\n'),
            ('</ol>', '\n'),
            ('<li>', '• '),  # Bullet point for list elements
            ('</li>', '\n'),
            
            # Remove other unsupported tags
            ('<small>', '<i>'),
            ('</small>', '</i>'),
            ('<sub>', ''),
            ('</sub>', ''),
            ('<sup>', ''),
            ('</sup>', ''),
            ('<div>', ''),
            ('</div>', '\n'),
            ('<span>', ''),
            ('</span>', ''),
            ('<br />', ' '),
            ('<li>', '• '),
            ('</li>', ' ')
        ]
        
        for old, new in replacements:
            html = html.replace(old, new)
        
        # Replace span tags with i tags
        html = re.sub(r'<span[^>]*>', '<i>', html)
        html = html.replace('</span>', '</i>')
        
        return html
    
    def _fix_links(self, html):
        """Corrects HTML links for Telegram"""
        # Remove reference-style links at end of text
        html = re.sub(r'\[\d+\](?!\()', '', html)
        
        # Remove line breaks in links
        html = re.sub(r'<a href="([^"]+)">\s+', r'<a href="\1">', html)
        html = re.sub(r'\s+</a>', '</a>', html)
        
        # Correct links without href
        html = re.sub(r'<a>([^<]+)</a>', r'\1', html)
        
        # Ensure URLs in href are correctly formatted
        def fix_url(match):
            url = match.group(1)
            if not url.startswith(('http://', 'https://', 'tg://')):
                url = 'https://' + url
            return f'<a href="{url}">'
        
        html = re.sub(r'<a href="([^"]+)">', fix_url, html)
        
        # Remove Markdown-style reference links at end
        html = re.sub(r'\n\s*(\[\d+\]:\s*https?://[^\s]+\s*)+$', '', html)
        
        return html
    
    def _remove_unsupported_tags(self, html):
        """Removes all HTML tags not supported by Telegram and ensures tags are correctly closed"""
        # Debug: HTML before tag removal
        # logger.debug("\nHTML before tag removal:")
        # logger.debug(html)
        
        # Temporarily protect code blocks
        protected_blocks = []
        
        def protect_block(match):
            protected_blocks.append(match.group(0))
            return f"[[PROTECTED_BLOCK_{len(protected_blocks)-1}]]"
        
        # Protect pre/code blocks
        html = re.sub(r'<pre><code[^>]*>.*?</code></pre>', protect_block, html, flags=re.DOTALL)
        
        # List of tags supported by Telegram
        supported_tags = ['b', 'i', 'u', 's', 'tg-spoiler', 'a', 'code', 'pre']
        
        # Temporarily protect code blocks
        code_blocks = []
        def save_code(match):
            code_blocks.append(match.group(0))
            return f"[[PROTECTED_CODE_{len(code_blocks)-1}]]"
        
        # Protect <pre><code> blocks
        html = re.sub(r'<pre><code[^>]*>.*?</code></pre>', save_code, html, flags=re.DOTALL)
        
        # Stack for open tags
        open_tags = []
        result = []
        
        # Split text into tokens (tags and text)
        tokens = re.split(r'(<[^>]+>)', html)
        
        for token in tokens:
            if not token:
                continue
                
            if token.startswith('</'):  # Closing tag
                tag = re.match(r'</(\w+)>', token)
                if tag and tag.group(1) in supported_tags:
                    if open_tags and open_tags[-1] == tag.group(1):
                        open_tags.pop()
                        result.append(token)
            elif token.startswith('<'):  # Opening tag
                tag = re.match(r'<(\w+)[^>]*>', token)
                if tag and tag.group(1) in supported_tags:
                    open_tags.append(tag.group(1))
                    result.append(token)
            else:  # Normal text
                result.append(token)
        
        # Close all remaining open tags
        for tag in reversed(open_tags):
            result.append(f'</{tag}>')
            
        html = ''.join(result)
        
        # Restore protected blocks
        for i, block in enumerate(protected_blocks):
            html = html.replace(f"[[PROTECTED_BLOCK_{i}]]", block)
            
        # Debug: Final HTML
        # logger.debug("\nFinal HTML after tag removal:")
        # logger.debug(html)
        
        return html
