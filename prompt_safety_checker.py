"""
Prompt Safety Checker - Helps identify prompts that may trigger RAI filters
"""

import re
from typing import Dict, List, Tuple

class PromptSafetyChecker:
    """Check prompts for content that may trigger Google Veo's RAI filters."""

    # Lists of terms that commonly trigger filters
    CELEBRITY_INDICATORS = [
        'elon musk', 'taylor swift', 'beyonce', 'trump', 'obama', 'biden',
        'kardashian', 'celebrity', 'famous person', 'actor', 'actress'
    ]

    BRAND_INDICATORS = [
        'nike', 'adidas', 'apple', 'google', 'microsoft', 'coca-cola',
        'pepsi', 'disney', 'marvel', 'star wars', 'pokemon', 'ferrari',
        'lamborghini', 'tesla', 'iphone', 'android', 'playstation', 'xbox'
    ]

    COPYRIGHTED_CHARACTERS = [
        'mickey mouse', 'superman', 'batman', 'spider-man', 'iron man',
        'harry potter', 'darth vader', 'pikachu', 'mario', 'sonic'
    ]

    VIOLENCE_INDICATORS = [
        'gun', 'weapon', 'sword', 'knife', 'blood', 'violence', 'fight',
        'attack', 'war', 'battle', 'explosion', 'shoot', 'kill', 'death',
        'murder', 'assault', 'combat'
    ]

    INAPPROPRIATE_CONTENT = [
        'naked', 'nude', 'sexy', 'sexual', 'intimate', 'erotic',
        'lingerie', 'bikini', 'underwear', 'revealing'
    ]

    DANGEROUS_ACTIVITIES = [
        'suicide', 'self-harm', 'overdose', 'poison', 'drugs', 'cocaine',
        'heroin', 'methamphetamine', 'bomb', 'terrorist', 'explosion'
    ]

    def __init__(self):
        self.warnings = []
        self.blockers = []

    def check_prompt(self, prompt: str) -> Dict[str, any]:
        """
        Check a prompt for potentially problematic content.

        Returns:
            dict: {
                "safe": bool,
                "risk_level": str ("low", "medium", "high"),
                "warnings": List[str],
                "blockers": List[str],
                "suggestions": List[str]
            }
        """
        self.warnings = []
        self.blockers = []
        suggestions = []

        prompt_lower = prompt.lower()

        # Check for celebrities/public figures
        for celebrity in self.CELEBRITY_INDICATORS:
            if celebrity in prompt_lower:
                self.blockers.append(f"Contains reference to public figure: '{celebrity}'")
                suggestions.append(f"Replace '{celebrity}' with a generic description like 'a person' or 'an entrepreneur'")

        # Check for brands
        for brand in self.BRAND_INDICATORS:
            if brand in prompt_lower:
                self.warnings.append(f"Contains brand name: '{brand}'")
                suggestions.append(f"Replace '{brand}' with a generic term")

        # Check for copyrighted characters
        for character in self.COPYRIGHTED_CHARACTERS:
            if character in prompt_lower:
                self.blockers.append(f"Contains copyrighted character: '{character}'")
                suggestions.append(f"Replace '{character}' with a generic description")

        # Check for violence
        for term in self.VIOLENCE_INDICATORS:
            if re.search(r'\b' + re.escape(term) + r'\b', prompt_lower):
                self.blockers.append(f"Contains violent content: '{term}'")
                suggestions.append(f"Remove or replace violent reference to '{term}'")

        # Check for inappropriate content
        for term in self.INAPPROPRIATE_CONTENT:
            if re.search(r'\b' + re.escape(term) + r'\b', prompt_lower):
                self.blockers.append(f"Contains inappropriate content: '{term}'")
                suggestions.append(f"Remove or replace inappropriate reference to '{term}'")

        # Check for dangerous activities
        for term in self.DANGEROUS_ACTIVITIES:
            if re.search(r'\b' + re.escape(term) + r'\b', prompt_lower):
                self.blockers.append(f"Contains dangerous content: '{term}'")
                suggestions.append(f"Remove reference to dangerous activity: '{term}'")

        # Determine risk level and safety
        if len(self.blockers) > 0:
            risk_level = "high"
            safe = False
        elif len(self.warnings) > 2:
            risk_level = "medium"
            safe = False
        elif len(self.warnings) > 0:
            risk_level = "medium"
            safe = True
        else:
            risk_level = "low"
            safe = True

        return {
            "safe": safe,
            "risk_level": risk_level,
            "warnings": self.warnings,
            "blockers": self.blockers,
            "suggestions": list(set(suggestions))  # Remove duplicates
        }

    def get_safe_alternative(self, prompt: str) -> str:
        """
        Attempt to automatically create a safer version of the prompt.
        Note: This is basic and may not catch all issues.
        """
        safe_prompt = prompt

        # Replace celebrities with generic terms
        replacements = {
            # Celebrities
            r'\belon musk\b': 'an entrepreneur',
            r'\btaylor swift\b': 'a singer',
            r'\bbeyonce\b': 'a performer',
            r'\btrump\b': 'a business person',
            r'\bobama\b': 'a leader',

            # Brands
            r'\bnike\b': 'athletic shoes',
            r'\btesla\b': 'an electric car',
            r'\biphone\b': 'a smartphone',
            r'\bmcdonald\'?s\b': 'a fast food restaurant',

            # Characters
            r'\bmickey mouse\b': 'a cartoon mouse',
            r'\bspider-?man\b': 'a superhero',
            r'\bdarth vader\b': 'a sci-fi character',
        }

        for pattern, replacement in replacements.items():
            safe_prompt = re.sub(pattern, replacement, safe_prompt, flags=re.IGNORECASE)

        return safe_prompt


def check_prompt_safety(prompt: str, verbose: bool = True) -> Tuple[bool, Dict]:
    """
    Convenience function to check prompt safety.

    Args:
        prompt: The prompt to check
        verbose: Whether to print detailed warnings

    Returns:
        Tuple of (is_safe, details_dict)
    """
    checker = PromptSafetyChecker()
    result = checker.check_prompt(prompt)

    if verbose:
        print(f"\n{'='*60}")
        print(f"PROMPT SAFETY CHECK")
        print(f"{'='*60}")
        print(f"Prompt: {prompt}")
        print(f"\nRisk Level: {result['risk_level'].upper()}")
        print(f"Safe to use: {'✅ YES' if result['safe'] else '❌ NO'}")

        if result['blockers']:
            print(f"\n⛔ BLOCKERS (will likely be filtered):")
            for blocker in result['blockers']:
                print(f"  - {blocker}")

        if result['warnings']:
            print(f"\n⚠️  WARNINGS (may cause issues):")
            for warning in result['warnings']:
                print(f"  - {warning}")

        if result['suggestions']:
            print(f"\n💡 SUGGESTIONS:")
            for suggestion in result['suggestions']:
                print(f"  - {suggestion}")

        if not result['safe']:
            alternative = checker.get_safe_alternative(prompt)
            if alternative != prompt:
                print(f"\n✨ SUGGESTED ALTERNATIVE:")
                print(f"  {alternative}")

        print(f"{'='*60}\n")

    return result['safe'], result


if __name__ == "__main__":
    # Test examples
    test_prompts = [
        "A peaceful sunset over the ocean",
        "Elon Musk walking on Mars",
        "Iron Man flying through New York City",
        "A chef preparing a gourmet meal",
        "Taylor Swift performing on stage with a guitar",
        "A violent fight scene with weapons",
        "A person in a Nike shirt running in the park",
    ]

    print("\n" + "="*60)
    print("TESTING PROMPT SAFETY CHECKER")
    print("="*60)

    for prompt in test_prompts:
        is_safe, details = check_prompt_safety(prompt)
