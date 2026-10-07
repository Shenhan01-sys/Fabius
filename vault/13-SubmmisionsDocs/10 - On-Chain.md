---
tags: [submission, deck, slide]
slide: 10
id: onchain
layout: stack
theme: night
section: "09 — On-chain"
transition: fade
guards: []
---

# 10 · On-chain: five contracts carry the flow, all ours

**Bagian dari:** [[13-SubmmisionsDocs/00 - Hub Submission Deck]]
**Sumber:** [[02-Contracts/C7 - SignalAnchor]] · [[02-Contracts/C6 - LockRegistry]] · [[04-Tools/TL33 - agent analis]] · [[04-Tools/TL34 - meja AI 5 menit]] · [[04-Tools/TL32 - gerbang x402 per sinyal]] · [[Quick-Reference]] · [[05-Ecosystem/01 - ERC-8004 Identity]] · `deployments/97.json`
**Ringkasan:** Lima kontrak yang ditulis dan di-deploy Fabius di BNB testnet (SignalAnchor = alur utama), dua jaminan yang berupa revert di kode (TooLate, LockedAfterBar), dan pemisahan tegas dari rel standar yang hanya kami pakai (ERC-8004, proxy x402, Permit2).

## Scene

**Setting.** Night. A ledger of five rows, each a glass card with a small isometric slab as its icon.

**Left: the five contracts.** SignalAnchor is first and brighter: its card has a violet rim, a luminous white slab, and a MAIN FLOW chip. The other four have indigo slabs (the test token has a dark one). Each row shows the contract name in bold, one line saying what it guarantees, and its short address in mono on the right.

**Right, top: enforced by the contract.** A glass card with two red chips: TooLate and LockedAfterBar. Red here marks the two ways a commit is *refused*. One plain sentence underneath: the rule is code, not good intentions.

**Right, bottom: not ours.** A dashed card, quieter, titled STANDARD RAILS WE USE · NOT OURS: the ERC-8004 identity registry and the x402 payment proxy with Permit2. We use them; we did not write them.

**Under it all.** One mono line naming the network and where the full addresses live.

**Feeling.** A balance sheet with the assets and the borrowed items on separate lines.

## Slide

```yaml
headline: "Five contracts. *All ours.*"
sub: "Written and deployed by Fabius on BNB Smart Chain testnet. They carry the whole flow."
contracts:
  - {name: "SignalAnchor", role: "Per-bar Merkle commit of every signal; late ones revert.", addr: "0x9B78200beFbbBe836585d31bd5b6dB32587064f3", main: true}
  - {name: "LockRegistry", role: "Write-once lock of each rule, with block time.", addr: "0xcF6fBF95fc04DEd8d670512CEc0723a2246Fbb0C"}
  - {name: "SelectionAnchor", role: "Analysts' daily bot pick, sealed before the bar closes.", addr: "0xc0c16337e6c286ec54902d8de7aadf232587f3b1"}
  - {name: "DeskAnchor", role: "Merkle root of each 5-minute cycle, only while it runs.", addr: "0x706da379a5112aa7c86803dcf58d8fdab442305f"}
  - {name: "FabiusCredit (FAB)", role: "Test token that pays for signals. No value.", addr: "0xc7b6d5cdbdc881daae0dbcc095d4f184b70ec881", kind: token}
enforced:
  title: "ENFORCED BY THE CONTRACT"
  errors: ["TooLate", "LockedAfterBar"]
  text: "A commit after the 12-hour window, or for a rule locked after the bar, reverts. The rule is code, not good intentions."
external:
  title: "STANDARD RAILS WE USE · NOT OURS"
  items:
    - "ERC-8004 Identity Registry: home of Fabius agent #2494"
    - "x402 payment proxy and Permit2: settlement"
foot: "BNB SMART CHAIN TESTNET · CHAIN ID {{chain_id}} · FULL ADDRESSES IN deployments/97.json · EARLIER DEPLOYMENTS LISTED THERE TOO"
```

## Narration

Everything you have seen is anchored by five contracts that we wrote and deployed on BNB Smart Chain testnet.

SignalAnchor is the main flow: the per-bar commit of every signal, with late commits rejected. LockRegistry is the write-once lock for each rule. SelectionAnchor records the analysts' daily pick, DeskAnchor the five-minute desk roots, and FabiusCredit is the test token that pays for signals.

Two of our guarantees are not promises. They are reverts in the contract code: TooLate, and LockedAfterBar.

And on the right, what we do not own: the ERC-8004 identity registry, and the x402 payment proxy with Permit2. We use them. We did not write them. Earlier deployments, such as our first decision anchor, are listed in the repo's deployments file.

## Claims check

| on the slide | evidence | status |
|---|---|---|
| Five addresses, roles | `deployments/97.json`; [[Quick-Reference]] address table; verified by the unit test that each address string appears in `deployments/97.json` | live on chain 97 |
| `TooLate`, `LockedAfterBar` revert | `contracts/SignalAnchor.sol:69,71` | enforced |
| Window = 12 h | `maxLag` 43200 s (`deployments/97.json`, constructor of SignalAnchor) | true |
| LockRegistry is write-once | `contracts/LockRegistry.sol:8,32,41` (`AlreadyLocked`) | enforced |
| SelectionAnchor = daily pick; DeskAnchor = 5-minute root | `contracts/SelectionAnchor.sol:6`, `contracts/DeskAnchor.sol:5` | true |
| FAB has no value | `contracts/FabiusCredit.sol:8` | true |
| Not ours: ERC-8004 registry, x402 proxy, Permit2 | [[05-Ecosystem/01 - ERC-8004 Identity]]; [[10-Submissions/03 - Form Fields]] ("registry pihak ketiga") | true |
| No third-party audit | none documented | stated here so nobody assumes one |
