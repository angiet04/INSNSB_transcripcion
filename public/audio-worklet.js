class PCM16Processor extends AudioWorkletProcessor {
  constructor() {
    super();
    this.buffer = [];
    this.chunkSize = 3200;
  }
  process(inputs) {
    const input = inputs[0][0];
    if (!input) return true;
    const pcm16 = new Int16Array(input.length);
    for (let i = 0; i < input.length; i++) {
      const s = Math.max(-1, Math.min(1, input[i]));
      pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
    }
    const bytes = new Uint8Array(pcm16.buffer);
    this.buffer.push(bytes);
    let total = this.buffer.reduce((a,b) => a + b.length, 0);
    while (total >= this.chunkSize) {
      const chunk = new Uint8Array(this.chunkSize);
      let offset = 0;
      while (offset < this.chunkSize && this.buffer.length) {
        const head = this.buffer[0];
        const need = this.chunkSize - offset;
        const take = Math.min(need, head.length);
        chunk.set(head.subarray(0, take), offset);
        offset += take;
        if (take === head.length) this.buffer.shift();
        else this.buffer[0] = head.subarray(take);
      }
      total -= this.chunkSize;
      this.port.postMessage({type:'pcm16', chunk: chunk.buffer}, [chunk.buffer]);
    }
    return true;
  }
}
registerProcessor('pcm16-worklet', PCM16Processor);
