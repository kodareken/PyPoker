#!/usr/bin/env python3
"""
Monte Carlo Poker Equity Simulator for Texas Hold'em

Features:
- Exact 7-card hand evaluator (straight, flush, straight flush, pairs, etc.)
- Simulates random opponent hands and remaining board cards from a given street
- Reports win probability (strict wins) and equity (including split pots)

Usage examples:
  python3 monte_carlo_poker_equity.py \
      --iterations 200000 \
      --opponents 5 \
      --hero "Jd 4h" \
      --board "5c 3c 3s" \
      --seed 42

Card notation:
- Ranks: 2 3 4 5 6 7 8 9 T J Q K A
- Suits: c d h s
Examples: As, Td, 9h, 3c

Author: Agent Mode
"""
from __future__ import annotations
import argparse
import math
import random
from typing import List, Tuple, Sequence

RANKS = "23456789TJQKA"
SUITS = "cdhs"

# Hand categories (higher is better)
# 8 Straight Flush
# 7 Four of a Kind
# 6 Full House
# 5 Flush
# 4 Straight
# 3 Three of a Kind
# 2 Two Pair
# 1 One Pair
# 0 High Card


def card_str_to_int(card: str) -> int:
    card = card.strip()
    if len(card) != 2:
        raise ValueError(f"Invalid card: {card}")
    r, s = card[0].upper(), card[1].lower()
    try:
        r_idx = RANKS.index(r)
        s_idx = SUITS.index(s)
    except ValueError:
        raise ValueError(f"Invalid card: {card}")
    return s_idx * 13 + r_idx


def parse_cards_str(cards_str: str) -> List[int]:
    # Accept space- or comma-separated (and tolerate double spaces)
    toks = [t for t in cards_str.replace(",", " ").split() if t]
    return [card_str_to_int(t) for t in toks]


def int_to_rank(card: int) -> int:
    # 0..51 -> rank 2..14
    return (card % 13) + 2


def int_to_suit(card: int) -> int:
    # 0..51 -> suit 0..3 (c,d,h,s)
    return card // 13


def straight_high_from_ranks_mask(mask: int) -> int:
    """Return high card of the best straight given a rank bit mask.

    mask has bits at positions r (2..14) if that rank is present.
    Also include bit 1 if Ace (14) is present to handle A-5 wheel.
    Returns 0 if no straight.
    """
    # Check from Ace-high (14) down to 5-high
    for high in range(14, 4, -1):
        need = 0
        for d in range(0, 5):
            r = high - d
            need |= (1 << r)
        if (mask & need) == need:
            return high
    return 0


def evaluate_7(cards: Sequence[int]) -> Tuple[int, Tuple[int, ...]]:
    """Evaluate a 7-card hand. Returns (category, tiebreakers...) tuple.
    Higher tuple compares as stronger.
    """
    # Count ranks and suits
    rank_counts = [0] * 15  # 0..14, we use 2..14
    suit_counts = [0] * 4
    for c in cards:
        r = int_to_rank(c)
        s = int_to_suit(c)
        rank_counts[r] += 1
        suit_counts[s] += 1

    # Prepare masks for straight detection
    rank_mask = 0
    for r in range(2, 15):
        if rank_counts[r] > 0:
            rank_mask |= (1 << r)
    if rank_counts[14]:
        rank_mask |= (1 << 1)  # Ace as low (for wheel)

    # Detect flush
    flush_suit = -1
    for s in range(4):
        if suit_counts[s] >= 5:
            flush_suit = s
            break

    # Collect ranks sorted descending
    unique_ranks = [r for r in range(14, 1, -1) if rank_counts[r] > 0]

    # Straight flush check
    if flush_suit != -1:
        # Build mask of ranks within the flush suit
        flush_ranks = [int_to_rank(c) for c in cards if int_to_suit(c) == flush_suit]
        flush_mask = 0
        present_ace = False
        for r in set(flush_ranks):
            flush_mask |= (1 << r)
            if r == 14:
                present_ace = True
        if present_ace:
            flush_mask |= (1 << 1)
        sf_high = straight_high_from_ranks_mask(flush_mask)
        if sf_high:
            # Straight flush
            return (8, (sf_high,))

    # Quads, trips, pairs
    quads = []
    trips = []
    pairs = []
    kickers = []
    for r in range(14, 1, -1):
        cnt = rank_counts[r]
        if cnt == 4:
            quads.append(r)
        elif cnt == 3:
            trips.append(r)
        elif cnt == 2:
            pairs.append(r)
        elif cnt == 1:
            kickers.append(r)

    if quads:
        quad_rank = quads[0]
        # Best kicker is highest rank not equal to quad_rank
        kicker = max([r for r in unique_ranks if r != quad_rank])
        return (7, (quad_rank, kicker))

    if trips and (pairs or len(trips) >= 2):
        # Full house: use highest trip, then next highest trip (as pair) or highest pair
        trip_rank = trips[0]
        if len(trips) >= 2:
            pair_rank = trips[1]
        else:
            pair_rank = pairs[0]
        return (6, (trip_rank, pair_rank))

    if flush_suit != -1:
        flush_cards = sorted([int_to_rank(c) for c in cards if int_to_suit(c) == flush_suit], reverse=True)
        top5 = tuple(flush_cards[:5])
        return (5, top5)

    # Straight
    st_high = straight_high_from_ranks_mask(rank_mask)
    if st_high:
        return (4, (st_high,))

    if trips:
        trip_rank = trips[0]
        # two highest kickers excluding trip_rank
        ks = [r for r in unique_ranks if r != trip_rank]
        k1 = ks[0]
        k2 = ks[1]
        return (3, (trip_rank, k1, k2))

    if len(pairs) >= 2:
        p1, p2 = pairs[0], pairs[1]
        kicker = max([r for r in unique_ranks if r != p1 and r != p2])
        return (2, (p1, p2, kicker))

    if len(pairs) == 1:
        p = pairs[0]
        ks = [r for r in unique_ranks if r != p]
        k1, k2, k3 = ks[0], ks[1], ks[2]
        return (1, (p, k1, k2, k3))

    # High card: top 5 ranks
    top5 = tuple(unique_ranks[:5])
    return (0, top5)


def compare_hands(a: Tuple[int, Tuple[int, ...]], b: Tuple[int, Tuple[int, ...]]) -> int:
    """Compare two evaluated hands. Return 1 if a>b, -1 if a<b, 0 if tie."""
    if a[0] != b[0]:
        return 1 if a[0] > b[0] else -1
    # Same category; compare tiebreakers lexicographically
    if a[1] == b[1]:
        return 0
    return 1 if a[1] > b[1] else -1


def deck_without(exclude: Sequence[int]) -> List[int]:
    excl = set(exclude)
    return [c for c in range(52) if c not in excl]


def simulate_equity(
    hero: Sequence[int],
    board: Sequence[int],
    n_opponents: int,
    iterations: int,
    seed: int | None = None,
) -> Tuple[float, float, int, int, int]:
    """Run Monte Carlo simulation.

    Returns (win_rate, equity, wins, ties, losses) where:
      - win_rate = P(hero strictly best) = wins / iterations
      - equity = (wins + split_shares) / iterations; split_shares is hero's fractional share of tied pots
    """
    if seed is not None:
        random.seed(seed)

    known = list(hero) + list(board)
    base_deck = deck_without(known)

    wins = 0
    ties = 0
    losses = 0
    equity_shares = 0.0

    need_cards = n_opponents * 2 + (5 - len(board))

    for _ in range(iterations):
        # Sample remaining cards needed for opponents and runout
        draw = random.sample(base_deck, need_cards)
        opp_cards = [draw[i*2:(i+1)*2] for i in range(n_opponents)]
        runout = draw[n_opponents*2:]

        full_board = list(board) + runout
        hero_eval = evaluate_7(list(hero) + full_board)

        best_cmp = 1  # 1 means hero currently best; 0 tie; -1 lost
        n_best = 1    # number of players tied at best (including hero)

        for oc in opp_cards:
            opp_eval = evaluate_7(oc + full_board)
            cmp = compare_hands(opp_eval, hero_eval)
            if cmp > 0:  # opponent better
                best_cmp = -1
                n_best = 1
                break
            elif cmp == 0:  # tie with hero so far
                n_best += 1
                best_cmp = 0
            # if cmp < 0: hero still best so far

        if best_cmp == 1:
            wins += 1
            equity_shares += 1.0
        elif best_cmp == 0:
            ties += 1
            equity_shares += 1.0 / n_best
        else:
            losses += 1

    win_rate = wins / iterations
    equity = equity_shares / iterations
    return win_rate, equity, wins, ties, losses


def format_cards(cards: Sequence[int]) -> str:
    out = []
    for c in cards:
        r = RANKS[c % 13]
        s = SUITS[c // 13]
        out.append(f"{r}{s}")
    return " ".join(out)


def main():
    parser = argparse.ArgumentParser(description="Monte Carlo Hold'em Equity Simulator")
    parser.add_argument("--iterations", "-n", type=int, default=100000, help="Number of Monte Carlo iterations")
    parser.add_argument("--opponents", "-o", type=int, default=5, help="Number of active opponents")
    parser.add_argument("--hero", type=str, default="Jd 4h", help="Hero hole cards (e.g., 'As Kd' or 'Jd 4h')")
    parser.add_argument("--board", type=str, default="5c 3c 3s", help="Known community cards (space/comma separated)")
    parser.add_argument("--seed", type=int, default=None, help="Random seed for reproducibility")
    args = parser.parse_args()

    hero_cards = parse_cards_str(args.hero)
    board_cards = parse_cards_str(args.board)

    if len(hero_cards) != 2:
        raise SystemExit("Hero must have exactly 2 cards")
    if len(board_cards) > 5:
        raise SystemExit("Board cannot exceed 5 cards")

    # Sanity: no duplicates
    if len(set(hero_cards + board_cards)) != len(hero_cards) + len(board_cards):
        raise SystemExit("Duplicate cards detected in hero/board inputs")

    print("Configuration:")
    print(f"  Iterations:       {args.iterations}")
    print(f"  Opponents:        {args.opponents}")
    print(f"  Hero:             {format_cards(hero_cards)}")
    print(f"  Board (known):    {format_cards(board_cards)}")
    if args.seed is not None:
        print(f"  Seed:             {args.seed}")

    win_rate, equity, wins, ties, losses = simulate_equity(
        hero=hero_cards,
        board=board_cards,
        n_opponents=args.opponents,
        iterations=args.iterations,
        seed=args.seed,
    )

    n = args.iterations
    # Approx 95% CI using normal approximation
    def ci(p: float) -> Tuple[float, float]:
        se = math.sqrt(p * (1 - p) / n) if n > 0 else 0.0
        return max(0.0, p - 1.96 * se), min(1.0, p + 1.96 * se)

    win_lo, win_hi = ci(win_rate)
    eq_lo, eq_hi = ci(equity)

    print("\nResults:")
    print(f"  Wins:             {wins}")
    print(f"  Ties:             {ties}")
    print(f"  Losses:           {losses}")
    print(f"  Win probability:  {win_rate:.5f} (95% CI: {win_lo:.5f}..{win_hi:.5f})")
    print(f"  Equity (incl tie):{equity:.5f} (95% CI: {eq_lo:.5f}..{eq_hi:.5f})")


if __name__ == "__main__":
    main()
