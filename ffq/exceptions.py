"""Custom exception types used to raise specific errors"""


class FfqException(Exception):
    """Base FFQ Exception class to allow generic catches"""
    pass


class CliError(FfqException):
    """Raised when the CLI is called with invalid arguments"""
    pass


class InvalidAccession(FfqException):
    """Raised when an accession appears to be invalid"""
    pass


class ConnectionError(FfqException):
    """Raised for any errors when fetching data"""
    pass


class BadData(FfqException):
    """Raised when returned data does not look as expected"""
    pass
