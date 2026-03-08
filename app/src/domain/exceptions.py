class FactusAPIError(Exception):
    """
    Excepción lanzada cuando Factus devuelve un error HTTP.
    Preserva el status code original para que el endpoint lo propague al cliente.
    """
    def __init__(self, message: str, status_code: int = 400):
        super().__init__(message)
        self.status_code = status_code
