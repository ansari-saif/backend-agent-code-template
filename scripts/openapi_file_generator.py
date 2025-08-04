import json

def generate_openapi_file(modules, openapi_file_path):
    """
    Generate an OpenAPI file based on the provided modules.
    
    Args:
        modules (list): Input Content
        openapi_file_path (str): output path : The path to the output OpenAPI file.
    """
    # Load the existing OpenAPI spec file if it exists; otherwise, initialize a new one
    try:
        with open(openapi_file_path, "r") as file:
            openapi_structure = json.load(file)
    except FileNotFoundError:
        # Initialize the base OpenAPI structure if the file does not exist
        openapi_structure = {
            "openapi": "3.1.0",
            "info": {
                "title": "Cogent Ai",
                "version": "0.1.0"
            },
            "servers": [
                {
                    "url": "http://localhost:8000",
                    "description": "Local development server"
                }
            ],
            "paths": {},
            "components": {
                "schemas": {}
            }
        }

    # Function to update paths and schemas for a given module
    def add_module_to_openapi(module, openapi_structure):
        module_name = module["module"]
        base_path = f"/api/v1/{module_name}/"
        item_path = f"/api/v1/{module_name}/{{{module_name}_id}}"

        # Add paths for GET and POST
        if base_path not in openapi_structure["paths"]:
            openapi_structure["paths"][base_path] = {
                "get": {
                    "tags": [module_name],
                    "summary": f"List All {module_name.capitalize()}",
                    "operationId": f"list_all_{module_name}_api_v1_{module_name}__get",
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "items": {
                                            "$ref": f"#/components/schemas/{module_name.capitalize()}Read"
                                        },
                                        "type": "array",
                                        "title": f"Response List All {module_name.capitalize()} Api V1 {module_name} Get"
                                    }
                                }
                            }
                        }
                    }
                },
                "post": {
                    "tags": [module_name],
                    "summary": f"Create {module_name.capitalize()}",
                    "operationId": f"create_{module_name}_api_v1_{module_name}__post",
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": f"#/components/schemas/{module_name.capitalize()}Create"
                                }
                            }
                        },
                        "required": True
                    },
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": f"#/components/schemas/{module_name.capitalize()}Read"
                                    }
                                }
                            }
                        }
                    }
                }
            }

        # Add paths for GET, PUT, and DELETE for an individual item
        if item_path not in openapi_structure["paths"]:
            openapi_structure["paths"][item_path] = {
                "get": {
                    "tags": [module_name],
                    "summary": f"Get a single {module_name.capitalize()}",
                    "operationId": f"get_{module_name}_api_v1_{module_name}_id__get",
                    "parameters": [
                        {
                            "name": f"{module_name}_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "integer",
                                "title": f"{module_name.capitalize()} Id"
                            }
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": f"#/components/schemas/{module_name.capitalize()}Read"
                                    }
                                }
                            }
                        }
                    }
                },
                "put": {
                    "tags": [module_name],
                    "summary": f"Update a {module_name.capitalize()}",
                    "operationId": f"update_{module_name}_api_v1_{module_name}_id__put",
                    "parameters": [
                        {
                            "name": f"{module_name}_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "integer",
                                "title": f"{module_name.capitalize()} Id"
                            }
                        }
                    ],
                    "requestBody": {
                        "content": {
                            "application/json": {
                                "schema": {
                                    "$ref": f"#/components/schemas/{module_name.capitalize()}Update"
                                }
                            }
                        },
                        "required": True
                    },
                    "responses": {
                        "200": {
                            "description": "Successful Response",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": f"#/components/schemas/{module_name.capitalize()}Read"
                                    }
                                }
                            }
                        }
                    }
                },
                "delete": {
                    "tags": [module_name],
                    "summary": f"Delete a {module_name.capitalize()}",
                    "operationId": f"delete_{module_name}_api_v1_{module_name}_id__delete",
                    "parameters": [
                        {
                            "name": f"{module_name}_id",
                            "in": "path",
                            "required": True,
                            "schema": {
                                "type": "integer",
                                "title": f"{module_name.capitalize()} Id"
                            }
                        }
                    ],
                    "responses": {
                        "204": {
                            "description": "No Content"
                        }
                    }
                }
            }

        # Initialize schemas for Create, Read, and Update
        create_schema = {
            "properties": {},
            "type": "object",
            "required": [],
            "title": f"{module_name.capitalize()}Create"
        }
        read_schema = {
            "properties": {
                "id": {
                    "type": "integer",
                    "title": "Id"
                }
            },
            "type": "object",
            "required": ["id"],
            "title": f"{module_name.capitalize()}Read"
        }
        update_schema = {
            "properties": {},
            "type": "object",
            "title": f"{module_name.capitalize()}Update"
        }

        # Add fields to the schemas
        for field in module["fields"]:
            field_name = field["name"]
            field_type = field["type"]

            # Update Create schema
            create_schema["properties"][field_name] = {
                "type": field_type,
                "title": field_name.capitalize()
            }
            create_schema["required"].append(field_name)

            # Update Read schema
            read_schema["properties"][field_name] = {
                "type": field_type,
                "title": field_name.capitalize()
            }
            read_schema["required"].append(field_name)

            # Update Update schema (optional fields)
            update_schema["properties"][field_name] = {
                "type": field_type,
                "title": field_name.capitalize()
            }

        # Add schemas to components if not already present
        schemas = openapi_structure["components"]["schemas"]
        schemas[f"{module_name.capitalize()}Create"] = create_schema
        schemas[f"{module_name.capitalize()}Read"] = read_schema
        schemas[f"{module_name.capitalize()}Update"] = update_schema

    # Add each module to the OpenAPI structure
    for module in modules:
        add_module_to_openapi(module, openapi_structure)

    # Write the updated OpenAPI structure back to the file
    with open(openapi_file_path, "w") as file:
        json.dump(openapi_structure, file, indent=2)

    print(f"Updated OpenAPI spec saved to {openapi_file_path}")
