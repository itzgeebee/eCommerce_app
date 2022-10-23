from src.helpers.auth_tokens import decode_auth_token
from src.helpers.errors import invalid_token_response


def check_valid_header(header):
    if not header:
        return False
    if not header.startswith("Bearer "):
        return False
    auth_token = header.split(" ")[1]

    return auth_token


def verify_token(req):
    auth_header = req.headers.get('Authorization')
    resp = check_valid_header(auth_header)
    decoded_token = decode_auth_token(auth_header)
    if not resp:
        return invalid_token_response()

    return decoded_token
