class APIException(Exception):
    def __init__(self, response, status_code):
        self.response = response
        self.status_code = status_code
        