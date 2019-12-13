# Ref: 4.1.2 Byte serialization of fields
def serialize_field_value(value):
  # FIXME: This does not conform to specification
  return str(value).encode('utf8')
