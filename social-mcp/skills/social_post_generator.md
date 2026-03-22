# Skill: social_post_generator

Generate platform-optimized social media content and save drafts to the vault for human approval.

## Trigger
When the user asks to create, write, draft, or generate a social media post.

## Workflow

1. **Identify target platform(s)**: Facebook, Instagram, Twitter, LinkedIn, or all.
2. **Adapt content per platform**:
   - **Twitter**: Max 280 chars. Punchy, concise. 2-3 hashtags max.
   - **LinkedIn**: Professional tone, 500-2000 chars. Industry hashtags. CTA at end.
   - **Facebook**: Conversational, 100-500 chars. Emojis OK. Link preview friendly.
   - **Instagram**: Visual-first caption, 100-300 chars. 5-10 hashtags. Emoji-rich.
3. **Use MCP tools to save drafts**:
   - `fb_generate_post` for Facebook
   - `ig_generate_post` for Instagram
   - `tw_generate_post` for Twitter
   - `li_generate_post` for LinkedIn
4. **Present all drafts** to the user for review.
5. **On approval**, use `*_publish_post` or `*_schedule_post` to post.

## Example Usage

User: "Create a post about our new AI product launch"

Response:
- Generate 4 platform-specific drafts
- Save each to vault `/Social/Drafts/`
- Present for approval
- Publish approved ones

## Rules
- NEVER publish without user approval (use draft mode first)
- Always include vault file paths in response
- Respect platform character limits
- Include relevant hashtags per platform
