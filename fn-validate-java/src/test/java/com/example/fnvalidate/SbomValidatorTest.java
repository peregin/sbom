package com.example.fnvalidate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.BeforeEach;
import org.junit.jupiter.api.Test;

import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class SbomValidatorTest {

    private SbomValidator validator;
    private ObjectMapper objectMapper;

    @BeforeEach
    void setUp() {
        validator = new SbomValidator();
        objectMapper = new ObjectMapper();
    }

    @Test
    void testInvalidWithoutSpecVersion() throws Exception {
        String bomJson = "{\n" +
            "    \"bomFormat\": \"CycloneDX\",\n" +
            "    \"version\": 1\n" +
            "}";
        JsonNode bom = objectMapper.readTree(bomJson);

        SbomValidator.ValidationResult result = validator.validateBom(bom);

        assertFalse(result.isValid());
        assertEquals("", result.getVersion());
        assertFalse(result.getErrors().isEmpty());
        assertTrue(result.getErrors().get(0).getMessage().contains("Unsupported") ||
                  result.getErrors().get(0).getMessage().contains("specVersion"));
    }

    @Test
    void testValidMinimal15() throws Exception {
        String bomJson = "{\n" +
            "    \"bomFormat\": \"CycloneDX\",\n" +
            "    \"specVersion\": \"1.5\",\n" +
            "    \"version\": 1,\n" +
            "    \"metadata\": {\n" +
            "        \"timestamp\": \"2024-01-01T00:00:00Z\",\n" +
            "        \"tools\": [{\"name\": \"unit-test-tool\"}]\n" +
            "    }\n" +
            "}";
        JsonNode bom = objectMapper.readTree(bomJson);

        SbomValidator.ValidationResult result = validator.validateBom(bom);

        assertTrue(result.isValid(), "Expected valid BOM, got errors: " + result.getErrors());
        assertEquals("1.5", result.getVersion());
    }

    @Test
    void testValidMinimal16() throws Exception {
        String bomJson = "{\n" +
            "    \"bomFormat\": \"CycloneDX\",\n" +
            "    \"specVersion\": \"1.6\",\n" +
            "    \"version\": 1,\n" +
            "    \"metadata\": {\n" +
            "        \"timestamp\": \"2024-01-01T00:00:00Z\",\n" +
            "        \"tools\": [{\"name\": \"unit-test-tool\"}]\n" +
            "    }\n" +
            "}";
        JsonNode bom = objectMapper.readTree(bomJson);

        SbomValidator.ValidationResult result = validator.validateBom(bom);

        assertTrue(result.isValid(), "Expected valid BOM, got errors: " + result.getErrors());
        assertEquals("1.6", result.getVersion());
        assertEquals(0, result.getErrors().size(), "No validation errors expected, but got: " + result.getErrors());
    }

    @Test
    void testRejectsUnsupportedVersion() throws Exception {
        String bomJson = "{\n" +
            "    \"bomFormat\": \"CycloneDX\",\n" +
            "    \"specVersion\": \"1.7\",\n" +
            "    \"version\": 1\n" +
            "}";
        JsonNode bom = objectMapper.readTree(bomJson);

        SbomValidator.ValidationResult result = validator.validateBom(bom);

        assertFalse(result.isValid());
        assertEquals("1.7", result.getVersion());
        assertFalse(result.getErrors().isEmpty());
        assertTrue(result.getErrors().get(0).getMessage().contains("Unsupported"));
    }
}
