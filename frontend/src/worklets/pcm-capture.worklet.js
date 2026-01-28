/* AudioWorklet processor for capturing mic audio and downsampling to 16k PCM. */

class PcmCaptureProcessor extends AudioWorkletProcessor {
  constructor() {
    super()
    this._pending = []
    this._chunkSize = 320
  }

  process(inputs) {
    const input = inputs[0] && inputs[0][0]
    if (!input || input.length === 0) {
      return true
    }

    const targetRate = 16000
    const ratio = sampleRate / targetRate
    const outputLength = Math.max(1, Math.floor(input.length / ratio))
    const output = new Int16Array(outputLength)

    for (let i = 0; i < outputLength; i += 1) {
      const idx = i * ratio
      const idxLow = Math.floor(idx)
      const idxHigh = Math.min(idxLow + 1, input.length - 1)
      const frac = idx - idxLow
      const sample = input[idxLow] + (input[idxHigh] - input[idxLow]) * frac
      const clamped = Math.max(-1, Math.min(1, sample))
      output[i] = Math.round(clamped * 0x7fff)
    }

    for (let i = 0; i < output.length; i += 1) {
      this._pending.push(output[i])
    }

    while (this._pending.length >= this._chunkSize) {
      const chunk = this._pending.splice(0, this._chunkSize)
      const pcmChunk = Int16Array.from(chunk)
      this.port.postMessage(pcmChunk.buffer, [pcmChunk.buffer])
    }
    return true
  }
}

registerProcessor('pcm-capture', PcmCaptureProcessor)
