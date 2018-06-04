import logging
from os import getenv
import json
import datetime
import yaml
import uuid

from schematics.models import Model
from schematics.types import (StringType, DateTimeType, IntType, BooleanType,
                              ListType, FloatType, ModelType, DictType)


logging.basicConfig(level=logging.getLevelName(getenv("LOG_LEVEL", "INFO")))


class UUIDType(StringType):
    def __init__(self, *args, **kwargs):
        self.regex = r"^[a-zA-Z0-9]{8}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{4}-[a-zA-Z0-9]{12}$"
        self.required = True
        self._mock = str(uuid.uuid4())
        self.max_length = self.min_length = 36
        super().__init__(required=self.required,
                         min_length=self.min_length,
                         max_length=self.max_length,
                         regex=self.regex)


class StringType(StringType):
    def __init__(self, **kwargs):
        try:
            self.example = kwargs.pop("example")
        except KeyError:
            raise TypeError("Example is a required parameter.")
        super().__init__(**kwargs)


class IntType(IntType):
    def __init__(self, *arg, **kwargs):
        try:
            self.example = kwargs.pop("example")
        except KeyError:
            raise TypeError("Example is a required parameter.")
        super().__init__(**kwargs)


class FloatType(FloatType):
    def __init__(self, *arg, **kwargs):
        try:
            self.example = kwargs.pop("example")
        except KeyError:
            raise TypeError("Example is a required parameter.")
        super().__init__(**kwargs)


class Model(Model):
    def document_model(self, render_to_yaml=False):
        model_name = str(self).split(" ")[0][1:]
        model_doc_json = {model_name:
                              {"type": "object",
                               "required": [],
                               "properties": {}
                               }
                          }

        for name, field in self.fields.items():
            if field.required:
                model_doc_json[model_name]["required"].append(name)
            model_doc_json[model_name]["properties"][name] = Model.document_field(field)

        if render_to_yaml:
            return yaml.dump(model_doc_json, default_flow_style=False)

        return model_doc_json

    @staticmethod
    def document_field(field):
        if type(field) is UUIDType:
            return {"type": "string", "format": "UUID", "example": field._mock()}

        elif type(field) is StringType:
            field_doc = {"type": "string", "example": field.example}
            if field.max_length:
                field_doc["maximum"] = field.max_length
            if field.min_length is not None:
                field_doc["minumum"] = field.min_length
            return field_doc

        elif type(field) is IntType:
            field_doc = {"type": "integer", "format": "int32"}
            if field.min_value is not None:
                field_doc["minimium"] = field.min_value
            if field.max_value is not None:
                field_doc["maximum"] = field.max_value
            return field_doc

        elif type(field) is FloatType:
            field_doc = {"type": "number", "format": "float"}
            if field.min_value is not None:
                field_doc["minimium"] = field.min_value
            if field.max_value is not None:
                field_doc["maximum"] = field.max_value
            return field_doc

        elif type(field) is BooleanType:
            return {"type": "boolean"}

        elif type(field) is DateTimeType:
            return {"type": "string", "format": "date-time", "example": datetime.datetime.now().isoformat()}

        elif type(field) is ModelType:
            field_doc = {}
            for name, sub_field in field.model_class().fields.items():
                field_doc[name] = Model.document_field(sub_field)
            return field_doc

        elif type(field) is ListType:
            field_doc = {"type": "array"}
            if field.min_size is not None:
                field_doc["minimum"] = field.min_size
            if field.max_size is not None:
                field_doc["maximum"] = field.max_size
            field_doc["items"] = Model.document_field(field.field)
            return field_doc

        elif type(field) is DictType:
            field_doc = {"type": "object", "additionalProperties": "true"}
            return field_doc

        else:
            return {"ERROR": f"Unable to generate documentation for {field.name}"}


class EvalModel(Model):
    etype = StringType(required=True, choices=("initial", "postconditioning", "final"), example="initial")
    record_tstamp = DateTimeType(required=False)
    method_of_record_creation = StringType(example="Unicorn")
    conductivity_Sm = FloatType(min_value=0, required=True, example=3.45)
    notes = StringType(required=False, max_length=255, example="DOlor vsdvsfv")


e = EvalModel()
print(e.document_model(render_to_yaml=True))