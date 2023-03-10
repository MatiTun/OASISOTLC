import sys
sys.stdout = sys.stderr
sys.path.insert(0,"/var/www/OASISOTLC")

from run import app as application