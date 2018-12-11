class InconsistentVersionException(Exception):
    """Exception raised when declaring an handler version that mismatch parent versions"""

    def __init__(self, wrong_version, parent_versions):
        self.message = f"Handler version {wrong_version} is not in parent versions {parent_versions}"
