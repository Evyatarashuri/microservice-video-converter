import grpc
import os
from gateway import auth_pb2, auth_pb2_grpc


class AuthGrpcClient:
    def __init__(self):
        address = os.getenv("AUTH_GRPC_ADDRESS", "auth:50051")
        self.channel = grpc.insecure_channel(address)
        self.stub = auth_pb2_grpc.AuthServiceStub(self.channel)

    def login(self, username, password):
        request = auth_pb2.LoginRequest(username=username, password=password)
        return self.stub.Login(request)

    def validate(self, token):
        request = auth_pb2.ValidateRequest(token=token)
        return self.stub.ValidateToken(request)
