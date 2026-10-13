/**
 * Algorithm Animation Engine
 * Replays server or client-computed algorithm step snapshots with interactive
 * playback controls (Play, Pause, Step Next, Step Prev, Reset, Speed).
 */

class AlgorithmAnimationPlayer {
  constructor(options = {}) {
    this.options = Object.assign({
      baseIntervalMs: 800,
      onStepChange: null,
      onComplete: null,
    }, options);

    this.steps = [];
    this.currentIndex = -1;
    this.isPlaying = false;
    this.timer = null;
    this.speedMultiplier = 1.0;
  }

  loadSteps(steps) {
    this.pause();
    this.steps = steps || [];
    this.currentIndex = -1;
    if (this.steps.length > 0) {
      this.goToStep(0);
    }
  }

  play() {
    if (this.steps.length === 0) return;
    if (this.isPlaying) return;

    if (this.currentIndex >= this.steps.length - 1) {
      this.currentIndex = -1;
    }
    this.isPlaying = true;
    this._scheduleNext();
  }

  pause() {
    this.isPlaying = false;
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  }

  togglePlay() {
    if (this.isPlaying) {
      this.pause();
    } else {
      this.play();
    }
    return this.isPlaying;
  }

  stepForward() {
    this.pause();
    if (this.currentIndex < this.steps.length - 1) {
      this.goToStep(this.currentIndex + 1);
    }
  }

  stepBackward() {
    this.pause();
    if (this.currentIndex > 0) {
      this.goToStep(this.currentIndex - 1);
    }
  }

  reset() {
    this.pause();
    if (this.steps.length > 0) {
      this.goToStep(0);
    }
  }

  setSpeed(multiplier) {
    this.speedMultiplier = Math.max(0.2, Number(multiplier) || 1.0);
    if (this.isPlaying) {
      this.pause();
      this.play();
    }
  }

  goToStep(index) {
    if (index < 0 || index >= this.steps.length) return;
    this.currentIndex = index;
    const currentStep = this.steps[this.currentIndex];

    if (this.options.onStepChange) {
      try {
        this.options.onStepChange(currentStep, this.currentIndex, this.steps.length);
      } catch (err) {
        console.error('[Animation Player] Error in onStepChange callback:', err);
      }
    }
  }

  getCurrentStep() {
    if (this.currentIndex >= 0 && this.currentIndex < this.steps.length) {
      return this.steps[this.currentIndex];
    }
    return null;
  }

  _scheduleNext() {
    if (!this.isPlaying) return;

    const delay = Math.max(80, this.options.baseIntervalMs / this.speedMultiplier);
    this.timer = setTimeout(() => {
      if (this.currentIndex < this.steps.length - 1) {
        this.goToStep(this.currentIndex + 1);
        this._scheduleNext();
      } else {
        this.pause();
        if (this.options.onComplete) {
          try {
            this.options.onComplete();
          } catch (err) {
            console.error('[Animation Player] Error in onComplete callback:', err);
          }
        }
      }
    }, delay);
  }
}

window.AlgorithmAnimationPlayer = AlgorithmAnimationPlayer;
