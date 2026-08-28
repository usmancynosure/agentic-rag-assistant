# CI workflow (pending `workflow` OAuth scope)

`ci/ci.yml` is the GitHub Actions workflow for this project. It is temporarily
stored here instead of `.github/workflows/` because the push token did not yet
have the `workflow` scope.

## To activate CI

1. Grant the scope once:
   ```bash
   gh auth refresh -h github.com -s workflow
   ```
2. Move the file to its real location and push:
   ```bash
   mkdir -p .github/workflows
   git mv ci/ci.yml .github/workflows/ci.yml
   git rm ci/README.md
   git commit -m "chore: activate CI workflow"
   git push
   ```

GitHub will then run lint + type-check + tests on every push and PR.
