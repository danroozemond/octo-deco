# Please see LICENSE.md
from flask import abort;

from . import db;
from .user import get_user_details;
from .app import cache;

from octodeco.deco import DiveProfileSer;

# All functions in this file are focused on the current user, no need
# to explicitly supply

