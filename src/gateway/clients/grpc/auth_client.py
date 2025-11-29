import grpc
import auth_pb2
import auth_pb2_grpc
import os


AUTH_GRPC_ADDRESS = os.getenv("AUTH_GRPC_ADDRESS", "auth:50051")


class AuthGrpcClient:

    def __init__(self):
        self.channel = grpc.insecure_channel(AUTH_GRPC_ADDRESS)
        self.stub = auth_pb2_grpc.AuthServiceStub(self.channel)

    def login(self, username, password):
        request = auth_pb2.LoginRequest(
            username=username,
            password=password,
        )
        return self.stub.Login(request)

    def validate(self, token):
        request = auth_pb2.ValidateRequest(token=token)
        return self.stub.ValidateToken(request)
