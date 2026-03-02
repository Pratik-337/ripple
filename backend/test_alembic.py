
from alembic.config import Config
from alembic import command
import traceback
sys = __import__('sys')

try:
    alembic_cfg = Config('alembic.ini')
    command.upgrade(alembic_cfg, 'head')
except Exception as e:
    with open('alembic_err4.txt', 'w') as f:
        traceback.print_exc(file=f)

