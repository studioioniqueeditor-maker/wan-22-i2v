# Google Veo RAI (Responsible AI) Filtering Guide

## What is RAI Filtering?

Google's Veo API includes Responsible AI safety filters that automatically block content that violates their usage policies. When content is blocked, you'll see an error like:

```
Content blocked by Responsible AI filters: Veo could not generate 1 videos based on the prompt provided.
```

## Common Reasons for Filtering

### 1. **People & Identifiable Individuals**
- ❌ Real people's names or likenesses
- ❌ Celebrities, politicians, public figures
- ❌ Identifiable minors (people under 18)
- ✅ Generic descriptions like "a person", "a woman", "a man"

### 2. **Violent or Dangerous Content**
- ❌ Violence, weapons, blood, injuries
- ❌ Dangerous activities or harmful scenarios
- ✅ Safe, everyday activities

### 3. **Sexual or Suggestive Content**
- ❌ Nudity, sexual content, or suggestive poses
- ❌ Revealing clothing or intimate scenarios
- ✅ Professional, appropriate attire and settings

### 4. **Copyrighted or Trademarked Content**
- ❌ Brand names, logos, trademarked characters
- ❌ Specific movie/TV show references
- ✅ Generic descriptions without brand names

### 5. **Misinformation or Deceptive Content**
- ❌ Fake news, misleading information
- ❌ Impersonation attempts
- ✅ Factual, educational content

## How to Fix RAI Filtering Issues

### Step 1: Review Your Prompt
Check your prompt for any of the blocked content types listed above:
- Remove specific names
- Replace brand references with generic terms
- Ensure content is safe and appropriate

### Step 2: Review Your Image
If using image-to-video:
- Ensure no identifiable people (unless they've given consent)
- No copyrighted characters or logos
- No inappropriate content

### Step 3: Rephrase for Safety

**Instead of:**
> "Elon Musk walking on Mars"

**Try:**
> "An astronaut walking on the surface of Mars"

---

**Instead of:**
> "Iron Man flying through New York City"

**Try:**
> "A person in a futuristic suit flying through a cityscape"

---

**Instead of:**
> "Taylor Swift performing on stage"

**Try:**
> "A singer performing on a concert stage"

## Debugging RAI Filtering

### 1. Simplify Your Prompt
Start with a very simple, generic prompt to test:
```
"A peaceful landscape with mountains and a lake"
```

If this works, gradually add back elements from your original prompt to identify what triggers the filter.

### 2. Check Your Image
If using image-to-video, try with a different image:
- Use AI-generated or stock images without people
- Avoid images with logos or brands
- Test with simple landscapes or objects

### 3. Review the Error Message
The error message may include a "support code" - save this for reference if you need to contact Google support.

## Best Practices for Avoiding Filters

1. **Use Generic Descriptions**
   - Instead of specific people: "a person", "a chef", "a scientist"
   - Instead of brands: "a smartphone", "a sports car", "a sneaker"

2. **Keep it Professional**
   - Focus on educational, creative, or business content
   - Avoid controversial topics

3. **Test Incrementally**
   - Start with simple prompts
   - Add complexity gradually
   - Identify what triggers filters

4. **Use Appropriate Images**
   - Stock photos with proper licenses
   - AI-generated content
   - Your own original photos (without identifiable people)

## Still Getting Filtered?

If you believe your content should not be filtered:

1. **Review Google's Usage Policies**
   - Check the latest Google Cloud AI/ML policies
   - Ensure compliance with terms of service

2. **Contact Google Support**
   - Include the support code from the error message
   - Describe your use case
   - Request a review

3. **Modify Your Approach**
   - Consider alternative prompts that achieve similar results
   - Use more abstract or artistic descriptions

## Example Safe Prompts

```
✅ "A serene sunset over ocean waves"
✅ "A futuristic city with flying vehicles"
✅ "A chef preparing a gourmet meal in a modern kitchen"
✅ "A scientist examining samples in a laboratory"
✅ "An athlete running on a track during sunrise"
✅ "A drone flying over a vineyard landscape"
✅ "Abstract colorful paint swirling in water"
✅ "A time-lapse of clouds moving across the sky"
```

## Configuration Options

The Veo API has a `person_generation` setting that controls how people are generated:
- `allow_adult`: Allows generation of adult figures (18+)
- `dont_allow`: Blocks all human generation

Currently set to: `allow_adult`

## Support

If you continue experiencing issues:
- Check application logs for detailed error messages
- Review the prompt and image carefully
- Try alternative phrasings
- Contact support with error codes

---

*Last Updated: 2025-12-26*
