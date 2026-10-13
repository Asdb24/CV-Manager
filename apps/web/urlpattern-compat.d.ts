// Next 16.4 references these global names; Node 26 exposes the same strict standard types in node:url.
// Keep skipLibCheck false. Reuse official types instead of widening the declarations.
type URLPatternInput = import("node:url").URLPatternInput;
type URLPatternOptions = import("node:url").URLPatternOptions;
