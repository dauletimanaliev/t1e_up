#!/usr/bin/env python3
"""
App entry point for T1EUP Web Application
Compatibility layer for Render deployment
"""

from test_app import application

# Для Render
app = application

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
