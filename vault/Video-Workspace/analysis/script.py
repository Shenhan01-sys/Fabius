"""The voiceover script: one entry per display line, shared by the TTS, the aligner and the SFX cue sheet.

Each line is (plate, display text). The display text is what the plates show (karaoke words are split on
spaces). SPOKEN maps a display token to the words actually said, for numbers, acronyms and coined words;
SAY_FIX rewrites the text handed to the TTS so it says those tokens the same way.

Every factual sentence here was checked against a command or a file in the repo (see ../SCRIPT.md).
Change a line here, then re-run tts_kokoro.py (scratch voice) or align_vo.py (your own recording).
"""
import re

LINES = [
    ("hook", "Over two thousand years ago, Rome kept losing to Hannibal in open battle."),
    ("hook", "So one general did something radical: he refused the battles Hannibal wanted."),
    ("hook", "His name was Fabius."),
    ("problem", "Most trading bots want the battle."),
    ("problem", "They charge in, then show you a screenshot of profit, taken after the market moved."),
    ("problem", "You can’t check what they decided, or when."),
    ("idea", "Fabius is a paper-trading desk that commits its decisions to BNB Chain before the outcome exists."),
    ("idea", "Even the decision to do nothing."),
    ("lock", "It starts with the rules."),
    ("lock", "Each of our six bots has its strategy hashed and locked on-chain."),
    ("lock", "A strategy that wasn’t locked first can’t commit a signal."),
    ("commit", "Every bar, a bot’s signals become one Merkle root, committed to chain 97."),
    ("commit", "Late commits are rejected. Every reveal is checked against the root."),
    ("commit", "Anyone can rerun the ledger. No keys needed."),
    ("desk", "On top runs the AI desk."),
    ("desk", "Every five minutes, AI analysts, each with an ERC-8004 identity, vote on which bot to run, and where."),
    ("desk", "A locked formula turns their votes into one book."),
    ("desk", "And its root must reach the chain before the five minutes are up."),
    ("split", "The AI picks the rulebook. Code computes the position."),
    ("open", "And the desk is open."),
    ("open", "Bring your own bot as declarative rules, or plug in your own agent."),
    ("open", "Every bot runs the same gates in public, and every verdict comes with its reason."),
    ("bnb", "Signals sell over x402, and the buyer pays no gas."),
    ("bnb", "All on testnet, with a test token. No real money, by design."),
    ("honest", "Because here’s what we don’t claim: profit."),
    ("honest", "The forward clock started on October 1st."),
    ("honest", "To pass, a bot needs 20 signals, 20 days, 2 months, and a confidence interval above zero."),
    ("honest", "Today, zero of six have passed."),
    ("end", "So Fabius does what Fabius does best."),
    ("end", "It waits."),
    ("end", "Fabius. Refuse the battle. Prove the decision."),
]

# display token (punctuation stripped, lower case) -> spoken words
SPOKEN = {
    "97": ["ninety", "seven"],
    "ai": ["a", "i"],
    "erc8004": ["e", "r", "c", "eighty", "oh", "four"],
    "x402": ["x", "four", "oh", "two"],
    "bnb": ["b", "n", "b"],
    "onchain": ["on", "chain"],
    "papertrading": ["paper", "trading"],
    "1st": ["first"],
    "20": ["twenty"],
    "2": ["two"],
}

# what the TTS is given instead of the display text (same words as SPOKEN, written so it reads them right)
SAY_FIX = [
    (r"\bERC-8004\b", "E R C eighty oh four"),
    (r"\bx402\b", "x four oh two"),
    (r"\bBNB\b", "B N B"),
    (r"\bAI\b", "A I"),
    (r"\bchain 97\b", "chain ninety-seven"),
    (r"\bOctober 1st\b", "October first"),
    (r"\b20 signals, 20 days, 2 months\b", "twenty signals, twenty days, two months"),
]

# pronunciations the aligner's dictionary lacks (CMU phones)
EXTRA_DICT = {
    "fabius": "F EY B IY AH S",
    "merkle": "M ER K AH L",
    "testnet": "T EH S T N EH T",
    "rulebook": "R UW L B UH K",
    "bot's": "B AA T S",
    "rerun": "R IY R AH N",
    "screenshot": "S K R IY N SH AA T",
}


def norm(tok: str) -> str:
    return re.sub(r"[^a-z0-9']", "", tok.lower().replace("’", "'")).strip("'")


def spoken(tok: str) -> list[str]:
    k = re.sub(r"[^a-z0-9]", "", tok.lower())
    if k in SPOKEN:
        return SPOKEN[k]
    n = norm(tok)
    return [n] if n else []


def say(text: str) -> str:
    s = text.replace("’", "'")
    for pat, rep in SAY_FIX:
        s = re.sub(pat, rep, s)
    return s


def plates() -> list[str]:
    seen = []
    for p, _ in LINES:
        if p not in seen:
            seen.append(p)
    return seen
