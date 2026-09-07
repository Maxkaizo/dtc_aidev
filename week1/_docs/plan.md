# Product Definition: Shared Household Chores

## Goal

Help a couple organize household chores through a shared board where each person can choose a chore, reserve it, and mark it as completed.

## Users

A couple sharing a home. The MVP supports one household with two profiles.

## Initial MVP Scope

- Create one-off and recurring chores.
- Require a due date for every chore.
- Allow either partner to claim an available chore.
- Reserve a claimed chore for its owner until they complete or release it.
- Mark chores as completed.
- Show status, owner, and due date on the board, highlighting overdue chores.

## Agreed Rules

- Partners choose chores freely; there is no fixed assignment or automatic rotation.
- Claiming a chore reserves it; it does not complete it.
- The status flow is **Available → Claimed → Done**.
- Every chore must have a due date.
- Recurring chores follow a fixed schedule, regardless of when they are completed.
- An overdue chore keeps its owner. Being overdue is an additional condition, not a workflow status.

## Implemented Design Decisions

These decisions complement the agreed rules and are included in the initial implementation:

| Decision | Rationale |
| --- | --- |
| Allow the owner to release a chore, returning it to Available. | Lets the other partner claim it when plans change. |
| Represent each recurring occurrence as a separate chore. | Preserves unfinished chores without shifting the schedule or losing pending work. |
| Limit the product to one household with two profiles. | Keeps the homework focused on a couple. |
| Show owner, due date, and overdue status on the board. | Makes it easy to see who is doing what and what needs attention. |

## Main Flow

1. A partner creates a chore with a title, due date, and optional recurrence.
2. The chore appears as Available on the shared board.
3. Either partner claims it; its status becomes Claimed and its owner is displayed.
4. The owner completes the chore or releases it so it becomes available again.
5. If the chore becomes overdue before completion, it is highlighted and keeps its owner, if assigned.
6. For recurring chores, the next occurrence follows the fixed schedule even if the previous occurrence remains unfinished.

## Out of Scope

- Notifications and reminders.
- Points, rewards, and gamification.
- Fairness or workload distribution reports.
- Calendar integrations.
- Automatic assignment and chore rotation.
- Multiple households or groups of more than two people.

## Acceptance Criteria

- Users can create one-off and recurring chores; neither can be saved without a due date.
- Both profiles see the same board and can claim available chores.
- A claimed chore has exactly one owner and cannot be claimed simultaneously by both profiles.
- Completing a chore changes its status to Done.
- Releasing a chore removes its owner and returns it to Available.
- Becoming overdue does not release a chore or change its owner.
- Completing a recurring chore late does not alter the due dates of subsequent occurrences.
- A new occurrence does not replace or delete an unfinished previous occurrence.

## Implementation Status

The initial MVP is implemented with Python 3.12, Django 5.2, Django templates and authentication, SQLite, uv, and Docker Compose. Exact dependency versions are recorded in [uv.lock](../uv.lock).

- Daily, weekly, and monthly recurrences are supported. Opening the board generates missing occurrences through today plus the next future occurrence; no background scheduler runs.
- Monthly schedules use the last valid day in shorter months and return to the original day afterward.
- Due dates are calendar dates in the configured household timezone; chores become overdue the following day.
- Editing/deleting chores and cancelling recurrence are not implemented and were not included in the initial scope.
- The 16 automated tests passed locally and in Docker during initial validation. Claim exclusivity is tested with sequential competing requests; truly simultaneous requests are not yet covered by a test.

See [README.md](../README.md) for setup and usage, and [AGENTS.md](../AGENTS.md) for development conventions.
