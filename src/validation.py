"""Validation functions for the configuration file."""

import json
import typing as t
import jsonschema
from functools import lru_cache


@lru_cache()
def LoadConfigSchema() -> dict:
    """Loads the JSON schema for configuration validation.
    Caches the schema to avoid reloading it on each call.
    """

    # avoids circular import
    from src.config import SCHEMA_FILE

    try:
        with open(SCHEMA_FILE, "r") as f:
            return json.load(f)
        
    # distinguishes between file not found and invalid JSON
    except FileNotFoundError:
        raise ValueError(f"Schema file not found: {SCHEMA_FILE}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in schema file: {e}")


def GetObjectErrorsFromSchema(obj: dict[str, t.Any], schema: dict) -> list[str]:
    """Detects errors in a dictionary (JSON object) against a schema."""
    
    # builds validator and validates object against schema
    validator = jsonschema.Draft7Validator(schema)

    # formats errors into user-friendly messages
    return [FormatValidationError(e) for e in list(validator.iter_errors(obj))]


def GetConfigErrors(config: dict) -> list[str]:
    """Validate configuration using JSON schema file, returning a list of errors.
    Returns empty list if no errors are found.
    """

    # processes one schema = LoadConfigSchema()
    schema = LoadConfigSchema()
    errors = GetObjectErrorsFromSchema(config, schema)

    # additional semantic validations
    for domain, entry in config.items():
        errors.extend(GetWebsiteErrors(domain, entry))

    return errors


def GetWebsiteErrors(domain: str, entry: dict) -> list[str]:
    """Additional semantic validations beyond JSON Schema."""
    
    url = entry.get("url", "")
    if url == "" or not isinstance(url, str): return []

    # checks if URL contains {manuCode} or *
    if url and isinstance(url, str) and "*" not in url and "{manuCode}" not in url:
        return [
            f"❌ Error in 'url' of website '{domain}':\n"
            f"   URL must contain placeholder '{{manuCode}}' or wildcard(s) '*'\n"
            f"   Current value: '{url}'\n"
            f"   Correct example: 'https://example.com/part-{{manuCode}}'"
        ]
    return []


def FormatJsonPath(path: t.Sequence[str | int]) -> str:
    """Format a JSON path for error messages, adding [ ] around keys containing dots.
    For example, ["mouser.com", "files", "datasheet"] becomes "[mouser.com].files.datasheet".
    """
    return ".".join(
        # adds [ ] around keys containing dots, or list item indexes
        f"[{part}]" if (isinstance(part, str) and "." in part or isinstance(part, int))
        else str(part)
        for part in path if part != ""
    )


def FormatValidationError(error: jsonschema.ValidationError, domain: str = "") -> str:
    """Format a JSON Schema validation error into a user-friendly message."""
    
    # builds the path to the error
    errorPath = FormatJsonPath(error.absolute_path)
    
    # formats the error message based on error type

    # missing required field
    if error.validator == "required":
        missingField = error.message.split("'")[1] if "'" in error.message else "unknown"
        return (f"❌ Error in '{errorPath}':\n"
               f"   Missing required field '{missingField}'")
    
    # at least one of the following is required
    elif error.validator == "oneOf":
        return (f"❌ Error in '{errorPath}':\n"
               f"   Invalid value for this field\n"
               f"   Check the configuration")
    
    # invalid value for this field
    elif error.validator == "type":

        # gets expected type from schema
        expectedType = "unknown"
        if hasattr(error, 'schema') and isinstance(error.schema, dict):
            expectedType = error.schema.get("type", "unknown")

        # gets actual value from error
        actualValue = error.instance
        return (f"❌ Error in '{errorPath}':\n"
               f"   Current value: {json.dumps(actualValue)} of type {type(actualValue).__name__}\n"
               f"   Expected type: {expectedType}")
    
    # empty value not allowed
    elif error.validator == "minLength":
        return (f"❌ Error in '{errorPath}':\n"
               f"   Empty value not allowed\n"
               f"   Please provide a valid value")
    
    # unknown key
    elif error.validator == "additionalProperties":
        return (f"❌ Error in '{errorPath}':\n"
               f"   Unknown key: {error.message}\n"
               f"   Remove the key or check documentation")
    
    else:
        # generic error message
        return f"❌ Error in '{errorPath}': {error.message}"
