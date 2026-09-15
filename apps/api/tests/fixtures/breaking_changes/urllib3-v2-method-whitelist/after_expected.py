from urllib3.util import Retry

def get_retry_policy():
    return Retry(total=3, allowed_methods=["GET", "POST"])
