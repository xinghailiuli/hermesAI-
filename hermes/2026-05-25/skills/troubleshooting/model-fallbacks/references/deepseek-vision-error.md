# Vision Rejection Signature (DeepSeek)

Error returned by DeepSeek API when `vision_analyze` sends an image:

```
Error code: 400 - {'error': {'message': 'Failed to deserialize the JSON body into the target type: messages[0]: unknown variant `image_url`, expected `text` at line 1 column XXXXX', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}
```

The key diagnostic phrase is: **`unknown variant 'image_url', expected 'text'`**

This means the provider's API does not accept multipart image+text messages. The model has no vision capability. Immediate action: stop retrying vision, move to fallback chain.

## Confirmed models lacking vision (as of 2025-05):
- `deepseek-v4-pro` via DeepSeek API — returns the above error

## Note
Even when vision_analyze fails with this error, the `file` command still works to confirm the image is valid:
```
$ file image.jpg
image.jpg: JPEG image data, ... 864x1920, components 3
```
This confirms the image isn't corrupted — the model just can't see it.
