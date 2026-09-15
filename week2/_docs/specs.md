# Chip In — Functional Specifications

## 1. Purpose

Build a simple web application that splits event expenses among groups of attendees based on the expense categories each person participates in.

The application must clearly show what each group paid, how expenses were allocated, each group’s share, and who should pay whom to settle the balances.

## 2. Scope

This first version is a small school project. It prioritizes quick data entry, clear calculations, and traceable results.

All information is assumed to be entered correctly. Editing and deleting records are outside the scope.

## 3. Key Concepts

| Concept | Definition |
|---|---|
| Event | Gathering for which attendees and shared expenses are recorded. |
| Group | A family, couple, or individual whose expenses are calculated together. |
| Group representative | Person who represents a group when entering information, paying, or receiving money. |
| Attendee | A group member who participates in one or more expense categories. |
| Category | Classification that determines which attendees share an expense. |
| Expense | Purchase paid for by a group and assigned to an event category. |

A representative who attends the event must also be registered as an attendee, without being counted twice.

## 4. Access and Registration

### 4.1. Event Setup

- Allow users to create an event by entering its name.
- Generate a shared link to access the event.
- Use a single currency per event.

### 4.2. Access

- Access the event through its shared link.
- Register a new group or select an existing group.
- Do not require accounts, email addresses, or passwords.
- Allow representatives to view the event’s expenses and results.

Selecting a group identifies which group the information is attributed to; it does not verify the user’s identity.

### 4.3. Groups and Attendees

Use a single screen to enter:

- Group name.
- Representative’s name.
- Attendees’ names.
- Categories each attendee participates in.

An individual attending alone forms a group of one.

## 5. Fixed Categories

| Category | Included Attendees |
|---|---|
| Food | Attendees participating in shared meals. |
| Alcoholic Beverages | Attendees consuming alcoholic beverages. |
| Games | Attendees participating in games or activities with a cost. |
| General Expenses | All attendees, included automatically. |

Categories are selected individually for each attendee. For example:

- A child may participate in Food and Games.
- An adult may participate in Food and Alcoholic Beverages.
- Both are also included in General Expenses.

Users cannot create additional categories in this version.

## 6. Expense Entry

Any representative can record purchases made by their group.

### Expense Fields

| Field | Description |
|---|---|
| Description | Brief description of the purchase, such as “Napkins.” |
| Amount | Amount paid. |
| Category | Category to which the expense belongs. |
| Paying group | Group credited with paying the expense. |

To simplify entry, the currently selected group is prefilled as the paying group.

Each expense belongs to one category. If a purchase includes items from different categories, users must enter a separate amount for each category.

## 7. Allocation Rules

### 7.1. Allocation by Category

1. Add all expenses within a category.
2. Count the attendees included in that category.
3. Divide the total equally among those attendees.
4. Add each group member’s share to calculate the group’s charge for that category.

All attendees in the same category have equal weight. No age-based rates apply.

**Example:** If beverages cost $600 and three attendees participate, each attendee’s share is $200. A group with two participating attendees owes $400, while a group with one owes $200.

### 7.2. Group Totals

A group’s total share is the sum of its charges across all categories.

A group’s contribution is the sum of all expenses it paid, regardless of whether its members participate in the purchased category.

### 7.3. Group Balance

**Balance = amount paid by the group − group’s total share**

- Positive balance: the group should receive money.
- Negative balance: the group should pay money.
- Zero balance: the group’s account is balanced.

### 7.4. Precision

- Calculate amounts using the currency’s smallest unit, such as cents.
- Allocate leftover cents to included attendees in registration order until the full amount is assigned.
- Make rounding adjustments visible in the breakdown.
- The sum of allocated charges must exactly match total expenses.
- If a category has expenses but no included attendees, display that allocation cannot be completed until participants are registered for that category.

## 8. Application Stages

### Stage 1: Groups and Attendees

Display:

- Registered groups and their representatives.
- Members of each group.
- Each attendee’s categories.
- Total attendee count and attendee count per category.

### Stage 2: Expenses and Contributions

Display:

- Expense list with description, amount, category, and paying group.
- Total expenses per category.
- Total paid by each group.
- Total event expenses.

### Stage 3: Expense Allocation

For each category, display:

- Total amount.
- Number of included attendees.
- Amount per attendee and any rounding adjustments.
- Included members of each group.
- Each group’s charge.

Also display each group’s total share across all categories.

### Stage 4: Payments Between Groups

Display:

- Total paid by each group.
- Each group’s total share.
- Amount each group owes or should receive.
- Suggested transfers, including the paying group, receiving group, and amount.

Example: **“Ana’s group pays $200 to Luis’s group.”**

Suggested transfers must exactly settle outstanding balances. The application should produce a straightforward distribution without requiring the mathematically smallest possible number of transfers.

This stage displays payment instructions only. It does not process payments or track whether they were completed.

## 9. Complete Example

### Attendees

| Group | Attendee | Food | Alcoholic Beverages | Games | General Expenses |
|---|---|---|---|---|---|
| Ana | Ana | Yes | Yes | No | Yes |
| Ana | Child | Yes | No | Yes | Yes |
| Luis | Luis | Yes | Yes | No | Yes |

### Expenses

| Description | Category | Amount | Paying Group |
|---|---|---:|---|
| Shared meal | Food | $600 | Ana |
| Beverages | Alcoholic Beverages | $200 | Luis |
| Children’s activity | Games | $100 | Ana |
| Napkins | General Expenses | $90 | Luis |
| **Total** | | **$990** | |

### Allocation

| Category | Included Attendees | Ana’s Group Share | Luis’s Group Share |
|---|---:|---:|---:|
| Food | 3 | $400 | $200 |
| Alcoholic Beverages | 2 | $100 | $100 |
| Games | 1 | $100 | $0 |
| General Expenses | 3 | $60 | $30 |
| **Total** | | **$660** | **$330** |

### Settlement

| Group | Amount Paid | Group’s Share | Result |
|---|---:|---:|---|
| Ana | $700 | $660 | Receives $40 |
| Luis | $290 | $330 | Pays $40 |

**Suggested payment: Luis’s group pays $40 to Ana’s group.**

## 10. Usability Requirements

- Spanish-language interface that adapts to mobile screens.
- Brief data entry without unnecessary personal information.
- Checkboxes for selecting attendee categories.
- Clearly labeled stages.
- Results updated after each new entry.
- Saved information available when the shared link is reopened.
- Enough detail to trace calculations from individual expenses to suggested payments.

## 11. Out of Scope

- Accounts, passwords, and identity verification.
- Advanced roles and permissions.
- Editing and deleting records.
- Custom categories.
- Percentage-based, weighted, or custom individual allocations.
- Multiple currencies and currency conversion.
- Receipts, photographs, and receipt scanning.
- Banking integrations and payment processing.
- Confirmation or tracking of completed transfers.
- Notifications and reminders.
- Change history.

## 12. Acceptance Criteria

1. A representative can access an event through its shared link without creating an account.
2. A representative can register a group and its attendees, including their categories.
3. All attendees are automatically included in General Expenses.
4. Any representative can record an expense attributed to their group.
5. Each expense is allocated only among attendees included in its category.
6. Individual shares are correctly accumulated by group.
7. Total expenses equal both total contributions and total allocated charges.
8. Users can inspect how each group’s share was calculated.
9. Suggested transfers settle all group balances.
10. The example in this document produces a single $40 payment from Luis’s group to Ana’s group.