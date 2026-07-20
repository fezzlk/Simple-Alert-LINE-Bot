# Firestore test strategy

- Date: 2026-07-19
- Status: Accepted

## Decision

- The default local and CI test suites do not start Firestore Emulator.
- Firestore integration tests are opt-in with `RUN_FIRESTORE_INTEGRATION_TESTS=1`.
- Opt-in runs require `FIRESTORE_TEST_PROJECT_ID` and reject the production project ID.
- Unit tests use dummy or fake repositories and must not depend on Application Default Credentials.
- The deployment pipeline must stop when lint, unit tests, or dependency auditing fails.

## Context

Firestore Emulator had already been evaluated and was not selected as the default CI path. The repository later retained emulator scripts, which made it easy to mistake them for the intended architecture. Inferring whether integration tests should run from the presence of Application Default Credentials was also unsafe because Cloud Build has credentials and could access a real Firestore project.

## Change-safety rule

Before replacing test infrastructure or CI architecture, inspect the relevant Git history and existing decision records. Do not infer architectural intent from the presence of scripts alone.

## Future work

- Increase coverage through in-memory fake repositories.
- If real Firestore compatibility tests are needed, run them separately against a dedicated disposable test project with an explicit cost and cleanup policy.
