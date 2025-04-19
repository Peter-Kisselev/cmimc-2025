# submission.py

# --- Helper Functions ---
# These functions are defined at the module level to minimize the memory footprint
# of the SubmissionPlayer class instance, as methods stored per instance can add overhead.
# They use bit manipulation for efficiency and low memory usage.

def _count_set_bits(n):
    """
    Counts the number of set bits (1s) in a non-negative integer.
    Uses Brian Kernighan's algorithm for efficiency.
    Example: _count_set_bits(0b10110) == 3
    """
    count = 0
    # The expression n &= (n - 1) clears the least significant set bit.
    # We repeat this until n becomes 0.
    while n > 0:
        n &= (n - 1)
        count += 1
    return count

def _get_card_by_rank(bitmask, n, highest_first):
    """
    Finds the nth available card (1-based index n) represented in the bitmask.
    Bits 1 to 15 of the bitmask correspond to cards 1 to 15.
    - bitmask: Integer mask where set bits indicate available cards.
    - n: The rank to find (e.g., 1 for the lowest/highest, 2 for the second, etc.). Must be >= 1.
    - highest_first: If True, finds the nth highest available card.
                     If False, finds the nth lowest available card.
    Returns the card number (1-15).
    Includes a fallback mechanism: If 'n' is greater than the number of available
    cards, it returns the actual highest (if highest_first=True) or
    lowest (if highest_first=False) available card.
    Returns 0 if the bitmask is empty (no cards available).
    """
    # Ensure rank 'n' is at least 1 for correct logic.
    if n <= 0:
        n = 1

    count = 0
    # Stores the first card found when iterating, used as fallback.
    fallback_card = 0

    if highest_first:
        # Iterate downwards from card 15 to 1 to find highest ranks first.
        for i in range(15, 0, -1):
            # Check if the bit corresponding to card 'i' is set in the mask.
            if (bitmask >> i) & 1:
                # If this is the first available card found, store it as fallback (it's the highest).
                if fallback_card == 0:
                    fallback_card = i
                count += 1
                # If we have found the nth card, return it.
                if count == n:
                    return i
        # If the loop finishes without returning, n was >= total available cards.
        # Return the highest card found (stored in fallback_card).
        return fallback_card
    else:
        # Iterate upwards from card 1 to 15 to find lowest ranks first.
        for i in range(1, 16):
            # Check if the bit corresponding to card 'i' is set in the mask.
            if (bitmask >> i) & 1:
                # If this is the first available card found, store it as fallback (it's the lowest).
                if fallback_card == 0:
                    fallback_card = i
                count += 1
                # If we have found the nth card, return it.
                if count == n:
                    return i
        # If the loop finishes without returning, n was >= total available cards.
        # Return the lowest card found (stored in fallback_card).
        return fallback_card

# --- Player Class ---
# No explicit base class inheritance is shown or required by the problem statement.
class SubmissionPlayer:
    """
    Implements the bidding strategy for the Bid game under strict memory constraints.

    The strategy uses a bitmask (`self.my_cards_bitmask`) to keep track of the
    player's available bidding cards (1 through 15). It does not store or use
    the `player_history` due to the 228-byte memory limit.

    The bidding logic is purely reactive to the current `score_card` and the set
    of available cards:
    - For high positive score cards (>= 7), it bids aggressively using high cards (highest or 2nd highest).
    - For medium positive score cards (4-6), it bids conservatively using a low card (3rd lowest) to save high cards.
    - For low positive score cards (1-3), it bids the lowest available card to discard it cheaply.
    - For negative score cards, it bids low cards (lowest, 2nd, or 3rd lowest depending on the penalty)
      aiming for the lowest unique bid to "win" (take) the negative card, hoping others bid lower or tie.
    The use of 2nd or 3rd highest/lowest cards is a heuristic to increase the chance of a unique bid.
    """
    def __init__(self, player_index):
        """
        Initializes the player agent.
        Args:
            player_index (int): The index (0-3) assigned to this player.
        """
        # Store player index (although not used in the current strategy logic). Size: ~4-8 bytes.
        self.player_index = player_index

        # Initialize the bitmask. (1 << 16) - 2 creates the integer value
        # equivalent to 0b1111111111111110 in binary.
        # This sets bits 1 through 15, representing that cards 1 to 15 are initially available.
        # Size: ~4-8 bytes.
        # Total instance memory usage is minimal, well within the 228-byte limit.
        self.my_cards_bitmask = (1 << 16) - 2

    def play(self, score_card, player_history):
        """
        Determines and returns the bidding card to play for the current round.

        Args:
            score_card (int): The value of the score card revealed this round.
            player_history (List[List[int]]): A history of bids made by all players
                                              in previous rounds. *Ignored by this strategy.*

        Returns:
            int: The bidding card (1-15) selected for this round.
        """
        # Get the current mask of available cards.
        mask = self.my_cards_bitmask
        # Count how many cards are available.
        num_available = _count_set_bits(mask)

        # Edge Case: No cards left. This should not happen in a standard 15-round game.
        if num_available == 0:
            return 1 # Return a default valid bid as a fallback.

        # Edge Case: Only one card left. Must play it.
        if num_available == 1:
            # Find the single remaining card (it's both the lowest and highest).
            bid = _get_card_by_rank(mask, 1, False) # n=1, highest_first=False gets the lowest (only) card.
            # Ensure a card was found (should always be > 0 if num_available is 1).
            if bid != 0:
                # Update the mask by clearing the bit for the played card.
                self.my_cards_bitmask &= ~(1 << bid)
                return bid
            else:
                # Should be unreachable, but return fallback just in case.
                return 1

        # --- Main Strategy Logic ---
        bid = 0
        if score_card > 0:
            # --- Positive Score Card Strategy ---
            if score_card >= 9:      # Scores 9, 10: Highest value. Bid highest available card.
                bid = _get_card_by_rank(mask, 1, True)
            elif score_card >= 7:    # Scores 7, 8: High value. Bid 2nd highest for uniqueness.
                bid = _get_card_by_rank(mask, 2, True)
            elif score_card >= 4:    # Scores 4, 5, 6: Medium value. Bid 3rd lowest to conserve high cards.
                bid = _get_card_by_rank(mask, 3, False)
            else:                    # Scores 1, 2, 3: Low value. Bid lowest available card to discard it.
                bid = _get_card_by_rank(mask, 1, False)
        else:
            # --- Negative Score Card Strategy ---
            # Aim for the lowest unique bid to take the card.
            abs_score = -score_card # Absolute value of score (1 to 5)
            if abs_score >= 4:       # Scores -4, -5: High penalty. Avoid tie on lowest.
                # Bid 3rd lowest for -5, 2nd lowest for -4.
                rank = 3 if abs_score == 5 else 2
                bid = _get_card_by_rank(mask, rank, False)
            else:                    # Scores -1, -2, -3: Lower penalty.
                # Bid 2nd lowest for -3, 1st lowest for -1, -2 (riskier but acceptable).
                rank = 2 if abs_score == 3 else 1
                bid = _get_card_by_rank(mask, rank, False)

        # --- Post-decision Processing ---
        # The _get_card_by_rank function includes fallbacks, so 'bid' should
        # always be a valid card number (1-15) if num_available > 0.
        # We add a safety check in case 'bid' somehow became 0.
        if bid == 0:
             # If bid is 0, it implies the helper function failed unexpectedly.
             # Default to playing the lowest available card as an absolute fallback.
             bid = _get_card_by_rank(mask, 1, False)
             # If even that fails (mask must be empty, contradicting earlier checks), return 1.
             if bid == 0:
                 return 1

        # Update the bitmask: Turn off the bit corresponding to the card being played.
        # This removes the card from the available set for future rounds.
        self.my_cards_bitmask &= ~(1 << bid)

        # Return the chosen bid card.
        return bid
