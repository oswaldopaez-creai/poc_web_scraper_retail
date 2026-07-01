## Ticket

Link to ticket.

## Description of Changes

Fixed a query error in the `okta_validator_superset` module where the `get_by_peoid` method was referencing a column that no longer exists in the `CBA_Clients` table. 

During a previous demo, a column was removed from the `CBA_Clients` table, but the code was not updated to reflect this change. This caused a SQL query error that was initially misidentified as an ODBC driver error. The error manifested in Application Insights logs (applicationinsight-creai-qa-002) showing that dashboards could not be found for certain peoIds (e.g., vns.dev).

**Root Cause:**
- A column was deleted from the `CBA_Clients` table during demo preparation
- The `get_by_peoid` method in `okta_validator_superset` still referenced this deleted column in its query
- This caused SQL query failures that appeared as ODBC driver errors

**Solution:**
- Removed the reference to the non-existent column from the query in the `get_by_peoid` method
- This change has no impact on the rest of the codebase functionality

## Type of change

Please delete options that are not relevant.

- [ ] hotfix: Urgent fix or patch that addresses a critical issue
- [x] fix: Bug fix (non-breaking change which fixes an issue)
- [ ] feat: New feature (non-breaking change which adds functionality)
- [ ] breaking: Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] chore: Routine maintenance or non-functional updates, such as dependency upgrades, tool configuration, or code cleanup. No impact on features or functionality.
- [ ] docs: This change requires a documentation update
- [ ] ci: Infrastructure change (changes to CI/CD, infrastructure as code, etc.)

## PR Checklist

- [x] Rename PR title to be meaningful and descriptive
- [x] Manually tested
- [ ] Added documentation
- [ ] Automated tests added (or explanation)
- [ ] E2E tests added (frontend only)
- [ ] IaC (Terraform) changes documented and reviewed
- [ ] API changes documented and reviewed

## Security Checklist

- [x] Security impact of change has been considered
- [x] Database migration is safe (i.e., does not drop/rename columns, change types, etc..)
- [ ] AWS resources are securely configured (IAM roles, security groups, etc.)

## Testing

**Manual Testing:**
- Reproduced the original error reported by Alberto
- Verified the error appeared in Application Insights logs (applicationinsight-creai-qa-002 - Microsoft Azure)
- Confirmed the error was related to a missing column reference in the query
- Tested the fix by removing the column reference from the `get_by_peoid` method
- Verified that the query now executes successfully without errors
- Confirmed no impact on other functionality

**Error Details:**
- Error location: `okta_validator_superset` module, `get_by_peoid` method
- Error symptom: Query failure when looking up dashboards for peoId (e.g., vns.dev)
- Error type: SQL query error (initially appeared as ODBC driver error)
- Root cause: Reference to deleted column in `CBA_Clients` table

## Screenshots (optional)
