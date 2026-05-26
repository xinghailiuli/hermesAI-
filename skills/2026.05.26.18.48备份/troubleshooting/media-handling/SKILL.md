---
name: media-handling
description: Receive, save, organize, and send media files (stickers, images, GIFs) sent by users through messaging platforms.
triggers:
  - User sends images/stickers/GIFs they want saved for reuse
  - User asks to "save" or "store" media files
  - Need to send media back to user via MEDIA: syntax
  - Building or managing a sticker/emote collection for chat
---

# Media Handling

## Image Cache Location

When users send images through QQ (or other platforms), Hermes Agent receives them and caches them at:

```
/home/admin/.hermes/image_cache/img_*.jpg
```

Files are named with a hash (e.g., `img_c9124ad87db5.jpg`). These are temporary — copy them out to a permanent location if you want to keep them.

## Saving User-Sent Media

When the user sends you media that they want to keep and reuse:

1. **Identify the files** — use `ls /home/admin/.hermes/image_cache/` sorted by modification time
2. **Copy to a permanent directory** — e.g., `/home/admin/stickers/`
3. **Batch copy when many files arrive** — use wildcard patterns:

```bash
# Copy all recently cached images to stickers dir
cp /home/admin/.hermes/image_cache/img_*.jpg /home/admin/stickers/
```

## Sending Media Back

Use the `MEDIA:` prefix in your response message:

```
MEDIA:/home/admin/stickers/blush_0.gif
```

This sends the file as a native media attachment on the user's platform (photo for images, document for other files).

## Sticker Collection Convention

For this user:
- **Sticker directory**: `/home/admin/stickers/`
- **Naming**: Keep original filenames from cache (hashed) for traceability, or rename with descriptive labels (e.g., `blush_0.gif`, `angry_0.png`)
- **Preference**: User wants their OWN curated sticker collection (anime-style / 二次元表情包), NOT AI-generated images

## Pitfalls

- The image cache is temporary — always copy files out, don't reference them in place
- User may send 50+ images at once; handle the batch efficiently with wildcard cp
- User explicitly dislikes AI-generated/Pillow-drawn images — only use their provided media or web-sourced images
- When the user says "把我的表情包下载下来" they mean copy from the Hermes image cache, not download from the internet
