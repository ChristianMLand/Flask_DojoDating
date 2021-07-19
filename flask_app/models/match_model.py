from flask_app.config.orm2 import Model,table
from flask_app import MESSAGE_COUNT

@table('matches')
class Match(Model):
    def __init__(self, **data):
#----------------attributes--------------------#
        self.id = data.get('id')
        self._matcher_id = data.get('matcher_id')
        self._matched_id = data.get('matched_id')
        self.created_at = data.get('created_at')
        self.updated_at = data.get('updated_at')
#---------------relationships-------------------#
        self.matcher = User.retrieve(id=self._matcher_id)
        self.matched = User.retrieve(id=self._matched_id)
        self.messages = DirectMessage.retrieve(match_id=self.id).order_by(desc=True).limit(MESSAGE_COUNT)
#-----------------------------------------------#
from .user_model import User
from .direct_message_model import DirectMessage