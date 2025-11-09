package com.example.fnvalidate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.networknt.schema.*;

import java.io.IOException;
import java.io.InputStream;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public class SbomValidator {

    private static final String SCHEMA_DIR = "/schemas/";
    private static final Map<String, String> SCHEMA_FILES = Map.of(
        "1.5", SCHEMA_DIR + "bom-1.5.schema.json",
        "1.6", SCHEMA_DIR + "bom-1.6.schema.json"
    );

    private final ObjectMapper objectMapper;
    private final Map<String, JsonSchema> validatorCache;

    public SbomValidator() {
        this.objectMapper = new ObjectMapper();
        this.validatorCache = new ConcurrentHashMap<>();
    }

    public ValidationResult validateBom(JsonNode bom) {
        String version = detectVersion(bom);

        if (!Set.of("1.5", "1.6").contains(version)) {
            return ValidationResult.invalid(
                version,
                List.of(new ValidationError(
                    "Unsupported or missing specVersion; expected 1.5 or 1.6, got '" + (version.isEmpty() ? "none" : version) + "'.",
                    "/specVersion",
                    null,
                    "specVersion",
                    List.of("1.5", "1.6"),
                    null
                ))
            );
        }

        try {
            JsonSchema validator = getValidator(version);
            Set<ValidationMessage> validationMessages = validator.validate(bom);

            if (validationMessages.isEmpty()) {
                return ValidationResult.valid(version);
            } else {
                List<ValidationError> errors = validationMessages.stream()
                    .map(this::formatValidationError)
                    .sorted(Comparator.comparing(ValidationError::getPath))
                    .toList();
                return ValidationResult.invalid(version, errors);
            }
        } catch (Exception e) {
            return ValidationResult.invalid(
                version,
                List.of(new ValidationError(
                    "Internal schema/validator error: " + e.getClass().getSimpleName() + ": " + e.getMessage(),
                    "/",
                    null,
                    null,
                    null,
                    null
                ))
            );
        }
    }

    private String detectVersion(JsonNode bom) {
        JsonNode specVersionNode = bom.get("specVersion");
        if (specVersionNode != null && specVersionNode.isTextual()) {
            String version = specVersionNode.asText().trim();
            if (!version.isEmpty()) {
                return version;
            }
        }

        // fallback to schema URL
        JsonNode schemaNode = bom.get("$schema");
        if (schemaNode != null && schemaNode.isTextual()) {
            String schemaUrl = schemaNode.asText();
            if (schemaUrl.contains("bom-1.5")) {
                return "1.5";
            }
            if (schemaUrl.contains("bom-1.6")) {
                return "1.6";
            }
        }

        return "";
    }

    private JsonSchema getValidator(String version) {
        return validatorCache.computeIfAbsent(version, v -> {
            try {
                return loadValidator(v);
            } catch (IOException e) {
                throw new RuntimeException(e);
            }
        });
    }

    private JsonSchema loadValidator(String version) throws IOException {
        String schemaPath = SCHEMA_FILES.get(version);
        if (schemaPath == null) {
            throw new IOException("No schema available for specVersion " + version);
        }

        try (InputStream schemaStream = getClass().getResourceAsStream(schemaPath)) {
            if (schemaStream == null) {
                throw new IOException("Schema file not found: " + schemaPath);
            }

            JsonNode schemaNode = objectMapper.readTree(schemaStream);
            JsonSchemaFactory factory = JsonSchemaFactory.getInstance(SpecVersion.VersionFlag.V7);
            return factory.getSchema(schemaNode);
        }
    }

    private ValidationError formatValidationError(ValidationMessage message) {
        String path = message.getPath() != null && !message.getPath().isEmpty()
            ? message.getPath()
            : "/";

        String schemaPath = message.getSchemaPath() != null && !message.getSchemaPath().isEmpty()
            ? message.getSchemaPath()
            : "/";

        return new ValidationError(
            message.getMessage(),
            path,
            schemaPath,
            message.getType(),
            null, // validator_value - simplified
            null // context - simplified for now
        );
    }

    public static class ValidationResult {
        private final boolean valid;
        private final String version;
        private final List<ValidationError> errors;

        private ValidationResult(boolean valid, String version, List<ValidationError> errors) {
            this.valid = valid;
            this.version = version;
            this.errors = errors != null ? errors : Collections.emptyList();
        }

        public static ValidationResult valid(String version) {
            return new ValidationResult(true, version, null);
        }

        public static ValidationResult invalid(String version, List<ValidationError> errors) {
            return new ValidationResult(false, version, errors);
        }

        public boolean isValid() {
            return valid;
        }

        public String getVersion() {
            return version;
        }

        public List<ValidationError> getErrors() {
            return errors;
        }
    }

    public static class ValidationError {
        private final String message;
        private final String path;
        private final String schemaPath;
        private final String validator;
        private final Object validatorValue;
        private final Object context;

        public ValidationError(String message, String path, String schemaPath,
                             String validator, Object validatorValue, Object context) {
            this.message = message;
            this.path = path;
            this.schemaPath = schemaPath;
            this.validator = validator;
            this.validatorValue = validatorValue;
            this.context = context;
        }

        public String getMessage() {
            return message;
        }

        public String getPath() {
            return path;
        }

        public String getSchemaPath() {
            return schemaPath;
        }

        public String getValidator() {
            return validator;
        }

        public Object getValidatorValue() {
            return validatorValue;
        }

        public Object getContext() {
            return context;
        }
    }
}
