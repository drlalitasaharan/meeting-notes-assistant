# MeetIQ Pilot Support Triage and Admin Checklist

## Purpose

This checklist helps manage controlled pilot feedback without building a full admin dashboard yet.

Use this during early MeetIQ pilot testing to track:

- Upload issues
- Processing failures
- Stuck meetings
- Notes quality feedback
- Usage limit or pilot access requests
- Confusing user experience
- Follow-up product improvements

## Pilot Support Intake

When a pilot user reports an issue, collect:

- Account email
- Meeting title
- Meeting ID, if available
- Approximate recording length
- File type
- Upload date/time
- Issue type
- What happened
- What the user expected
- Screenshot or error message, if available
- Whether the issue blocks pilot use

## Issue Types

### Upload issue

Examples:

- File did not upload
- Upload appears stuck
- Unsupported file type
- File too large
- User does not understand upload requirements

### Processing issue

Examples:

- Processing gets stuck
- Meeting never completes
- Result page does not appear
- Worker or backend issue suspected

### Notes quality issue

Examples:

- Summary is too shallow
- Key points are missing
- Decisions are missing or wrong
- Risks are missing or weak
- Action items are incomplete
- Owners or names are incorrect

### Usage or access issue

Examples:

- User reaches upload limit
- User needs more pilot capacity
- User cannot access account
- User is confused by trial or pilot allowance

### UX confusion

Examples:

- User does not know where to upload
- User does not know where to find completed meetings
- User does not know how to copy, edit, download, or share notes
- User does not know where to send feedback

## Severity Levels

### Low

The user can continue testing.

Examples:

- Minor notes quality issue
- Small wording confusion
- Non-blocking UX feedback

Action:

- Log feedback
- Review during weekly pilot review

### Medium

The user can continue, but the issue affects confidence.

Examples:

- Important action item missed
- Decision extraction partially wrong
- User confused by flow
- Upload succeeds but result is less useful than expected

Action:

- Log feedback
- Reproduce if possible
- Decide whether this becomes a near-term improvement

### High

The user is blocked from completing pilot testing.

Examples:

- Upload fails
- Processing never completes
- Meeting result cannot be opened
- User cannot sign in
- Notes output is unusable for a normal structured meeting

Action:

- Investigate immediately
- Check hosted backend, worker, Redis, database, and storage health
- Record the issue and resolution
- Consider a code fix before inviting more users

## Daily Pilot Admin Check

During active pilot testing, check:

- New support emails
- Upload failures reported by users
- Meetings stuck in processing
- Notes quality complaints
- Usage limit requests
- Whether users can complete upload to notes flow
- Whether feedback points to a repeated issue

## Weekly Pilot Review

Once per week during pilot, summarize:

- Number of pilot users invited
- Number of meetings uploaded
- Number of successful meeting outputs
- Number of failed or stuck uploads
- Most common notes quality feedback
- Most common UX confusion
- Top 3 product improvements
- Whether pilot should continue, pause, or expand

## Pilot Success Criteria

A controlled pilot is successful if:

- Users can upload and process short structured meetings
- Generated notes are useful enough to review, edit, copy, or share
- Users understand where to find results
- Users understand how to send feedback
- Critical upload or processing failures are rare and traceable
- Repeated notes quality issues are documented for product improvement

## When to Create a Code Task

Create a code task when:

- The same issue happens for multiple users
- A user is blocked from completing upload to notes flow
- A security, privacy, or data retention concern appears
- Usage limits behave incorrectly for public launch expectations
- The product output misses a repeated class of important information

## What Not to Store in the Repository

Do not commit:

- Private recordings
- Full private transcripts
- User personal data
- Sensitive client names
- Medical, legal, HR, or financial meeting details
- Screenshots containing private user information

Store only sanitized summaries and product-level learnings in the repository.

## Current Pilot Decision

For controlled pilot testing, manual support/admin tracking is acceptable.

Before public self-serve launch, MeetIQ should have stronger admin visibility for:

- Upload count
- Processing status
- Errors
- User usage
- Failed jobs
- Support follow-up
