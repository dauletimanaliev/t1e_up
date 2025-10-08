#!/usr/bin/env python3
"""
App entry point for T1EUP Web Application
Compatibility layer for deployment platforms
"""

from web_app import app

# Для Render и других платформ
application = app

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
