# Chip In frontend

An interactive Spanish-language frontend for the event expense splitter. Built with JavaScript, CSS, and Node.js tooling. No dependencies or backend required.

## Run

```sh
cd frontent
npm run dev
```

Open http://localhost:5173. Use **Explorar un ejemplo** to load the specification's example, or create an empty event. The example produces a $40 MXN transfer from Luis to Ana's group.

## Features

- Create events with one fixed currency (MXN, USD, or EUR).
- Register groups, representatives, and attendees with individual categories.
- Select a group and record expenses with that group prefilled.
- Inspect category totals, contributions, individual allocations, rounding adjustments, and settlement instructions.
- Copy event links and reopen saved events in the same browser.

## Mock data access

All persistence is centralized in `src/api.js`, which exposes asynchronous methods that can later be replaced by HTTP requests. Data is stored in localStorage. Links identify events in that browser's storage; they do **not** share data between devices or browsers. Clearing browser storage removes saved events. The interface explicitly explains this limitation.

`src/calculations.js` calculates allocations in integer cents and assigns leftover cents in attendee registration order. Settlement is blocked when a category has expenses but no participants. No payment processing or completion tracking is implemented.

Google Fonts are optional; system fonts are used if unavailable.

## Verify

```sh
npm test
```

Tests cover the specification example, persistence, rounding, missing participants, invalid amounts, and balance conservation.
