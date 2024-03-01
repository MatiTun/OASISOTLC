from app import dbaws as db

class APIKey(db.Model):
    __bind_key__    = 'AWS'
    __tablename__   = 'CV2_API_KEYS'
    AK_USERNAME     = db.Column(db.String(100), primary_key=True)
    AK_TOKEN        = db.Column(db.String(64))
    AK_IP           = db.Column(db.String(100))
    
    def __init__(self, username, token):
        self.AK_USERNAME    = username
        self.AK_TOKEN       = token

class User(db.Model):
    __bind_key__    = 'AWS'
    __tablename__   = 'CV2_USERS'
    ID              = db.Column(db.Integer, primary_key=True)
    USERNAME        = db.Column(db.String(100), nullable=False, index=True)
    ACTIVE          = db.Column(db.Integer, nullable=False, default=1)