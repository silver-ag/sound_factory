# The Sound Factory

sound factory is like factorio or shapez but for sounds. it's effectively a slightly weird synth. oscillator components generate one-second
blocks of sound that you can then move around on conveyors, pass through various effects and ultimately deliver to an output.

### controls

- click on an empty space to create an instance of the currently selected component type
- click on the icon in the top left showing the currently selected component type to select a different one
- click on a component to rotate it
- right click on a component to destroy it
- <kbd>shift</kbd> click on a component to edit its settings

note that components (except those that consume their input and produce no output) have a direction in which they send blocks (indicated by
an arrow), but don't care which direction they receive them from. in the case where several different blocks are directed onto one space
things typically settle into a consistent loop where each source is used in turn, but there's no actual guarantee of this.
