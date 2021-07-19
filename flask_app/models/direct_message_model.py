from flask_app.config.orm2 import Model,table

@table('direct_messages')
class DirectMessage(Model):
    def __init__(self, **data):
#----------------attributes--------------------#
        self.id = data.get('id')
        self._sender_id = data.get('sender_id')
        self._match_id = data.get('match_id')
        self.is_deleted = data.get('is_deleted')
        self.content = data.get('content')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
#---------------relationships-------------------#
        self.sender = User.retrieve(id=self._sender_id)
        self.match = Match.retrieve(id=self._match_id)
#-----------------------------------------------#
from .user_model import User
from .match_model import Match