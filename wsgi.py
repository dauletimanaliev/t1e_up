#!/usr/bin/env python3
"""
WSGI entry point for T1EUP Web Application
"""

from simple_app import application

if __name__ == "__main__":
    import os
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    application.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
