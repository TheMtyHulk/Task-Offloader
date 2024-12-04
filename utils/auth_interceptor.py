import grpc
import logging
import jwt
from dotenv import load_dotenv
import os

load_dotenv()
base_dir = os.path.dirname(os.path.abspath(__file__))

class JWTAuthInterceptor(grpc.ServerInterceptor):
    def __init__(self, secret_key):
        self.secret_key = secret_key

    def intercept_service(self, continuation, handler_call_details):
        metadata = dict(handler_call_details.invocation_metadata)
        token = metadata.get('authorization')
        if not token:
            context = handler_call_details.invocation_metadata
            context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Authorization token is missing')
        try:
            jwt.decode(token, self.secret_key, algorithms=['HS256'])
            # print(f"Authentication successful for token: {token}")
            logging.info(f"Authentication successful for token: {token}")
        except jwt.ExpiredSignatureError:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Token has expired')
            logging.info(f"Token has expired for token: {token}")
        except jwt.InvalidTokenError:
            context.abort(grpc.StatusCode.UNAUTHENTICATED, 'Invalid token')
            logging.info(f"Ivalid token: {token}")
        return continuation(handler_call_details)