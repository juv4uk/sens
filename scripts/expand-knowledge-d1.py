#!/usr/bin/env python3
import base64, gzip
from pathlib import Path
B64 = open(__file__).read().split('B64 = """')[1].split('"""')[0] if False else None
# embedded below
exec("""
B64 = open('/dev/null')
""")
