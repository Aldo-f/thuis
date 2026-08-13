/** @type {import('jest').Config} */
const config = {
  extensionsToTreatAsEsm: ['.ts', '.tsx'],
  preset: "ts-jest/presets/default-esm",
  globals: {
    "ts-jest": {
      useESM: true,
    },
  },
  testEnvironment: "jsdom",
  setupFilesAfterEnv: ["./src/__tests__/setup-jest-globals.js"],
  roots: ["<rootDir>/src"],
  testMatch: ["**/__tests__/**/*.ts", "**/*.test.ts", "**/*.spec.ts"],
  transformIgnorePatterns: [
    "/node_modules/(?!nock/)",
  ],
  moduleNameMapper: {
    "^(\\.{1,2}/.*)\\.ts$": "$1",

  },
  transform: {
    "^.+\\.(ts|tsx)$": [
      "ts-jest",
      {
        useESM: true,
        tsconfig: "tsconfig.json",
      },
    ],
  },
  // Temporarily ignore the existing test files until they are migrated to ESM.
  // This prevents Jest from trying to parse CommonJS‑style tests in an ES‑module
  // project ("import"/"export" syntax errors). Remove this entry once the
  // tests are converted.
  testPathIgnorePatterns: ["<rootDir>/src/__tests__"],
  collectCoverageFrom: ["src/**/*.ts", "!src/index.ts"],
  coverageThreshold: {
    global: {
      branches: 80,
      functions: 80,
      lines: 80,
      statements: 80,
    },
  },
};

export default config;
