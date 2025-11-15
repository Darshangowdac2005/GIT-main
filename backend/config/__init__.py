# backend/config/__init__.py
# This file marks the directory as a Python package.

# The db_connector is the only essential module to expose
from .db_connector import db, create_tables_and_seed