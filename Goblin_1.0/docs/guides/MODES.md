# Modes: Offline vs Online

Goblin offers two processing modes: **Offline** (default, free) and **Online** (requires API key).

## Offline Mode (🔌)

Process files entirely on your computer using local AI models.

### How It Works
1. Models are downloaded once (~3-4 GB total)
2. Files are processed locally using your CPU/GPU
3. No internet connection required after model download
4. Results stay on your machine

### Audio Transcription
**Model:** faster-whisper (optimized Whisper implementation)

| Model | Download | Speed | Accuracy | RAM |
|-------|----------|-------|----------|-----|
| **tiny** | 39 MB | 10-20x real-time | Fair | 1 GB |
| **base** | 74 MB | 2-5x real-time | Good | 2 GB |
| **medium** | 769 MB | 0.5-1x real-time | Excellent | 5 GB |

*Real-time ratios: 1x = processing takes same time as audio duration*

**Recommended:** Use **base** for a good balance of speed and accuracy.

### Handwriting Recognition (OCR)
**Models:** TrOCR (Microsoft) + PaddleOCR

- **Download size:** ~1.5 GB
- **RAM required:** 2-3 GB
- **Speed:** 5-30 seconds per image
- **Accuracy:** Good for printed text, moderate for handwriting

**Tips for best results:**
- Use high-contrast images
- Ensure text is clearly legible
- Straighten tilted pages
- Remove background clutter
- Lighting should be even

### First-Time Setup
1. Click "Manuscrit" or "Audio" toggle
2. Choose offline mode
3. App downloads models (~1-2 hours, ~3 GB)
4. Models cached for future use

### Pros ✅
- **Free** — No API costs
- **Fast** — No network latency (for audio with GPU)
- **Privacy** — Data never leaves your computer
- **Offline** — Works anywhere, anytime
- **No limits** — Process unlimited files

### Cons ❌
- **Storage** — Requires 3-4 GB for models
- **RAM** — Needs 4+ GB RAM, 8+ GB recommended
- **Setup time** — Initial model download takes time
- **Accuracy** — Lower than online mode for handwriting
- **Speed** — Slow on CPU-only machines

---

## Online Mode (🌐)

Use OpenAI's powerful APIs for higher accuracy and speed.

### How It Works
1. Upload file to OpenAI servers
2. Process using Whisper or GPT-4o-mini
3. Download results
4. Requires internet connection

### Audio Transcription
**Model:** OpenAI Whisper API

- **Speed:** 10-30 seconds per minute of audio (much faster!)
- **Accuracy:** Excellent, especially with accents/background noise
- **Latency:** 1-2 seconds overhead
- **Cost:** ~$0.02 per hour of audio (~$0.002 per minute)

### Handwriting Recognition (OCR)
**Model:** OpenAI GPT-4o-mini

- **Speed:** 5-15 seconds per image
- **Accuracy:** Excellent, near-perfect for handwriting
- **Latency:** 1-2 seconds overhead
- **Cost:** ~$0.15 per 1M tokens (~$0.01-0.05 per image)

### Setup

1. **Get API key:**
   - Visit https://platform.openai.com/api-keys
   - Create a new key (or use existing)
   - Copy the key

2. **Add to Goblin:**
   - Click **🔑 Clé API** button in header
   - Paste your key
   - Key is saved securely locally

3. **Set default mode:**
   - Toggle "Audio" to "En ligne" (online)
   - Toggle "Manuscrit" to "En ligne" (online)
   - Start processing!

### Cost Estimation

| Usage | Files/Month | Est. Cost |
|-------|-------------|-----------|
| **Light** | 5-10 files | $0.01-0.10 |
| **Medium** | 20-30 files | $0.10-0.50 |
| **Heavy** | 100+ files | $0.50-5.00 |

*Estimates based on typical 1-2 minute audio or single-page images*

### Pros ✅
- **Fast** — Much faster than offline
- **Accurate** — Best-in-class models
- **Simple setup** — Just add API key
- **No storage** — No models to download
- **Low RAM** — Works on any machine

### Cons ❌
- **Internet required** — Needs connection
- **Costs money** — OpenAI API billing
- **Privacy** — Data sent to OpenAI servers
- **Rate limits** — May be throttled at high volume
- **Requires account** — OpenAI account setup

---

## Choosing Your Mode

### Use **Offline** if:
- ✅ You want free processing
- ✅ You value privacy
- ✅ You work offline frequently
- ✅ You're processing small batches
- ✅ You have 4+ GB RAM and good storage

### Use **Online** if:
- ✅ You need maximum speed
- ✅ You want best accuracy (especially handwriting)
- ✅ You process large batches regularly
- ✅ You're on a fast internet connection
- ✅ Cost per file ($0.01-0.05) is acceptable

### Hybrid Approach
Use **both** for different tasks:
- **Offline** for quick drafts and proof-of-concept
- **Online** for final, high-quality transcriptions
- Toggle as needed using the mode buttons

---

## Advanced Configuration

### Offline Model Selection
In the UI, choose model size:
- **tiny** — fastest, weakest accuracy
- **base** — recommended (good balance)
- **medium** — very good accuracy, much slower

### Smart Naming
When enabled in the UI, Goblin can rename saved transcriptions automatically with GPT-3.5-turbo using a short excerpt of the transcript. The rename happens after the file is already saved.

### Model Cache Location
Models stored in:
- **Windows:** `%USERPROFILE%\.cache\huggingface`
- **macOS/Linux:** `~/.cache/huggingface`

To delete models and free space:
```bash
# Clear all models
rm -rf ~/.cache/huggingface

# Or selectively delete:
rm -rf ~/.cache/huggingface/hub/models--openai*
rm -rf ~/.cache/huggingface/hub/models--paddle*
```

### API Key Security
- Stored in user config directory (encrypted)
- Never sent except to OpenAI servers
- Can be removed anytime via Goblin UI
- No key telemetry to third parties

---

## Switching Between Modes

Simply click the toggle buttons in the header:

**Audio Mode:**
- Click "Audio : Hors-ligne" → "Audio : En ligne" (or vice versa)

**Handwriting Mode:**
- Click "Manuscrit : En ligne" → "Manuscrit : Hors-ligne" (or vice versa)

Each mode can be configured independently.
