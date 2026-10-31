class ImageError(Exception):
    def __init__(self, code, message, *, uncertain=False):
        super().__init__(message)
        self.code = code
        self.uncertain = uncertain

    def as_dict(self):
        return {'code': self.code, 'message': str(self), 'uncertain': self.uncertain}
