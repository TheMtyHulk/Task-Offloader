# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# NO CHECKED-IN PROTOBUF GENCODE
# source: coordinator.proto
# Protobuf Python Version: 5.27.2
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import runtime_version as _runtime_version
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
_runtime_version.ValidateProtobufRuntimeVersion(
    _runtime_version.Domain.PUBLIC,
    5,
    27,
    2,
    '',
    'coordinator.proto'
)
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x11\x63oordinator.proto\x12\x0b\x63oordinator\"=\n\x10HeartbeatRequest\x12\x0e\n\x06\x65\x64geId\x18\x01 \x01(\t\x12\x19\n\x11\x63omputation_power\x18\x02 \x01(\x02\";\n\x0cTaskResponse\x12\x0b\n\x03\x61\x63k\x18\x01 \x01(\t\x12\x0e\n\x06taskId\x18\x02 \x01(\t\x12\x0e\n\x06\x65\x64geId\x18\x03 \x01(\t2e\n\x12\x43oordinatorService\x12O\n\x0fHeartbeatStream\x12\x1d.coordinator.HeartbeatRequest\x1a\x19.coordinator.TaskResponse(\x01\x30\x01\x62\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'coordinator_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  DESCRIPTOR._loaded_options = None
  _globals['_HEARTBEATREQUEST']._serialized_start=34
  _globals['_HEARTBEATREQUEST']._serialized_end=95
  _globals['_TASKRESPONSE']._serialized_start=97
  _globals['_TASKRESPONSE']._serialized_end=156
  _globals['_COORDINATORSERVICE']._serialized_start=158
  _globals['_COORDINATORSERVICE']._serialized_end=259
# @@protoc_insertion_point(module_scope)
