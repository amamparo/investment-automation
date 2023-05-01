from abc import ABC, abstractmethod

from injector import Module as InjectorModule, provider

from src.env import Environment, LocalEnvironment, LambdaEnvironment


class Module(ABC, InjectorModule):
    @abstractmethod
    @provider
    def provide_environment(self) -> Environment:
        pass


class LocalModule(Module):
    def provide_environment(self) -> Environment:
        return LocalEnvironment()


class LambdaModule(Module):
    def provide_environment(self) -> Environment:
        return LambdaEnvironment()
