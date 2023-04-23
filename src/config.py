from injector import Module, provider

from src.env import Environment, LocalEnvironment, AwsEnvironment


class LocalModule(Module):
    @provider
    def provide_environment(self) -> Environment:
        return LocalEnvironment()


class AwsModule(Module):
    @provider
    def provide_environment(self) -> Environment:
        return AwsEnvironment()
