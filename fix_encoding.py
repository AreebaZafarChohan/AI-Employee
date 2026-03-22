#!/usr/bin/env python3
"""Fix emoji encoding in test_real_social_posting.py"""

import re

emoji_map = {
    '📂': '[FILE]',
    '✅': '[OK]',
    '🚀': '[GO]',
    '🐦': '[TW]',
    '📘': '[FB]',
    '📸': '[IG]',
    '🔧': '[MCP]',
    '📡': '[URL]',
    '📝': '[MSG]',
    '📄': '[RES]',
    '📊': '[SUM]',
    '📈': '[STAT]',
    '💾': '[SAVE]',
    '❌': '[ERR]',
    '✓': '[Y]',
}

with open('test_real_social_posting.py', 'r', encoding='utf-8') as f:
    content = f.read()

for emoji, replacement in emoji_map.items():
    content = content.replace(emoji, replacement)

with open('test_real_social_posting.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("[OK] File updated successfully!")
