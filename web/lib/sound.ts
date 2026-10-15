// Original UI sounds synthesised with the Web Audio API: no audio files, no
// licensing questions. Each sound is a couple of short oscillator blips with a
// fast envelope, which is roughly how console menu sounds feel.

export type UiSound = "move" | "select" | "back";

let ctx: AudioContext | null = null;

function audio(): AudioContext | null {
  if (typeof window === "undefined") return null;
  if (!ctx) {
    const Ctor = window.AudioContext;
    if (!Ctor) return null;
    ctx = new Ctor();
  }
  return ctx;
}

function blip(ac: AudioContext, freq: number, start: number, dur: number, type: OscillatorType, gain: number): void {
  const osc = ac.createOscillator();
  const amp = ac.createGain();
  osc.type = type;
  osc.frequency.setValueAtTime(freq, start);
  amp.gain.setValueAtTime(0, start);
  amp.gain.linearRampToValueAtTime(gain, start + 0.005);
  amp.gain.exponentialRampToValueAtTime(0.0001, start + dur);
  osc.connect(amp).connect(ac.destination);
  osc.start(start);
  osc.stop(start + dur + 0.02);
}

export function playSound(kind: UiSound): void {
  const ac = audio();
  if (!ac) return;
  if (ac.state === "suspended") void ac.resume();
  const t = ac.currentTime;
  if (kind === "move") {
    blip(ac, 880, t, 0.04, "square", 0.025);
  } else if (kind === "select") {
    blip(ac, 660, t, 0.06, "square", 0.04);
    blip(ac, 990, t + 0.05, 0.09, "square", 0.04);
  } else {
    blip(ac, 520, t, 0.06, "triangle", 0.06);
    blip(ac, 330, t + 0.05, 0.1, "triangle", 0.06);
  }
}
