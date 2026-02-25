<script>
  let { variant = "default", size = "default", class: className = "", ...rest } = $props();

  const base =
    "inline-flex items-center justify-center rounded-md text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-400 focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 ring-offset-white dark:ring-offset-slate-950";

  const variants = {
    default: "bg-slate-900 text-slate-50 hover:bg-slate-900/90 dark:bg-slate-50 dark:text-slate-900 dark:hover:bg-slate-50/90",
    secondary:
      "bg-slate-100 text-slate-900 hover:bg-slate-100/80 dark:bg-slate-800 dark:text-slate-50 dark:hover:bg-slate-800/80",
    outline:
      "border border-slate-200 bg-white text-slate-900 hover:bg-slate-100 dark:border-slate-800 dark:bg-slate-950 dark:text-slate-50 dark:hover:bg-slate-800",
  };

  const sizes = {
    default: "h-10 px-4 py-2",
    sm: "h-9 rounded-md px-3",
    lg: "h-11 rounded-md px-8",
  };

  const classes = $derived(() => {
    let v = variants.default;
    if (variant === "secondary") v = variants.secondary;
    if (variant === "outline") v = variants.outline;

    let s = sizes.default;
    if (size === "sm") s = sizes.sm;
    if (size === "lg") s = sizes.lg;

    return [base, v, s, className].filter(Boolean).join(" ");
  });
</script>

<button class={classes} {...rest}>
  <slot />
</button>
