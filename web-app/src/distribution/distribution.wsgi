import sys
import os
sys.path.insert(0, '/var/www/distribution')

def application(environ, start_response):
    from distribution import app as _application
    return _application(environ, start_response)
