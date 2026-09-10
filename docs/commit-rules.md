# Git Commit Message Rules

Use clear, concise Git commit messages that explain **what the commit does** and, when necessary, **why the change exists**.

## Format

```text
<Imperative subject> (<optional suffix>) [OPTIONAL-ISSUE-ID]

<Optional body explaining why the change was necessary>
```

Example:

```text
Fix broken 'Logout' button (hotfix) [FML-456]

The previous change introduced an invalid logout URL, preventing users
from ending their sessions from the Dashboard.
```

## Rules

1. **Start with a capitalized imperative verb**

   * `Add user authentication`
   * `Fix invoice calculation`
   * `Remove deprecated endpoint`
   * `Update Pesapal integration`
   * `Refactor user profile layout`

2. **Do not use Conventional Commit prefixes**

   * ❌ `feat: Add authentication`
   * ❌ `fix: Correct invoice calculation`
   * ✅ `Add authentication`
   * ✅ `Correct invoice calculation`

3. **Keep the subject concise**

   * Maximum **50 characters** where practical.
   * Treat it as a title, not a sentence.
   * Do not end it with a period.
   * Remove unnecessary filler words.

4. **Preserve correct product and feature casing**

   * ❌ `pesapal`
   * ✅ `Pesapal`

5. **Quote literal UI text with single quotes**

   * `Add 'Forgot Password' link to Login page`
   * `Fix 'Save Changes' button state`

6. **Use optional suffixes for special changes**

   * Normal brackets: `(hotfix)`, `(chore)`, `(docs)`, etc.
   * Put the suffix after the subject.

7. **Append the Linear issue ID when available**

   * Use square brackets.
   * Use uppercase, hyphenated IDs.
   * `Add password reset flow [TF-245]`
   * Do not invent an issue ID when none exists.

8. **Add a body only when useful**

   * Separate it from the subject with a blank line.
   * Explain **why** the change was necessary, not implementation details
     already visible in the diff.
   * Wrap body lines at approximately **72 characters**.

## Quick Check

Before committing, the subject should complete:

> If this commit is applied, it will **[commit subject]**.

For example:

> If this commit is applied, it will **Add password reset flow**.

If that sentence does not make sense, rewrite the subject.

## Preferred Examples

```text
Add password reset flow [TF-245]
```

```text
Fix invoice calculation error (hotfix) [TF-312]
```

```text
Update Pesapal payment endpoint
```

```text
Add 'Forgot Password' link to Login page
```

```text
Remove deprecated authentication endpoint
```

When generating commit messages from code changes, inspect the actual diff
and describe the primary purpose of the change. Do not guess functionality,
issue IDs, or reasons that cannot be established from the changes or provided
context.
