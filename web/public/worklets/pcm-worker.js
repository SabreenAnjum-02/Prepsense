class PCMProcessor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.bufferSize = 4096;
    this.buffer = new Float32Array(this.bufferSize);
    this.bufferIndex = 0;
  }

  process(inputs, outputs, parameters) {
    const input = inputs[0];
    if (input && input.length > 0) {
      const float32Data = input[0];
      
      for (let i = 0; i < float32Data.length; i++) {
        this.buffer[this.bufferIndex++] = float32Data[i];
        
        if (this.bufferIndex >= this.bufferSize) {
          const int16Data = new Int16Array(this.bufferSize);
          for (let j = 0; j < this.bufferSize; j++) {
            let s = Math.max(-1, Math.min(1, this.buffer[j]));
            int16Data[j] = s < 0 ? s * 0x8000 : s * 0x7FFF;
          }
          this.port.postMessage(int16Data.buffer, [int16Data.buffer]);
          this.bufferIndex = 0;
        }
      }
    }
    return true;
  }
}
registerProcessor('pcm-processor', PCMProcessor);
