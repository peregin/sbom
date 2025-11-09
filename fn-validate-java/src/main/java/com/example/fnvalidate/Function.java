package com.example.fnvalidate;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.HashMap;
import java.util.Map;
import java.util.Scanner;

public class Function {

    private final ObjectMapper objectMapper;
    private final SbomValidator validator;

    public Function() {
        this.objectMapper = new ObjectMapper();
        this.validator = new SbomValidator();
    }

    public String handleRequest(String inputJson) throws IOException {
        try {
            if (inputJson == null || inputJson.trim().isEmpty()) {
                return createErrorResponse(400, "Empty request body");
            }

            JsonNode requestBody = objectMapper.readTree(inputJson);

            JsonNode bom;
            if (requestBody.has("sbom")) {
                bom = requestBody.get("sbom");
            } else {
                bom = requestBody;
            }

            if (!bom.isObject()) {
                return createErrorResponse(400, "Expected SBOM JSON object");
            }

            // Validate the BOM
            SbomValidator.ValidationResult result = validator.validateBom(bom);

            // Prepare response
            Map<String, Object> response = new HashMap<>();
            if (result.isValid()) {
                response.put("valid", true);
                response.put("specVersion", result.getVersion());
            } else {
                response.put("valid", false);
                response.put("specVersion", result.getVersion() != null ? result.getVersion() : null);
                response.put("errors", result.getErrors().subList(0, Math.min(result.getErrors().size(), 50)));
            }

            // Return response as JSON string
            return objectMapper.writeValueAsString(response);

        } catch (IOException e) {
            return createErrorResponse(400, "Invalid JSON: " + e.getMessage());
        } catch (Exception e) {
            return createErrorResponse(500, "Internal error: " + e.getMessage());
        }
    }

    private String createErrorResponse(int statusCode, String errorMessage) throws IOException {
        Map<String, Object> errorResponse = new HashMap<>();
        errorResponse.put("error", errorMessage);
        errorResponse.put("statusCode", statusCode);
        return objectMapper.writeValueAsString(errorResponse);
    }

    // Main method for testing
    public static void main(String[] args) throws IOException {
        Function function = new Function();
        Scanner scanner = new Scanner(System.in);
        System.out.println("Enter SBOM JSON to validate (or 'quit' to exit):");

        while (true) {
            System.out.print("> ");
            String input = scanner.nextLine();
            if ("quit".equalsIgnoreCase(input.trim())) {
                break;
            }

            String result = function.handleRequest(input);
            System.out.println("Response: " + result);
        }
    }
}
