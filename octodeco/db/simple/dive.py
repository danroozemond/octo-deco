import base64;
from typing import Optional
from pydantic import BaseModel


# Probably when I grow up I want to use SQLAlchemy
class DBDive(BaseModel):
    dive_id: Optional[str] = None
    user_id: Optional[int] = None
    dive_desc: Optional[str] = None
    is_public: bool
    is_demo: Optional[bool] = None
    is_ephemeral: Optional[bool] = None
    dive_serialized: Optional[str] = None
    object_version: Optional[int] = 0

    @staticmethod
    def from_row(row):
        if row is None:
            return None;
        d = { k : row[k] for k in row.keys() };
        r = DBDive(**d);
        if 'dive' in row.keys():
            r.dive_serialized = base64.b64encode(row['dive']).decode('utf-8');
        return r;