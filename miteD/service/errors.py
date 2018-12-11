class MiteDRPCError(Exception):
    def __init__(self, result):
        self.status = result['status']
        self.message = result['body']
