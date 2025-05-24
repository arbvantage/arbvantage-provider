"""
This __init__.py file re-exports the generated gRPC classes for the Hub service.

Why is this important?
-----------------------------------
By importing hub_pb2 and hub_pb2_grpc here, you make it easy for other modules in the package
(or users of the package) to import the gRPC classes from a single location. This improves
code organization and discoverability.
"""

# Import all symbols from the generated hub_pb2 module.
# hub_pb2 contains the Python classes generated from your .proto file (messages, enums, etc.).
# These classes are used to serialize/deserialize data for gRPC communication.
from .hub_pb2 import *

# Import all symbols from the generated hub_pb2_grpc module.
# hub_pb2_grpc contains the gRPC service stubs and servicers generated from your .proto file.
# These are used to implement and call gRPC services in Python.
from .hub_pb2_grpc import *

# __all__ defines the public API of this module.
# By listing 'hub_pb2' and 'hub_pb2_grpc' here, you make it clear that these are the intended
# exports for users who do 'from arbvantage_provider.protos import *' or similar imports.
# This helps with code completion, documentation, and prevents accidental import of private symbols.
__all__ = ['hub_pb2', 'hub_pb2_grpc']
