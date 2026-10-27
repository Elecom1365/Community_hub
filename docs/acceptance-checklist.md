# Manual acceptance checklist

## Accounts and access
- [ ] Register a volunteer account.
- [ ] Sign in and sign out.
- [ ] Confirm a volunteer receives a forbidden response for administrator-only donation and reporting pages.
- [ ] Confirm administrators can review members and update another member's role.

## Donations and fundraising
- [ ] Record a financial donation.
- [ ] Record an in-kind donation.
- [ ] Generate and open a PDF receipt.
- [ ] Create a fundraising campaign.
- [ ] Confirm donation totals appear in campaign reporting.
- [ ] Export the report as CSV.

## Volunteers and shifts
- [ ] Create a shift as an administrator.
- [ ] Book a shift as a volunteer.
- [ ] Confirm the same volunteer cannot book the same shift twice.
- [ ] Confirm a full shift cannot accept further bookings.
- [ ] Cancel a booking and confirm capacity is released.

## Tasks and resource needs
- [ ] Create a task and assign it to a volunteer.
- [ ] Update task progress as a volunteer.
- [ ] Create an urgent resource need.
- [ ] Confirm members can view resource needs.

## Quality checks
- [ ] Run `python manage.py check`.
- [ ] Run `python manage.py test`.
- [ ] Check the interface at desktop and mobile widths.
- [ ] Complete keyboard-only navigation checks.
- [ ] Run Lighthouse and axe checks.
- [ ] Run an OWASP ZAP baseline scan against a local test instance.
- [ ] Record observed results and unresolved issues in the project report.
