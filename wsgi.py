#!/usr/bin/env python3
"""
WSGI entry point for T1EUP Web Application
"""

import os
from web_app import app

if __name__ == "__main__":
    # Настройки для продакшена
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    
    app.run(
        host='0.0.0.0',
        port=port,
        debug=debug
    )
